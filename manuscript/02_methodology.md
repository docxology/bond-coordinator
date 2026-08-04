# Methodology {#sec:methodology}

All four modules live under `src/bond_coordinator/` and are pure: they import
only the standard library and `pyyaml`, never `infrastructure.*`, and never a
sibling BOND package.  Thin orchestrators in `scripts/` bind them to the
filesystem (persisting the ledger, writing the dashboard, printing the report).

## Registry

`registry.py` defines a frozen `PackageRecord` (rank, slug, film, year,
codename, status, coverage, concepts) and the module-level `ROSTER` tuple of
all 27 film packages, in Eon-canon order then non-Eon, exactly per `SCOPE.md`
§2.1.  Status is the enum `scaffolded | building | ready | red`; coverage is a
measured percentage or `None`.  At the time of writing every package is a
phase-0 scaffold, so all records start `scaffolded` with `coverage=None`.
Mission codenames are **assigned by mission control** from each film's
canonical plot element (e.g. Goldfinger's Operation Grand Slam → `GRAND SLAM`)
and are provisional until a film package declares its own via `bond-api`.

The registry also provides `get_package`, `find_by_status`, and `subset_roster`
(the last is how tests seed deterministic 5-film fixtures without depending on
the whole fleet).

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

Every transition writes a frozen `LedgerEntry` (slug, phase, `updated_by`,
`updated_at`, version, note), so the audit trail answers *who changed which
package's state, when, and at what version*.  Staleness is a pure function of
entry age and an injectable clock: a debriefed mission is never stale.

## Suite status

`status.py::build_status(roster, ledger, ...)` assembles one deterministic
snapshot: counts by status and by phase, a `CoverageSummary` (known count,
mean/min/max over measured packages, count meeting the 90% gate), the set of
stale packages, and a set of `BlockedPackage` reasons computed from the
combination of status and phase:

- a `red` package is blocked ("flagged red");
- executing before ready is blocked;
- planning while still scaffolded is blocked.

All time-dependent inputs (`now`, `stale_days`) are injectable so the report
is reproducible byte-for-byte.

## Situation room

`situation.py::build_situation_room(status, roster, ledger, gadgets)` renders
a single self-contained HTML document (no external assets, no JavaScript):
summary cards, a per-package table (rank, slug, film, codename, status, phase,
coverage), and the Q-branch gadget table.  Every value is HTML-escaped; the
document is deterministic given its inputs.  `scripts/build_situation_room.py`
writes it to the gitignored `output/` tree.
