# bond-coordinator TODO

Forward-only backlog for **bond-coordinator** — mission control (Layer 2) of
the BOND suite.  Local-only working tree; no remote.

## Status

- Phase 1 build complete and green: registry + ledger + status + situation
  room + manuscript variables, all with a zero-mock real-data test suite.
- Verified: `uv run pytest tests/ --cov=src --cov-fail-under=90` passes
  (coverage well above the 90% gate); `ruff check`, `ruff format --check`, and
  `mypy` clean on `src/bond_coordinator` and `scripts/`.

## Integration points (dependencies not yet built)

`bond-coordinator` depends on `bond-api` (Layer 1) and `bond-utilities`
(Layer 0), neither of which is built yet.  As instructed, this package ships a
**pure-core** implementation and defers integration:

1. **Protocol types** (`bond-api`).  `src/bond_coordinator/types.py` carries a
   pure-core mirror of the Layer-1 shapes (`Asset`, `Gadget`, `GadgetRegistry`,
   `PackageStatus`, `MissionPhase`) with identical field names/semantics per
   `SCOPE.md` §3.2.  **When `bond-api` lands**, swap `registry.py`/`types.py`
   to import from `bond_api.registry` — the swap is a single import and changes
   no public API.  The runtime probe in `scripts/{status_report,build_situation_room}.py`
   already reports `dependency_ready` and flips on automatically.
2. **Provenance I/O** (`bond-utilities`).  `MissionLedger.to_json/from_json`
   and the `scripts/advance_mission.py` persistence are local stdlib
   equivalents of `bond-utilities` `mission_io`.  When available, route ledger
   persistence through `mission_io` for shared provenance conventions.

## Roadmap

- [x] `src/bond_coordinator/registry.py` — 27-film ROSTER, codenames, status/coverage.
- [x] `src/bond_coordinator/ledger.py` — lifecycle phases, forward-only rules, audit trail, staleness, JSON.
- [x] `src/bond_coordinator/status.py` — aggregate counts, coverage summary, stale/blocked flags.
- [x] `src/bond_coordinator/situation.py` — HTML situation room (packages + gadgets).
- [x] `src/bond_coordinator/manuscript_variables.py` — config identity + registry tokens.
- [x] Thin `scripts/` (status_report, advance_mission, build_situation_room, z_generate_manuscript_variables).
- [x] Zero-mock, deterministic test suite (5-film fixture + full-registry checks).
- [x] Re-identity: README, AGENTS, TODO, docs, manuscript, CITATION, domain/experiment overlays.
- [ ] Wire real `bond-api` registry types when Layer 1 is built (see above).
- [ ] Route ledger provenance through `bond-utilities` `mission_io`.
- [ ] Consume `bond-ops` aggregate gate output to update `registry.py`
      status/coverage (currently all packages are honest `scaffolded`/`None`).
- [ ] Supply-recorded gadget inventory from film packages into the situation room
      (currently the gadget registry is fed by `output/data/gadgets.json` if present).

## Guardrails (persistent)

- Zero-mock testing; real data + computation only.
- ≥90% line+branch coverage on `src/` (`--cov-fail-under=90`).
- Deterministic: fixed seeds/clocks; no untracked random reliance.
- Thin orchestrators in `scripts/`; business logic in `src/`.
- `ruff` + `mypy` clean on `src/bond_coordinator` and `scripts/`.
- Local-only: never push to any remote (there is none).  Commit path-scoped
  inside this package only.
