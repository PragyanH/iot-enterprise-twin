# Aegis Lab VM — Controlled Attack Tooling

This directory is intentionally isolated from `services/backend` and the rest
of `scripts/`. It contains only the narrow, controlled attack tooling that
runs **inside the team-owned VMware Linux VM**, never on the Windows host.

```text
scripts/lab_vm/
  pi_syn_demo.py       controlled SYN scenario generator (single target, bounded rate/lifetime)
  aegis_lab_agent.py    VM-side attack controller (pi-syn-demo only, no shell surface)
  tests/                unit tests; never send real packets or spawn real subprocesses
```

Both scripts are stdlib + Scapy only — no FastAPI/uvicorn is required inside
the VM. No Docker is required or expected inside the VM.

## Safety model (do not weaken without updating `tests/`)

- `pi_syn_demo.py` only accepts a single explicit private/lab IPv4/IPv6
  address (no hostnames, no ranges, no public addresses). A requested rate
  above `AEGIS_LAB_SYN_RATE_MAX` (default 400/s) is **rejected with a
  non-zero exit**, never silently run at a different rate than requested;
  lifetime is clamped to `AEGIS_LAB_SYN_MAX_DURATION_SECONDS` (default 120s)
  regardless of what is requested. No source-IP spoofing, no payload
  options, no port sweeping. Ctrl+C stops it immediately.
- `aegis_lab_agent.py` only understands the literal job id `pi-syn-demo`. It
  never accepts a shell command, script path, or arbitrary target/rate from
  an HTTP request body — `start` always launches `pi_syn_demo.py` with
  arguments built from the agent's own local environment configuration, and
  request bodies are read and discarded. `stop`/`start` require
  `Authorization: Bearer <AEGIS_ATTACK_CONTROLLER_TOKEN>`; `start` is
  disabled by default (`--enable-start` / `AEGIS_LAB_AGENT_ENABLE_START=true`
  to turn it on) so a human always decides when the attack begins.

## VM install runbook

1. Install VMware Workstation/Player on the Windows host.
2. Create a lightweight Linux VM (e.g. Debian/Ubuntu minimal or Alpine with
   Python 3). No Docker is required inside the VM.
3. Configure **two virtual NICs**:
   - **NIC 1 — Management (host-only)**: used only for
     `Windows FastAPI <-> VM attack controller` traffic (the `aegis_lab_agent.py`
     HTTP API). Example: Windows `172.16.50.1`, VM `172.16.50.10`.
   - **NIC 2 — Attack path**: bind this adapter specifically to the Windows
     network adapter the Raspberry Pi is connected to (not VMware's automatic
     bridge, if an explicit adapter binding is available). Example: Windows Pi
     adapter `192.168.56.1`, VM attack NIC `192.168.56.10`, Pi `192.168.56.20`.
4. Install Python 3 and Scapy inside the VM:

   ```bash
   sudo apt-get update && sudo apt-get install -y python3 python3-pip
   pip3 install scapy
   ```

5. Copy this `lab_vm/` directory to the VM (e.g. `scp -r scripts/lab_vm vm-user@172.16.50.10:~/aegis-lab-vm`).
6. Set the shared configuration on the VM before starting the agent:

   ```bash
   export AEGIS_ATTACK_CONTROLLER_TOKEN="<same local shared token as Windows AEGIS_ATTACK_CONTROLLER_TOKEN>"
   export AEGIS_PI_TARGET_IP="192.168.56.20"
   export AEGIS_LAB_SYN_PORT="8443"
   export AEGIS_LAB_SYN_RATE="250"
   ```

7. Start the controller (management NIC only; do not expose it on the attack NIC):

   ```bash
   python3 aegis_lab_agent.py --bind-host 172.16.50.10 --port 9000
   ```

8. From Windows, verify the controller:

   ```powershell
   Invoke-RestMethod http://172.16.50.10:9000/health
   Invoke-RestMethod http://172.16.50.10:9000/jobs/pi-syn-demo/status
   ```

9. From the VM, verify the Pi is reachable on the attack NIC before ever
   running the scenario:

   ```bash
   ping -c 3 192.168.56.20
   ```

10. Run the controlled scenario manually when ready (or enable `--enable-start`
    on the agent so the backend's remediation contract, and an authenticated
    operator command, can start/stop it):

    ```bash
    python3 pi_syn_demo.py --target-ip 192.168.56.20 --port 8443 --rate 250 --duration-seconds 60
    ```

11. Stop the registered job from Windows using the existing remediation
    contract (`AttackControllerStopProvider`) or directly:

    ```powershell
    Invoke-RestMethod -Method Post http://172.16.50.10:9000/jobs/pi-syn-demo/stop -Headers @{Authorization="Bearer $env:AEGIS_ATTACK_CONTROLLER_TOKEN"}
    ```

## What this is not

- Not a general port-scanner or attack framework — it only ever targets one
  pre-configured lab IP with SYN packets.
- Not a replacement for `services/backend/api/app/services/remediation.py` —
  the backend's `AttackControllerStopProvider` is the authenticated client;
  this agent is the server it talks to.
- Not required to run with Docker; keep it a native VM process.
