# AI Agent Instructions — bond-coordinator

`bond-coordinator` is the **mission control (Layer 2)** package of the BOND
suite.  Read this file before touching any other file in this project.

## Rule 1: Read the Hub First

Reading order is mandatory, not advisory.

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** | All modifications | Risk all violations below |
| [`architecture.md`](architecture.md) | Any file-boundary change | Risk breaking the pure-core / thin-script boundary |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification | Risk mocks or coverage regressions |
| [`style_guide.md`](style_guide.md) | Any source code modification | Risk wrong exception types, wrong layer, bad messages |
| [`syntax_guide.md`](syntax_guide.md) | Any manuscript `.md` / token change | Risk hand-authored fleet counts |

## Rule 2: Coverage Gate — ≥90% on `src/`

The enforced gate:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Before changing `src/bond_coordinator/`, count the tests covering the function.
After changing, re-run the gate with `--cov-report=term-missing` and fix gaps —
**never delete tests** to make the number work.

## Rule 3: The Layer Boundary — pure `src/`, thin `scripts/`

**`src/bond_coordinator/`** is pure: standard library + `pyyaml` only.  No
`infrastructure.*`, no sibling BOND imports, no filesystem side-effects
(`MissionLedger` JSON methods are pure codecs; only `scripts/` calls them on
real files).

**`scripts/*.py`** orchestrates: argv parsing, file I/O, `bond_api` provider
discovery + availability probing, and calls into `src/`.

**Boundary test**: if a line in `scripts/` decides a transition rule, computes a
status count, generates HTML, or *interprets* a value (e.g. deriving a gadget's
purpose from its payload), it violates the boundary.  That logic belongs in
`src/` and must be tested.  `reconcile.gadget_purpose` was moved into `src/`
for exactly this reason after the inline version harvested builtin docstrings.

## Rule 3b: Cross-Package Reads Must Degrade, Never Abort

`scripts/reconcile.py` imports 27 independently developed sibling packages.
Any of them may be mid-edit and raise **any** exception at import time.

- Guard per film with `except Exception`, print the slug plus the exception
  **type and message** to stderr, and record the slug as skipped.
- Never narrow that guard to a specific exception tuple — a `NameError` from a
  half-saved sibling must not take down a fleet-wide run.
- Never make it silent: an unharvestable film is reported, not dropped.
- Never write a test that asserts a *sibling's* internals (a specific codename
  or gadget name). Assert this package's contract against whatever the fleet's
  state is; use `--bond-root` with a purpose-built fixture film when you need
  a deterministic film to test against.

## Rule 4: "Show, Not Tell" Documentation

Reference explicit paths and functions.  Use file paths like
`src/bond_coordinator/ledger.py::MissionLedger.advance`, not "the ledger
module".

## Rule 5: Determinism Policy

- All time-dependent paths accept an injectable clock (`now`, `now_fn`); tests
  pin a fixed UTC reference.
- No wall-clock tokens in generated artifacts.
- No random reliance: `tests/conftest.py` seeds everything from fixed data.

## Rule 6: Style and Syntax Guides Govern Their Domains

- [`style_guide.md`](style_guide.md) governs `src/` and `scripts/`.
- [`syntax_guide.md`](syntax_guide.md) governs `manuscript/*.md`.

## Rule 7: `output/` Is Disposable

Never edit anything under `output/`.  Regenerate from source:
`scripts/status_report.py`, `scripts/advance_mission.py`,
`scripts/build_situation_room.py`, `scripts/z_generate_manuscript_variables.py`.

## Verification Checklist

Run before submitting any change:

1. `uv run pytest tests/ --cov=src --cov-fail-under=90`
2. `grep -rE "unittest\.mock|MagicMock|@patch|create_autospec" tests/ || echo "Clean"`
3. `uv run ruff check src scripts tests` and `uv run ruff format --check src scripts tests`
4. `uv run mypy`
5. `rg` drift sweep → empty (no leftover exemplar identity strings).
6. `git status` clean after your commit.

All must pass before you say "done".
