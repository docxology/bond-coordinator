# AGENTS.md — bond-coordinator

**Mission control for the BOND suite** · codename **MISSION CONTROL** ·
Layer 2 of a 33-package fleet (27 film packages + 6 mission-infrastructure
packages).  This package is the authoritative **registry and situation room**:
it records, audits, and reports on the fleet; it implements no film algorithms.

This is an **active project** under `projects/working/bond/`.  Behavioral rules
for agents live in [`docs/agent_instructions.md`](docs/agent_instructions.md) —
**read it before modifying any file here**.  Architecture boundaries:
[`docs/architecture.md`](docs/architecture.md).  Test philosophy:
[`docs/testing_philosophy.md`](docs/testing_philosophy.md).

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/bond_coordinator/` (pure core) | stdlib + `pyyaml` only — **no** `infrastructure.*`, **no** sibling BOND imports, **no** filesystem side-effects. `MissionLedger` JSON persistence is provided as pure methods; only `scripts/` touches disk. |
| `scripts/` | Thin orchestrators: argv parsing, file I/O, the `bond-api` availability probe. May import `bond_coordinator`. |
| `tests/` | Zero-mock, real-data. Deterministic 5-film fixture in `conftest.py`; full-registry completeness assertions as well. |

Enforced by `docs/architecture.md` and the `manuscript/layer_contract.yaml`.

## Overview

`bond-coordinator` answers three questions about the BOND fleet:

1. **What exists?** — `registry.py` holds all 27 film packages (slug, film,
   year, mission codename, status `scaffolded|building|ready|red`, coverage).
2. **Where is it in its mission?** — `ledger.py` tracks
   `brief → recon → plan → execute → debrief` with forward-only transition
   rules and an append-only audit trail.
3. **Is it healthy?** — `status.py` aggregates counts by state/phase, a
   coverage summary, and stale/blocked flags; `situation.py` renders the whole
   fleet as one HTML document.

## Key features & capabilities

- **Registry**: canon-ordered 27-film `ROSTER` seeded from
  `projects/working/bond/SCOPE.md` §2.1, with provisional mission codenames
  assigned by mission control.
- **Ledger**: strict forward-only transitions, same-phase re-entry (touch),
  multi-step forward `jump`, append-only `history`, lossless
  `to_json`/`from_json` provenance.
- **Status**: deterministic snapshot `build_status(roster, ledger, now=, ...)`
  with injectable clock; stale = unfinished + older than threshold; blocked =
  red, executing-before-ready, or planning-before-building.
- **Situation room**: self-contained HTML (no JS, no external assets), all
  values HTML-escaped, deterministic given inputs.
- **Manuscript variables**: identity from `manuscript/config.yaml` + registry
  counts injected as `{{TOKEN}}`s — never hand-authored in prose.
- **Zero-mock, ≥90%** (`--cov-fail-under=90` on `src/`), ruff + mypy clean.

## Repository layout

```
src/bond_coordinator/
    types.py                Asset, Gadget, GadgetRegistry, PackageStatus, MissionPhase (bond-api mirror)
    registry.py             PackageRecord, ROSTER (27), build_roster, get_package, find_by_status, subset_roster
    ledger.py               LedgerEntry, MissionLedger (transitions, audit, staleness, JSON)
    status.py               CoverageSummary, BlockedPackage, SuiteStatus, build_status
    situation.py            build_situation_room, write_situation_room
    manuscript_variables.py load_config, generate_variables, resolve_manuscript_tree
    __init__.py             public API
scripts/
    status_report.py        print/persist suite status (human or --json)
    advance_mission.py      advance a package's phase in the persisted ledger
    build_situation_room.py regenerate output/situation_room.html
    z_generate_manuscript_variables.py  hydrate {{TOKEN}}s (runs last; z_ prefix)
tests/
    conftest.py             5-film deterministic fixture + fixed clock
    test_registry.py test_ledger.py test_status.py test_situation.py
    test_manuscript_variables.py test_scripts_smoke.py
manuscript/                 config.yaml identity + 8 sections with {{TOKEN}} injection
docs/                       agent-facing rulebook (read-first: agent_instructions.md)
output/                     gitignored generated artifacts (indicative only)
```

## Install / run

Dependencies install from this directory with `uv sync --extra dev`.  This
package is not part of the template uv workspace (`members = []`), so run all
commands from **inside** this directory.

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src scripts tests
uv run mypy
```

## Usage examples

### Programmatic

```python
from bond_coordinator import (
    build_roster, MissionLedger, MissionPhase, build_status,
    build_situation_room, GadgetRegistry,
)

roster = build_roster()                       # all 27 film packages
ledger = MissionLedger(roster)                # every package at brief
ledger.advance("goldfinger", "agent-007", "0.1.0")   # brief -> recon
ledger.jump("skyfall", "debrief", "agent-007", "0.1.0")
status = build_status(roster, ledger)
print(status.counts_by_status)
html = build_situation_room(status, roster, ledger, GadgetRegistry())
```

### CLI

```bash
uv run python scripts/status_report.py
uv run python scripts/advance_mission.py --slug goldfinger --phase plan --by agent-007
uv run python scripts/build_situation_room.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Testing

```bash
# Canonical gate (from this directory):
uv run pytest tests/ --cov=src --cov-fail-under=90

# With missing-line detail:
uv run pytest tests/ --cov=src --cov-report=term-missing
```

- **Zero-mock policy**: no `unittest.mock`, `MagicMock`, `@patch`, or
  `create_autospec` anywhere in `tests/`.  Every test uses real data and real
  computation.
- **Determinism**: the fixture pins a fixed UTC clock; all time-dependent
  assertions use it; the situation room is asserted byte-identical across
  repeated builds.
- **Fixture**: a 5-film subset (`dr_no`, `goldfinger`, `goldeneye`, `skyfall`,
  `no_time_to_die`) seeds behavior tests; a full-registry test independently
  asserts 27 unique, canon-ordered packages.

## Troubleshooting

- **`ModuleNotFoundError: bond_coordinator`** — run from this directory, or
  ensure `src/` is on `PYTHONPATH` (scripts bootstrap it themselves).
- **Coverage below 90%** — do not delete tests to make the number work; the
  situation room, ledger JSON, and manuscript variables all carry dedicated
  tests.  Fix the gap.
- **`output/` changes not showing in git** — correct: `output/` is gitignored
  and regenerated.  Do not hand-edit generated files.

## Compliance

- Coverage gate: `--cov-fail-under=90` (line + branch) on `src/`.
- Zero mocks (lexical gate + semantic inventory).
- Deterministic: fixed clock, no wall-clock tokens, no untracked random draws.
- Types/style: `ruff check` + `mypy` clean on `src/bond_coordinator` and
  `scripts/`.
- Boundary: `src/` core has no `infrastructure.*` or sibling imports (drift
  check pattern from the template).
- Identity: no leftover exemplar identity strings anywhere in this fork.

## See also

- `docs/agent_instructions.md` — read-first behavioral rules.
- `docs/architecture.md`, `docs/testing_philosophy.md` — boundaries + test bar.
- `manuscript/config.yaml` + `manuscript/SYNTAX.md` — identity + `{{TOKEN}}` table.
- `../SCOPE.md` — the fleet roster (§2.1) this registry mirrors.
