# tests/

Zero-mock, deterministic test suite for `bond-coordinator`.

```
conftest.py                  path setup + 5-film fixture + fixed clock
test_registry.py             ROSTER completeness, accessors, GadgetRegistry
test_ledger.py               lifecycle transitions, audit, staleness, JSON
test_status.py               aggregation, coverage summary, stale/blocked
test_situation.py            situation-room HTML, escaping, determinism
test_manuscript_variables.py config + registry tokens, tree resolution
test_scripts_smoke.py        thin orchestrators end-to-end
```

Gate: `uv run pytest tests/ --cov=src --cov-fail-under=90` (line + branch).
No mocks; real data + computation only.
