# Manuscript Pipeline — bond-coordinator

The coordinator's manuscript is light by design: it carries the exemplar's
`manuscript/` surface (identity config + numbered sections + `{{TOKEN}}`
injection) but produces **no figures and no equations**.  The pixel-rendering
pipeline that the exemplar demonstrated (Pandoc → XeLaTeX via the template's
`infrastructure/rendering`) is out of scope for this package and will be
supplied by fleet rendering tooling later.

## Token hydration (the part that runs here)

1. `src/bond_coordinator/manuscript_variables.py::generate_variables` reads
   identity from `manuscript/config.yaml` (`paper:`, `mission:`) and derives
   fleet counts from the pure-core registry/ledger.
2. `scripts/z_generate_manuscript_variables.py` writes the resolved map to
   `output/data/manuscript_variables.json` and substitutes `{{TOKEN}}` in every
   `manuscript/*.md` template into `output/manuscript/*.md` via
   `resolve_manuscript_tree`.
3. Unknown `{{...}}` tokens are left in place (grep-able) so incomplete
   hydration is always detectable.

## No analysis-output gate

`generate_variables(..., require_outputs=...)` accepts the flag for pipeline
parity but never gates on generated files — there is no `output/data/*.csv`
dependency.  This is the one intentional divergence from the exemplar's strict
analysis-to-manuscript contract; see `manuscript/05_experimental_setup.md`.

## Unresolved-token check

```bash
rg -l "\{\{" output/manuscript/ || echo "All tokens resolved"
```
