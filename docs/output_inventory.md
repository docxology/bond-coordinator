# Output Inventory — bond-coordinator

All artifacts are generated under `output/` (gitignored, disposable),
populated by the thin `scripts/` orchestrators.  Never hand-edit anything here.

| Artifact | Producer script | Pure-core generator | Notes |
|---|---|---|---|
| `output/data/suite_status.json` | `scripts/status_report.py` | `src/bond_coordinator/status.py::build_status` | machine-readable fleet snapshot |
| `output/data/mission_ledger.json` | `scripts/advance_mission.py` | `src/bond_coordinator/ledger.py::MissionLedger.to_json` | append-only audit trail, load-bearing provenance |
| `output/data/gadgets.json` | `scripts/reconcile.py --gadgets` | `src/bond_coordinator/reconcile.py::harvest_gadgets` + `gadget_purpose` | flat Q-branch inventory harvested from the real films; consumed by the situation room |
| `output/data/reconciled.json` | `scripts/reconcile.py --write` | `src/bond_coordinator/reconcile.py::override_codenames` | reconciled roster manifest: per-film codename + gadgets, plus the `skipped` list |
| `output/data/manuscript_variables.json` | `scripts/z_generate_manuscript_variables.py` | `src/bond_coordinator/manuscript_variables.py::generate_variables` | resolved `{{TOKEN}}` map |
| `output/manuscript/*.md` | `scripts/z_generate_manuscript_variables.py` | `src/bond_coordinator/manuscript_variables.py::resolve_manuscript_tree` | token-substituted manuscript templates |
| `output/situation_room.html` | `scripts/build_situation_room.py` | `src/bond_coordinator/situation.py::build_situation_room` | self-contained HTML dashboard; **consumes** `output/data/reconciled.json` (film-declared codenames) and the fleet gate manifest (measured status/coverage), and names both in its provenance block |

### Consumed, not produced

| Input | Written by | Consumed by | Effect when absent |
|---|---|---|---|
| `../output/aggregate/gate_manifest.json` | `bond-ops` (sibling package) | `status_report.py`, `build_situation_room.py`, `z_generate_manuscript_variables.py` via `src/bond_coordinator/gates.py` | rows keep the registry's unmeasured seed defaults; every consumer says so on stderr and in its own output |
| `output/data/reconciled.json` | `scripts/reconcile.py --write` | `build_situation_room.py` via `reconcile.py::override_codenames` | the dashboard renders provisional codenames and labels them provisional |

## Regeneration sequence

1. `uv run python scripts/status_report.py` — (re)build the fleet snapshot.
2. `uv run python scripts/advance_mission.py --slug <s> --phase <p>` — record phase moves (optional).
3. `uv run python scripts/reconcile.py --write output/data/reconciled.json --gadgets output/data/gadgets.json`
   — harvest real films' codenames + gadgets (optional; requires `bond_api`
   importable, and reports any unloadable film on stderr).
4. `uv run python scripts/build_situation_room.py` — render the dashboard.
   Runs **after** step 3, because that is where the film-declared codenames
   come from; add `--no-gate-manifest` for a fleet-independent render.
5. `uv run python scripts/z_generate_manuscript_variables.py` — hydrate manuscript tokens (runs last).

To change what a generated file contains, change its **generator**, then
re-run.  Editing `output/` has zero lasting effect.
