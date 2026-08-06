# Introduction {#sec:introduction}

{{CONFIG_SUITE_NAME}} is a fleet of standalone software packages — one per
James Bond film, plus a shared layer of Q-branch infrastructure — built to the
same scientific bar as the research exemplar from which each package is
forked: pure tested cores, zero mocks, ≥{{GATE_COVERAGE_FLOOR}} coverage, thin orchestrators, and
deterministic, provenance-recorded outcomes.  With {{REGISTRY_TOTAL}} film
packages and {{REGISTRY_INFRA_PACKAGE_COUNT}} mission-infrastructure packages,
the fleet needs a single point of truth about *what exists, where it is in its
mission, and whether it is healthy*.

{{CONFIG_TITLE}} (codename **{{CONFIG_CODENAME}}**) is that point of truth: the
**registry and situation room** for the whole suite.  It does not implement any
film's algorithms; it records, audits, and reports on them.  Concretely it
provides six capabilities, each a pure module under `src/bond_coordinator/`
with a thin orchestrator in `scripts/`:

1. **Protocol mirror** (`types.py`) — `Asset`, `Gadget`, `GadgetRegistry`,
   `PackageStatus`, and the `MissionPhase` lifecycle enum, mirroring the
   `bond-api` shapes so the core carries no sibling imports.
2. **Registry** (`registry.py`) — the authoritative, curated list of the
   {{REGISTRY_TOTAL}} film packages: slug, film title, release year, mission
   codename, status, and measured coverage when available.
3. **Reconcile** (`reconcile.py`) — the merge that replaces mission control's
   provisional codenames with the codenames films actually declare, and
   harvests their gadget tables into the Q-branch inventory.
4. **Mission-state ledger** (`ledger.py`) — each package's lifecycle position
   ({{CONFIG_MISSION_LIFECYCLE}}) with forward-only transition rules,
   attributable-identity validation, and an append-only audit trail.
5. **Suite status** (`status.py`) — a deterministic aggregate snapshot: counts
   by state and phase, a coverage summary, stale / blocked flags, and a
   per-layer summary of the fleet topology.
6. **Situation room** (`situation.py`) — a self-contained HTML dashboard that
   renders the whole fleet plus the Q-branch gadget inventory.

A seventh module, `manuscript_variables.py`, injects this document's own
identity and every quantity it reports (§[@sec:results]).

The package sits at Layer 2 (mission control) in the suite's dependency
topology.  Its one cross-package consumer is the thin orchestrator
`scripts/reconcile.py`, which loads each film's Layer-1
`bond_api.protocol.MissionProvider` and converts the result to plain data
before it reaches the core.  The core itself imports neither `bond-api` nor
the Layer-0 `bond-utilities`: it keeps a pure-core mirror of the protocol
shapes as a deliberate boundary, not as a placeholder (see `TODO.md` and
`docs/architecture.md`).  Every module is deterministic, uses no framework
mocking, and is exercised by a zero-mock real-data test suite.

## Reader's guide

- [@sec:methodology] defines the registry, ledger, status, and situation-room
  models and their invariants.
- [@sec:results] reports the measured fleet state.
- [@sec:experimental_setup] documents the configuration surface and the
  enforced quality gates.
- [@sec:reproducibility] certifies determinism and provenance.
- [@sec:limitations] states honestly what every figure here does and does not
  certify, and how the seeded-versus-measured distinction can be misread.
- [@sec:scope] scopes the package and relates it to the rest of the fleet.
