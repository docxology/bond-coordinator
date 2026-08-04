# Output Inventory — bond-coordinator

All artifacts are generated under `output/` (gitignored, disposable),
populated by the thin `scripts/` orchestrators.  Never hand-edit anything here.

| Artifact | Producer script | Pure-core generator | Notes |
|---|---|---|---|
| `output/data/suite_status.json` | `scripts/status_report.py` | `src/bond_coordinator/status.py::build_status` | machine-readable fleet snapshot |
| `output/data/mission_ledger.json` | `scripts/advance_mission.py` | `src/bond_coordinator/ledger.py::MissionLedger.to_json` | append-only audit trail, load-bearing provenance |
| `output/data/gadgets.json` | *(optional input; not produced)* | `src/bond_coordinator/types.py::GadgetRegistry` | optional gadget inventory fed to the situation room |
| `output/data/manuscript_variables.json` | `scripts/z_generate_manuscript_variables.py` | `src/bond_coordinator/manuscript_variables.py::generate_variables` | resolved `{{TOKEN}}` map |
| `output/manuscript/*.md` | `scripts/z_generate_manuscript_variables.py` | `src/bond_coordinator/manuscript_variables.py::resolve_manuscript_tree` | token-substituted manuscript templates |
| `output/situation_room.html` | `scripts/build_situation_room.py` | `src/bond_coordinator/situation.py::build_situation_room` | self-contained HTML dashboard |

## Regeneration sequence

1. `uv run python scripts/status_report.py` — (re)build the fleet snapshot.
2. `uv run python scripts/advance_mission.py --slug <s> --phase <p>` — record phase moves (optional).
3. `uv run python scripts/build_situation_room.py` — render the dashboard.
4. `uv run python scripts/z_generate_manuscript_variables.py` — hydrate manuscript tokens (runs last).

To change what a generated file contains, change its **generator**, then
re-run.  Editing `output/` has zero lasting effect.
