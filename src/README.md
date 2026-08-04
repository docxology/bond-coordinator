# src/

Importable pure-core package for `bond-coordinator`:

```
bond_coordinator/
  __init__.py             public API
  types.py                Asset, Gadget, GadgetRegistry, PackageStatus, MissionPhase
  registry.py             PackageRecord, ROSTER (27 films), accessors, subset_roster
  ledger.py               MissionLedger (lifecycle, audit, staleness, JSON)
  status.py               SuiteStatus, build_status, CoverageSummary
  situation.py            situation-room HTML
  manuscript_variables.py config + registry {{TOKEN}} map, tree resolution
```

Pure core: standard library + `pyyaml` only.  No `infrastructure.*`, no
sibling BOND imports, no file I/O (thin `scripts/` handles the filesystem).

Gate: `uv run pytest tests/ --cov=src --cov-fail-under=90`.  Ruff + mypy clean.
