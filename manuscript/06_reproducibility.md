# Reproducibility Certification {#sec:reproducibility}

Reproducibility is a first-order requirement for mission control, because the
suite's provenance story depends on it.

## Determinism

- **Injectable clocks**: every time-dependent path (`MissionLedger`, `build_status`,
  `is_stale`) accepts an injectable `now`; tests pin a fixed UTC reference clock and
  assert exact timestamps and byte-identical outputs.
- **No wall-clock tokens**: `manuscript_variables.py` emits no
  `GENERATION_TIMESTAMP`-style token, so manuscript bytes depend only on the
  config file and registry/ledger state.  A test asserts the situation room is
  byte-identical across repeated builds with identical inputs.
- **Fixed seeds**: no random draws anywhere in `src/` or `tests/`.

## Provenance

- The ledger is **append-only**: every transition is recorded in the audit
  trail, and `to_json()`/`from_json()` round-trip state and history
  losslessly.  A thin CLI (`scripts/advance_mission.py`) persists the ledger to
  `output/data/mission_ledger.json` after each move.
- Generated artifacts — `output/situation_room.html`,
  `output/data/suite_status.json`, `output/data/manuscript_variables.json`, and
  the resolved manuscript tree — are gitignored and understood to be disposable:
  they are always regenerated from source, never hand-edited.

## Verification

The certification commands (identical to the enforced gates) are:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/bond_coordinator scripts
uv run mypy src/bond_coordinator scripts
```

A dependency on the not-yet-built Layer-1 package (`bond-api`) is detected at
runtime by a thin `import` probe in `scripts/`, reported in the status and
situation-room output, and — until it is available — the suite runs on the
pure-core protocol mirror described in `docs/architecture.md`.
