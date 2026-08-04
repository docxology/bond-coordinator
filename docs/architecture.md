# Architecture — bond-coordinator

## Layers

```
scripts/            thin orchestrators (argv, file I/O, bond_api probe)
  │  imports only
  ▼
src/bond_coordinator/   PURE CORE (stdlib + pyyaml; no infrastructure, no siblings)
  ├── types.py               Asset, Gadget, GadgetRegistry, PackageStatus, MissionPhase
  ├── registry.py            PackageRecord, ROSTER (27), get_package, find_by_status, subset_roster
  ├── ledger.py              LedgerEntry, MissionLedger (transitions, audit, staleness, JSON)
  ├── status.py              CoverageSummary, BlockedPackage, SuiteStatus, build_status
  ├── situation.py           build_situation_room, write_situation_room
  └── manuscript_variables.py  load_config, generate_variables, resolve_manuscript_tree
```

**Dependency arrow is strictly downward.**  `src/` never imports
`infrastructure.*` or a sibling BOND package; `scripts/` imports `src/` only.
The one deliberately external probe is `scripts/` checking whether `bond_api`
(the future Layer 1) is importable — it reports `dependency_ready` and never
fails when absent.

## Module responsibilities

- **`registry.py`** — the authoritative 27-film ROSTER (canon order), the
  `PackageRecord` shape, and lookup helpers.  Status/coverage are honest
  (currently all `scaffolded`/`None`); they change only from measured gate
  output.
- **`ledger.py`** — forward-only mission lifecycle per package, append-only
  audit trail, staleness.  Pure JSON codecs (`to_json`/`from_json`) for
  provenance; only `scripts/advance_mission.py` touches disk.
- **`status.py`** — `build_status(roster, ledger, now=, stale_days=,
  dependency_ready=)` → one deterministic `SuiteStatus` snapshot with
  stale/blocked flags and a coverage summary.
- **`situation.py`** — renders `SuiteStatus` + roster + ledger + `GadgetRegistry`
  into one self-contained, HTML-escaped document.
- **`manuscript_variables.py`** — identity from `manuscript/config.yaml`,
  fleet counts from registry/status, `{{TOKEN}}` map + tree resolution.

## Integration point (bond-api)

When `bond-api` lands, `types.py`/`registry.py` swap to import the real
protocol types from `bond_api.registry`.  The public API is unchanged, so
nothing else in the package moves (see `TODO.md`).

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
