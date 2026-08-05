# scripts/ — Thin Orchestrators

## Overview

`scripts/` contains **thin orchestrators** only.  All business logic — registry
content, transition rules, status aggregation, HTML generation, token maps —
lives in `src/bond_coordinator/` and is tested there — *interpretation* counts
as business logic, which is why `reconcile.gadget_purpose` lives in `src/` and
not inline here.  Scripts parse argv, touch files, discover film providers
through `bond-api` (and probe its availability), and delegate to the pure core.

**Cross-package reads must degrade, never abort.**  `reconcile.py` imports
independently developed sibling packages; each film is guarded with
`except Exception`, its failure printed to stderr with the exception type, and
the slug recorded as skipped.  One broken sibling must never end a fleet-wide
run, and a skip must never be silent.

## Scripts

| Script | Responsibility | Primary output |
|---|---|---|
| `status_report.py` | Print/persist the aggregate suite status (human or `--json`, per-layer summary). | `output/data/suite_status.json` |
| `advance_mission.py` | Advance one package's phase in the persisted ledger (validated, forward-only). | `output/data/mission_ledger.json` |
| `build_situation_room.py` | Regenerate the situation-room HTML dashboard. | `output/situation_room.html` |
| `reconcile.py` | Reconcile registry codenames + harvest gadgets from real films via `bond-api`. | reconciled manifest / `gadgets.json` |
| `z_generate_manuscript_variables.py` | Hydrate manuscript `{{TOKEN}}`s (runs last; `z_` prefix). | `output/data/manuscript_variables.json`, `output/manuscript/*.md` |

## Usage

```bash
uv run python scripts/status_report.py [--json] [--ledger PATH]
uv run python scripts/advance_mission.py --slug <s> --phase <p> [--by USER] [--version V] [--note N] [--ledger PATH]
uv run python scripts/build_situation_room.py [--out PATH]
uv run python scripts/reconcile.py [--slugs FILM ...] [--write PATH] [--gadgets PATH]
uv run python scripts/z_generate_manuscript_variables.py [--config PATH] [--allow-draft]
```

## Conventions

- Each script computes `PROJECT_ROOT = Path(__file__).resolve().parent.parent`
  and inserts `../src` into `sys.path` so it runs from the package root.
- Scripts never contain business logic (no transition rules, no counts, no
  HTML); any such line is a boundary violation (see `../docs/architecture.md`).
- Scripts exit non-zero on illegal/unknown input (e.g. `advance_mission.py`
  returns 1 for a backwards transition).
- `z_` prefix keeps `z_generate_manuscript_variables.py` last alphabetically.

## Testing

Covered end-to-end by `tests/test_scripts_smoke.py` (real subprocesses, exit
codes, persisted artifacts).  `ruff` + `mypy` clean.
