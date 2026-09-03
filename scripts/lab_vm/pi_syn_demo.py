"""Controlled SYN scenario generator for the isolated Aegis finals lab.

This is intentionally narrow: it only understands one target, one port, one
rate, and one bounded lifetime. It is not a general attack tool.

Mandatory safeguards (do not relax these without updating the tests):
  - target must be an explicit, non-loopback, private/lab IPv4/IPv6 address
    (no hostnames, no ranges, no public addresses);
  - a single destination only;
  - rate is clamped to a hard maximum regardless of what is requested;
  - lifetime is clamped to a hard maximum regardless of what is requested;
  - no source-IP spoofing, no payload options, no port sweeping;
  - Ctrl+C stops the run immediately and cleanly.

Run only inside the isolated, team-owned VMware lab VM against PI-001.
"""

from __future__ import annotations

import argparse
import ipaddress
import os
import signal
import sys
import threading
import time
from typing import Callable


DEFAULT_RATE = float(os.getenv("AEGIS_LAB_SYN_RATE", "250"))
HARD_MAX_RATE = float(os.getenv("AEGIS_LAB_SYN_RATE_MAX", "400"))
DEFAULT_PORT = int(os.getenv("AEGIS_LAB_SYN_PORT", "8443"))
HARD_MAX_DURATION_SECONDS = float(os.getenv("AEGIS_LAB_SYN_MAX_DURATION_SECONDS", "120"))

Sender = Callable[[str, int], None]


def validate_lab_target(value: str) -> str:
    """Reject anything that is not a single private, non-loopback lab address."""

    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid target IP: {value!r} (hostnames and ranges are not accepted)"
        ) from exc
    if not address.is_private or address.is_loopback or address.is_unspecified or address.is_multicast:
        raise argparse.ArgumentTypeError(
            "target must be a single non-loopback private/lab address, never a public IP or hostname"
        )
    return str(address)


def clamp_rate(requested: float) -> float:
    """Bound a *default configuration* rate (used by aegis_lab_agent.py's own
    startup config). The CLI itself does not call this for a requested --rate:
    an explicit request above the hard maximum is rejected in main(), not
    silently clamped, so an operator never gets a different rate than asked for.
    """

    return max(1.0, min(requested, HARD_MAX_RATE))


def clamp_duration(requested: float) -> float:
    return max(1.0, min(requested, HARD_MAX_DURATION_SECONDS))


def _default_sender(target_ip: str, port: int) -> None:
    from scapy.all import IP, TCP, send  # imported lazily: only required on the lab VM

    send(IP(dst=target_ip) / TCP(dport=port, flags="S"), verbose=False)


def send_syn_scenario(
    target_ip: str,
    port: int,
    rate: float,
    duration_seconds: float,
    stop_flag: threading.Event,
    *,
    sender: Sender | None = None,
    verbose: bool = False,
) -> int:
    """Send SYN packets at `rate` pps against target_ip:port for duration_seconds.

    `sender` defaults to a real Scapy send and is swappable so automated tests
    never emit real packets.
    """

    active_sender = sender or _default_sender
    interval = 1.0 / rate
    deadline = time.monotonic() + duration_seconds
    sent = 0
    next_send = time.monotonic()
    while time.monotonic() < deadline and not stop_flag.is_set():
        now = time.monotonic()
        if now < next_send:
            time.sleep(min(next_send - now, 0.01))
            continue
        active_sender(target_ip, port)
        sent += 1
        next_send += interval
        if verbose and sent % max(1, int(rate)) == 0:
            print(f"pi-syn-demo: sent={sent}")
    return sent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled pi-syn-demo SYN scenario against a single lab Raspberry Pi target"
    )
    parser.add_argument("--target-ip", type=validate_lab_target, required=True)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--rate", type=float, default=DEFAULT_RATE)
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.rate <= 0:
        parser.error("--rate must be greater than zero")
    if args.rate > HARD_MAX_RATE:
        parser.error(
            f"--rate {args.rate}/s exceeds the hard maximum of {HARD_MAX_RATE}/s; "
            "refusing to run rather than silently sending at a different rate than requested"
        )
    if args.duration_seconds <= 0:
        parser.error("--duration-seconds must be greater than zero")
    if args.port <= 0 or args.port > 65535:
        parser.error("--port must be a valid TCP port")

    rate = args.rate
    duration = clamp_duration(args.duration_seconds)
    if duration != args.duration_seconds:
        print(f"NOTE: requested duration {args.duration_seconds}s clamped to hard maximum {HARD_MAX_DURATION_SECONDS}s")

    stop_flag = threading.Event()

    def _handle_sigint(_signum: int, _frame: object) -> None:
        stop_flag.set()

    signal.signal(signal.SIGINT, _handle_sigint)
    print(
        f"pi-syn-demo: target={args.target_ip} port={args.port} rate={rate}/s "
        f"duration={duration}s (Ctrl+C to stop)"
    )
    sent = send_syn_scenario(args.target_ip, args.port, rate, duration, stop_flag, verbose=args.verbose)
    print(f"pi-syn-demo stopped: sent={sent} packets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
