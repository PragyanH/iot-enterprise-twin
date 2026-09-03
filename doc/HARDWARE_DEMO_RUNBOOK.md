# Aegis-Twin Windows Hardware Demo Runbook

Status: **READY FOR HARDWARE VALIDATION**. The adapter and parser are software-tested; no physical Pi/Npcap result is claimed here.

## Frozen topology

- Windows Pi-facing adapter: example `192.168.56.1`
- VMware attack NIC: example `192.168.56.10`
- Raspberry Pi `PI-001`: example `192.168.56.20`
- Registered attack job: `pi-syn-demo`
- Primary live sensor: Npcap + TShark on Windows
- Alternate sensor: Zeek on Linux

Prefer a separate VM host-only management NIC for the controller API. Do not depend on public Wi-Fi.

## One-time setup

1. Install Wireshark and select Npcap during setup.
2. Ensure TShark exists, normally at `C:\Program Files\Wireshark\tshark.exe`.
3. Install backend dependencies and start FastAPI on port 8000.
4. Configure the Pi IP, interface and controller values from `.env.example`. Never commit the controller token.

List capture interfaces and verify Pi reachability:

```powershell
python scripts/tshark_live.py --list-interfaces
Test-Connection 192.168.56.20 -Count 3
```

## Parser-only dry run

This requires neither Npcap nor a Pi:

```powershell
python scripts/tshark_live.py --dry-run --fixture scripts/fixtures/tshark_syn_sample.tsv
```

It prints the normalized payload and does not post it as live data.

## Start live telemetry

```powershell
python scripts/tshark_live.py `
  --interface 4 `
  --target-ip 192.168.56.20 `
  --api-url http://localhost:8000 `
  --device-id PI-001 `
  --job-id pi-syn-demo
```

Replace interface `4` and the IP with frozen lab values. Confirm state:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/devices/PI-001/state
```

Expected after clean traffic: `source_mode=live_hardware`, `sensor=tshark_npcap`, `state=HEALTHY`, trust at least 95. A quiet functioning capture sends an explicit zero-packet observation; it does not fabricate baseline traffic.

## Record labelled sessions

Normal:

```powershell
python scripts/tshark_live.py --interface 4 --target-ip 192.168.56.20 `
  --record data/pi_sessions.jsonl --label normal --scenario finals-normal
```

Controlled SYN, only in the isolated team-owned VM/Pi lab:

```powershell
python scripts/tshark_live.py --interface 4 --target-ip 192.168.56.20 `
  --record data/pi_sessions.jsonl --label syn_flood --scenario pi-syn-demo
```

Stop with Ctrl+C. Each JSONL row contains session ID, label, source, sensor, timestamp, attack job and points. Start a new process/session for each recording.
The recorder begins writing after 20 real one-second samples so every training row contains the frozen temporal sequence length; keep each capture running longer than 20 seconds.

## Physical acceptance

1. Start backend and frontend.
2. Start `tshark_live.py` on the verified Pi interface.
3. Generate normal traffic and confirm trust remains at least 95.
4. Start only the rate-limited registered `pi-syn-demo` job from the isolated VM.
5. Confirm raw SYN rate/incomplete ratio rise and handshake completion falls.
6. Confirm `AEGIS-SYN-001`, MITRE `T1498.001`, `ATTACK`, and trust below 30.
7. Call remediation and verify the controller actually stops `pi-syn-demo`.
8. Observe three clean windows and confirm trust returns above 95.
9. Repeat locally and record hardware results separately from replay/software acceptance.

### Exact Step 3 physical validation

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/system/capabilities
Invoke-RestMethod http://localhost:8000/api/v1/devices/PI-001/state
Invoke-RestMethod 'http://localhost:8000/api/v1/incidents?device_id=PI-001'
```

After starting the pre-registered `pi-syn-demo` job, verify one incident—not one per sample—then remediate:

```powershell
$incident = (Invoke-RestMethod 'http://localhost:8000/api/v1/incidents?device_id=PI-001').incidents[0]
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/devices/PI-001/remediate
Invoke-RestMethod "http://localhost:8000/api/v1/incidents/$($incident.incident_id)"
Invoke-WebRequest "http://localhost:8000/api/v1/incidents/$($incident.incident_id)/report" -OutFile incident.html
```

Independently confirm on the isolated VM that the registered attack process stopped. Then observe backend recovery progress `1/3`, `2/3`, and `3/3`; only the third clean hybrid window may produce `HEALTHY`, trust at least 95, and a closed/recovery-verified incident. Stop TShark for longer than the configured stale timeout and verify `STALE`; restart it and verify inference resumes from real telemetry.

## Attack-controller contract

```text
AEGIS_ATTACK_CONTROLLER_URL=http://192.168.57.10:9000
AEGIS_ATTACK_CONTROLLER_TOKEN=<local-shared-token>
AEGIS_ALLOWED_ATTACK_JOB_IDS=pi-syn-demo
```

```text
POST /jobs/pi-syn-demo/stop
Authorization: Bearer <local-shared-token>
Content-Type: application/json

{"job_id":"pi-syn-demo"}
```

The backend never accepts shell commands. An unreachable controller is visible failure, not successful containment.

## Failure handling

- Missing TShark: install Wireshark/Npcap or set `AEGIS_TSHARK_PATH`; no fake data is sent.
- Wrong interface/permission: use `--list-interfaces`, select the Pi adapter, and verify Npcap access.
- No packets: verify target address and adapter; inspect structured packet counts.
- FastAPI unavailable: `telemetry_post_failed` is logged and capture continues.
- Capture exit: diagnostic stderr is logged and capture reconnects unless `--no-reconnect` is used.

## Emergency replay

Replay remains explicitly labelled `recorded_replay`:

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/api/v1/demo/replay/pi_syn?speed=4"
```

It traverses the same engine/SSE path and is not a prerecorded UI video.

## Alternate Zeek sensor

```powershell
python scripts/zeek_tail.py C:\path\to\aegis_live.log --job-id pi-syn-demo
```

Zeek records normalize into the same API and report `sensor=zeek`.
