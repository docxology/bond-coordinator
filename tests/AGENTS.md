# tests/ — Test Suite

## Overview

Zero-mock, deterministic tests for `bond-coordinator`.  Every test uses real
data, real computation, and real files; there is no `unittest.mock` /
`MagicMock` / `@patch` anywhere.

## Key concepts

- **5-film fixture**: `conftest.py` defines `sample_slugs` (dr_no, goldfinger,
  goldeneye, skyfall, no_time_to_die), `sample_roster` (real records via
  `subset_roster`), `fixed_clock` (pinned `FIXED_NOW`), `sample_gadgets`, and
  `aged_ledger`.  Behavior tests never depend on the other 22 films.
- **Determinism**: all time-dependent assertions use `FIXED_NOW`; the
  situation room is asserted byte-identical across repeated builds.
- **Coverage**: enforced `--cov=src --cov-fail-under=90` (line + branch).

## Files

| File | Covers |
|---|---|
| `conftest.py` | path setup + fixtures |
| `test_registry.py` | ROSTER completeness (27), accessors, `subset_roster`, `GadgetRegistry` (+ errors) |
| `test_ledger.py` | transitions (forward/touch/jump/backwards/past-debrief), `validate_transition` + identity validation, audit summaries (`transition_summary`, `per_agent_summary`, `phase_timeline`), staleness, JSON (+ malformed/unknown/incomplete) |
| `test_status.py` | fresh vs mixed fleets, coverage summary, blocked rules, stale flags, per-layer summaries (`SUITE_LAYERS`, `layer_ready`), count helpers |
| `test_situation.py` | HTML structure, coverage heat buckets, mission-timeline bars, per-film gadget groups, suite-layers section, audit-trail timeline, escaping, determinism, file write |
| `test_reconcile.py` | codename overrides, gadget harvest (refresh/idempotent), report; real-films CLI smoke |
| `test_manuscript_variables.py` | config parsing (+ errors), tokens (full/subset, layer/ledger), tree resolution, live `{{TOKEN}}` cross-reference gate |
| `test_scripts_smoke.py` | thin orchestrators end-to-end (incl. layers in status JSON + situation HTML); illegal transitions exit 1 |

## Running

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run pytest tests/ --cov=src --cov-report=term-missing   # gap detail
```

## Rules

- No mocks.  If a test uses a fake, it is a defect.
- Do not delete tests to raise coverage — fix the gap.
- All error paths (`ValueError`, `KeyError`, `FileNotFoundError`) are exercised.
