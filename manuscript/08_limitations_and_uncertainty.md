# Limitations and Uncertainty {#sec:limitations}

No claim below is a discovery about any film; every statement is about the
registry, ledger, and status machinery this package ships, and about the
boundaries of what those numbers do and do not certify.

## The seeded registry is not a measurement

The `ROSTER` literal in `src/bond_coordinator/registry.py` ships every one of
the {{REGISTRY_TOTAL}} film rows with `status=scaffolded` and `coverage=None`.
Those are *seed defaults*: they mean "this process has not applied gate output
to this row", never "the fleet is unbuilt" and never "this film passes at some
coverage".  When a manuscript or dashboard is built with
`--no-gate-manifest`, every figure that reads "*{{REGISTRY_MEASUREMENT_SOURCE}}*"
is therefore a statement about the seed, and only about the seed.  The number
{{REGISTRY_READY}} "ready" / {{REGISTRY_SCAFFOLDED}} "scaffolded" in such a
build must not be read as a claim about any film package's actual state.

## Measured values are only as good as the manifest that supplies them

The single path by which a row becomes `ready`/`building`/`red` with a real
number is `gates.apply_gate_results`, consuming the fleet aggregate that
`bond-ops` writes at a *convention* location
(`../output/aggregate/gate_manifest.json`).  Three properties bound the
uncertainty of anything reported as "measured":

1. **The path is a convention, not a contract.**  Nothing in this package
   forces `bond-ops` to keep writing that exact path; if the sibling relocates
   its aggregate, every consumer here degrades to the unmeasured seed.  That
   degradation is *announced* (the provenance line says
   `{{REGISTRY_MEASUREMENT_SOURCE}}`, and the scripts print `no gate manifest
   at …` to stderr), so it is not a silent lie — but a fleet whose sibling
   moved a file is indistinguishable, in these outputs, from a fleet that was
   never measured.
2. **Coverage is treated as a bounded percentage.**  A row whose coverage is
   non-finite, negative, or above 100 is rejected loudly by
   `parse_gate_manifest` (`ValueError`) rather than coerced into the fleet
   mean.  This closes the class of bug where a stray `NaN`/`Infinity` in a
   manifest silently poisons `CoverageSummary.mean`.
3. **Absence of a row is absence of evidence.**  A film with no gate row keeps
   its seed state.  We cannot distinguish "not yet gated" from "gated and
   skipped", which is honest but makes `{{REGISTRY_COVERAGE_UNKNOWN}}` an
   upper bound on how much of the fleet the status report actually certifies.

## Ledger truthfulness is bounded by its inputs

The forward-only transition rule is *exact and centralised*: the same
`_require_forward` helper backs both the mutating path and the non-mutating
`validate_transition`, so the two cannot drift, and the defensive invalid-jump
guard is reachable and tested rather than excluded.  But the ledger records
what a caller tells it.  It validates that a move is forward and attributable;
it does not verify that a film objectively "is" a given phase, nor that the
`updated_by` identity is real.  A `touch` re-stamps the current phase, so the
audit tail's per-phase counts (`LEDGER_PHASE_COUNT` phases, `brief →
recon → plan → execute → debrief`) include same-phase re-entries and can
overcount *activity* relative to *movement*.  Staleness
(`{{GATE_STALE_DAYS}}` days) is a heuristic: a mission is "stale" purely
because no transition was recorded within the window, which treats an
abandoned mission and an idle-but-legitimate one identically.

## Gadget purposes are derived shapes, not film confessions

`reconcile.gadget_purpose` deliberately refuses to read a builtin's
`__doc__`, because doing so recorded CPython's own strings as a film's
declared purpose.  The flip side is that a plain-data payload is summarised by
its *shape* ("data payload: dict of 8 entries"), which is factual but conveys
nothing about what the gadget does.  Purposes derived this way understate
semantic content by construction; they make no claim about the gadget's real
behaviour.

## Reconciliation is partial by design

`scripts/reconcile.py` imports {{REGISTRY_TOTAL}} independently developed
packages, each guarded individually: a film that raises at import is skipped
with its exception type and message reported, and the other films still
reconcile.  The cost is that a run's completeness is a runtime fact, not a
constant — the set of films that declared a codename or harvested a gadget
varies with what is built on disk that day.  Nothing here should be read as
"all {{REGISTRY_TOTAL}} films reconciled"; the skipped set is always reported.

## The situation room reflects its inputs, exactly

`build_situation_room` renders whatever roster, ledger, gadget table, and
provenance wording it is handed, and says which of the reconciled/measured
manifests (if any) were loaded.  It is deterministic and HTML-escaped, so it
cannot *distort* its inputs — but it cannot *repair* them either.  A dashboard
built with stale manifests is a faithful rendering of stale facts.

## Uncertainty statement

Because this package issues no scientific quantities of its own, most
conventional uncertainty analysis (error bars, confidence intervals) does not
apply.  Its uncertainties are *modelling* and *provenance* uncertainties, and
they are qualitative: how complete a reconciliation run was, whether a
seed-vs-measured figure is being read as the other, and whether the fleet gate
aggregate this run consumed is the one the current `bond-ops` produces.  We
insist on stating those explicitly in every rendered artifact rather than
quantifying them, because a spurious precision here would be the most
misleading output the package could produce.

The reproducibility bar is documented in §[sec:reproducibility] and follows
the reproducibility-in-research-software guidance of
[@sandve2013tensimplerules; @peng2011reproducibleresearch].
