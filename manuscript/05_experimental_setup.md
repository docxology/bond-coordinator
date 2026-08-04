# Experimental Setup {#sec:experimental_setup}

## Configuration surface

The manuscript identity is loaded from `manuscript/config.yaml` by
`src/bond_coordinator/manuscript_variables.py::load_config` and injected as
tokens; the only hand-authored prose values are the tokens themselves, never
hardcoded numbers.  Identity fields (title `{{CONFIG_TITLE}}`, subtitle
`{{CONFIG_SUBTITLE}}`, version `{{CONFIG_VERSION}}`, codename
`{{CONFIG_CODENAME}}`, keywords) live under `paper:` and `mission:`.

There is deliberately **no `experiment:` block**: unlike the exemplar, the
coordinator has no analysis-output dependency.  `generate_variables(...,
require_outputs=...)` accepts the flag for pipeline parity but never gates on
generated files — this is the one intentional divergence from the exemplar's
strict analysis-to-manuscript contract, documented in `docs/architecture.md`.

## Dependencies

- **Runtime**: `pyyaml` (manuscript config parsing).  Everything else is the
  Python standard library.
- **Developer**: `pytest`, `pytest-cov` (coverage gate), `ruff` (lint +
  format), `mypy` (types).

## Quality gates

The enforced gates for this package are:

1. **Coverage**: `uv run pytest tests/ --cov=src --cov-fail-under=90` —
   line + branch coverage on `src/` at or above 90%.
2. **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in
   `tests/`; all tests use real data and real computation.
3. **Types/style**: `ruff check` and `mypy` clean on `src/bond_coordinator`
   and `scripts/`.
4. **Determinism**: fixed clocks and fixed seeds; no wall-clock tokens in
   generated artifacts.

## Test data

Behavioral tests are seeded from a **deterministic 5-film fixture** of
representative packages (`dr_no`, `goldfinger`, `goldeneye`, `skyfall`,
`no_time_to_die`) via `subset_roster`, so the suite exercises every rule
without depending on all 27 packages being built.  A full-registry test
independently asserts completeness (27 unique, canon-ordered slugs).
