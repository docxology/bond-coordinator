# manuscript/

Publication-shaped manuscript for `bond-coordinator`.

- `config.yaml` — identity (`BOND-COORDINATOR`, codename `MISSION CONTROL`),
  authors, keywords. Loaded by `src/bond_coordinator/manuscript_variables.py`.
- `00_abstract.md` … `07_scope_and_related_work.md` — numbered sections with
  `{{TOKEN}}` injection (fleet counts are never hand-authored).
- `99_references.md` + `references.bib` — bibliography (rendered by the
  pipeline via `--natbib`).
- `SYNTAX.md` — section labels, citation syntax, `{{TOKEN}}` table.
- `preamble.md` — LaTeX preamble.
- `layer_contract.yaml` — pure-core boundary declaration.
- `config.yaml.example` — copy-and-customize reference.

The coordinator produces **no figures and no equations**; it is an
infrastructure/mission-control package.  Hydrate tokens with
`uv run python scripts/z_generate_manuscript_variables.py` (writes
`output/manuscript/*.md`).  See `docs/rendering_pipeline.md` for the flow.
