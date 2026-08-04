# Introduction {#sec:introduction}

{{CONFIG_SUITE_NAME}} is a fleet of standalone software packages — one per
James Bond film, plus a shared layer of Q-branch infrastructure — built to the
same scientific bar as the research exemplar from which each package is
forked: pure tested cores, zero mocks, ≥90% coverage, thin orchestrators, and
deterministic, provenance-recorded outcomes.  With twenty-seven film packages
and six infrastructure packages, the fleet needs a single point of truth about
*what exists, where it is in its mission, and whether it is healthy*.

{{CONFIG_TITLE}} (codename **{{CONFIG_CODENAME}}**) is that point of truth: the
**registry and situation room** for the whole suite.  It does not implement any
film's algorithms; it records, audits, and reports on them.  Concretely it
provides four capabilities, each a thin-over-pure module under
`src/bond_coordinator/`:

1. **Registry** (`registry.py`) — the authoritative, curated list of the 27
   film packages: slug, film title, release year, mission codename, status, and
   measured coverage when available.
2. **Mission-state ledger** (`ledger.py`) — each package's lifecycle position
   (brief → recon → plan → execute → debrief) with forward-only transition
   rules and an append-only audit trail.
3. **Suite status** (`status.py`) — a deterministic aggregate snapshot: counts
   by state and phase, a coverage summary, and stale / blocked flags.
4. **Situation room** (`situation.py`) — a self-contained HTML dashboard that
   renders the whole fleet plus the Q-branch gadget inventory.

The package sits at Layer 2 (mission control) in the suite's dependency
topology.  It is designed to consume the Layer-1 protocol types from
`bond-api` and provenance helpers from `bond-utilities`; because those packages
are not yet built, it ships a pure-core mirror of the protocol shapes with a
documented swap point (see `TODO.md`).  Every module is deterministic, uses no
framework mocking, and is exercised by a zero-mock real-data test suite.

## Reader's guide

- [@sec:methodology] defines the registry, ledger, status, and situation-room
  models and their invariants.
- [@sec:results] reports the measured fleet state.
- [@sec:experimental_setup] documents the configuration surface and the
  enforced quality gates.
- [@sec:reproducibility] certifies determinism and provenance.
- [@sec:scope] scopes the package and relates it to the rest of the fleet.
