---
name: bond-coordinator
description: Mission control (Layer 2) for the BOND fleet — registry, reconciliation, mission-state ledger, suite status, situation room. Load when working inside this package.
version: 0.1.0
author: docxology
license: MIT
tags: [bond, mission-control, registry, reconcile, ledger, situation-room]
---

# bond-coordinator

Project-scoped skill for the `bond-coordinator` repository itself.  Load when
working inside this repo.

## When to Use

- Working inside `bond-coordinator` — editing `src/bond_coordinator/`,
  `scripts/`, tests, or docs.
- Verifying the pure-core / thin-orchestrator boundary or the zero-mock,
  determinism, and coverage contracts.
- Re-identifying or maintaining this BOND package.

## Quick Reference

```bash
# From this repository's root
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src scripts tests && uv run ruff format --check src scripts tests
uv run mypy
```

## Run the tools

```bash
uv run python scripts/status_report.py
uv run python scripts/advance_mission.py --slug goldfinger --phase recon --by agent-007
uv run python scripts/build_situation_room.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Pitfalls

- **Keep scripts thin.**  Registry/ledger/status/situation logic belongs in
  `src/bond_coordinator/` — a transition rule or count in `scripts/` violates
  the boundary.
- **No mocks.**  All tests use real data/files/computation.  Determinism comes
  from the injected `FIXED_NOW` clock in `tests/conftest.py`.
- **Pure core.**  `src/` imports stdlib + `pyyaml` only — no
  `infrastructure.*`, no sibling BOND packages, no file I/O.
- **Outputs are disposable.**  Never edit `output/`; regenerate from source.
- **Standalone repository.**  Own git repo with `origin`
  (`docxology/bond-coordinator`, default branch `main`); commit at the root,
  not into a nesting template worktree.
- **bond-api is built — the mirror is a boundary, not a stopgap.**  The pure
  core ships its own protocol mirror (`src/bond_coordinator/types.py`) so `src/`
  imports no sibling (see `docs/architecture.md`).

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- Read-first rules: [`docs/agent_instructions.md`](../../../docs/agent_instructions.md)
- Architecture & layer contract: [`docs/architecture.md`](../../../docs/architecture.md)
