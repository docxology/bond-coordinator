# Results {#sec:results}

All figures in this section are generated from source by
`src/bond_coordinator/manuscript_variables.py` and injected as substitution
tokens — they are never hand-authored in prose.

## Fleet state

The registry currently tracks **{{REGISTRY_TOTAL}}** film packages.  Their
distribution across statuses is {{REGISTRY_SCAFFOLDED}} scaffolded,
{{REGISTRY_BUILDING}} building, {{REGISTRY_READY}} ready, and {{REGISTRY_RED}}
red.  Because the fleet is still in phase-0 scaffold, every package is
`scaffolded` and none has measured coverage yet; the coverage token therefore
reports {{REGISTRY_COVERAGE_KNOWN}} measured packages with mean
{{REGISTRY_COVERAGE_MEAN}} and {{REGISTRY_COVERAGE_AT_90}} at/above the
{{GATE_COVERAGE_FLOOR}} gate.

## Registry completeness

The roster is canon-ordered and complete: it spans `{{REGISTRY_FIRST_SLUG}}`
({{REGISTRY_FIRST_YEAR}}) through `{{REGISTRY_LAST_SLUG}}`
({{REGISTRY_LAST_YEAR}}) with every Eon entry and both non-Eon entries.
The full slug list is: {{REGISTRY_PACKAGES_CSV}}.  Each record carries a
provisional mission codename and the core concepts that will power that film's
software payload, so the registry is both an inventory and a build briefing.

## Suite layers

The coordinator declares **{{REGISTRY_LAYER_COUNT}}** topology layers —
{{REGISTRY_LAYER_CSV}} — and reports each in the status snapshot and the
situation room.  In this build every film is scaffolded, so the `films` layer
reports all {{REGISTRY_TOTAL}} tracked with none ready; the infrastructure
layers report readiness only where probed (layer 1 tracks the `bond-api`
probe).  This turn-count is derived, never hand-authored.

## Reconciliation against the real fleet

Reconciliation is the point where mission control stops asserting and starts
measuring.  `scripts/reconcile.py` loads each built film's `MissionProvider`,
reads its declared codename, harvests its gadget table, and hands plain data
to the pure merge in `reconcile.py`.  Two properties are established by test
rather than by inspection of a particular run, because the fleet's contents
change as film packages are built:

- **Per-film isolation is a positive control, not a promise.** A film that
  raises on import is skipped individually — with its exception type and
  message reported — while every other film still reconciles.  The test
  materialises a film whose module raises at import time and asserts the run
  still succeeds and still harvests its healthy neighbour.  This replaced a
  guard narrow enough that one half-edited package aborted the fleet-wide run.
- **No borrowed provenance.** A gadget's purpose is derived by
  `reconcile.gadget_purpose`, which accepts a docstring only from payloads
  that syntactically carry one (routines, classes, modules), takes a string
  payload as the film's own words, and otherwise emits a factual shape
  summary.  Reading `payload.__doc__` unconditionally instead resolves to the
  *builtin type's* docstring for plain data, recording CPython's own strings
  as purposes the film never declared.  A parametrised test asserts the
  derived purpose differs from `payload.__doc__` for every plain-data shape.

## Ledger and status behaviour

The ledger's forward-only rules are verified by tests that walk a package the
full lifecycle, attempt illegal backwards and past-debrief transitions, assert
that empty or non-attributable transitions are rejected, and check the
deterministic audit summaries (`transition_summary`, `per_agent_summary`,
`phase_timeline`).  The status aggregator is verified against deliberately
heterogeneous rosters (ready/building/scaffolded/red mixes) to exercise every
blocked rule, the coverage summary, and the per-layer summaries.  Observed
behaviour in this build: **{{REGISTRY_BLOCKED_COUNT}}** packages blocked and
**{{REGISTRY_STALE_COUNT}}** stale, consistent with a fresh ledger at `brief`
whose audit trail holds {{LEDGER_TRANSITION_TOTAL}} entries (one per
registered package).  Coverage heat, mission-timeline bars, per-film
gadget grouping, and the recent-transitions table are all rendered
deterministically and asserted byte-identical across repeated builds.
