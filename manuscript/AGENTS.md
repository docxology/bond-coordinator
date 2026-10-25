---
title: "Manuscript directory: bond-coordinator"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`manuscript/`)

Read-first behavioral rules live in [`../docs/agent_instructions.md`](../docs/agent_instructions.md).
This file covers manuscript-specific editing for the coordinator.

## File Inventory

| File / Pattern | Role |
|---|---|
| `config.yaml` | Identity (`paper:`, `mission.codename`, `keywords`) + author metadata. Loaded by `../src/bond_coordinator/manuscript_variables.py`. |
| `config.yaml.example` | Copy-and-customize reference. |
| `00_abstract.md` … `08_limitations_and_uncertainty.md` | Numbered sections, `{{TOKEN}}` injection. |
| `99_references.md` | References section (rendered from `references.bib`). |
| `references.bib` | Bibliography (8 scholarly entries). |
| `SYNTAX.md` | Section labels + `{{TOKEN}}` table + citation syntax. |
| `preamble.md` | LaTeX preamble injected at render time. |
| `layer_contract.yaml` | Declares the pure-core boundary (`allow_infrastructure_imports: []`). |

## `{{TOKEN}}` Protocol

Fleet counts are **never hand-authored in prose**.  They are injected by
`scripts/z_generate_manuscript_variables.py` →
`src/bond_coordinator/manuscript_variables.py::generate_variables()`.

- Identity tokens come from `config.yaml` (`CONFIG_TITLE`, `CONFIG_SUBTITLE`,
  `CONFIG_VERSION`, `CONFIG_CODENAME`, `CONFIG_KEYWORDS`).
- Fleet tokens derive from the registry/status core (`REGISTRY_*`).
- The authoritative token list is the return value of `generate_variables()`;
  `tests/test_manuscript_variables.py` is the cross-reference gate.
- Unknown `{{...}}` tokens remain grep-able:
  `rg -l "\{\{" output/manuscript/ || echo "All tokens resolved"`.

## Figures / equations

The coordinator defines **no figures and no equations**.  Do not add figure or
equation registries to `SYNTAX.md`.

## Section/Identity edit protocol

1. Change identity → edit `config.yaml`; do not touch prose numbers.
2. Change a fleet token → edit `src/bond_coordinator/` + the test cross-ref.
3. Re-run `scripts/z_generate_manuscript_variables.py`, verify no unresolved
   `{{...}}` remain.
4. Update `SYNTAX.md` token table if the set changed.
