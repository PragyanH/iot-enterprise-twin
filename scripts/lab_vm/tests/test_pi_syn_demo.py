from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lab_vm import pi_syn_demo
from scripts.lab_vm.pi_syn_demo import (
    HARD_MAX_DURATION_SECONDS,
    HARD_MAX_RATE,
    clamp_duration,
    clamp_rate,
    send_syn_scenario,
    validate_lab_target,
)


def test_public_ip_is_rejected() -> None:
    with pytest.raises(Exception):
        validate_lab_target("8.8.8.8")


def test_loopback_is_rejected() -> None:
    with pytest.raises(Exception):
        validate_lab_target("127.0.0.1")


def test_hostname_is_rejected() -> None:
    with pytest.raises(Exception):
        validate_lab_target("example.com")


def test_multicast_is_rejected() -> None:
    with pytest.raises(Exception):
        validate_lab_target("224.0.0.1")


def test_private_lab_ip_is_accepted() -> None:
    assert validate_lab_target("192.168.56.20") == "192.168.56.20"


def test_clamp_rate_bounds_default_agent_configuration_only() -> None:
    """clamp_rate() is used by aegis_lab_agent.py to bound its own default
    config; the CLI itself rejects an out-of-range --rate instead (see below)."""
    assert clamp_rate(HARD_MAX_RATE * 100) == HARD_MAX_RATE
    assert clamp_rate(1.0) == 1.0


def test_duration_is_clamped_to_hard_maximum() -> None:
    assert clamp_duration(HARD_MAX_DURATION_SECONDS * 100) == HARD_MAX_DURATION_SECONDS
    assert clamp_duration(1.0) == 1.0


def test_send_syn_scenario_never_touches_scapy_when_sender_is_injected() -> None:
    calls: list[tuple[str, int]] = []

    def fake_sender(target_ip: str, port: int) -> None:
        calls.append((target_ip, port))

    stop_flag = threading.Event()
    sent = send_syn_scenario("192.168.56.20", 8443, rate=50.0, duration_seconds=0.2, stop_flag=stop_flag, sender=fake_sender)
    assert sent >= 1
    assert calls
    assert all(call == ("192.168.56.20", 8443) for call in calls)
    assert len(calls) == sent


def test_stop_flag_halts_the_scenario_immediately() -> None:
    calls: list[tuple[str, int]] = []
    stop_flag = threading.Event()
    stop_flag.set()
    sent = send_syn_scenario("192.168.56.20", 8443, rate=250.0, duration_seconds=5.0, stop_flag=stop_flag, sender=lambda *_: calls.append(_))
    assert sent == 0
    assert calls == []


def test_cli_rejects_rate_above_hard_maximum_with_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr(pi_syn_demo, "send_syn_scenario", lambda *args, **kwargs: calls.append(1) or 0)
    with pytest.raises(SystemExit) as exc_info:
        pi_syn_demo.main(
            ["--target-ip", "192.168.56.20", "--rate", str(HARD_MAX_RATE + 1), "--duration-seconds", "1"]
        )
    assert exc_info.value.code not in (0, None)
    assert calls == [], "an over-limit rate must never reach send_syn_scenario, clamped or not"


def test_cli_accepts_rate_exactly_at_hard_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_rates: list[float] = []

    def fake_send(target_ip: str, port: int, rate: float, duration_seconds: float, stop_flag, **kwargs) -> int:
        observed_rates.append(rate)
        return 0

    monkeypatch.setattr(pi_syn_demo, "send_syn_scenario", fake_send)
    exit_code = pi_syn_demo.main(
        ["--target-ip", "192.168.56.20", "--rate", str(HARD_MAX_RATE), "--duration-seconds", "1"]
    )
    assert exit_code == 0
    assert observed_rates == [HARD_MAX_RATE]


def test_cli_accepts_rate_below_hard_maximum_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_rates: list[float] = []

    def fake_send(target_ip: str, port: int, rate: float, duration_seconds: float, stop_flag, **kwargs) -> int:
        observed_rates.append(rate)
        return 0

    monkeypatch.setattr(pi_syn_demo, "send_syn_scenario", fake_send)
    exit_code = pi_syn_demo.main(["--target-ip", "192.168.56.20", "--rate", "150", "--duration-seconds", "1"])
    assert exit_code == 0
    assert observed_rates == [150.0]


def test_cli_still_clamps_duration_above_hard_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_durations: list[float] = []

    def fake_send(target_ip: str, port: int, rate: float, duration_seconds: float, stop_flag, **kwargs) -> int:
        observed_durations.append(duration_seconds)
        return 0

    monkeypatch.setattr(pi_syn_demo, "send_syn_scenario", fake_send)
    exit_code = pi_syn_demo.main(
        ["--target-ip", "192.168.56.20", "--rate", "100", "--duration-seconds", str(HARD_MAX_DURATION_SECONDS * 100)]
    )
    assert exit_code == 0
    assert observed_durations == [HARD_MAX_DURATION_SECONDS]
