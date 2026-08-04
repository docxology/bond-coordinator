# scripts/

Thin orchestrators for `bond-coordinator` (all business logic lives in
`src/bond_coordinator/`).

```
status_report.py                    print/persist suite status (--json)
advance_mission.py                  advance a package's phase in the ledger
build_situation_room.py             regenerate output/situation_room.html
z_generate_manuscript_variables.py  hydrate manuscript {{TOKEN}}s (runs last)
```

```bash
uv run python scripts/status_report.py
uv run python scripts/advance_mission.py --slug goldfinger --phase recon
uv run python scripts/build_situation_room.py
uv run python scripts/z_generate_manuscript_variables.py
```

Thin by design: `ruff` + `mypy` clean, smoke-tested in
`tests/test_scripts_smoke.py`.
