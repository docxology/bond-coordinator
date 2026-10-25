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
`scripts/advance_mission.py`, which rewrites it from the registry.  The
reporting scripts (`status_report.py`, `build_situation_room.py`) only read that
file — they never rebuild it.

## Situation room shows "No gadgets registered yet"

That is correct until gadget data exists.  Provide `output/data/gadgets.json`
with records `{"name", "film", "purpose"}` and run
`scripts/build_situation_room.py`.

## `importlib.util.find_spec("bond_api")` returns False

This is an **importability** result, not an existence claim: `bond-api` is
built, but it is not installed in this interpreter's environment.  The
coordinator reports `dependency_ready: false`, renders "not importable in this
environment (pure-core mirror in use)", and keeps working — the pure core never
needed it.  No action is required unless you want live reconciliation:
`scripts/reconcile.py` needs `bond_api` importable to read films' real
codenames, and without it every film keeps its provisional codename (reported
on stderr).

## Git shows no changes under `output/`

Correct: `output/` is gitignored and regenerated.  Commit only source/config/
docs changes.
