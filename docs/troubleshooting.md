# Troubleshooting — bond-coordinator

## `ModuleNotFoundError: bond_coordinator`

Run from this package directory, or ensure `src/` is on `PYTHONPATH`.
`scripts/*.py` bootstrap their own `sys.path` to `../src`, so
`uv run python scripts/<name>.py` works from the package root.

## Coverage below 90%

`uv run pytest tests/ --cov=src --cov-report=term-missing` shows the gaps.
Do **not** delete tests.  Common gaps: an error path (unknown slug, malformed
JSON, missing config token) or a `GadgetRegistry` branch.  Add a focused test.

## `ValueError: ... moves the mission backwards`

You called `advance`/`jump` to an earlier phase.  The ledger is forward-only
by design; use the current or a later phase.  To re-stamp the current phase
use `touch` (or `jump` to the same phase).

## `ValueError: malformed ledger JSON` / `ledger references unknown package`

A persisted `output/data/mission_ledger.json` is corrupt or from a different
roster.  Regenerate: delete the file (it is disposable) and re-run
`scripts/advance_mission.py`, or rebuild with `scripts/status_report.py`.

## Situation room shows "No gadgets registered yet"

That is correct until gadget data exists.  Provide `output/data/gadgets.json`
with records `{"name", "film", "purpose"}` and run
`scripts/build_situation_room.py`.

## `importlib.util.find_spec("bond_api")` returns False

Expected: `bond-api` (Layer 1) is not built yet.  The coordinator runs on its
pure-core protocol mirror and reports `dependency_ready: false`.  No action
needed.

## Git shows no changes under `output/`

Correct: `output/` is gitignored and regenerated.  Commit only source/config/
docs changes.
