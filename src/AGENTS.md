# src/ — Pure-Core Mission Control

## Overview

`src/bond_coordinator/` is the **pure core** of this package: registry,
mission-state ledger, aggregate status, situation room, and manuscript
variables.  It imports only the standard library plus `pyyaml` — no
`infrastructure.*`, no sibling BOND packages, and no filesystem side-effects.
This purity lets the core run in any Python 3.10+ environment, exactly as the
exemplar's mathematical core could.

## Modules

- `types.py` — `Asset`, `AssetKind`, `Gadget`, `GadgetRegistry`, `PackageStatus`,
  `MissionPhase`.  A pure-core mirror of the Layer-1 `bond-api` protocol shapes
  (swap point documented in `TODO.md`).
- `registry.py` — `PackageRecord`, the 27-film `ROSTER`, `build_roster`,
  `get_package`, `find_by_status`, `subset_roster`, identity constants.
- `ledger.py` — `LedgerEntry`, `MissionLedger` (forward-only transitions,
  append-only audit, staleness, lossless `to_json`/`from_json`).
- `status.py` — `CoverageSummary`, `BlockedPackage`, `SuiteStatus`,
  `build_status`, `count_by_status`.
- `situation.py` — `build_situation_room`, `write_situation_room` (HTML).
- `manuscript_variables.py` — `load_config`, `generate_variables`,
  `resolve_manuscript_tree`.
- `__init__.py` — public API re-export (`__all__`).

## Layer boundary

`src/` never calls `scripts/`, never touches the filesystem, and never imports
`infrastructure.*` or a sibling package.  `scripts/` is the only layer that
reads/writes files and probes for `bond_api`.

## Testing

Zero-mock, deterministic suite over a 5-film fixture (`tests/conftest.py`) plus
full-registry completeness checks.  Gate: `--cov=src --cov-fail-under=90`.

## Adding a module

1. Keep it pure (stdlib + pyyaml; no I/O, no infra imports).
2. Export the public surface in `__init__.py`.
3. Add a dedicated test file covering success *and* error paths.
4. Run `uv run ruff format` and `uv run mypy` before committing.
