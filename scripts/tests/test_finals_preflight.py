from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "services" / "backend" / "api"
for path in (str(ROOT), str(BACKEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from scripts import finals_preflight as preflight


def test_backend_importable_and_artifacts_present() -> None:
    check, config = preflight.check_backend_importable()
    assert check.status == "PASS"
    assert config is not None
    results = preflight.check_model_artifacts(config)
    assert all(result.status == "PASS" for result in results), [r.to_dict() for r in results if r.status != "PASS"]


def test_missing_artifact_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, config = preflight.check_backend_importable()
    fake_config = SimpleNamespace(**vars(config))
    fake_config.MODEL_PACKAGE_PATH = tmp_path / "does-not-exist"
    fake_config.RULES_PATH = config.RULES_PATH
    fake_config.MITRE_SCENARIOS_PATH = config.MITRE_SCENARIOS_PATH
    results = preflight.check_model_artifacts(fake_config)
    assert any(result.status == "FAIL" and "manifest.json" in result.name for result in results)


def test_storage_check_reports_writable_directories(tmp_path: Path) -> None:
    _, config = preflight.check_backend_importable()
    fake_config = SimpleNamespace(
        INCIDENT_DB_PATH=tmp_path / "incidents.db",
        AUTH_DB_PATH=tmp_path / "auth.db",
        FORENSIC_REPORTS_DIR=tmp_path / "reports",
    )
    results = preflight.check_storage(fake_config)
    assert all(result.status == "PASS" for result in results)


def test_unreachable_backend_is_reported_as_failure() -> None:
    results = preflight.check_backend("http://127.0.0.1:1")
    assert results[0].status == "FAIL"
    assert results[0].critical is True


def test_backend_reachable_but_wrong_capabilities_contract_is_a_hard_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_http_get_json(url: str, *, token: str | None = None, timeout: float = 2.0):
        if url.endswith("/api/v1/health"):
            return True, 200, {"status": "ok"}
        if url.endswith("/api/v1/system/capabilities"):
            return False, 404, "Not Found"
        raise AssertionError(f"unexpected URL requested: {url}")

    monkeypatch.setattr(preflight, "_http_get_json", fake_http_get_json)
    results = preflight.check_backend("http://localhost:8000")
    assert results[0].status == "PASS"  # health still succeeded
    capabilities_result = next(r for r in results if r.name == "Backend capabilities")
    assert "/api/v1/system/capabilities" in capabilities_result.detail
    assert capabilities_result.status == "FAIL"
    assert capabilities_result.critical is True


def test_backend_capabilities_check_calls_the_versioned_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    def fake_http_get_json(url: str, *, token: str | None = None, timeout: float = 2.0):
        requested_urls.append(url)
        return True, 200, {"status": "ok", "remediation": {}}

    monkeypatch.setattr(preflight, "_http_get_json", fake_http_get_json)
    preflight.check_backend("http://localhost:8000")
    assert any(url.endswith("/api/v1/system/capabilities") for url in requested_urls)
    assert not any(url.endswith("/system/capabilities") and "/api/v1" not in url for url in requested_urls)


def test_unreachable_attack_controller_is_reported_as_failure() -> None:
    results = preflight.check_attack_controller("http://127.0.0.1:1", "token")
    assert results[0].status == "FAIL"


def test_public_pi_ip_is_rejected() -> None:
    results = preflight.check_pi("8.8.8.8")
    assert results[0].status == "FAIL"
    assert "private" in results[0].name.lower()


def test_smtp_disabled_is_warn_not_critical() -> None:
    fake_config = SimpleNamespace(SMTP_ENABLED=False, SMTP_HOST="", SMTP_USERNAME="", SMTP_PASSWORD="", SMTP_FROM="", SMTP_PORT=587)
    result = preflight.check_smtp(fake_config)
    assert result.status == "WARN"
    assert result.critical is False


def test_smtp_enabled_but_missing_credentials_is_misconfigured() -> None:
    fake_config = SimpleNamespace(SMTP_ENABLED=True, SMTP_HOST="", SMTP_USERNAME="", SMTP_PASSWORD="", SMTP_FROM="", SMTP_PORT=587)
    result = preflight.check_smtp(fake_config)
    assert result.status == "WARN"
    assert "MISCONFIGURED" in result.detail


def test_smtp_enabled_and_fully_configured_passes() -> None:
    fake_config = SimpleNamespace(SMTP_ENABLED=True, SMTP_HOST="smtp.local", SMTP_USERNAME="u", SMTP_PASSWORD="p", SMTP_FROM="a@b.c", SMTP_PORT=587)
    result = preflight.check_smtp(fake_config)
    assert result.status == "PASS"
    assert result.critical is False


def test_run_degrades_safely_with_nothing_configured() -> None:
    parser = preflight.build_parser()
    args = parser.parse_args(["--backend-url", "", "--pi-ip", "", "--controller-url", ""])
    results, hardware_ready = preflight.run(args)
    assert isinstance(hardware_ready, bool)
    assert any(result.name == "Backend reachable" and result.status == "SKIP" for result in results)
    assert any(result.name == "Attack controller reachable" and result.status == "SKIP" for result in results)


def test_json_output_shape(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = preflight.main(["--backend-url", "", "--pi-ip", "", "--controller-url", "", "--json"])
    output = capsys.readouterr().out
    assert '"hardware_attack_path_ready"' in output
    assert '"results"' in output
    assert exit_code in (0, 1)
