# Forking & Standalone Contract — bond-coordinator

`bond-coordinator` is one package of the BOND fleet, itself forked from the
code-first research exemplar.  Three
behaviors matter to anyone working here:

1. **Own identity, own git repo.**  This package has its own `git init` history,
   its own `pyproject.toml` name/version, config, and manuscript.  Its
   re-identity removed exemplar strings from src/, tests/, scripts/, and
   manuscript/.  The only residual mention of the exemplar is in docs prose
   explaining lineage, and currently there is none.

2. **Local-only.**  There is no remote.  Never push anywhere.  Commit path-scoped
   changes inside this package only with `git add -A` inside this directory.

3. **Pure core, thin orchestrators.**  Business logic lives in
   `src/bond_coordinator/` (stdlib + pyyaml); `scripts/` only parses argv,
   touches files, and probes for `bond_api`.  If you move logic into a script,
   you break the layer contract (see `docs/architecture.md`).

## Friction points

- **Coverage**: the gate is `--cov=src --cov-fail-under=90` (line + branch).
  Do not delete tests to hit it.
- **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in
  `tests/`.
- **Determinism**: fixed clocks in fixtures; no wall-clock tokens in generated
  artifacts.
- **Drift sweep**: an `rg` over the tree for leftover exemplar identity
  strings must return nothing (any occurrence is a defect).
