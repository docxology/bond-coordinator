# bond-coordinator TODO

Forward-only backlog for **bond-coordinator** — mission control (Layer 2) of
the BOND suite.  Local-only working tree; no remote.

## Status

- **Phase 4 (deep improvement) green**: ledger transition validation + audit
  summaries (`validate_transition`, `transition_summary`, `per_agent_summary`,
  `phase_timeline`); status per-layer summaries (`SUITE_LAYERS`,
  `LayerSummary`, `build_status(layer_ready=)`); situation room deepened with
  coverage heat, mission-timeline bars, per-film gadget groups, suite-layers
  and recent-transitions sections.  Reconcile (refresh/replace) untouched.
- Verified: `uv run pytest tests/ --cov=src --cov-fail-under=90` passes ~99%
  coverage; `ruff check`/`ruff format --check`/`mypy` clean; 0 mocks, 0
  failures, 0 skipped.

## Integration points

`bond-coordinator` depends on `bond-api` (Layer 1, **built** — drives
`scripts/reconcile.py` discovery) and `bond-utilities` (Layer 0, not yet
built).  Unfinished integration:

1. **Provenance I/O** (`bond-utilities`).  `MissionLedger.to_json/from_json`
   and `scripts/advance_mission.py` persistence are local stdlib equivalents
   of `bond-utilities` `mission_io`.  When available, route ledger persistence
   through `mission_io` for shared provenance conventions.

## Roadmap

- [x] `src/bond_coordinator/registry.py` — 27-film ROSTER, codenames, status/coverage.
- [x] `src/bond_coordinator/ledger.py` — lifecycle phases, forward-only rules, audit trail, staleness, JSON.
- [x] `src/bond_coordinator/status.py` — aggregate counts, coverage summary, stale/blocked flags.
- [x] `src/bond_coordinator/situation.py` — HTML situation room (packages + gadgets).
- [x] `src/bond_coordinator/manuscript_variables.py` — config identity + registry tokens.
- [x] Thin `scripts/` (status_report, advance_mission, build_situation_room, z_generate_manuscript_variables).
- [x] Zero-mock, deterministic test suite (5-film fixture + full-registry checks).
- [x] Re-identity: README, AGENTS, TODO, docs, manuscript, CITATION, domain/experiment overlays.
- [x] `src/bond_coordinator/reconcile.py` + `scripts/reconcile.py` — merge real films' codenames + gadgets (refresh/replace).
- [x] **Phase 4** ledger validation + audit summaries; status per-layer summaries; situation room coverage heat / mission timeline / per-film gadgets / layers section / audit tail.
- [x] **Phase 4** live `{{TOKEN}}` cross-reference gate over numbered manuscript sections.
- [ ] Route ledger provenance through `bond-utilities` `mission_io`.
- [ ] Feed per-layer infra readiness from a real fleet probe (currently `layer1` tracks `dependency_ready`; others are injectable via `layer_ready`).

## Guardrails (persistent)

- Zero-mock testing; real data + computation only.
- ≥90% line+branch coverage on `src/` (`--cov-fail-under=90`).
- Deterministic: fixed seeds/clocks; no untracked random reliance.
- Thin orchestrators in `scripts/`; business logic in `src/`.
- `ruff` + `mypy` clean on `src/bond_coordinator` and `scripts/`.
- Local-only: never push to any remote (there is none).  Commit path-scoped
  inside this package only.

