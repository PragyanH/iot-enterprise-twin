from __future__ import annotations

import http.client
import json
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lab_vm.aegis_lab_agent import AegisLabAgentHandler, AegisLabAgentServer, JOB_ID, JobManager


class FakePopen:
    """Stands in for subprocess.Popen so tests never launch pi_syn_demo.py or send packets."""

    def __init__(self, command: list[str]) -> None:
        self.command = command
        self.pid = 4242
        self.returncode: int | None = None

    def poll(self) -> int | None:
        return self.returncode

    def send_signal(self, _sig: int) -> None:
        self.returncode = 0

    def terminate(self) -> None:
        self.returncode = 0

    def kill(self) -> None:
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int | None:
        return self.returncode


def _make_server(*, token: str = "secret-token", start_enabled: bool = True, target_ip: str = "192.168.56.20"):
    jobs = JobManager(target_ip=target_ip, port=8443, rate=250.0, duration_seconds=30.0, popen=FakePopen)
    server = AegisLabAgentServer(("127.0.0.1", 0), AegisLabAgentHandler, jobs=jobs, token=token, start_enabled=start_enabled)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, jobs, thread


def _stop_server(server: AegisLabAgentServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


def _request(server: AegisLabAgentServer, method: str, path: str, *, token: str | None = None, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        payload = json.loads(raw) if raw else {}
        return response.status, payload
    finally:
        conn.close()


@pytest.fixture
def agent():
    server, jobs, thread = _make_server()
    try:
        yield server, jobs
    finally:
        _stop_server(server, thread)


def test_health_endpoint(agent) -> None:
    server, _jobs = agent
    status, payload = _request(server, "GET", "/health")
    assert status == 200
    assert payload == {"status": "ok"}


def test_status_reports_not_running_initially(agent) -> None:
    server, _jobs = agent
    status, payload = _request(server, "GET", f"/jobs/{JOB_ID}/status")
    assert status == 200
    assert payload["job_id"] == JOB_ID
    assert payload["running"] is False


def test_unknown_job_id_is_rejected(agent) -> None:
    server, _jobs = agent
    status, _payload = _request(server, "GET", "/jobs/some-other-job/status")
    assert status == 404
    status, _payload = _request(server, "POST", "/jobs/some-other-job/stop", token="secret-token")
    assert status == 404


def test_stop_without_token_is_rejected(agent) -> None:
    server, _jobs = agent
    status, _payload = _request(server, "POST", f"/jobs/{JOB_ID}/stop")
    assert status == 401


def test_stop_with_wrong_token_is_rejected(agent) -> None:
    server, _jobs = agent
    status, _payload = _request(server, "POST", f"/jobs/{JOB_ID}/stop", token="wrong-token")
    assert status == 401


def test_start_status_stop_and_idempotent_stop(agent) -> None:
    server, jobs = agent
    status, payload = _request(server, "POST", f"/jobs/{JOB_ID}/start", token="secret-token")
    assert status == 200
    assert payload["started"] is True

    status, payload = _request(server, "GET", f"/jobs/{JOB_ID}/status")
    assert status == 200
    assert payload["running"] is True

    status, payload = _request(server, "POST", f"/jobs/{JOB_ID}/stop", token="secret-token")
    assert status == 200
    assert payload["stopped"] is True

    status, payload = _request(server, "POST", f"/jobs/{JOB_ID}/stop", token="secret-token")
    assert status == 200
    assert payload["already_stopped"] is True


def test_start_ignores_body_supplied_target_and_rate(agent) -> None:
    server, jobs = agent
    _request(
        server,
        "POST",
        f"/jobs/{JOB_ID}/start",
        token="secret-token",
        body={"target_ip": "8.8.8.8", "rate": 999999, "job_id": "rm -rf /"},
    )
    status, payload = _request(server, "GET", f"/jobs/{JOB_ID}/status")
    assert status == 200
    assert payload["target_ip"] == "192.168.56.20"
    assert payload["rate"] == 250.0


def test_start_disabled_by_default_returns_404() -> None:
    server, jobs, thread = _make_server(start_enabled=False)
    try:
        status, _payload = _request(server, "POST", f"/jobs/{JOB_ID}/start", token="secret-token")
        assert status == 404
    finally:
        _stop_server(server, thread)


def test_no_arbitrary_command_surface_exists(agent) -> None:
    server, _jobs = agent
    for method, path in (
        ("GET", "/execute"),
        ("POST", "/execute"),
        ("POST", "/shell"),
        ("POST", "/run-command"),
        ("GET", "/jobs"),
        ("POST", f"/jobs/{JOB_ID}/run"),
    ):
        status, _payload = _request(server, method, path, token="secret-token")
        assert status == 404, f"{method} {path} should not be a recognized route"
