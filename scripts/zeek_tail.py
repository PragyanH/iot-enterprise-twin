"""Tail Aegis Zeek JSON counters and post normalized windows to FastAPI."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


def post_window(
    api_url: str,
    record: dict[str, object],
    job_id: str,
    device_id: str,
    session_id: str,
) -> None:
    payload = {
        "device_id": device_id,
        "source": "live_hardware",
        "sensor": "zeek",
        "session_id": session_id,
        "sequence_seconds": 20,
        "attack_job_id": job_id,
        "points": [
            {
                "packet_size": float(record.get("mean_packet_size", 420.0)),
                "iat": float(record.get("mean_iat", 0.12)),
                "flow_symmetry": float(record.get("flow_symmetry", 0.92)),
                "syn_rate": float(record.get("syn", 0.0)),
                "syn_ack_rate": float(record.get("syn_ack", 0.0)),
                "ack_rate": float(record.get("ack", 0.0)),
                "incomplete_ratio": float(record.get("incomplete_ratio", 0.0)),
                "handshake_completion_ratio": float(record.get("handshake_completion_ratio", 1.0)),
                "unique_sources": float(record.get("unique_sources", 1.0)),
                "unique_destination_ports": float(record.get("unique_destination_ports", 1.0)),
                "rejected_connections": float(record.get("rejected", 0.0)),
                "reset_connections": float(record.get("resets", 0.0)),
                "orig_packets": float(record.get("orig_packets", 0.0)),
                "resp_packets": float(record.get("resp_packets", 0.0)),
                "orig_bytes": float(record.get("orig_bytes", 0.0)),
                "resp_bytes": float(record.get("resp_bytes", 0.0)),
                "connection_duration_mean": float(record.get("mean_duration", 0.0)),
                "ssh_attempts": float(record.get("ssh_attempts", 0.0)),
                "ssh_failures": float(record.get("ssh_failures", 0.0)),
                "capture_loss": float(record.get("capture_loss", 0.0)),
            }
        ],
    }
    outbound = request.Request(
        f"{api_url.rstrip('/')}/api/v1/telemetry/windows",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(outbound, timeout=2.0) as response:
        response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path, help="Zeek aegis_live.log written in JSON format")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--job-id", default="pi-syn-demo")
    parser.add_argument("--device-id", default="PI-001")
    parser.add_argument(
        "--session-id",
        default=f"zeek-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}",
    )
    args = parser.parse_args()

    with args.log.open("r", encoding="utf-8") as handle:
        handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                post_window(args.api, json.loads(line), args.job_id, args.device_id, args.session_id)
            except (ValueError, OSError) as exc:
                print(f"telemetry forwarding error: {exc}")


if __name__ == "__main__":
    main()
