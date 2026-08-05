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
   line + branch coverage on `src/` at or above {{GATE_COVERAGE_FLOOR}}, the
   same floor `status.py::COVERAGE_FLOOR` applies when grading the fleet.
2. **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in
   `tests/`; all tests use real data and real computation.
3. **Types/style**: `ruff check` and `mypy` clean on `src/bond_coordinator`
   and `scripts/`.
4. **Determinism**: fixed clocks and fixed seeds; no wall-clock tokens in
   generated artifacts.

## Test data

Behavioral tests are seeded from a **deterministic five-film fixture** of
representative packages (`dr_no`, `goldfinger`, `goldeneye`, `skyfall`,
`no_time_to_die`) via `subset_roster`, so the suite exercises every rule
without depending on all {{REGISTRY_TOTAL}} packages being built.  A
full-registry test independently asserts completeness ({{REGISTRY_TOTAL}}
unique, canon-ordered slugs).

Tests that touch the live fleet are written to assert **this package's**
contract rather than a sibling's internals, because sibling packages are
developed concurrently and may be mid-edit at any moment.  Where a
deterministic film is required — for the broken-film isolation control and the
gadget-purpose regression guard — the test materialises its own minimal film
package in a temporary directory and points the CLI at it with `--bond-root`.
This keeps the suite's result a function of this package alone.
