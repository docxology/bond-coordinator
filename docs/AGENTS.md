# docs/ — AGENTS.md

Technical overview of `docs/` for `bond-coordinator`.  Every document here is a
hard constraint, not a suggestion; the read-first entry point is
[`agent_instructions.md`](agent_instructions.md).

## Layer contract (reflected in every doc)

- `src/bond_coordinator/` — pure core (stdlib + pyyaml).  No
  `infrastructure.*`, no sibling BOND imports, no filesystem side-effects.
- `scripts/` — thin orchestrators; the only place that parses argv, touches
  files, and imports `bond-api` (to discover film `MissionProvider`s and to
  probe its availability).
- `tests/` — zero-mock, deterministic, ≥90% coverage on `src/`.

## Reading order

1. `agent_instructions.md` — start here.
2. `architecture.md` — boundaries before touching files.
3. `testing_philosophy.md` — before writing/modifying tests.
4. `syntax_guide.md` — before editing manuscript/tokens.
5. `style_guide.md` — before writing source.

## REQUIRED vs AESTHETIC

| Path | Status | Enforcing gate |
|---|---|---|
| `src/bond_coordinator/*.py` | REQUIRED | coverage gate + ruff + mypy |
| `tests/*` | REQUIRED | 90% coverage gate |
| `scripts/*.py` | REQUIRED | ruff + mypy + smoke tests |
| `manuscript/config.yaml` | REQUIRED | `generate_variables` identity tokens |
| `docs/*` | convention | cross-references resolve |
