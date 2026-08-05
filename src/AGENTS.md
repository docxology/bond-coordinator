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
  `MissionPhase`.  A pure-core mirror of the Layer-1 `bond-api` protocol
  shapes.  `bond-api` is built; the mirror is the layer boundary that keeps
  `src/` free of sibling imports, not a placeholder (see
  `docs/architecture.md`).
- `registry.py` — `PackageRecord`, the 27-film `ROSTER`, `build_roster`,
  `get_package`, `find_by_status`, `subset_roster`, identity constants.
- `reconcile.py` — `override_codenames`, `harvest_gadgets`, `reconcile_report`:
  pure merge of real films' codenames + gadget tables over the provisional
  registry (refresh/replace semantics; inputs are immutable).  Also
  `gadget_purpose`, which derives a gadget's one-line purpose from its payload
  without ever borrowing a builtin type's docstring.
- `ledger.py` — `LedgerEntry`, `MissionLedger` (forward-only transitions,
  attributable-identity validation, `validate_transition`, append-only audit
  with deterministic summaries `transition_summary`/`per_agent_summary`/
  `phase_timeline`, staleness, lossless `to_json`/`from_json`).
- `status.py` — `CoverageSummary`, `BlockedPackage`, `LayerSummary`,
  `SUITE_LAYERS`, `SuiteStatus`, `build_status` (incl. `layer_ready`),
  `count_by_status`.
- `situation.py` — `build_situation_room` (coverage heat, mission-timeline
  bars, per-film gadget groups, suite-layers + recent-transitions sections),
  `write_situation_room` (HTML).
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
