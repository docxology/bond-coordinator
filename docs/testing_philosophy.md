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
| `test_ledger.py` | lifecycle transitions (forward, touch, jump, backwards/past-debrief errors), identity validation, audit trail + summaries, staleness, JSON round-trip + malformed/unknown-package errors |
| `test_status.py` | fresh vs. mixed fleets, coverage summary, every blocked rule, stale flags, the applied `stale_days` threshold, per-layer summaries, count helpers |
| `test_situation.py` | HTML structure, every slug/film/codename, gadget rendering + escaping, coverage heat, timeline bars, layers section (present **and** absent), stale-threshold text, dependency-probe wording, byte-determinism, file write |
| `test_reconcile.py` | codename override + gadget harvest merge semantics, `gadget_purpose` across every payload shape, real-films CLI, broken-film isolation, builtin-docstring regression guard |
| `test_manuscript_variables.py` | config parsing (success + all error paths), identity + registry tokens (full + subset + empty), roster-span and gate-threshold tokens, `resolve_manuscript_tree`, live prose-token cross-reference gate |
| `test_scripts_smoke.py` | each thin orchestrator runs end-to-end and exits 0; illegal transitions exit 1 |

## Positive controls

A guard that has never been observed to fire is a guard that might not work.
Two of this package's contracts are therefore tested by *causing the failure*,
not by asserting the happy path:

- **Broken-film isolation.**
  `test_reconcile.py::test_reconcile_isolates_a_broken_film` writes a real
  film package whose `mission.py` raises `NameError` at import, points the CLI
  at it with `--bond-root`, and asserts the run still exits 0, names the
  failure on stderr, and still harvests the healthy film.  This caught a live
  defect: the guard originally caught only `(ImportError, RuntimeError)`, so a
  single half-edited sibling aborted reconciliation for all 27 films.
- **No borrowed docstrings.**
  `TestGadgetPurpose::test_plain_data_never_returns_a_builtin_docstring`
  asserts the derived purpose *differs from* `payload.__doc__` for every
  plain-data shape.  This is the exact inversion of the defect that put
  `"dict() -> new empty dictionary"` into 19 of 73 harvested gadget purposes.

## Assertions must be able to fail

Prefer assertions bound to structure over substring checks that could pass
vacuously.  Concretely: assert `"<td>yes</td>" in html`, not `"yes" in html`;
assert a threshold *changes the outcome* (`default.stale_packages !=
relaxed.stale_packages`), not merely that a field echoes back the value it was
handed.

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
