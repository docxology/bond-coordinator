# Syntax Guide — bond-coordinator

Covers manuscript `{{TOKEN}}` conventions and where the authoritative list
lives on this package.

## `{{TOKEN}}` injection

Fleet counts and identity are **never hand-authored in prose**.  They are
injected by `scripts/z_generate_manuscript_variables.py` →
`src/bond_coordinator/manuscript_variables.py::generate_variables()`.

The authoritative token table is the return value of `generate_variables()`,
and the cross-reference gate is `tests/test_manuscript_variables.py` (it reads
the real `manuscript/config.yaml`).  `manuscript/SYNTAX.md` mirrors that table
for humans but may lag the code; the test is the source of truth.

## Identity config

`manuscript/config.yaml` provides:

- `paper.title`, `paper.subtitle`, `paper.version` → `CONFIG_TITLE`, `CONFIG_SUBTITLE`, `CONFIG_VERSION`
- `mission.codename` → `CONFIG_CODENAME`
- `keywords` → `CONFIG_KEYWORDS`

## Registry-derived tokens

`REGISTRY_TOTAL`, `REGISTRY_READY/BUILDING/SCAFFOLDED/RED`,
`REGISTRY_COVERAGE_KNOWN/UNKNOWN/MEAN/AT_90`, `REGISTRY_BLOCKED_COUNT`,
`REGISTRY_STALE_COUNT`, `REGISTRY_PACKAGES_CSV`,
`REGISTRY_INFRA_PACKAGE_COUNT`, `REGISTRY_FIRST_SLUG/FIRST_YEAR`,
`REGISTRY_LAST_SLUG/LAST_YEAR`, `LEDGER_TRANSITION_TOTAL`,
`LEDGER_PHASE_COUNT` — all computed from
`src/bond_coordinator/registry.py` + `status.py`, so they can never drift from
the code.

## Adding a token

1. Add a key/value in `generate_variables()`.
2. Add an assertion in `tests/test_manuscript_variables.py`.
3. Reference it in a manuscript file as `{{TOKEN}}`.
4. Verify: `uv run python scripts/z_generate_manuscript_variables.py`, then
   `rg -l "\{\{" output/manuscript/ || echo "All tokens resolved"`.

## Manuscript Markdown

- Citation keys resolve from `manuscript/references.bib`; never write raw
  `\cite{}` (see `manuscript/SYNTAX.md`).
- Every H1 carries a `{#sec:<name>}` label (section registry in
  `manuscript/SYNTAX.md`).
- No figures or equations exist for this package.

## Gate-threshold tokens

`GATE_COVERAGE_FLOOR` and `GATE_STALE_DAYS` are read from the constants that
*enforce* them (`status.py::COVERAGE_FLOOR`, `status.py::DEFAULT_STALE_DAYS`),
not restated.  Prose that mentions a threshold must use the token, so changing
the gate updates the manuscript rather than leaving a stale figure behind.
