# Testing Philosophy — bond-coordinator

## Zero-Mock Policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`.  Every test exercises real data, real computation, and real files.
Coverage is enforced via `pyproject.toml` (`fail_under = 90`, branch = true).

## Determinism

- All time-dependent paths take an injectable clock.  `tests/conftest.py`
  defines `FIXED_NOW` and the `fixed_clock` fixture; every timestamp assertion
  pins to it.
- `to_json()` is asserted deterministic; the situation room is asserted
  byte-identical across repeated builds.
- No random draws anywhere.

## The 5-film fixture

Behavioral tests run against a **deterministic 5-film subset** of the real
registry (`dr_no`, `goldfinger`, `goldeneye`, `skyfall`, `no_time_to_die`) via
`subset_roster` — representative canon spread, no dependence on the other 22
being built.  A full-registry test independently asserts 27 uniqueness and
canon ordering.

## Test files

| File | Covers |
|---|---|
| `conftest.py` | path setup, fixtures (`sample_roster`, `fixed_clock`, `sample_gadgets`, `aged_ledger`) |
| `test_registry.py` | 27-film ROSTER completeness, accessors, `subset_roster`, `GadgetRegistry` incl. constructor seeding + duplicate/missing errors |
| `test_ledger.py` | lifecycle transitions (forward, touch, jump, backwards/past-debrief errors), audit trail, staleness, JSON round-trip + malformed/unknown-package errors |
| `test_status.py` | fresh vs. mixed fleets, coverage summary, every blocked rule, stale flags, count helpers |
| `test_situation.py` | HTML structure, every slug/film/codename, gadget rendering + escaping, blocked/stale rendering, byte-determinism, file write |
| `test_manuscript_variables.py` | config parsing (success + all error paths), identity + registry tokens (full + subset), `resolve_manuscript_tree` |
| `test_scripts_smoke.py` | each thin orchestrator runs end-to-end and exits 0; illegal transitions exit 1 |

## Test categories

- **Unit**: registry/ledger/status/situation pure logic.
- **Integration**: manuscript token generation against the real `config.yaml`;
  script subprocess smoke tests.
- **Error paths**: every `ValueError` / `KeyError` / `FileNotFoundError`
  branch is asserted (malformed JSON, unknown slug, missing config, illegal
  transition, duplicate gadget).

## Running

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run pytest tests/ --cov=src --cov-report=term-missing   # find gaps
```
