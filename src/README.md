# src/

Importable pure-core package for `bond-coordinator`:

```
bond_coordinator/
  __init__.py             public API
  types.py                Asset, Gadget, GadgetRegistry, PackageStatus, MissionPhase
  registry.py             PackageRecord, ROSTER (27 films), accessors, subset_roster
  gates.py                gate-manifest decode (parse_gate_manifest), apply_gate_results
  reconcile.py            codename/gadget merge rules, gadget_purpose, report
  ledger.py               MissionLedger (lifecycle, audit, staleness, JSON)
  status.py               SuiteStatus, build_status, CoverageSummary
  situation.py            situation-room HTML
  manuscript_variables.py config + registry {{TOKEN}} map, tree resolution
```

Pure core: standard library + `pyyaml` only.  No `infrastructure.*`, no
sibling BOND imports, and no file I/O except the two writers that take their
destination from the caller (`situation.write_situation_room`,
`manuscript_variables.resolve_manuscript_tree`) — thin `scripts/` supplies
every path.

Gate: `uv run pytest tests/ --cov=src --cov-fail-under=90`.  Ruff + mypy clean.
