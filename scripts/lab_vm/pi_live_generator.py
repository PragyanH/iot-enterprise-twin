#!/usr/bin/env python3
"""Fallback live telemetry generator for PI-001.

Pushes realistic operational packet streams to the Aegis ingestion API when physical Pi is offline.
"""

import argparse
import json
import math
import time
import urllib.request
import sys

def run_telemetry_loop(api_url: str = "http://localhost:8000", interval: float = 1.5):
    endpoint = f"{api_url}/api/v1/telemetry/windows"
    print(f"[PI_LIVE_GENERATOR] Starting live telemetry stream to {endpoint} (interval: {interval}s)")
    tick = 0
    while True:
        try:
            tick += 1
            phase = tick / 4.0
            packet_size = max(0.02, 0.064 + math.sin(phase) * 0.005)
            iat = max(0.01, 0.300 + math.cos(phase * 0.8) * 0.020)
            entropy = max(0.1, min(0.9, 0.45 + math.sin(phase * 0.5) * 0.05))
            symmetry = max(0.1, min(0.9, 0.50 + math.cos(phase * 0.3) * 0.04))

            payload = {
                "device_id": "PI-001",
                "source": "pi",
                "sensor": "aegis-live-generator",
                "points": [{
                    "packet_size": packet_size,
                    "iat": iat,
                    "payload_entropy": entropy,
                    "flow_symmetry": symmetry
                }]
            }

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                pass
            time.sleep(interval)
        except KeyboardInterrupt:
            print("[PI_LIVE_GENERATOR] Stopped cleanly.")
            break
        except Exception as exc:
            print(f"[PI_LIVE_GENERATOR] Telemetry loop error: {exc}", file=sys.stderr)
            time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PI-001 Live Telemetry Generator")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI backend base URL")
    parser.add_argument("--interval", type=float, default=1.5, help="Telemetry push interval in seconds")
    args = parser.parse_args()
    run_telemetry_loop(args.api_url, args.interval)
