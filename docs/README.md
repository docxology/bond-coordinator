# docs/ — Agent-Facing Documentation Hub

Operational rulebook for AI agents and developers inside `bond-coordinator`.

## Read-first protocol

Agents must read [`agent_instructions.md`](agent_instructions.md) before
modifying any project file.  It is the gate for the other documents.

## Document map

| File | Purpose |
|---|---|
| **This file (`README.md`)** | The index you are reading. |
| [`AGENTS.md`](AGENTS.md) | Technical overview of `docs/`: the layer contract, reading order, and which paths are REQUIRED vs conventional. |
| [`agent_instructions.md`](agent_instructions.md) | **Read first.** The hard rules (layer boundary, coverage gate, determinism, cross-package degradation) + verification checklist. |
| [`architecture.md`](architecture.md) | Module-by-module architecture of `src/`, how the pieces compose, and how this package consumes the frozen `bond_api` `MissionProvider`. |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, determinism, 5-film fixture, positive controls, test inventory. |
| [`style_guide.md`](style_guide.md) | 7 source-style rules + formatting (ruff). |
| [`syntax_guide.md`](syntax_guide.md) | `{{TOKEN}}` conventions; authoritative list = `generate_variables()` + cross-ref test. |
| [`output_conventions.md`](output_conventions.md) | `output/` layout + regeneration rules. |
| [`output_inventory.md`](output_inventory.md) | Producer/consumer graph for generated artifacts. |
| [`quickstart.md`](quickstart.md) | 5-minute first run. |
| [`troubleshooting.md`](troubleshooting.md) | Symptom-driven recipes. |
| [`faq.md`](faq.md) | Common questions (no figures, seed vs. measured status, codenames, deps). |
| [`forking_guide.md`](forking_guide.md) | Own-git / standalone-repo / boundary contract. |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript token hydration (no pixel pipeline here). |

## Key conventions

- **Pure core**: `src/bond_coordinator/` = stdlib + pyyaml, no `infrastructure.*`,
  no siblings.  Its only writers take the destination from the caller
  (`situation.write_situation_room`, `manuscript_variables.resolve_manuscript_tree`);
  everything else computes and returns.  `scripts/` owns paths, argv, and probes.
- **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in `tests/`.
- **Determinism**: injectable clocks; `generated_at` is the one wall-clock field
  in generated output, and tests pin `FIXED_NOW` so builds are byte-stable.
- **Show-not-tell**: reference explicit paths/functions.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src scripts tests && uv run ruff format --check src scripts tests
uv run mypy
grep -rE "unittest\.mock|MagicMock|@patch|create_autospec" tests/ || echo Clean
```
