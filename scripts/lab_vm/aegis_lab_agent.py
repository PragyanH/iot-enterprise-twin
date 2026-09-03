"""VM-side attack controller for the registered `pi-syn-demo` job only.

Implements exactly the contract `AttackControllerStopProvider`
(`services/backend/api/app/services/remediation.py`) already speaks:

    GET  /health
    GET  /jobs/pi-syn-demo/status
    POST /jobs/pi-syn-demo/stop      (Bearer auth)
    POST /jobs/pi-syn-demo/start     (Bearer auth, disabled by default)

There is no generic command/shell surface. The child process is always
`pi_syn_demo.py` invoked with a fixed argument list built from local
environment configuration; request bodies are read and discarded, never
executed. Run this only inside the isolated, team-owned VMware lab VM.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


JOB_ID = "pi-syn-demo"
SCRIPT_PATH = Path(__file__).resolve().parent / "pi_syn_demo.py"


class JobManager:
    """Owns exactly one child `pi_syn_demo.py` process for the pi-syn-demo job."""

    def __init__(
        self,
        *,
        target_ip: str,
        port: int,
        rate: float,
        duration_seconds: float,
        script_path: Path = SCRIPT_PATH,
        python_executable: str | None = None,
        popen: Any = None,
    ) -> None:
        self.target_ip = target_ip
        self.port = port
        self.rate = rate
        self.duration_seconds = duration_seconds
        self.script_path = script_path
        self.python_executable = python_executable or sys.executable
        self._popen = popen or subprocess.Popen
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = self._process is not None and self._process.poll() is None
            return {
                "job_id": JOB_ID,
                "running": running,
                "pid": self._process.pid if running and self._process else None,
                "target_ip": self.target_ip,
                "port": self.port,
                "rate": self.rate,
            }

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return {"already_running": True, "job_id": JOB_ID, "pid": self._process.pid}
            if not self.target_ip:
                return {"started": False, "job_id": JOB_ID, "error": "no target_ip configured on the lab agent"}
            command = [
                self.python_executable,
                str(self.script_path),
                "--target-ip",
                self.target_ip,
                "--port",
                str(self.port),
                "--rate",
                str(self.rate),
                "--duration-seconds",
                str(self.duration_seconds),
            ]
            self._process = self._popen(command)
            return {"started": True, "job_id": JOB_ID, "pid": self._process.pid}

    def stop(self) -> dict[str, Any]:
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                return {"already_stopped": True, "job_id": JOB_ID}
            try:
                self._process.send_signal(signal.SIGINT)
            except (ProcessLookupError, OSError):
                pass
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.terminate()
                try:
                    self._process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=2.0)
            return {"stopped": True, "job_id": JOB_ID}


def _authorized(headers: Any, token: str) -> bool:
    if not token:
        return False
    header = headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False
    return hmac.compare_digest(header[len("Bearer ") :], token)


class AegisLabAgentHandler(BaseHTTPRequestHandler):
    server_version = "AegisLabAgent/1.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _discard_body(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length:
            self.rfile.read(length)  # request bodies never drive behavior; discard only

    def do_GET(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler name
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == f"/jobs/{JOB_ID}/status":
            self._send_json(200, self.server.jobs.status())  # type: ignore[attr-defined]
            return
        self._send_json(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - required BaseHTTPRequestHandler name
        self._discard_body()
        if self.path == f"/jobs/{JOB_ID}/stop":
            if not _authorized(self.headers, self.server.token):  # type: ignore[attr-defined]
                self._send_json(401, {"detail": "unauthorized"})
                return
            self._send_json(200, self.server.jobs.stop())  # type: ignore[attr-defined]
            return
        if self.path == f"/jobs/{JOB_ID}/start":
            if not self.server.start_enabled:  # type: ignore[attr-defined]
                self._send_json(404, {"detail": "not found"})
                return
            if not _authorized(self.headers, self.server.token):  # type: ignore[attr-defined]
                self._send_json(401, {"detail": "unauthorized"})
                return
            self._send_json(200, self.server.jobs.start())  # type: ignore[attr-defined]
            return
        self._send_json(404, {"detail": "not found"})

    def log_message(self, format: str, *args: Any) -> None:  # keep tokens out of default access logs
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")


class AegisLabAgentServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler], *, jobs: JobManager, token: str, start_enabled: bool) -> None:
        super().__init__(address, handler)
        self.jobs = jobs
        self.token = token
        self.start_enabled = start_enabled


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VM-side attack controller for the registered pi-syn-demo job")
    parser.add_argument("--bind-host", default=os.getenv("AEGIS_LAB_AGENT_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("AEGIS_LAB_AGENT_PORT", "9000")))
    parser.add_argument("--target-ip", default=os.getenv("AEGIS_PI_TARGET_IP", ""))
    parser.add_argument("--syn-port", type=int, default=int(os.getenv("AEGIS_LAB_SYN_PORT", "8443")))
    parser.add_argument("--rate", type=float, default=float(os.getenv("AEGIS_LAB_SYN_RATE", "250")))
    parser.add_argument("--duration-seconds", type=float, default=float(os.getenv("AEGIS_LAB_SYN_MAX_DURATION_SECONDS", "120")))
    parser.add_argument("--enable-start", action="store_true", default=_bool_env("AEGIS_LAB_AGENT_ENABLE_START"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    from scripts.lab_vm.pi_syn_demo import clamp_duration, clamp_rate

    token = os.getenv("AEGIS_ATTACK_CONTROLLER_TOKEN", "")
    if not token:
        print("WARNING: AEGIS_ATTACK_CONTROLLER_TOKEN is not set; stop/start requests will always be rejected", file=sys.stderr)
    if not args.target_ip:
        print("WARNING: no --target-ip / AEGIS_PI_TARGET_IP configured; start will fail until it is set", file=sys.stderr)

    jobs = JobManager(
        target_ip=args.target_ip,
        port=args.syn_port,
        rate=clamp_rate(args.rate),
        duration_seconds=clamp_duration(args.duration_seconds),
    )
    server = AegisLabAgentServer(
        (args.bind_host, args.port),
        AegisLabAgentHandler,
        jobs=jobs,
        token=token,
        start_enabled=args.enable_start,
    )
    print(f"aegis-lab-agent listening on {args.bind_host}:{args.port} (job={JOB_ID}, start_enabled={args.enable_start})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        jobs.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
