# Results {#sec:results}

All numeric results in this section are generated from source by
`src/bond_coordinator/manuscript_variables.py` and injected as substitution
tokens — they are never hand-authored in prose.

## Fleet state

The registry currently tracks **{{REGISTRY_TOTAL}}** film packages.  Their
distribution across statuses is {{REGISTRY_SCAFFOLDED}} scaffolded,
{{REGISTRY_BUILDING}} building, {{REGISTRY_READY}} ready, and {{REGISTRY_RED}}
red, with {{REGISTRY_COVERAGE_KNOWN}} packages carrying measured coverage
(mean {{REGISTRY_COVERAGE_MEAN}}, {{REGISTRY_COVERAGE_AT_90}} at/above the
{{GATE_COVERAGE_FLOOR}} gate).

Those figures describe **the roster this document was built from**, and their
provenance is stated by the same generator that produced them:
*{{REGISTRY_MEASUREMENT_SOURCE}}*.  The distinction matters, because the two
possible answers look identical in the numbers and are not the same claim.
The `ROSTER` literal in `registry.py` ships every row as `scaffolded` with
`coverage=None` — a seed default, meaning *this process has measured nothing*,
never *the fleet is unbuilt*.  A build run with `--no-gate-manifest` therefore
reports all {{REGISTRY_TOTAL}} rows scaffolded with no coverage, and that is a
statement about the seed, not a measurement of the {{REGISTRY_TOTAL}} film
packages.  Measured values enter only through
`gates.apply_gate_results`, from the `bond-ops` gate aggregate; a build run
against that manifest reports each package's real status and real coverage.
Nothing in this package measures a film package itself, and no figure above is
evidence about any film's actual test suite.

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
situation room.  The `films` layer reports {{REGISTRY_TOTAL}} tracked with
{{REGISTRY_READY}} ready and mean coverage over the measured rows only; the
infrastructure layers report readiness only where probed (layer 1 tracks the
`bond-api` probe, the rest report the tri-state "not probed" unless a caller
supplies readiness).  Every one of these counts is derived from the roster
handed to the generator, never hand-authored.

## Reconciliation boundaries

The standalone replay does not measure reconciliation across the suite.
The coordinator's merge logic accepts package declarations as data and uses
replacement semantics when a declaration changes. For plain-data records,
the interpreter's built-in type documentation provides no evidence of what
a package author declared. The merge therefore distinguishes declared text
from a derived description of the data's shape.

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

## Summary table (live-generated)

Every value below is injected from the registry/ledger by
`src/bond_coordinator/manuscript_variables.py` — none is hand-authored.

| Metric | Value |
|---|---|
| Tracked film packages | {{REGISTRY_TOTAL}} |
| Declared suite-topology layers | {{REGISTRY_LAYER_COUNT}} |
| Mission-infrastructure packages (non-films layers) | {{REGISTRY_INFRA_PACKAGE_COUNT}} |
| Lifecycle phases | {{LEDGER_PHASE_COUNT}} |
| Enforced coverage floor | {{GATE_COVERAGE_FLOOR}} |
| Default staleness threshold | {{GATE_STALE_DAYS}} days |
| Roster span | `{{REGISTRY_FIRST_SLUG}}` ({{REGISTRY_FIRST_YEAR}}) → `{{REGISTRY_LAST_SLUG}}` ({{REGISTRY_LAST_YEAR}}) |
Table: Registry roster and reporting configuration. {#tbl:registry-roster}

| Metric | Value |
|---|---|
| Measured coverage (known / at-or-above floor / mean) | {{REGISTRY_COVERAGE_KNOWN}} / {{REGISTRY_COVERAGE_AT_90}} / {{REGISTRY_COVERAGE_MEAN}} |
| Status counts (scaffolded / building / ready / red) | {{REGISTRY_SCAFFOLDED}} / {{REGISTRY_BUILDING}} / {{REGISTRY_READY}} / {{REGISTRY_RED}} |
| Blocked / stale packages | {{REGISTRY_BLOCKED_COUNT}} / {{REGISTRY_STALE_COUNT}} |
| Audit-trail entries (fresh ledger) | {{LEDGER_TRANSITION_TOTAL}} |

Table: Status counts and initial ledger summary. {#tbl:status-counts}

Provenance of the status and coverage columns:
*{{REGISTRY_MEASUREMENT_SOURCE}}* — read the Limitations section
(“Limitations and Uncertainty”) before interpreting them as claims about any film.
