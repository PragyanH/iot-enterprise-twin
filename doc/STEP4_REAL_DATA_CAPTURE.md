# Step 4A — Real Data Capture Protocol

Status: **SOFTWARE PREPARATION COMPLETE — PHYSICAL CAPTURE PENDING.**

This document is the operator checklist for capturing a real PI-001 dataset.
It does not train or calibrate anything. Step 4B (training/calibration/model
freeze) may only begin after a capture here passes
`scripts/validate_pi_sessions.py` with zero `FAIL` issues. See
`doc/HARDWARE_DEMO_RUNBOOK.md` for the underlying topology/contract details
and `scripts/lab_vm/README.md` for the VM side.

## Exact physical order

1. Windows backend works (`uvicorn` starts, `/api/v1/health` returns `ok`).
2. Connect the Raspberry Pi to Windows.
3. Windows sees the Pi network adapter.
4. Assign/freeze lab IPs (Pi, Windows Pi-facing adapter, VM NICs).
5. Ping the Pi.
6. SSH the Pi.
7. Verify the TShark interface: `python scripts/tshark_live.py --list-interfaces`.
8. Run `python scripts/finals_preflight.py --pi-ip <PI_IP> --interface <IFACE> --json` and confirm no `FAIL`.
9. Start TShark live telemetry (`python scripts/tshark_live.py --interface <IFACE> --target-ip <PI_IP>`).
10. Confirm `GET /api/v1/devices/PI-001/state` reports `source_mode=live_hardware`, `sensor=tshark_npcap`.
11. Confirm normal telemetry is sensible (trust >= 95, state HEALTHY).
12. Record several independent NORMAL sessions (below).
13. Install/configure VMware (see `scripts/lab_vm/README.md`).
14. Configure the management NIC (VM <-> Windows controller traffic).
15. Configure the attack NIC (VM <-> Pi, bound to the Pi-facing adapter).
16. Verify VM -> Pi reachability (`ping` from inside the VM).
17. Run `aegis_lab_agent.py` on the VM.
18. Verify Windows -> controller (`GET /health`, `GET /jobs/pi-syn-demo/status`).
19. Start the controlled Scapy SYN scenario (`pi_syn_demo.py`, or `POST /jobs/pi-syn-demo/start` if enabled).
20. Confirm TShark sees real divergence (SYN rate up, handshake completion down).
21. Record several independent SYN sessions (below).
22. Stop the attack using the controller (`POST /jobs/pi-syn-demo/stop`).
23. Verify the Pi remains manageable (SSH/ping still work).
24. Run `python scripts/validate_pi_sessions.py data/finals-capture/pi_sessions.jsonl --json --write-manifest`.
25. **STOP.** Step 4B training may only begin after the dataset passes with zero `FAIL` issues.

## Capture protocol

We want **multiple independent sessions**, not one giant recording. Each
recording is its own process invocation of `tshark_live.py`, which mints its
own `session_id` — never reuse a `session_id` across recordings and never
let a single session span both normal and attack phases.

### NORMAL

5-8 independent sessions, each roughly 45-90 seconds, covering realistic
finals activity: Pi idle, an SSH session, normal management traffic, and
ordinary device network traffic. Do not run the SYN scenario during a
NORMAL recording.

```powershell
python scripts\tshark_live.py `
  --interface <PI_INTERFACE> `
  --target-ip <PI_IP> `
  --record data\finals-capture\pi_sessions.jsonl `
  --label normal `
  --scenario finals-normal-01 `
  --duration-seconds 60
```

Repeat with incrementing scenario names (`finals-normal-02`, ...) for each
independent session.

### SYN

5-8 independent attack sessions. **Every window inside a `syn_flood`-labelled
session must be genuine, stable attack traffic — no baseline lead-in and no
recovery/cooldown windows.** This is a training-label requirement, not a
demo-narrative requirement: the live finals demo still shows baseline ->
attack -> recovery on screen, but that full arc must never be captured
inside one `syn_flood`-labelled training recording.

Order of operations for each SYN session:

1. Start the controlled job from the VM **first**:

   ```bash
   python3 pi_syn_demo.py --target-ip <PI_IP> --port 8443 --rate 250 --duration-seconds 45
   ```

   Or, if `--enable-start` is configured on the lab agent:

   ```powershell
   Invoke-RestMethod -Method Post http://<VM_MGMT_IP>:9000/jobs/pi-syn-demo/start -Headers @{Authorization="Bearer $env:AEGIS_ATTACK_CONTROLLER_TOKEN"}
   ```

2. Wait approximately **3-5 seconds** for the physical traffic signature to
   stabilize (SYN rate up, handshake completion collapsed) before recording
   anything.

3. Only then start the `syn_flood`-labelled recording:

   ```powershell
   python scripts\tshark_live.py `
     --interface <PI_INTERFACE> `
     --target-ip <PI_IP> `
     --record data\finals-capture\pi_sessions.jsonl `
     --label syn_flood `
     --scenario finals-syn-01 `
     --duration-seconds 45
   ```

4. **Stop the labelled recording before stopping the attack** (Ctrl+C or let
   `--duration-seconds` end it), so the session never trails off into
   recovery traffic. Only after the recording has stopped, stop the attack:

   ```powershell
   Invoke-RestMethod -Method Post http://<VM_MGMT_IP>:9000/jobs/pi-syn-demo/stop -Headers @{Authorization="Bearer $env:AEGIS_ATTACK_CONTROLLER_TOKEN"}
   ```

## Session independence

Each physical recording gets a new `session_id` (minted automatically by
`tshark_live.py` per process invocation). Do not record 500 windows under
one session and treat them as independent held-out examples — Step 4B splits
by session, not by window. `validate_pi_sessions.py` reports how many
independent sessions exist per label and warns if there are too few for a
meaningful held-out split.

## Port scan / SSH brute-force classes

The known classifier also defines `port_scan` and `ssh_bruteforce`, but SYN
flood is the only mandatory physical attack for the finals hardware path.
Do not delay Step 4A capture waiting for physical port-scan/SSH data, and do
not fabricate physical validation for those classes — Step 4B may combine
real NORMAL/SYN data with existing controlled data for the secondary known
classes, with clearly scoped metrics.

## Optional raw PCAP sidecar

If easy and completely independent, run Dumpcap/TShark PCAP recording in
parallel for forensic backup. Model training must still use the normalized
Aegis telemetry JSONL from `tshark_live.py --record`; PCAP is never a
critical dependency.

## Before trusting any capture

1. Inspect real NORMAL PI-001 ranges directly from the validator's feature
   sanity report (`python scripts/validate_pi_sessions.py ...`) — SYN rate,
   IAT, handshake completion, incomplete ratio, flow symmetry, orig/resp
   packets, packet size. Do not overwrite `baselines.json` from one
   recording; Step 4B computes robust statistics across independent normal
   sessions.
2. Confirm the controlled attack visibly produced SYN rate up, incomplete
   ratio up, handshake completion down, IAT down, and flow symmetry
   down/orig-resp divergence, via the validator's NORMAL vs SYN FLOOD table.
   If it did not, diagnose the physical capture/topology first — do not
   "fix" the model to match a bad capture.

## Exit state

This document ends at **PHYSICAL CAPTURE PENDING**. Step 4B (training,
calibration, model freeze) begins only once:

- `scripts/finals_preflight.py` reports `HARDWARE ATTACK PATH READY`;
- at least 5 independent NORMAL sessions and 5 independent SYN sessions
  exist in `data/finals-capture/pi_sessions.jsonl`;
- `scripts/validate_pi_sessions.py` reports zero `FAIL` issues and a
  believable NORMAL vs SYN FLOOD separation.
