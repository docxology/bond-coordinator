# Methodology {#sec:methodology}

The pure core lives under `src/bond_coordinator/`: `types.py` (protocol
mirror), `registry.py`, `reconcile.py`, `ledger.py`, `status.py`, and
`situation.py`, plus `manuscript_variables.py`.  All are pure: they import
only the standard library and `pyyaml`, never `infrastructure.*`, and never a
sibling BOND package.  Thin orchestrators in `scripts/` bind them to the
filesystem (persisting the ledger, writing the dashboard, printing the report).

## Registry

`registry.py` defines a frozen `PackageRecord` (rank, slug, film, year,
codename, status, coverage, concepts) and the module-level `ROSTER` tuple of
all 27 film packages, in Eon-canon order then non-Eon, exactly per `SCOPE.md`
§2.1.  Status is the enum `scaffolded | building | ready | red`; coverage is a
measured percentage or `None`.  Mission codenames are **assigned by mission
control** from each film's canonical plot element (e.g. Goldfinger's Operation
Grand Slam → `GRAND SLAM`) and are provisional until a film package declares
its own via `bond-api`.

The registry also provides `get_package`, `find_by_status`, and `subset_roster`
(the last is how tests seed deterministic 5-film fixtures without depending on
the whole fleet).  `reconcile.py` implements the merge half of the codename
policy: when a film declares its real codename and gadget table, `override_codenames`
and `harvest_gadgets` return an updated registry with **refresh/replace**
semantics (a later build wins), leaving the source immutable.

## Mission-state ledger

`ledger.py` tracks each package's position in the lifecycle
{{CONFIG_MISSION_LIFECYCLE}}, encoded by the `MissionPhase` enum.  A
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
mean/min/max over measured packages, count meeting the 90% gate), the set of
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
are injectable, so the report is reproducible byte-for-byte.

## Situation room

`situation.py::build_situation_room(status, roster, ledger, gadgets)` renders
a single self-contained HTML document (no external assets, no JavaScript):

- summary cards and a **per-package table** with status, phase, a five-cell
  **mission-timeline progress bar** (done / current / ahead), last update, and
  **coverage heat** — each coverage cell color-coded against the 90% gate
  (≥90% green, 50–90% amber, <50% red, unmeasured gray) with a legend;
- a **suite-layers table** from `status.layers`;
- a **per-film gadget table** grouping the Q-branch inventory by film, with a
  count of which tracked films have none;
- a **recent-transitions (audit trail)** table of the newest ledger entries.

Every value is HTML-escaped; the document is deterministic given its inputs.
`scripts/build_situation_room.py` writes it to the gitignored `output/` tree.
