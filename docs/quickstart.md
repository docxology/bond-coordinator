# Quickstart — bond-coordinator

5-minute first-run walkthrough.

## 1. Install

```bash
# from this repository's root
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

- `status_report.py` prints `PROJECT BOND — MISSION CONTROL`, `Packages: 27 total`,
  by-status/by-phase counts, and a `gates:` line naming where the status and
  coverage numbers came from.  With `--no-gate-manifest` (or no manifest on
  disk) that line reads `none applied — registry seed defaults`, and the
  by-status counts are the seed's, not a measurement of the film packages.
- The situation room shows all 27 slugs, a **Data provenance** block naming the
  codename and measurement sources, and — until gadgets are supplied — a
  "No gadgets registered yet" note.  Pass `--reconciled` (from
  `scripts/reconcile.py --write`) to show film-declared codenames and
  `--gate-manifest` to show measured coverage.
- `.venv/` and `output/` are created locally and gitignored.
