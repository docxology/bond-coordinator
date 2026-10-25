# Manuscript Syntax Reference (bond-coordinator)

Project-specific overlay on the canonical `docs/guides/manuscript-semantics.md`
guide, which ships with the template workspace and not with this standalone
repository; local token plumbing is documented in
[`docs/rendering_pipeline.md`](../docs/rendering_pipeline.md).
This file documents the **bond-coordinator**-specific section labels and the
`{{TOKEN}}` table.  The coordinator defines no figures and no equations (it is
an infrastructure/mission-control package), so those registries are absent.

## Citation Syntax (Pandoc)

```markdown
[@brooks1987nosilverbullet]
[@gamma1995designpatterns; @fowler2002patterns, pp. 42-45]
@hunt1999pragmatic showed that...
```

All citation keys must exist in [`references.bib`](references.bib).  Pandoc with
`--natbib` converts `[@key]` to the right LaTeX cite command automatically;
**never** write raw `\cite{}` in Markdown.

## Section Labels

Every H1 carries a `{#sec:<name>}` label so cross-section references survive
reordering:

| File | Section H1 | Label |
|---|---|---|
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `01_introduction.md` | Introduction | `{#sec:introduction}` |
| `02_methodology.md` | Methodology | `{#sec:methodology}` |
| `03_results.md` | Results | `{#sec:results}` |
| `04_conclusion.md` | Conclusion | `{#sec:conclusion}` |
| `05_experimental_setup.md` | Experimental Setup | `{#sec:experimental_setup}` |
| `06_reproducibility.md` | Reproducibility Certification | `{#sec:reproducibility}` |
| `07_scope_and_related_work.md` | Scope, Related Work, and Positioning | `{#sec:scope}` |
| `08_limitations_and_uncertainty.md` | Limitations and Uncertainty | `{#sec:limitations}` |
| `99_references.md` | References | `{#sec:references}` |

## `{{TOKEN}}` Reference

Tokens are injected by
`scripts/z_generate_manuscript_variables.py` →
`src/bond_coordinator/manuscript_variables.py::generate_variables()`.
**Never hand-author a fleet number in prose** — the registry-derived tokens
track the code.

| Token | Meaning |
|---|---|
| `CONFIG_TITLE` | Manuscript title (`paper.title`) |
| `CONFIG_SUBTITLE` | Subtitle (`paper.subtitle`) |
| `CONFIG_VERSION` | Package version (`paper.version`) |
| `CONFIG_CODENAME` | Codename (`mission.codename`) |
| `CONFIG_SUITE_NAME` | Fleet name (PROJECT BOND) |
| `CONFIG_KEYWORDS` | Comma-joined keywords |
| `CONFIG_MISSION_LIFECYCLE` | brief → recon → plan → execute → debrief |
| `REGISTRY_TOTAL` | Number of tracked film packages |
| `REGISTRY_READY` / `REGISTRY_BUILDING` / `REGISTRY_SCAFFOLDED` / `REGISTRY_RED` | Counts by status |
| `REGISTRY_COVERAGE_KNOWN` / `REGISTRY_COVERAGE_UNKNOWN` | Measured / unmeasured count |
| `REGISTRY_COVERAGE_MEAN` | Mean measured coverage (or "N/A") |
| `REGISTRY_COVERAGE_AT_90` | Count at/above the coverage gate |
| `REGISTRY_MEASUREMENT_SOURCE` | Whether the status/coverage tokens above are measured gate output or the registry's unmeasured seed defaults (derived from the roster's own records) |
| `REGISTRY_BLOCKED_COUNT` / `REGISTRY_STALE_COUNT` | Blocked / stale count |
| `REGISTRY_PACKAGES_CSV` | Comma-joined slug list |
| `REGISTRY_LAYER_COUNT` | Number of declared suite-topology layers |
| `REGISTRY_LAYER_CSV` | Comma-joined `layer (label)` list |
| `REGISTRY_INFRA_PACKAGE_COUNT` | Mission-infrastructure packages (every layer except `films`) |
| `REGISTRY_FIRST_SLUG` / `REGISTRY_FIRST_YEAR` | First roster row's slug and release year |
| `REGISTRY_LAST_SLUG` / `REGISTRY_LAST_YEAR` | Last roster row's slug and release year |
| `LEDGER_TRANSITION_TOTAL` | Total audit-trail entries (fresh: one per registered package) |
| `LEDGER_PHASE_COUNT` | Number of lifecycle phases in `MissionPhase` |
| `GATE_COVERAGE_FLOOR` | Enforced coverage floor, read from `status.py::COVERAGE_FLOOR` |
| `GATE_STALE_DAYS` | Default staleness threshold, read from `status.py::DEFAULT_STALE_DAYS` |

The authoritative source of truth is the return value of
`generate_variables()`; `tests/test_manuscript_variables.py` cross-checks the
real `manuscript/config.yaml`, and
`TestManuscriptCrossReference::test_every_prose_token_is_generated` is a live
gate asserting every `{{TOKEN}}` used in a numbered section is actually
produced.

Two token families exist so that prose never restates a number the code owns:
the `REGISTRY_*` / `LEDGER_*` tokens are derived from the registry and ledger,
and the `GATE_*` tokens are read from the constants that *enforce* the
thresholds — change `COVERAGE_FLOOR` and the manuscript follows.

## Section Numbering

Files assemble in lexicographic order: `00_` abstract … `07_` scope, then
`99_` references last.

## Prose Conventions

- No "In summary" / "In conclusion" at section ends.
- Use explicit file paths when referencing code: `src/bond_coordinator/registry.py`,
  not "the registry module".
- Keep paragraphs focused — one idea per paragraph.

## See Also

- [`AGENTS.md`](AGENTS.md) — manuscript editing protocol.
- [`../docs/architecture.md`](../docs/architecture.md) — module boundaries.
- [`../docs/syntax_guide.md`](../docs/syntax_guide.md) — token conventions.
