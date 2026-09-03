# Scripts

This folder is reserved for operational automation and project maintenance tasks.

Planned contents include:

- model training entrypoints
- data preparation and preprocessing utilities
- deployment or bootstrap helpers
- validation and smoke tests
- database migration or repair scripts
- one-off maintenance commands

Implemented scripts:

- `train_hybrid_models.py`: trains the 64/16 LSTM-VAE checkpoints and Pi XGBoost classifier from labeled JSONL sessions or controlled synthetic demo data.
- `tshark_live.py`: primary Windows Npcap/TShark adapter; derives one-second PI-001 telemetry, forwards it to FastAPI, and optionally records labelled JSONL sessions.
- `zeek_tail.py`: tails the JSON `aegis_live.log` stream and posts one-second Pi telemetry windows to FastAPI.
- `zeek/aegis-live.zeek`: emits live SYN/handshake counters for the Raspberry Pi target.
- `run_demo_acceptance.py`: executes the complete normal → known SYN/T1498.001 → exactly-one incident → frozen forensic report → replay containment → 1/3, 2/3, 3/3 recovery → verified closure workflow repeatedly without requiring the web stack.

Quick verification:

```bash
python scripts/run_demo_acceptance.py --loops 20
```

Bootstrap learned demo artifacts inside the backend environment:

```bash
python scripts/train_hybrid_models.py --synthetic-demo --epochs 30
```

The training JSONL format matches `POST /api/v1/telemetry/windows` and adds `label` plus `session_id` to every row.

List Windows capture interfaces:

```powershell
python scripts/tshark_live.py --list-interfaces
```

Validate parsing without TShark or live packets:

```powershell
python scripts/tshark_live.py --dry-run --fixture scripts/fixtures/tshark_syn_sample.tsv
```

Capture and record a labelled normal session:

```powershell
python scripts/tshark_live.py --interface 4 --target-ip 192.168.56.20 --record data/pi_sessions.jsonl --label normal --scenario finals-baseline
```

The adapter intentionally exits with a clear error when TShark is unavailable; it never replaces failed live capture with generated telemetry.

## Demo user seed

`seed_demo_users.py` idempotently creates `admin@aegis.local`, `owner@aegis.local`, and `vendor@aegis.local`. Passwords are read only from environment variables and are never embedded or printed.

```powershell
$env:AEGIS_DEMO_ADMIN_PASSWORD="choose-a-demo-secret"
$env:AEGIS_DEMO_OWNER_PASSWORD="choose-a-different-secret"
$env:AEGIS_DEMO_VENDOR_PASSWORD="choose-a-third-secret"
python scripts/seed_demo_users.py
```
