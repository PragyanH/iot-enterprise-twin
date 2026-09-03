"""Train frozen LSTM-VAE and XGBoost artifacts for the hackathon topology.

Input JSONL rows use the telemetry API shape plus `label` and `session_id`.
Use `--synthetic-demo` to bootstrap artifacts before real captures are ready.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "backend" / "api"
sys.path.insert(0, str(API_ROOT))

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, recall_score
from torch.utils.data import DataLoader, TensorDataset
import xgboost as xgb

from app.domain.telemetry import TelemetryPoint
from app.ml.hybrid_engine import DEFAULT_PROFILES, MOCK_FEATURES, PI_FEATURES
from app.ml.temporal_vae import LSTMTemporalVAE, temporal_vae_loss


LABELS = {"normal": 0, "syn_flood": 1, "port_scan": 2, "ssh_bruteforce": 3}


def normalized_sequence(points: list[dict[str, float]], source: str, device_id: str) -> list[list[float]]:
    profile = DEFAULT_PROFILES[device_id]
    features = PI_FEATURES if source == "pi" else MOCK_FEATURES
    sequence = points[-20:]
    while len(sequence) < 20:
        sequence.insert(0, sequence[0])
    return [
        [
            (float(point.get(feature, profile.baseline[feature])) - profile.baseline[feature])
            / max(profile.deviation[feature], 1e-6)
            for feature in features
        ]
        for point in sequence
    ]


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def synthetic_rows(seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    for device_id, profile in DEFAULT_PROFILES.items():
        for sample in range(240):
            points = []
            for _ in range(20):
                point = TelemetryPoint()
                for feature in profile.feature_names:
                    setattr(point, feature, rng.gauss(profile.baseline[feature], profile.deviation[feature] * 0.35))
                points.append(point.to_dict())
            rows.append(
                {
                    "device_id": device_id,
                    "source": profile.source,
                    "label": "normal",
                    "session_id": f"synthetic-normal-{sample // 40}",
                    "points": points,
                }
            )

    pi = DEFAULT_PROFILES["PI-001"]
    for label in ("syn_flood", "port_scan", "ssh_bruteforce"):
        for sample in range(240):
            points = []
            for _ in range(20):
                point = TelemetryPoint()
                for feature in pi.feature_names:
                    setattr(point, feature, rng.gauss(pi.baseline[feature], pi.deviation[feature] * 0.4))
                if label == "syn_flood":
                    point.syn_rate = rng.uniform(120, 420)
                    point.syn_ack_rate = rng.uniform(0, 8)
                    point.ack_rate = rng.uniform(0, 6)
                    point.incomplete_ratio = rng.uniform(0.75, 0.99)
                    point.handshake_completion_ratio = rng.uniform(0.0, 0.25)
                elif label == "port_scan":
                    point.unique_destination_ports = rng.uniform(25, 180)
                    point.rejected_connections = rng.uniform(15, 150)
                else:
                    point.ssh_attempts = rng.uniform(10, 80)
                    point.ssh_failures = rng.uniform(8, 75)
                points.append(point.to_dict())
            rows.append(
                {
                    "device_id": "PI-001",
                    "source": "pi",
                    "label": label,
                    "session_id": f"synthetic-{label}-{sample // 40}",
                    "points": points,
                }
            )
    rng.shuffle(rows)
    return rows


def train_vae(rows: list[dict[str, Any]], source: str, output: Path, epochs: int) -> float:
    normal_rows = [row for row in rows if row["source"] == source and row["label"] == "normal"]
    sequences = np.asarray(
        [normalized_sequence(row["points"], source, row["device_id"]) for row in normal_rows],
        dtype=np.float32,
    )
    torch.manual_seed(42)
    model = LSTMTemporalVAE(input_size=sequences.shape[-1])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(TensorDataset(torch.from_numpy(sequences)), batch_size=64, shuffle=True)
    model.train()
    for _ in range(epochs):
        for (batch,) in loader:
            optimizer.zero_grad()
            loss = temporal_vae_loss(model(batch), batch)
            loss.backward()
            optimizer.step()
    torch.save(model.state_dict(), output / f"temporal_vae_{source}.pt")
    model.eval()
    with torch.no_grad():
        scores, _, _ = model.anomaly_components(torch.from_numpy(sequences))
    return float(np.quantile(scores.numpy(), 0.995))


def train_classifier(rows: list[dict[str, Any]], output: Path) -> dict[str, float]:
    pi_rows = [row for row in rows if row["source"] == "pi" and row["label"] in LABELS]
    sessions = sorted({str(row["session_id"]) for row in pi_rows})
    held_out = set(sessions[:: max(1, len(sessions) // 5)])
    train_rows = [row for row in pi_rows if row["session_id"] not in held_out]
    test_rows = [row for row in pi_rows if row["session_id"] in held_out]
    if not test_rows:
        split = max(1, len(pi_rows) // 5)
        train_rows, test_rows = pi_rows[split:], pi_rows[:split]

    def matrix(items: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
        features = []
        labels = []
        for row in items:
            latest = row["points"][-1]
            features.append([float(latest.get(feature, 0.0)) for feature in PI_FEATURES])
            labels.append(LABELS[row["label"]])
        return np.asarray(features, dtype=np.float32), np.asarray(labels, dtype=np.int64)

    x_train, y_train = matrix(train_rows)
    x_test, y_test = matrix(test_rows)
    classifier = xgb.XGBClassifier(
        n_estimators=180,
        max_depth=5,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=4,
        random_state=42,
    )
    classifier.fit(x_train, y_train)
    classifier.save_model(output / "xgboost.json")
    predictions = classifier.predict(x_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
        "macro_f1": round(float(f1_score(y_test, predictions, average="macro")), 6),
        "syn_flood_recall": round(float(recall_score(y_test == 1, predictions == 1)), 6),
        "held_out_sessions": len(held_out),
        "train_windows": len(train_rows),
        "test_windows": len(test_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Session-labeled telemetry JSONL")
    parser.add_argument("--synthetic-demo", action="store_true", help="Generate controlled hackathon training data")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "model-store" / "aegis-hybrid-trust" / "v1",
    )
    args = parser.parse_args()
    if not args.synthetic_demo and args.input is None:
        parser.error("provide --input or --synthetic-demo")

    rows = synthetic_rows() if args.synthetic_demo else load_rows(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    pi_threshold = train_vae(rows, "pi", args.output, args.epochs)
    mock_threshold = train_vae(rows, "mock", args.output, args.epochs)
    metrics = train_classifier(rows, args.output)
    calibration = {"vae_thresholds": {"pi": pi_threshold, "mock": mock_threshold}}
    (args.output / "calibration.json").write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    metrics.update(
        {
            "status": "trained",
            "source": "synthetic-demo" if args.synthetic_demo else str(args.input),
            "training_epochs": args.epochs,
            "demo_scenario_success_rate": None,
            "metric_scope": "session-held-out training metrics; run the separate demo acceptance suite",
        }
    )
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
