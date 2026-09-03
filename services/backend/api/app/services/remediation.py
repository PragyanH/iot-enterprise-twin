from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from urllib import error, parse, request


@dataclass(frozen=True, slots=True)
class RemediationResult:
    provider: str
    success: bool
    outcome: str
    job_id: str | None
    error: str | None = None
    http_status: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stopped"] = self.success
        payload["reason"] = self.outcome
        return payload


class RemediationProvider(Protocol):
    provider_id: str

    def execute(self, job_id: str | None) -> RemediationResult: ...

    def capability(self) -> dict[str, object]: ...


class AttackControllerStopProvider:
    """Stops only allowlisted controller jobs; never accepts commands."""

    provider_id = "attack_controller_stop"

    def __init__(
        self,
        base_url: str,
        token: str,
        allowed_job_ids: set[str],
        *,
        timeout_seconds: float = 3.0,
        opener: Any = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.allowed_job_ids = frozenset(allowed_job_ids)
        self.timeout_seconds = max(0.1, float(timeout_seconds))
        self._opener = opener or request.urlopen

    def capability(self) -> dict[str, object]:
        return {
            "id": self.provider_id,
            "available": bool(self.base_url and self.allowed_job_ids),
            "mode": "controlled_lab",
            "authentication_configured": bool(self.token),
            "allowlisted_jobs": sorted(self.allowed_job_ids),
        }

    def execute(self, job_id: str | None) -> RemediationResult:
        if not job_id:
            return RemediationResult(self.provider_id, False, "no_registered_attack_job", None)
        if job_id not in self.allowed_job_ids:
            return RemediationResult(self.provider_id, False, "not_allowlisted", job_id)
        if not self.base_url:
            return RemediationResult(self.provider_id, False, "controller_unavailable", job_id)
        url = f"{self.base_url}/jobs/{parse.quote(job_id, safe='')}/stop"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        outbound = request.Request(
            url,
            data=json.dumps({"job_id": job_id}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener(outbound, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                result = json.loads(body) if body else {}
                already = bool(result.get("already_stopped")) or result.get("status") == "already_stopped"
                stopped = bool(result.get("stopped", response.status < 300))
                success = stopped or already
                outcome = "already_stopped" if already else "stopped" if success else "controller_rejected"
                return RemediationResult(self.provider_id, success, outcome, job_id, http_status=response.status)
        except error.HTTPError as exc:
            outcome = "authentication_failure" if exc.code in {401, 403} else "controller_rejected"
            return RemediationResult(self.provider_id, False, outcome, job_id, http_status=exc.code)
        except (TimeoutError, socket.timeout) as exc:
            return RemediationResult(self.provider_id, False, "timeout", job_id, error=str(exc))
        except error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                return RemediationResult(self.provider_id, False, "timeout", job_id, error=str(exc.reason))
            return RemediationResult(self.provider_id, False, "controller_unavailable", job_id, error=str(exc.reason))
        except json.JSONDecodeError as exc:
            return RemediationResult(self.provider_id, False, "invalid_controller_response", job_id, error=str(exc))
        except Exception as exc:  # Controller integration must not crash inference/remediation state.
            return RemediationResult(self.provider_id, False, "unexpected_failure", job_id, error=str(exc))

    def stop(self, job_id: str | None) -> dict[str, Any]:
        """Backward-compatible lower-level contract used by existing callers."""
        result = self.execute(job_id).to_dict()
        legacy = {
            "not_allowlisted": "attack_job_not_allowlisted",
            "controller_unavailable": "attack_controller_not_configured" if not self.base_url else "attack_controller_unavailable",
        }
        result["reason"] = legacy.get(str(result["reason"]), result["reason"])
        return result


class ReplayStopProvider:
    provider_id = "replay_stop"

    def execute(self, job_id: str | None) -> RemediationResult:
        return RemediationResult(self.provider_id, True, "replay_stream_stopped", job_id)

    def capability(self) -> dict[str, object]:
        return {"id": self.provider_id, "available": True, "mode": "recorded_replay"}


class MockResetProvider:
    provider_id = "mock_generator_reset"

    def execute(self, job_id: str | None = None) -> RemediationResult:
        return RemediationResult(self.provider_id, True, "mock_generator_reset", job_id)

    def capability(self) -> dict[str, object]:
        return {"id": self.provider_id, "available": True, "mode": "simulation"}
