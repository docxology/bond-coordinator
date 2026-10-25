# AGENTS.md — bond-coordinator

**Mission control for the BOND suite** · codename **MISSION CONTROL** ·
Layer 2 of a 33-package fleet (27 film packages + 6 mission-infrastructure
packages).  This package is the authoritative **registry and situation room**:
it records, audits, and reports on the fleet; it implements no film algorithms.

This is the standalone `bond-coordinator` repository — the fleet's other
packages (`../bond-api`, `../bond-utilities`, `../bond-ops`, `../bond-cli`,
`../bond-orchestrator`, and the 27 `../bond-<film>` repos) are sibling
checkouts, never subdirectories.  Behavioral rules
for agents live in [`docs/agent_instructions.md`](docs/agent_instructions.md) —
**read it before modifying any file here**.  Architecture boundaries:
[`docs/architecture.md`](docs/architecture.md).  Test philosophy:
[`docs/testing_philosophy.md`](docs/testing_philosophy.md).

## Layer contract

| Surface | Rule |
| --- | --- |
| `src/bond_coordinator/` (pure core) | stdlib + `pyyaml` only — **no** `infrastructure.*`, **no** sibling BOND imports, and no filesystem side-effects beyond the two writers that take an explicit destination (`situation.write_situation_room`, `manuscript_variables.resolve_manuscript_tree`). `MissionLedger` JSON persistence is provided as pure methods; `scripts/` supplies every path. |
| `scripts/` | Thin orchestrators: argv parsing, file I/O, `bond-api` provider discovery + availability probe. May import `bond_coordinator`. Cross-package reads are guarded per film with `except Exception` and reported on stderr — one broken sibling must never abort a fleet-wide run. |
| `tests/` | Zero-mock, real-data. Deterministic 5-film fixture in `conftest.py`; full-registry completeness assertions as well. |

Enforced by `docs/architecture.md` and the `manuscript/layer_contract.yaml`.

## Overview

`bond-coordinator` answers three questions about the BOND fleet:

1. **What exists?** — `registry.py` holds all 27 film packages (slug, film,
   year, mission codename, status `scaffolded|building|ready|red`, coverage).
   The shipped literal leaves status/coverage at unmeasured seed defaults;
   `gates.py` is the only path by which they become measured values.
2. **Where is it in its mission?** — `ledger.py` tracks
   `brief → recon → plan → execute → debrief` with forward-only transition
   rules and an append-only audit trail.
3. **Is it healthy?** — `status.py` aggregates counts by state/phase, a
   coverage summary, and stale/blocked flags; `situation.py` renders the whole
   fleet as one HTML document.

## Key features & capabilities

- **Registry**: canon-ordered 27-film `ROSTER` (the literal in
  `src/bond_coordinator/registry.py` is the authority), with provisional mission
  codenames assigned by mission control.
- **Ledger**: strict forward-only transitions, same-phase re-entry (touch),
  multi-step forward `jump`, append-only `history`, lossless
  `to_json`/`from_json` provenance.
- **Status**: deterministic snapshot `build_status(roster, ledger, now=, ...)`
  with injectable clock; stale = unfinished + older than threshold; blocked =
  red, executing-before-ready, or planning-before-building.
- **Situation room**: self-contained HTML (no JS, no external assets), all
  values HTML-escaped, deterministic given inputs.
- **Reconcile**: merges films' real codenames + gadget tables over the
  provisional registry with refresh/replace semantics; `gadget_purpose` derives
  a gadget's one-line purpose from its payload without ever borrowing a
  builtin's docstring.
- **Manuscript variables**: identity from `manuscript/config.yaml` + registry
  counts, roster span, and enforced-gate thresholds injected as `{{TOKEN}}`s —
  never hand-authored in prose.
- **Zero-mock, ≥90%** (`--cov-fail-under=90` on `src/`), ruff + mypy clean.

## Repository layout

```
src/bond_coordinator/
    types.py                Asset, AssetKind, Gadget, GadgetRegistry, PackageStatus, MissionPhase (bond-api mirror)
    registry.py             PackageRecord, ROSTER (27), build_roster, get_package, find_by_status, subset_roster
    reconcile.py            gadget_purpose, override_codenames, harvest_gadgets, reconcile_report
    gates.py                GateResult, parse_gate_manifest, apply_gate_results, measurement_summary, measured_row_summary
    ledger.py               LedgerEntry, MissionLedger (transitions, validation, audit summaries, staleness, JSON)
    status.py               COVERAGE_FLOOR, CoverageSummary, BlockedPackage, LayerSummary, SUITE_LAYERS, SuiteStatus, build_status
    situation.py            build_situation_room, write_situation_room (coverage heat, mission timeline, per-film gadgets, layers, audit tail)
    manuscript_variables.py load_config, generate_variables, resolve_manuscript_tree
    __init__.py             public API
scripts/
    status_report.py        print/persist suite status (human or --json, per-layer, --gate-manifest/--no-gate-manifest)
    reconcile.py            merge real films' codenames + gadgets into the registry (bond-api probe)
    advance_mission.py      advance a package's phase in the persisted ledger
    build_situation_room.py regenerate output/situation_room.html (--reconciled, --gate-manifest/--no-gate-manifest)
    z_generate_manuscript_variables.py  hydrate {{TOKEN}}s (runs last; z_ prefix)
tests/
    conftest.py             5-film deterministic fixture + fixed clock
    test_registry.py test_ledger.py test_status.py test_situation.py test_reconcile.py test_gates.py
    test_manuscript_variables.py test_scripts_smoke.py
manuscript/                 config.yaml identity + 10 numbered sections (00-08, 99_references) with {{TOKEN}} injection
docs/                       agent-facing rulebook (read-first: agent_instructions.md)
output/                     gitignored generated artifacts (indicative only)
```

## Install / run

Dependencies install from this directory with `uv sync --extra dev`.  This
package is standalone — there is no parent `uv` workspace — so run all commands
from **inside** this directory.  The `bond-api` dependency resolves through the
sibling path declared in `[tool.uv.sources]`.

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
- `src/bond_coordinator/registry.py` — the `ROSTER` literal this registry
  reports (the fleet-level `SCOPE.md` is a sibling-workspace document, not
  shipped here).
