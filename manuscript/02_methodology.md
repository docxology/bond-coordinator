# Methodology {#sec:methodology}

The pure core lives under `src/bond_coordinator/`: `types.py` (protocol
mirror), `registry.py`, `reconcile.py`, `gates.py`, `ledger.py`, `status.py`,
and `situation.py`, plus `manuscript_variables.py`.  All are pure: they import
only the standard library and `pyyaml`, never `infrastructure.*`, and never a
sibling BOND package.  Thin orchestrators in `scripts/` bind them to the
filesystem (persisting the ledger, writing the dashboard, printing the report).

## Registry

`registry.py` defines a frozen `PackageRecord` (rank, slug, film, year,
codename, status, coverage, concepts) and the module-level `ROSTER` tuple of
all {{REGISTRY_TOTAL}} film packages, in Eon-canon order then non-Eon, exactly per `SCOPE.md`
§2.1.  Status is the enum `scaffolded | building | ready | red`; coverage is a
measured percentage or `None`.  Mission codenames are **assigned by mission
control** from each film's canonical plot element (e.g. Goldfinger's Operation
Grand Slam → `GRAND SLAM`) and are provisional until a film package declares
its own via `bond-api`.

The shipped `ROSTER` literal fills only the identity fields; every row's status
and coverage are seed defaults (`scaffolded` / `None`) meaning *unmeasured by
this process*.  `gates.py` is the sole path by which they change:
`parse_gate_manifest` decodes the `bond-ops` gate aggregate — raising on a
malformed manifest rather than degrading to an empty result, since "nothing
measured" is indistinguishable from an honest seed — and `apply_gate_results`
derives each row's status by rule (failed run → `red`; passing at or above
`COVERAGE_FLOOR` → `ready`; passing below it, or passing with no coverage
number, → `building`; no gate row → untouched).  The rule is what makes the
status a derived fact rather than an assertion, and it is asserted in both
directions by tests that break when the rule is altered.

The registry also provides `get_package`, `find_by_status`, and `subset_roster`
(the last is how tests seed deterministic film fixtures without depending on
the whole fleet).

## Reconciliation

`reconcile.py` implements the merge half of the codename policy: when a film
declares its real codename and gadget table, `override_codenames` and
`harvest_gadgets` return an updated registry with **refresh/replace**
semantics (a later build wins), leaving the source immutable.

The module also owns `gadget_purpose`, which reduces a film-registered gadget
payload to one line.  The rule is explicit rather than duck-typed, because the
obvious implementation is wrong: reading `payload.__doc__` on a plain-data
payload resolves through to the *builtin type's* docstring, so a `dict` reports
`"dict() -> new empty dictionary"` and a `list` reports `"Built-in mutable
sequence."`.  Those are attributes of the interpreter, not declarations by the
film, and recording them as a gadget's purpose fabricates provenance.
`gadget_purpose` therefore accepts a docstring only from a routine, class, or
module — the shapes that syntactically carry one at their definition site —
uses a string payload verbatim as the film's own words, and otherwise derives a
factual shape summary from the object itself
(`"data payload: dict of 8 entries"`).

Discovery is deliberately outside the pure core.  `scripts/reconcile.py` loads
each film's `bond_api.protocol.MissionProvider` via
`bond_api.discovery.load_provider`, reads `provider.brief()` and the film's
module-level `GADGETS`, and converts both to plain dictionaries before calling
these functions — so no protocol type from a sibling package ever crosses the
`src/` boundary.  Because reconciliation imports {{REGISTRY_TOTAL}}
independently developed packages, each film is guarded individually: any
exception raised while importing one film skips that film alone, with its
exception type and message reported, and the remaining films still reconcile.

## Mission-state ledger

`ledger.py` tracks each package's position in the lifecycle
{{CONFIG_MISSION_LIFECYCLE}} — {{LEDGER_PHASE_COUNT}} phases encoded by the
`MissionPhase` enum, whose ordinal drives every transition rule.  A
`MissionLedger` holds the current entry per package plus an append-only list of
every recorded transition.  The transition rules are strict and executable:

1. A package must be registered in the roster.
2. Phases move strictly forward: brief → recon → plan → execute → debrief.
3. Re-entering the current phase is allowed (an idempotent *touch*).
4. Moving backwards, or `advance` past debrief, raises `ValueError`.  `jump`
   permits multi-step forward advances (still audible, still forward-only).

**Transition validation** goes further than forward-only ordering.  Every
transition must be attributable: both the acting agent (`updated_by`) and the
`version` being progressed must be non-empty strings, and an optional `note`
must be a string.  A public `validate_transition(slug, phase, by, version)`
runs the full rule set **without mutating the ledger**, so a caller (or CLI)
can gate a transition before committing it.

Every transition writes a frozen `LedgerEntry` (slug, phase, `updated_by`,
`updated_at`, version, note), so the audit trail answers *who changed which
package's state, when, and at what version*.  The ledger deepens the audit into
three deterministic views: `transition_summary` (entries per phase),
`per_agent_summary` (entries per agent), and `phase_timeline(slug)` — the
chronological `(phase, timestamp)` history that drives the situation room's
mission timeline.  Staleness is a pure function of entry age and an injectable
clock: a debriefed mission is never stale.

## Suite status

`status.py::build_status(roster, ledger, ...)` assembles one deterministic
snapshot: counts by status and by phase, a `CoverageSummary` (known count,
mean/min/max over measured packages, count meeting the
{{GATE_COVERAGE_FLOOR}} gate), the set of
stale packages, a set of `BlockedPackage` reasons computed from the
combination of status and phase, and a **per-layer summary**:

- a `red` package is blocked ("flagged red");
- executing before ready is blocked;
- planning while still scaffolded is blocked.

**Per-layer summaries** render the declared suite topology
(`SUITE_LAYERS`, §2.2 of `SCOPE.md`) as one `LayerSummary` per layer — the
five infrastructure layers (`layer0`…`layer4`), each with a readiness
tri-state, plus the `films` layer aggregating the registry: tracked count,
READY count, and mean coverage.  Readiness is injectable via `layer_ready`
(with `layer1` — the `bond-api` protocol — inferred from `dependency_ready`),
so the report reflects which of the suite's {{REGISTRY_LAYER_COUNT}} declared
layers are actually available.  All time-dependent inputs (`now`, `stale_days`)
are injectable, so the report is reproducible byte-for-byte.  The snapshot also
*carries* the `stale_days` threshold it was computed with (default
{{GATE_STALE_DAYS}} days), so a downstream renderer states the threshold that
was applied instead of assuming the default.

## Situation room

`situation.py::build_situation_room(status, roster, ledger, gadgets)` renders
a single self-contained HTML document (no external assets, no JavaScript):

- summary cards and a **per-package table** with status, phase, a
  **mission-timeline progress bar** of one cell per lifecycle phase (done /
  current / ahead), last update, and **coverage heat** — each coverage cell
  color-coded against the {{GATE_COVERAGE_FLOOR}} gate (at/above green,
  mid-range amber, low red, unmeasured gray) with a legend.  The renderer
  imports `COVERAGE_FLOOR` from `status.py` rather than restating it, so the
  legend cannot drift from the gate actually enforced;
- a **suite-layers table** from `status.layers`;
- a **per-film gadget table** grouping the Q-branch inventory by film, with a
  count of which tracked films have none;
- a **recent-transitions (audit trail)** table of the newest ledger entries.

Every value is HTML-escaped; the document is deterministic given its inputs.
`scripts/build_situation_room.py` writes it to the gitignored `output/` tree.
