# Architecture — bond-coordinator

## Layers

```
scripts/            thin orchestrators (argv, file I/O, bond_api discovery + probe)
  │  imports only
  ▼
src/bond_coordinator/   PURE CORE (stdlib + pyyaml; no infrastructure, no siblings)
  ├── types.py               Asset, AssetKind, Gadget, GadgetRegistry, PackageStatus, MissionPhase
  ├── registry.py            PackageRecord, ROSTER (27), build_roster, get_package, find_by_status, subset_roster
  ├── reconcile.py           gadget_purpose, override_codenames, harvest_gadgets, reconcile_report
  ├── ledger.py              LedgerEntry, MissionLedger (transitions, validation, audit summaries, staleness, JSON)
  ├── status.py              CoverageSummary, BlockedPackage, LayerSummary, SUITE_LAYERS, SuiteStatus, build_status
  ├── situation.py           build_situation_room, write_situation_room
  └── manuscript_variables.py  load_config, generate_variables, resolve_manuscript_tree
```

**Dependency arrow is strictly downward.**  `src/` never imports
`infrastructure.*` or a sibling BOND package; `scripts/` imports `src/` only.
The one deliberately external dependency lives in `scripts/`: it imports
`bond_api` to discover film providers, and probes importability with
`importlib.util.find_spec` to report `dependency_ready`.  Both degrade
gracefully — see "Consuming the bond-api MissionProvider" below.

## Module responsibilities

- **`registry.py`** — the authoritative 27-film ROSTER (canon order), the
  `PackageRecord` shape, and lookup helpers.  Status/coverage are honest
  (currently all `scaffolded`/`None`); they change only from measured gate
  output.
- **`reconcile.py`** — pure merge of real films' codenames + gadget tables
  over the provisional registry (`override_codenames`, `harvest_gadgets`);
  refresh/replace semantics, inputs immutable.  Also owns `gadget_purpose`,
  which turns a film's gadget payload into a one-line purpose: a routine,
  class, or module contributes its own first docstring line; a string payload
  is used verbatim; anything else gets a factual shape summary
  (`"data payload: dict of 8 entries"`).  This function exists precisely
  because reading `payload.__doc__` unconditionally resolves to the *builtin
  type's* docstring for plain data, recording CPython's `"dict() -> new empty
  dictionary"` as a purpose the film never declared.  The discovery lives in
  `scripts/reconcile.py` via `bond-api`.
- **`ledger.py`** — forward-only mission lifecycle per package with
  attributable-identity validation (`validate_transition` never mutates),
  append-only audit trail, deterministic audit summaries
  (`transition_summary`, `per_agent_summary`, `phase_timeline`), staleness.
  Pure JSON codecs (`to_json`/`from_json`) for provenance; only
  `scripts/advance_mission.py` touches disk.
- **`status.py`** — `build_status(roster, ledger, now=, stale_days=,
  dependency_ready=, layer_ready=)` → one deterministic `SuiteStatus` snapshot
  with stale/blocked flags, a coverage summary, and a per-layer summary
  (`SUITE_LAYERS` topology → `LayerSummary` per layer).  The snapshot carries
  the `stale_days` threshold it was computed with, so a renderer states the
  threshold that was actually applied rather than assuming the default.
  `COVERAGE_FLOOR` is defined here and imported by `situation.py`, so the
  dashboard legend cannot drift from the gate the status module enforces.
- **`situation.py`** — renders `SuiteStatus` + roster + ledger + `GadgetRegistry`
  into one self-contained, HTML-escaped document: per-package table with
  mission-timeline bars and coverage heat, suite-layers table, per-film gadget
  groups, and a recent-transitions audit tail.
- **`manuscript_variables.py`** — identity from `manuscript/config.yaml`,
  fleet counts from registry/status, `{{TOKEN}}` map + tree resolution.

## Consuming the bond-api MissionProvider

`bond-coordinator` has **no `mission.py` and implements no `MissionProvider`**,
and that is deliberate.  `bond_api.protocol.MissionProvider` is the structural
contract every *film* package satisfies — `film: str` plus `brief() →
MissionBrief`, `recon(ReconRequest) → ReconReport`, `plan(MissionBrief) →
MissionPlan`, `execute(MissionPlan) → MissionOutcome`, `debrief(MissionOutcome)
→ Debrief`.  `bond_api.discovery.load_provider(slug, search_paths=...)` finds
one by importing `<slug>/mission.py`.  This package is Layer 2: it is a
**consumer** of providers, not one of them.  Giving mission control a synthetic
provider would put a non-film into the fleet's discovery surface and make the
registry a member of the roster it governs.

The consumption happens in exactly one place — `scripts/reconcile.py`, the
thin orchestrator:

1. `_discover_briefs(slugs, root=)` calls `load_provider(slug, …)` for each
   film that has a `mission.py`, then reads `provider.brief()` for the film's
   real `codename` and `objectives`.
2. `_discover_gadgets(slugs, root=)` imports `<slug>.mission` and reads its
   module-level `GADGETS`, accepting both shapes films use in practice: a
   `bond_api.registry.GadgetRegistry` (probed via `gadgets_for` + `lookup`) and
   a plain `dict`.
3. Both hand plain data to the pure functions in `src/.../reconcile.py`.  No
   `bond_api` type ever crosses into `src/` — that is what keeps the core pure.

**Degradation contract.**  Reconciliation runs across 27 independently
developed packages, so importing a film executes third-party module-level code
that can raise anything. Two guards make partial failure survivable, and both
are covered by tests rather than only asserted here:

| Condition | Behavior |
|---|---|
| `bond_api` not importable | briefs discovery returns empty; every film keeps its provisional codename; reported on stderr |
| A film has no `mission.py` | recorded as skipped; provisional codename stands |
| A film raises **any** exception on import | that film alone is skipped, its exception type and message printed to stderr; the other 26 still reconcile |
| A film's `GADGETS` has an unrecognised shape | reported on stderr and recorded as skipped — never a silent no-op |

`tests/test_reconcile.py::test_reconcile_isolates_a_broken_film` is the
positive control: it materialises a real film package whose `mission.py`
raises `NameError` at import, runs the CLI against it via `--bond-root`, and
asserts the run still exits 0 while the healthy film's gadget is harvested.

`src/bond_coordinator/types.py` remains a pure-core **mirror** of the protocol
shapes (`Asset`, `Gadget`, `GadgetRegistry`) so the core keeps zero sibling
imports.  It is a boundary, not a placeholder: the mirror stays even though
`bond-api` is built (see `TODO.md`).

## Intentional divergence from the exemplar

The exemplar's strict *analysis → manuscript-variables* contract is relaxed:
the coordinator has no analysis outputs, so `generate_variables` never gates
on generated files (`require_outputs` is accepted for parity only).  Documented
in `manuscript/05_experimental_setup.md`.

## How to add a capability

1. Put the business logic in `src/bond_coordinator/` (pure — no I/O, no
   infra imports).
2. Expose it through `__init__.py`.
3. Test it with real data (≥90%, zero mocks), covering error paths.
4. Add a thin `scripts/` wrapper only if it needs argv/file I/O.
5. Update this file, `src/AGENTS.md`, `README.md`, and `manuscript/SYNTAX.md`.
