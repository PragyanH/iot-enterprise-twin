#!/usr/bin/env python3
"""Attack simulation script for PI-001.

Triggers a controlled SYN flood attack simulation against PI-001 via API or local lab generator.
"""

import argparse
import json
import urllib.request
import sys

def trigger_attack(api_url: str = "http://localhost:8000"):
    endpoint = f"{api_url}/api/v1/demo/replay/pi_syn?speed=4"
    print(f"[ATTACK.PY] Launching SYN flood attack against PI-001 -> {endpoint}")
    try:
        req = urllib.request.Request(endpoint, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"[ATTACK.PY] Attack launched successfully! Response: {data}")
    except Exception as exc:
        print(f"[ATTACK.PY] Error launching attack via API: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger attack against PI-001")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI backend base URL")
    args = parser.parse_args()
    trigger_attack(args.api_url)
