# bond-coordinator — mission control for the BOND suite

**Codename: MISSION CONTROL**

`bond-coordinator` is the Layer-2 **registry and situation room** for
**PROJECT BOND**, a fleet of standalone software packages — one per James Bond
film, plus a shared layer of Q-branch mission infrastructure — each built to a
scientific-research bar (pure tested cores, zero mocks, ≥90% coverage, thin
orchestrators, deterministic + provenance-recorded outcomes).

This package does **not** implement any film's algorithms.  It records, audits,
and reports on the fleet so that *what exists, where it is in its mission, and
whether it is healthy* are machine-checkable facts.

## What it provides

| Capability | Module | Responsibility |
|---|---|---|
| **Protocol mirror** | `src/bond_coordinator/types.py` | `Asset`, `AssetKind`, `Gadget`, `GadgetRegistry`, `PackageStatus`, `MissionPhase` — pure-core mirrors of the `bond-api` shapes, so the core keeps zero sibling imports. |
| **Registry** | `src/bond_coordinator/registry.py` | Authoritative, canon-ordered list of all 27 film packages: slug, film, year, mission codename, status, measured coverage. |
| **Reconcile** | `src/bond_coordinator/reconcile.py` | Merge real films' codenames + gadget tables over the provisional registry (refresh/replace semantics), plus `gadget_purpose` — the payload→one-line-purpose rule that refuses to borrow a builtin's docstring. `scripts/reconcile.py` drives discovery via `bond-api`. |
| **Mission-state ledger** | `src/bond_coordinator/ledger.py` | Each package's lifecycle (`brief → recon → plan → execute → debrief`) with forward-only transition rules, attributable-identity validation, an append-only audit trail, and deterministic audit summaries (`transition_summary`, `per_agent_summary`, `phase_timeline`). |
| **Suite status** | `src/bond_coordinator/status.py` | Deterministic aggregate snapshot: counts by state/phase, coverage summary, stale/blocked flags (carrying the `stale_days` threshold actually applied), and **per-layer summaries** of the declared suite topology. Owns `COVERAGE_FLOOR`, the gate the dashboard legend reads. |
| **Situation room** | `src/bond_coordinator/situation.py` | Self-contained HTML dashboard: per-package table with **mission-timeline bars** and **coverage heat**, suite-layers table, **per-film gadget groups**, and a recent-transitions audit tail. |
| **Manuscript variables** | `src/bond_coordinator/manuscript_variables.py` | Injects identity (from `manuscript/config.yaml`) and registry-derived counts as `{{TOKEN}}`s — never hand-authored in prose. |

The `src/bond_coordinator/` core is **pure**: standard library + `pyyaml` only,
no `infrastructure.*`, no sibling-package imports.  Thin orchestrators in
`scripts/` bind it to the filesystem.

## Quick start

```bash
# From this package directory
uv sync --extra dev

# Full gate (line + branch coverage ≥90% on src/)
uv run pytest tests/ --cov=src --cov-fail-under=90

# Quality gates
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
uv run mypy
```

### Run the tools

```bash
# Human-readable + JSON suite report (also writes output/data/suite_status.json)
uv run python scripts/status_report.py
uv run python scripts/status_report.py --json

# Advance one package's mission phase (persists output/data/mission_ledger.json)
uv run python scripts/advance_mission.py --slug goldfinger --phase recon \
    --by agent-007 --version 0.1.0 --note "watching Fort Knox"

# Regenerate the situation-room HTML dashboard (output/situation_room.html)
uv run python scripts/build_situation_room.py

# Reconcile the registry against real film packages (codenames + gadgets)
uv run python scripts/reconcile.py
uv run python scripts/reconcile.py --gadgets output/data/gadgets.json

# Hydrate manuscript {{TOKEN}}s (output/manuscript/*.md, runs last)
uv run python scripts/z_generate_manuscript_variables.py
```

All generated artifacts live under `output/` and are **gitignored and
disposable** — always regenerated from source, never hand-edited.

## The MissionProvider surface

This package **implements no `MissionProvider` and ships no `mission.py`** —
by design.  `bond_api.protocol.MissionProvider` (`film`, `brief`, `recon`,
`plan`, `execute`, `debrief`) is the contract every *film* package satisfies;
mission control is its **consumer**, not one of its implementers.  A synthetic
provider here would inject a non-film into the fleet's discovery surface and
make the registry a member of the roster it governs.

Consumption is confined to one thin orchestrator, `scripts/reconcile.py`,
which calls `bond_api.discovery.load_provider(slug, …)`, reads
`provider.brief()` for each film's real codename, and reads each film's
module-level `GADGETS`.  It converts everything to plain dicts before calling
the pure functions in `src/bond_coordinator/reconcile.py`, so no `bond_api`
type ever crosses into the core.  Films that are absent, unimportable, or
raise on import are skipped individually and reported on stderr — one broken
sibling never aborts a fleet-wide run.  Full contract and degradation table:
[`docs/architecture.md`](docs/architecture.md).

## Identity

- Package: `bond-coordinator` (Layer 2)
- Codename: `MISSION CONTROL`
- Depends on: `bond-api` (Layer 1, **built** — drives `scripts/reconcile.py`
  discovery) and `bond-utilities` (Layer 0, not yet built, for provenance I/O).
  The pure core deliberately imports neither: it ships its own protocol mirror
  (`src/bond_coordinator/types.py`) to keep `src/` sibling-free (see `TODO.md`).

## Repository layout

```
src/bond_coordinator/   pure core (types, registry, reconcile, ledger, status, situation,
                        manuscript_variables)
scripts/                thin orchestrators (status_report, reconcile, advance_mission,
                        build_situation_room, z_generate_manuscript_variables)
tests/                  zero-mock real-data suite; deterministic 5-film fixture (tests/conftest.py)
manuscript/             config.yaml identity + sections with {{TOKEN}} injection
docs/                   agent-facing operational rulebook
data/                   advisory validation overlays (claim_ledger.yaml)
```

## Author & license

Daniel Ari Friedman · Active Inference Institute
(`daniel@activeinference.institute`, ORCID 0000-0001-6232-9096) · MIT.
