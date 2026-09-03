"""Read-only finals hardware readiness checker.

This script only observes. It never launches an attack, never calls
remediation, and never mutates model/rule artifacts. It exists so the team
has one command that answers: "is the physical topology safe to try today?"
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "services" / "backend" / "api"
for path in (str(ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


STATUS_ORDER = {"PASS": 0, "SKIP": 1, "WARN": 2, "FAIL": 3}
REQUIRED_PACKAGES = ("fastapi", "uvicorn", "pydantic", "yaml", "numpy", "torch", "sklearn", "xgboost", "reportlab")


@dataclass(slots=True)
class CheckResult:
    name: str
    status: str
    detail: str
    critical: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "detail": self.detail, "critical": self.critical}


def _ok(name: str, detail: str, *, critical: bool = True) -> CheckResult:
    return CheckResult(name, "PASS", detail, critical)


def _warn(name: str, detail: str, *, critical: bool = True) -> CheckResult:
    return CheckResult(name, "WARN", detail, critical)


def _fail(name: str, detail: str, *, critical: bool = True) -> CheckResult:
    return CheckResult(name, "FAIL", detail, critical)


def _skip(name: str, detail: str) -> CheckResult:
    return CheckResult(name, "SKIP", detail, critical=False)


def check_python_runtime() -> CheckResult:
    version = sys.version_info
    detail = f"{platform.python_implementation()} {platform.python_version()} at {sys.executable}"
    if version < (3, 10):
        return _warn("Python runtime", detail + " (older than the 3.11 target; verify compatibility)")
    return _ok("Python runtime", detail)


def check_backend_importable() -> tuple[CheckResult, Any | None]:
    try:
        config = importlib.import_module("app.core.config")
    except Exception as exc:  # backend package must be importable for every other check
        return _fail("Backend package importable", f"import app.core.config failed: {exc}"), None
    return _ok("Backend package importable", f"resolved from {BACKEND_ROOT}"), config


def check_required_packages() -> CheckResult:
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except Exception:
            missing.append(package)
    if missing:
        return _fail("Required Python packages", f"missing: {', '.join(missing)}")
    return _ok("Required Python packages", f"all present: {', '.join(REQUIRED_PACKAGES)}")


def check_model_artifacts(config: Any) -> list[CheckResult]:
    results: list[CheckResult] = []
    model_path = Path(config.MODEL_PACKAGE_PATH)
    for filename in ("manifest.json", "baselines.json", "canonicalization.json", "intelligence.json", "calibration.json", "metrics.json", "xgboost.json", "temporal_vae_pi.pt"):
        target = model_path / filename
        if target.is_file():
            results.append(_ok(f"Artifact {filename}", str(target)))
        else:
            results.append(_fail(f"Artifact {filename}", f"missing at {target}"))
    try:
        from app.rules.engine import load_rule_engine

        engine = load_rule_engine(Path(config.RULES_PATH))
        results.append(_ok("Rules YAML valid", f"{len(engine.rules)} rules, version {engine.ruleset_version}"))
    except Exception as exc:
        results.append(_fail("Rules YAML valid", f"{config.RULES_PATH}: {exc}"))
    try:
        import yaml

        mitre_payload = yaml.safe_load(Path(config.MITRE_SCENARIOS_PATH).read_text(encoding="utf-8"))
        scenarios = mitre_payload.get("scenarios") if isinstance(mitre_payload, dict) else None
        if not scenarios:
            raise ValueError("no scenarios listed")
        results.append(_ok("MITRE scenarios YAML valid", f"{len(scenarios)} scenarios"))
    except Exception as exc:
        results.append(_fail("MITRE scenarios YAML valid", f"{config.MITRE_SCENARIOS_PATH}: {exc}"))
    return results


def _writable(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, prefix=".aegis_preflight_", delete=True):
            pass
        return True, str(path)
    except OSError as exc:
        return False, f"{path}: {exc}"


def check_storage(config: Any) -> list[CheckResult]:
    results: list[CheckResult] = []
    checks = [
        ("Incident DB directory writable", Path(config.INCIDENT_DB_PATH).parent),
        ("Auth DB directory writable", Path(config.AUTH_DB_PATH).parent),
        ("Reports directory writable", Path(config.FORENSIC_REPORTS_DIR)),
        ("Real-session capture directory writable", ROOT / "data" / "finals-capture"),
    ]
    for name, path in checks:
        ok, detail = _writable(path)
        results.append(_ok(name, detail) if ok else _fail(name, detail))
    return results


def check_windows_sensor(config: Any, tshark_path: str, interface: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        from scripts.tshark_live import locate_tshark

        executable = locate_tshark(tshark_path or config.TSHARK_PATH or None)
        results.append(_ok("TShark available", str(executable)))
    except FileNotFoundError as exc:
        results.append(_fail("TShark available", str(exc)))
        results.append(_skip("Npcap capture ready", "TShark was not found; interface listing skipped"))
        return results

    try:
        completed = subprocess.run([str(executable), "-D"], check=False, text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        results.append(_fail("Npcap capture ready", f"`tshark -D` failed to run: {exc}"))
        return results
    interfaces = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not interfaces:
        results.append(_fail("Npcap capture ready", f"`tshark -D` listed no interfaces (exit {completed.returncode}); Npcap driver may be missing"))
        return results
    configured = interface or config.TSHARK_INTERFACE
    if not configured:
        results.append(_warn("Npcap capture ready", f"{len(interfaces)} interfaces listed, but no interface is configured (--interface / AEGIS_TSHARK_INTERFACE)"))
        return results
    matched = any(configured == line.split(".", 1)[0].strip() or configured in line for line in interfaces)
    if matched:
        results.append(_ok("Npcap capture ready", f"configured interface {configured!r} found among {len(interfaces)} interfaces"))
    else:
        results.append(_fail("Npcap capture ready", f"configured interface {configured!r} not found among: {interfaces}"))
    return results


def _http_get_json(url: str, *, token: str | None = None, timeout: float = 2.0) -> tuple[bool, int | None, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    outbound = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(outbound, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return True, response.status, (json.loads(body) if body else {})
    except error.HTTPError as exc:
        return False, exc.code, None
    except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return False, None, str(exc)


def check_backend(backend_url: str) -> list[CheckResult]:
    ok, status, payload = _http_get_json(f"{backend_url.rstrip('/')}/api/v1/health")
    if not ok:
        return [_fail("Backend reachable", f"GET /api/v1/health failed: {payload}")]
    results = [_ok("Backend reachable", f"/api/v1/health -> {status} {payload}")]
    ok, status, payload = _http_get_json(f"{backend_url.rstrip('/')}/api/v1/system/capabilities")
    if ok and isinstance(payload, dict):
        remediation = payload.get("remediation", {})
        results.append(
            _ok(
                "Backend capabilities",
                f"tshark_available={remediation.get('tshark_available')} rules_loaded={remediation.get('rules_loaded')} "
                f"attack_controller_configured={remediation.get('attack_controller_configured')} forensic_storage_writable={remediation.get('forensic_storage_writable')}",
            )
        )
    else:
        # The backend answered /api/v1/health, so it is genuinely running; a failing
        # /api/v1/system/capabilities here means a wrong/incompatible API contract, not
        # an offline backend. Never hide that behind a WARN.
        results.append(_fail("Backend capabilities", f"GET /api/v1/system/capabilities failed: status={status} error={payload}"))
    return results


def check_pi(pi_ip: str) -> list[CheckResult]:
    from scripts.tshark_live import validate_target
    import argparse as _argparse

    try:
        target = validate_target(pi_ip)
    except _argparse.ArgumentTypeError as exc:
        return [_fail("Pi target address is private/lab", str(exc))]
    results = [_ok("Pi target address is private/lab", target)]
    ping_command = ["ping", "-n", "2", "-w", "1000", target] if os.name == "nt" else ["ping", "-c", "2", "-W", "1", target]
    try:
        completed = subprocess.run(ping_command, check=False, text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        results.append(_fail("Pi reachable (ICMP)", f"ping could not run: {exc}"))
        return results
    if completed.returncode == 0:
        results.append(_ok("Pi reachable (ICMP)", f"ping {target} succeeded"))
    else:
        results.append(_fail("Pi reachable (ICMP)", f"ping {target} failed (exit {completed.returncode}); check adapter/cabling"))
    return results


def check_attack_controller(controller_url: str, token: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    ok, status, payload = _http_get_json(f"{controller_url.rstrip('/')}/health", token=token)
    if ok:
        results.append(_ok("Attack controller reachable", f"GET /health -> {status} {payload}"))
    else:
        results.append(_fail("Attack controller reachable", f"GET /health failed: {payload or status}"))
        return results
    ok, status, payload = _http_get_json(f"{controller_url.rstrip('/')}/jobs/pi-syn-demo/status", token=token)
    if ok:
        results.append(_ok("pi-syn-demo job registered", f"GET /jobs/pi-syn-demo/status -> {status} {payload}"))
    else:
        results.append(_warn("pi-syn-demo job registered", f"GET /jobs/pi-syn-demo/status failed: {payload or status}"))
    return results


def check_smtp(config: Any) -> CheckResult:
    if not config.SMTP_ENABLED:
        return _warn("SMTP", "DISABLED (finals-safe default; does not block cyber-demo readiness)", critical=False)
    if config.SMTP_HOST and config.SMTP_USERNAME and config.SMTP_PASSWORD and config.SMTP_FROM:
        return _ok("SMTP", f"CONFIGURED host={config.SMTP_HOST} port={config.SMTP_PORT}", critical=False)
    return _warn("SMTP", "MISCONFIGURED: enabled but missing host/username/password/from", critical=False)


def run(args: argparse.Namespace) -> tuple[list[CheckResult], bool]:
    results: list[CheckResult] = [check_python_runtime()]
    backend_check, config = check_backend_importable()
    results.append(backend_check)
    if config is None:
        return results, False
    results.append(check_required_packages())
    results.extend(check_model_artifacts(config))
    results.extend(check_storage(config))
    results.extend(check_windows_sensor(config, args.tshark_path, args.interface))

    if args.backend_url:
        results.extend(check_backend(args.backend_url))
    else:
        results.append(_skip("Backend reachable", "no --backend-url supplied"))

    pi_ip = args.pi_ip or config.PI_TARGET_IP
    if pi_ip:
        results.extend(check_pi(pi_ip))
    else:
        results.append(_skip("Pi reachable", "no --pi-ip supplied and AEGIS_PI_TARGET_IP is unset"))

    controller_url = args.controller_url or config.ATTACK_CONTROLLER_URL
    if controller_url:
        token = args.controller_token or config.ATTACK_CONTROLLER_TOKEN
        results.extend(check_attack_controller(controller_url, token))
    else:
        results.append(_skip("Attack controller reachable", "no --controller-url supplied and AEGIS_ATTACK_CONTROLLER_URL is unset"))

    smtp_check = check_smtp(config)
    results.append(smtp_check)
    if args.require_smtp:
        smtp_check.critical = True

    hardware_ready = all(result.status != "FAIL" for result in results if result.critical)
    return results, hardware_ready


def render_human(results: list[CheckResult], hardware_ready: bool) -> str:
    lines = ["AEGIS-TWIN FINALS PREFLIGHT", ""]
    for result in results:
        lines.append(f"[{result.status}] {result.name} - {result.detail}")
    lines.append("")
    lines.append("FINAL STATUS:")
    lines.append("HARDWARE ATTACK PATH READY" if hardware_ready else "HARDWARE ATTACK PATH NOT READY")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe, read-only finals hardware readiness checker")
    parser.add_argument("--backend-url", default=os.getenv("AEGIS_TELEMETRY_API_URL", "http://localhost:8000"))
    parser.add_argument("--pi-ip", default=os.getenv("AEGIS_PI_TARGET_IP", ""))
    parser.add_argument("--interface", default=os.getenv("AEGIS_TSHARK_INTERFACE", ""))
    parser.add_argument("--controller-url", default=os.getenv("AEGIS_ATTACK_CONTROLLER_URL", ""))
    parser.add_argument("--controller-token", default=os.getenv("AEGIS_ATTACK_CONTROLLER_TOKEN", ""))
    parser.add_argument("--tshark-path", default=os.getenv("AEGIS_TSHARK_PATH", ""))
    parser.add_argument("--require-smtp", action="store_true", help="Fail overall readiness if SMTP is disabled/misconfigured")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    results, hardware_ready = run(args)
    if args.json:
        print(json.dumps({"results": [r.to_dict() for r in results], "hardware_attack_path_ready": hardware_ready}, indent=2))
    else:
        print(render_human(results, hardware_ready))
    return 0 if hardware_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
