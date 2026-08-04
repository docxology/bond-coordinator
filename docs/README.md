# docs/ — Agent-Facing Documentation Hub

Operational rulebook for AI agents and developers inside `bond-coordinator`.

## Read-first protocol

Agents must read [`agent_instructions.md`](agent_instructions.md) before
modifying any project file.  It is the gate for the other documents.

## Document map

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | This index. |
| [`agent_instructions.md`](agent_instructions.md) | **Read first.** 7 hard rules + verification checklist. |
| [`architecture.md`](architecture.md) | Layer boundaries (pure `src/`, thin `scripts/`), integration point. |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, determinism, 5-film fixture, test inventory. |
| [`style_guide.md`](style_guide.md) | 7 source-style rules + formatting (ruff). |
| [`syntax_guide.md`](syntax_guide.md) | `{{TOKEN}}` conventions; authoritative list = `generate_variables()` + cross-ref test. |
| [`output_conventions.md`](output_conventions.md) | `output/` layout + regeneration rules. |
| [`output_inventory.md`](output_inventory.md) | Producer/consumer graph for generated artifacts. |
| [`quickstart.md`](quickstart.md) | 5-minute first run. |
| [`troubleshooting.md`](troubleshooting.md) | Symptom-driven recipes. |
| [`faq.md`](faq.md) | Common questions (no figures, all-scaffolded, codenames, deps). |
| [`forking_guide.md`](forking_guide.md) | Own-git / local-only / boundary contract. |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript token hydration (no pixel pipeline here). |

## Key conventions

- **Pure core**: `src/bond_coordinator/` = stdlib + pyyaml, no `infrastructure.*`,
  no siblings, no file I/O.  `scripts/` is the only filesystem/probe layer.
- **Zero mocks**: no `unittest.mock` / `MagicMock` / `@patch` anywhere in `tests/`.
- **Determinism**: injectable clocks; no wall-clock tokens; byte-stable outputs.
- **Show-not-tell**: reference explicit paths/functions.

## Verification commands

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src scripts tests && uv run ruff format --check src scripts tests
uv run mypy
grep -rE "unittest\.mock|MagicMock|@patch|create_autospec" tests/ || echo Clean
```
