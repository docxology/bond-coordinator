# Standalone manuscript replay

The ordered source, identity, and bibliography live in [docs/manuscript](manuscript/).
The standalone replay reports the checked-in registry and initializes a fresh
ledger. The scaffolded labels are defaults and all sibling-package coverage
is unknown. It uses no gate manifest, provider discovery, or sibling imports.

Install Python 3.14, uv, Pandoc 3.14, compatible pandoc-crossref v0.3.26b, and
XeLaTeX with the [Template prerequisites](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2#prerequisites).
Set `COORDINATOR_CHECKOUT` to the absolute path of a committed checkout.

```sh
git clone https://github.com/docxology/template.git coordinator-template-runner
cd coordinator-template-runner
git checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
uv sync --locked --python 3.14
project=projects/working/bond-coordinator
mkdir -p projects/working
git -C "$COORDINATOR_CHECKOUT" worktree add --detach "$PWD/$project" HEAD
uv run python "$project/scripts/z_generate_manuscript_variables.py" --no-gate-manifest
uv run python scripts/pipeline/stage_03_render.py --project working/bond-coordinator --skip-manuscript-hydration
uv run python scripts/pipeline/stage_04_validate.py --project working/bond-coordinator
```

Manual hydration fixes the data source to the seed. It writes the resolved
variable mapping to `output/data/manuscript_variables.json` and the rendered
Markdown inputs to `output/manuscript/`. Template writes the PDF, HTML, and
validation reports under `output/pdf/`, `output/web/`, and `output/reports/`.

For the local seed-related code checks, run from the coordinator checkout
with its test dependencies installed.

```sh
uv run pytest tests/test_manuscript_variables.py tests/test_registry.py tests/test_status.py tests/test_ledger.py
```
