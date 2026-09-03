"""Windows-first TShark/Npcap adapter for PI-001 telemetry.

TShark observes packets. This adapter derives one-second, sensor-neutral Aegis
features and forwards them to FastAPI. It never substitutes mock data when live
capture fails.
"""

from __future__ import annotations

import argparse
from collections import deque
import ipaddress
import json
import logging
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, TextIO
from urllib import error, request


LOGGER = logging.getLogger("aegis.tshark")
TSHARK_FIELDS = (
    "frame.time_epoch",
    "frame.len",
    "ip.src",
    "ip.dst",
    "tcp.srcport",
    "tcp.dstport",
    "tcp.flags.syn",
    "tcp.flags.ack",
    "tcp.flags.reset",
    "tcp.analysis.retransmission",
)


def log_event(event: str, **fields: object) -> None:
    LOGGER.info(json.dumps({"event": event, **fields}, separators=(",", ":"), default=str))


@dataclass(frozen=True, slots=True)
class PacketRecord:
    timestamp: float
    length: int
    source_ip: str
    destination_ip: str
    source_port: int | None
    destination_port: int | None
    syn: bool
    ack: bool
    reset: bool
    retransmission: bool


def _optional_int(value: str) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _flag(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def parse_tshark_line(line: str) -> PacketRecord:
    """Parse one tab-separated TShark field row with strict core validation."""

    values = line.rstrip("\r\n").split("\t")
    if len(values) != len(TSHARK_FIELDS):
        raise ValueError(f"expected {len(TSHARK_FIELDS)} TShark fields, received {len(values)}")
    try:
        timestamp = float(values[0])
        length = int(values[1])
    except ValueError as exc:
        raise ValueError("invalid packet timestamp or frame length") from exc
    if timestamp < 0 or length < 0 or not values[2] or not values[3]:
        raise ValueError("packet row has invalid timestamp, length, or IP address")
    return PacketRecord(
        timestamp=timestamp,
        length=length,
        source_ip=values[2],
        destination_ip=values[3],
        source_port=_optional_int(values[4]),
        destination_port=_optional_int(values[5]),
        syn=_flag(values[6]),
        ack=_flag(values[7]),
        reset=_flag(values[8]),
        retransmission=bool(values[9]),
    )


class WindowAccumulator:
    """Calculate explicit Aegis features from packets seen during one interval."""

    def __init__(self, target_ip: str, sample_interval: float) -> None:
        self.target_ip = target_ip
        self.sample_interval = sample_interval
        self.packets: list[PacketRecord] = []

    def add(self, packet: PacketRecord) -> None:
        if packet.source_ip == self.target_ip or packet.destination_ip == self.target_ip:
            self.packets.append(packet)

    def point(self) -> dict[str, float]:
        packets = sorted(self.packets, key=lambda item: item.timestamp)
        inbound = [item for item in packets if item.destination_ip == self.target_ip]
        outbound = [item for item in packets if item.source_ip == self.target_ip]
        initial_syn = [item for item in inbound if item.syn and not item.ack]
        syn_ack = [item for item in outbound if item.syn and item.ack]
        final_ack = [item for item in inbound if item.ack and not item.syn]
        completed = min(len(initial_syn), len(syn_ack), len(final_ack))
        completion_ratio = completed / len(initial_syn) if initial_syn else 1.0
        incomplete_ratio = 1.0 - completion_ratio if initial_syn else 0.0
        intervals = [right.timestamp - left.timestamp for left, right in zip(packets, packets[1:])]
        nonnegative_intervals = [value for value in intervals if value >= 0]
        mean_iat = (
            sum(nonnegative_intervals) / len(nonnegative_intervals)
            if nonnegative_intervals
            else self.sample_interval
        )
        orig_packets = len(inbound)
        resp_packets = len(outbound)
        largest_direction = max(orig_packets, resp_packets)
        symmetry = min(orig_packets, resp_packets) / largest_direction if largest_direction else 1.0
        resets = [item for item in packets if item.reset]
        inbound_sources = {item.source_ip for item in inbound}
        destination_ports = {item.destination_port for item in inbound if item.destination_port is not None}
        ssh_attempts = sum(item.destination_port == 22 for item in initial_syn)
        ssh_failures = sum(item.source_port == 22 and item.reset for item in outbound)
        return {
            "packet_size": sum(item.length for item in packets) / len(packets) if packets else 0.0,
            "iat": mean_iat,
            "payload_entropy": 0.0,
            "flow_symmetry": symmetry,
            "syn_rate": float(len(initial_syn)) / self.sample_interval,
            "syn_ack_rate": float(len(syn_ack)) / self.sample_interval,
            "ack_rate": float(len(final_ack)) / self.sample_interval,
            "incomplete_ratio": incomplete_ratio,
            "handshake_completion_ratio": completion_ratio,
            "unique_sources": float(len(inbound_sources)),
            "unique_destination_ports": float(len(destination_ports)),
            "rejected_connections": float(sum(item.source_ip == self.target_ip and item.reset for item in resets)),
            "reset_connections": float(len(resets)),
            "orig_packets": float(orig_packets),
            "resp_packets": float(resp_packets),
            "orig_bytes": float(sum(item.length for item in inbound)),
            "resp_bytes": float(sum(item.length for item in outbound)),
            "connection_duration_mean": 0.0,
            "ssh_attempts": float(ssh_attempts),
            "ssh_failures": float(ssh_failures),
            "capture_loss": 0.0,
        }


def validate_target(value: str) -> str:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid target IP: {value}") from exc
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise argparse.ArgumentTypeError("target IP must be a non-loopback private lab address")
    return str(address)


def locate_tshark(explicit: str | None = None) -> Path:
    candidates = [
        explicit,
        os.getenv("AEGIS_TSHARK_PATH"),
        shutil.which("tshark"),
        str(Path(os.getenv("ProgramFiles", r"C:\Program Files")) / "Wireshark" / "tshark.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise FileNotFoundError(
        "TShark was not found. Install Wireshark with Npcap, then set AEGIS_TSHARK_PATH "
        "or pass --tshark-path. No live telemetry was generated."
    )


def build_tshark_command(executable: Path, interface: str, target_ip: str) -> list[str]:
    command = [
        str(executable),
        "-l",
        "-n",
        "-i",
        interface,
        "-f",
        f"host {target_ip} and tcp",
        "-Y",
        f"ip.addr == {target_ip} && tcp",
        "-T",
        "fields",
        "-E",
        "separator=/t",
        "-E",
        "occurrence=f",
        "-E",
        "quote=n",
    ]
    for field in TSHARK_FIELDS:
        command.extend(("-e", field))
    return command


def telemetry_payload(
    point: dict[str, float],
    *,
    device_id: str,
    job_id: str,
    session_id: str,
) -> dict[str, object]:
    return {
        "device_id": device_id,
        "source": "live_hardware",
        "sensor": "tshark_npcap",
        "sequence_seconds": 20,
        "attack_job_id": job_id,
        "session_id": session_id,
        "unavailable_features": ["payload_entropy", "connection_duration_mean"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "points": [point],
    }


def post_window(api_url: str, payload: dict[str, object], attempts: int = 3) -> dict[str, object]:
    endpoint = f"{api_url.rstrip('/')}/api/v1/telemetry/windows"
    outbound = request.Request(
        endpoint,
        data=json.dumps(payload, allow_nan=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with request.urlopen(outbound, timeout=2.0) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(0.25 * attempt)
    raise ConnectionError(f"FastAPI telemetry POST failed after {attempts} attempts: {last_error}")


class SessionRecorder:
    """Persist rolling 20-sample sequences with one immutable session ID."""

    def __init__(self, destination: Path, label: str, scenario: str | None) -> None:
        self.destination = destination
        self.label = label
        self.scenario = scenario
        self.points: deque[dict[str, float]] = deque(maxlen=20)

    def add(self, payload: dict[str, object], *, allow_partial: bool = False) -> bool:
        points = payload.get("points")
        if not isinstance(points, list) or not points or not isinstance(points[-1], dict):
            raise ValueError("recording payload must contain a telemetry point")
        self.points.append({str(key): float(value) for key, value in points[-1].items()})
        if len(self.points) < 20 and not allow_partial:
            return False
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        row = {
            **payload,
            "points": list(self.points),
            "label": self.label,
            "scenario": self.scenario,
        }
        with self.destination.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
        return True


def _read_stdout(stream: TextIO, output: queue.Queue[str], stopped: threading.Event) -> None:
    while not stopped.is_set():
        line = stream.readline()
        if not line:
            break
        output.put(line)


def run_fixture(args: argparse.Namespace) -> int:
    accumulator = WindowAccumulator(args.target_ip, args.sample_interval)
    malformed = 0
    with args.fixture.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                accumulator.add(parse_tshark_line(line))
            except ValueError as exc:
                malformed += 1
                log_event("packet_parse_failed", error=str(exc))
    payload = telemetry_payload(
        accumulator.point(),
        device_id=args.device_id,
        job_id=args.job_id,
        session_id=args.session_id,
    )
    if args.record:
        SessionRecorder(args.record, args.label, args.scenario).add(payload, allow_partial=True)
    print(json.dumps({"dry_run": True, "malformed_rows": malformed, "payload": payload}, indent=2))
    return 0


def run_live(args: argparse.Namespace, executable: Path) -> int:
    command = build_tshark_command(executable, args.interface, args.target_ip)
    stopped = threading.Event()
    recorder = SessionRecorder(args.record, args.label, args.scenario) if args.record else None
    try:
        while not stopped.is_set():
            log_event("sensor_started", interface=args.interface, target_ip=args.target_ip, sensor="tshark_npcap")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            assert process.stdout is not None
            assert process.stderr is not None
            rows: queue.Queue[str] = queue.Queue()
            error_rows: queue.Queue[str] = queue.Queue()
            diagnostics: deque[str] = deque(maxlen=20)
            reader = threading.Thread(target=_read_stdout, args=(process.stdout, rows, stopped), daemon=True)
            error_reader = threading.Thread(
                target=_read_stdout,
                args=(process.stderr, error_rows, stopped),
                daemon=True,
            )
            reader.start()
            error_reader.start()
            next_emit = time.monotonic() + args.sample_interval
            try:
                while process.poll() is None and not stopped.is_set():
                    wait = max(0.0, next_emit - time.monotonic())
                    time.sleep(min(wait, 0.1))
                    if time.monotonic() < next_emit:
                        continue
                    accumulator = WindowAccumulator(args.target_ip, args.sample_interval)
                    malformed = 0
                    while True:
                        try:
                            accumulator.add(parse_tshark_line(rows.get_nowait()))
                        except queue.Empty:
                            break
                        except ValueError as exc:
                            malformed += 1
                            if args.verbose:
                                log_event("packet_parse_failed", error=str(exc))
                    while True:
                        try:
                            diagnostic = error_rows.get_nowait().strip()
                            if diagnostic:
                                diagnostics.append(diagnostic)
                        except queue.Empty:
                            break
                    payload = telemetry_payload(
                        accumulator.point(),
                        device_id=args.device_id,
                        job_id=args.job_id,
                        session_id=args.session_id,
                    )
                    recorded = recorder.add(payload) if recorder else False
                    try:
                        prediction = post_window(args.api_url, payload)
                        log_event(
                            "telemetry_window_sent",
                            packets=len(accumulator.packets),
                            malformed_rows=malformed,
                            trust=prediction.get("trust"),
                            state=prediction.get("state"),
                            recorded=recorded,
                        )
                    except ConnectionError as exc:
                        log_event("telemetry_post_failed", error=str(exc))
                    next_emit += args.sample_interval
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1.0)
                reader.join(timeout=0.5)
                error_reader.join(timeout=0.5)
                while True:
                    try:
                        diagnostic = error_rows.get_nowait().strip()
                        if diagnostic:
                            diagnostics.append(diagnostic)
                    except queue.Empty:
                        break
                log_event(
                    "sensor_stopped",
                    exit_code=process.returncode,
                    diagnostic=" | ".join(diagnostics)[-500:],
                )
            if not args.reconnect:
                return process.returncode or 1
            log_event("sensor_reconnecting", delay_seconds=args.reconnect_delay)
            time.sleep(args.reconnect_delay)
    except KeyboardInterrupt:
        stopped.set()
        log_event("sensor_stopped", reason="operator_interrupt")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture PI-001 telemetry with Windows TShark/Npcap")
    parser.add_argument("--interface", default=os.getenv("AEGIS_TSHARK_INTERFACE", ""))
    parser.add_argument("--target-ip", type=validate_target, default=os.getenv("AEGIS_PI_TARGET_IP", "192.168.56.20"))
    parser.add_argument("--api-url", default=os.getenv("AEGIS_TELEMETRY_API_URL", "http://localhost:8000"))
    parser.add_argument("--device-id", default="PI-001")
    parser.add_argument("--job-id", default=os.getenv("AEGIS_ATTACK_JOB_ID", "pi-syn-demo"))
    parser.add_argument("--sample-interval", type=float, default=float(os.getenv("AEGIS_TELEMETRY_SAMPLE_INTERVAL", "1.0")))
    parser.add_argument("--tshark-path", default=os.getenv("AEGIS_TSHARK_PATH", ""))
    parser.add_argument("--record", type=Path)
    parser.add_argument("--label", choices=("normal", "syn_flood", "port_scan", "ssh_bruteforce"), default="normal")
    parser.add_argument("--scenario")
    parser.add_argument("--session-id", default=f"pi-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture", type=Path, help="TShark TSV fixture used only with --dry-run")
    parser.add_argument("--list-interfaces", action="store_true")
    parser.add_argument("--no-reconnect", dest="reconnect", action="store_false")
    parser.set_defaults(reconnect=True)
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    if args.sample_interval <= 0:
        parser.error("--sample-interval must be greater than zero")
    if args.reconnect_delay < 0:
        parser.error("--reconnect-delay cannot be negative")
    if args.fixture and not args.dry_run:
        parser.error("--fixture requires --dry-run")
    if args.dry_run and args.fixture:
        if not args.fixture.is_file():
            parser.error(f"fixture does not exist: {args.fixture}")
        return run_fixture(args)
    try:
        executable = locate_tshark(args.tshark_path)
    except FileNotFoundError as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    if args.list_interfaces:
        completed = subprocess.run([str(executable), "-D"], check=False, text=True, capture_output=True)
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return completed.returncode
    if not args.interface:
        parser.error("--interface or AEGIS_TSHARK_INTERFACE is required for live capture")
    command = build_tshark_command(executable, args.interface, args.target_ip)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "command": command}, indent=2))
        return 0
    return run_live(args, executable)


if __name__ == "__main__":
    raise SystemExit(main())
