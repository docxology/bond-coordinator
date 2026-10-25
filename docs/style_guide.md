# Style Guide — bond-coordinator

Seven rules, inherited from the research-exemplar bar and adapted to a
mission-control package.

## 1. Zero Mocks

Never use `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`.  Test
real behavior.

## 2. Reference, Don't Reimplement

`src/bond_coordinator/` is the single source of truth for registry/ledger/
status/situation logic.  `scripts/` calls into it; it does not re-derive
counts or rules.  If two places compute the same thing, that is a defect.

## 3. Pure Core, Thin Orchestrators

`src/` does no argv parsing and no implicit file I/O — the only writers are
`situation.write_situation_room` and
`manuscript_variables.resolve_manuscript_tree`, both of which take the
destination path from their caller.  `scripts/` does no business logic
(no transition rules, no aggregation, no HTML generation).  The dependency
arrow is strictly `scripts/ → src/`.

## 4. Show, Not Tell

Reference explicit paths and functions (`src/bond_coordinator/ledger.py::MissionLedger.advance`),
not module names.

## 5. Explicit Paths

Use `Path` objects rooted at the resolved project root; no string
concatenation of paths.  `scripts/` compute `PROJECT_ROOT` once and reuse it.

## 6. Type Hints

Every public function has full annotations (params and return).  `mypy` is
run with `disallow_untyped_defs = true`, so untyped signatures fail the gate.

## 7. Error Messages

Raise precise, actionable exceptions:

- `ValueError` for rule violations in the ledger (backwards transition, past
  debrief) and data-validity problems in JSON/config parsing — a single,
  documented exception contract per boundary.
- `KeyError` for unknown slugs / missing gadgets / unknown packages.
- `FileNotFoundError` (from the stdlib) for a missing config file.
  Never swallow an exception to hide a failure.

## Formatting

`ruff check` + `ruff format --check` clean on `src/`, `scripts/`, `tests/`
(line length 88).  Run `uv run ruff format` before committing.
