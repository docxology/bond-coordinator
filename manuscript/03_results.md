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
{{REGISTRY_COVERAGE_MEAN}} and {{REGISTRY_COVERAGE_AT_90}} at/above the 90%
gate.

## Registry completeness

The roster is canon-ordered and complete: it spans `dr_no` (1962) through
`never_say_never_again` (1983) with every Eon entry and both non-Eon entries.
The full slug list is: {{REGISTRY_PACKAGES_CSV}}.  Each record carries a
provisional mission codename and the core concepts that will power that film's
software payload, so the registry is both an inventory and a build briefing.

## Ledger and status behaviour

The ledger's forward-only rules are verified by tests that walk a package the
full lifecycle, attempt illegal backwards and past-debrief transitions, and
assert the append-only audit trail.  The status aggregator is verified against
deliberately heterogeneous rosters (ready/building/scaffolded/red mixes) to
exercise every blocked rule and the coverage summary.  Observed behaviour in
this build: **{{REGISTRY_BLOCKED_COUNT}}** packages blocked and
**{{REGISTRY_STALE_COUNT}}** stale, consistent with a fresh ledger at `brief`.
