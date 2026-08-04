# Abstract {#sec:abstract}

This paper presents **{{CONFIG_TITLE}}** (codename **{{CONFIG_CODENAME}}**), the
Layer-2 mission-control package for {{CONFIG_SUITE_NAME}}, a fleet of software
packages descended from a numerical-optimization research exemplar.  Where that
exemplar demonstrated optimization mathematics inside a single package,
{{CONFIG_TITLE}} demonstrates the *fleet* view: a deterministic registry of all
{{REGISTRY_TOTAL}} film packages, a forward-only mission-state ledger, an
aggregate suite-status report, and a self-contained HTML situation room.

The registry (`src/bond_coordinator/registry.py`) is seeded from the ROSTER
conventions in `projects/working/bond/SCOPE.md` §2.1 and assigns a provisional
mission codename per film; `reconcile.py` merges a film's real codename and
gadget table over it (refresh/replace semantics) once a film declares them via
`bond-api`.  The ledger (`src/bond_coordinator/ledger.py`) tracks each
package's lifecycle — {{CONFIG_MISSION_LIFECYCLE}} — with strict forward-only
transition rules, attributable-identity validation, an append-only audit trail
of who/when/version, and deterministic audit summaries.  The status module
(`src/bond_coordinator/status.py`) aggregates counts by state and phase, a
measured-coverage summary, stale/blocked flags, and a per-layer summary of the
fleet topology.  The situation room (`src/bond_coordinator/situation.py`)
renders the whole fleet — packages, mission-timeline bars, coverage heat,
suite layers, a per-film Q-branch gadget table, and the recent-transitions
audit tail — into one self-contained HTML document.

**Fleet state (this build):** {{REGISTRY_TOTAL}} packages tracked across
{{REGISTRY_LAYER_COUNT}} declared topology layers;
{{REGISTRY_SCAFFOLDED}} scaffolded, {{REGISTRY_BUILDING}} building,
{{REGISTRY_READY}} ready, {{REGISTRY_RED}} red; {{REGISTRY_COVERAGE_KNOWN}}
packages with measured coverage (mean {{REGISTRY_COVERAGE_MEAN}},
{{REGISTRY_COVERAGE_AT_90}} at/above the 90% gate, {{REGISTRY_COVERAGE_UNKNOWN}}
not yet gated); {{REGISTRY_BLOCKED_COUNT}} blocked;
{{REGISTRY_STALE_COUNT}} stale.

**Keywords:** {{CONFIG_KEYWORDS}}
