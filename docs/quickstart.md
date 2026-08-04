# Quickstart — bond-coordinator

5-minute first-run walkthrough.

## 1. Install

```bash
cd projects/working/bond/bond-coordinator
uv sync --extra dev
```

## 2. Run the gate

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

## 3. Drive mission control

```bash
# Fleet status (human + JSON); also writes output/data/suite_status.json
uv run python scripts/status_report.py
uv run python scripts/status_report.py --json

# Advance a package's phase (persists output/data/mission_ledger.json)
uv run python scripts/advance_mission.py --slug goldfinger --phase recon \
    --by agent-007 --version 0.1.0

# Render the situation room (output/situation_room.html)
uv run python scripts/build_situation_room.py

# Hydrate manuscript tokens (output/manuscript/*.md)
uv run python scripts/z_generate_manuscript_variables.py
```

## 4. Inspect the fleet programmatically

```python
from bond_coordinator import build_roster, MissionLedger, build_status

roster = build_roster()                       # 27 film packages
ledger = MissionLedger(roster)
ledger.advance("goldfinger", "agent-007", "0.1.0")
status = build_status(roster, ledger)
print(status.counts_by_status)
print([r.codename for r in roster[:5]])
```

## What you should see

- `status_report.py` prints `BOND — MISSION CONTROL`, `Packages: 27 total`,
  and by-status/by-phase counts (all scaffolded / all brief on a fresh ledger).
- The situation room shows all 27 slugs and, until gadgets are supplied, a
  "No gadgets registered yet" note.
- `.venv/` and `output/` are created locally and gitignored.
