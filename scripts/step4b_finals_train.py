from __future__ import annotations

import hashlib, json, random, shutil, statistics, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services" / "backend" / "api"
sys.path[:0] = [str(ROOT), str(API)]

import numpy as np
import torch
import xgboost as xgb
from sklearn.metrics import accuracy_score, f1_score, recall_score
from torch.utils.data import DataLoader, TensorDataset

from app.ml.hybrid_engine import PI_FEATURES, load_profiles
from app.ml.temporal_vae import LSTMTemporalVAE, temporal_vae_loss
from scripts.train_hybrid_models import synthetic_rows

DATA = ROOT / "data" / "finals-capture" / "pi_sessions.jsonl"
MODEL = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
BACKUP = MODEL.parent / f"v1-pre-step4b-{STAMP}"
LABELS = {"normal": 0, "syn_flood": 1, "port_scan": 2, "ssh_bruteforce": 3}

FLOOR = {
    "packet_size": 5.0, "iat": .03, "flow_symmetry": .03,
    "syn_rate": .5, "syn_ack_rate": .5, "ack_rate": .5,
    "incomplete_ratio": .02, "handshake_completion_ratio": .02,
    "unique_sources": .5, "unique_destination_ports": .5,
    "rejected_connections": .5, "reset_connections": .5,
    "orig_packets": 1.0, "resp_packets": 1.0,
    "ssh_attempts": .5, "ssh_failures": .5,
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def read_rows() -> list[dict]:
    out = []
    with DATA.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return [r for r in out if r.get("source") == "live_hardware"]

def calibrate_baseline(rows: list[dict]) -> None:
    path = MODEL / "baselines.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    pi = next(d for d in payload["devices"] if d["device_id"] == "PI-001")
    normal = [r for r in rows if r["label"] == "normal"]
    unavailable = {x for r in normal for x in (r.get("unavailable_features") or [])}
    by_session = defaultdict(list)
    for r in normal:
        by_session[str(r["session_id"])].extend(r["points"])

    for feature in pi["feature_names"]:
        if feature in unavailable:
            continue
        session_centers, all_values = [], []
        for points in by_session.values():
            vals = [float(p.get(feature, 0.0)) for p in points]
            if vals:
                session_centers.append(float(np.median(vals)))
                all_values.extend(vals)
        if not all_values:
            continue
        center = float(np.median(session_centers))
        spread = float(np.quantile(np.abs(np.asarray(all_values) - center), .95) / 2.0)
        pi["baseline"][feature] = round(center, 8)
        pi["deviation"][feature] = round(max(spread, FLOOR.get(feature, 1e-3)), 8)

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def norm(row: dict, profile) -> list[list[float]]:
    return [[
        (float(p.get(f, profile.baseline[f])) - profile.baseline[f]) /
        max(profile.deviation[f], 1e-6)
        for f in profile.feature_names
    ] for p in row["points"][-20:]]

def train_vae(rows: list[dict]) -> dict:
    profile = load_profiles(MODEL / "baselines.json")["PI-001"]
    normal = [r for r in rows if r["label"] == "normal"]
    sessions = sorted({str(r["session_id"]) for r in normal})
    held = sessions[-1]
    train = [r for r in normal if str(r["session_id"]) != held]
    cal = [r for r in normal if str(r["session_id"]) == held]

    xtr = np.asarray([norm(r, profile) for r in train], dtype=np.float32)
    xcal = np.asarray([norm(r, profile) for r in cal], dtype=np.float32)

    random.seed(42); np.random.seed(42); torch.manual_seed(42)
    model = LSTMTemporalVAE(input_size=len(profile.feature_names))
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(TensorDataset(torch.from_numpy(xtr)),
                        batch_size=min(32, len(xtr)), shuffle=True)
    model.train()
    for _ in range(30):
        for (batch,) in loader:
            opt.zero_grad()
            loss = temporal_vae_loss(model(batch), batch)
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        cal_err, _, _ = model.anomaly_components(torch.from_numpy(xcal))
    q995 = float(np.quantile(cal_err.numpy(), .995))
    threshold = max(q995 / .20, 1e-6)
    torch.save(model.state_dict(), MODEL / "temporal_vae_pi.pt")

    cp = MODEL / "calibration.json"
    cfg = json.loads(cp.read_text(encoding="utf-8"))
    cfg.setdefault("vae_thresholds", {})["pi"] = threshold
    cfg["pi_physical_calibration"] = {
        "method": "normal-only, held-out physical session",
        "held_out_session": held,
        "train_sessions": len(sessions) - 1,
        "train_windows": len(train),
        "calibration_windows": len(cal),
        "clean_q995_error": q995,
        "threshold": threshold,
    }
    cp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg["pi_physical_calibration"]

def canonical_latest(point: dict) -> dict:
    policy = json.loads((MODEL / "canonicalization.json").read_text(encoding="utf-8"))["severe_syn"]
    out = {f: float(point.get(f, 0.0)) for f in PI_FEATURES}
    if (out["syn_rate"] >= float(policy["syn_rate_min"])
        and out["incomplete_ratio"] >= float(policy["incomplete_ratio_min"])
        and out["handshake_completion_ratio"] <= float(policy["handshake_completion_ratio_max"])):
        out["syn_rate"] = float(policy["syn_rate_value"])
        out["incomplete_ratio"] = float(policy["incomplete_ratio_value"])
        out["handshake_completion_ratio"] = float(policy["handshake_completion_ratio_value"])
    return out

def train_classifier(rows: list[dict]) -> dict:
    physical = []
    for r in rows:
        if r["label"] in {"normal", "syn_flood"}:
            c = dict(r); c["source"] = "pi"; physical.append(c)

    secondary = [r for r in synthetic_rows()
                 if r.get("source") == "pi"
                 and r.get("label") in {"port_scan", "ssh_bruteforce"}]
    data = physical + secondary

    held = {}
    for label in LABELS:
        sessions = sorted({str(r["session_id"]) for r in data if r["label"] == label})
        if len(sessions) < 2:
            raise RuntimeError(f"not enough sessions for {label}")
        held[label] = sessions[-1]

    train = [r for r in data if str(r["session_id"]) != held[r["label"]]]
    test = [r for r in data if str(r["session_id"]) == held[r["label"]]]

    def matrix(items):
        x, y = [], []
        for r in items:
            p = canonical_latest(r["points"][-1])
            x.append([p[f] for f in PI_FEATURES])
            y.append(LABELS[r["label"]])
        return np.asarray(x, np.float32), np.asarray(y, np.int64)

    xtr, ytr = matrix(train); xte, yte = matrix(test)
    counts = Counter(ytr.tolist())
    w = np.asarray([len(ytr)/(4*counts[int(y)]) for y in ytr], np.float32)

    clf = xgb.XGBClassifier(
        n_estimators=180, max_depth=5, learning_rate=.06,
        subsample=.9, colsample_bytree=.9,
        objective="multi:softprob", num_class=4, random_state=42
    )
    clf.fit(xtr, ytr, sample_weight=w)
    clf.save_model(MODEL / "xgboost.json")
    pred = clf.predict(xte)

    recalls = {}
    for label, cid in LABELS.items():
        mask = yte == cid
        recalls[label] = round(float(np.mean(pred[mask] == cid)), 6)

    return {
        "accuracy": round(float(accuracy_score(yte, pred)), 6),
        "macro_f1": round(float(f1_score(yte, pred, average="macro")), 6),
        "syn_flood_recall": round(float(recall_score(yte == 1, pred == 1)), 6),
        "per_class_recall": recalls,
        "held_out_sessions": held,
        "train_windows": len(train),
        "test_windows": len(test),
    }

def main():
    rows = read_rows()
    sessions = {
        label: len({str(r["session_id"]) for r in rows if r["label"] == label})
        for label in ("normal", "syn_flood")
    }
    windows = {
        label: sum(r["label"] == label for r in rows)
        for label in ("normal", "syn_flood")
    }
    if sessions["normal"] < 5 or sessions["syn_flood"] < 5:
        raise SystemExit(f"need >=5 sessions/class, got {sessions}")

    shutil.copytree(MODEL, BACKUP)
    try:
        calibrate_baseline(rows)
        vae = train_vae(rows)
        clf = train_classifier(rows)

        metrics = {
            **clf,
            "status": "trained",
            "source": "real PI-001 live_hardware normal/SYN + controlled synthetic secondary classes",
            "training_epochs": 30,
            "physical_sessions": sessions,
            "physical_windows": windows,
            "pi_vae": vae,
            "dataset_sha256": sha(DATA),
            "metric_scope": "session-held-out finals calibration; physical metrics cover PI-001 normal/SYN",
        }
        (MODEL/"metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        mp = MODEL/"manifest.json"
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        manifest["finals_calibration"] = {
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "dataset": "data/finals-capture/pi_sessions.jsonl",
            "dataset_sha256": sha(DATA),
            "physical_sessions": sessions,
            "split": "label-stratified session holdout",
            "pi_vae_normal_only": True,
            "xgboost_physical_classes": ["normal", "syn_flood"],
            "xgboost_controlled_secondary_classes": ["port_scan", "ssh_bruteforce"],
        }
        mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        artifacts = [
            "baselines.json","calibration.json","temporal_vae_pi.pt","temporal_vae_mock.pt",
            "xgboost.json","metrics.json","manifest.json","canonicalization.json","intelligence.json"
        ]
        freeze = {
            "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "backup": str(BACKUP),
            "dataset_sha256": sha(DATA),
            "artifact_sha256": {name: sha(MODEL/name) for name in artifacts},
        }
        (MODEL/"finals_freeze.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")

        print(json.dumps({
            "status": "STEP4B_TRAINED_AND_FROZEN",
            "backup": str(BACKUP),
            "physical_sessions": sessions,
            "physical_windows": windows,
            "classifier": clf,
            "pi_vae": vae,
            "freeze_file": str(MODEL/"finals_freeze.json"),
        }, indent=2))
    except Exception:
        # Restore original model package if anything in Step 4B fails.
        shutil.rmtree(MODEL)
        shutil.copytree(BACKUP, MODEL)
        raise

if __name__ == "__main__":
    main()
