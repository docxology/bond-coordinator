# TODO — bond-coordinator (MISSION CONTROL)

`bond-coordinator` is Layer 2 of PROJECT BOND: the registry and situation room
for the 33-package fleet (27 film packages + 6 mission-infrastructure
packages).  It implements no film algorithms — it records what exists
(`registry.py`), where each package is in its mission (`ledger.py`), whether
the fleet is healthy (`status.py`, `gates.py`), and renders the whole thing as
one self-contained HTML dashboard (`situation.py`).  The `src/` core is pure
(stdlib + `pyyaml`, no sibling imports); `scripts/` holds the thin
orchestrators that bind it to disk and to `bond-api` discovery.

**Verified state, re-measured 2026-11-04 after the `bond-api` vendoring round**
(Python 3.14.9, pytest 9.1.1): **232 tests passing, 1 skipped, 100.00% line +
branch coverage on `src/`** (615 statements, 180 branches, 0 missed) against the
enforced `--cov-fail-under=90` floor.  `ruff check`, `ruff format --check` (32
files), and `mypy` (15 source files) are clean across `src scripts tests`, and
`scripts/vendor.py --check` reports `vendor/bond-api: ok` (0 findings).

Every item below is open as of that measurement.  Completed work is deleted, not
archived: the five findings from the adversarial audit
(`../output/verify/bond-coordinator.json` — the hollow reconcile-CLI gate, the
"bond-utilities is not yet built" claim in four files, the "every package is
scaffolded" claim in three files, reconciled codenames never reaching the
dashboard, and the self-asserting registry test) were all resolved in `a7300c7`
and are gone from this list.  I re-checked each one by grep against the current
tree before deleting it.

## Open work

Six items.  Five carry over from
`../output/verify/bond-coordinator.unresolved.json` (the audit findings the
remediation pass could **not** close); one (`LEDGER-BRANCH-1`) predates them.
(`DOC-XREF-1` — the positional `TODO.md item 1` cross-references — is closed
and deleted: `README.md`, `docs/faq.md`, and `src/bond_coordinator/ledger.py`
now cite `TODO.md#ledger-io-1`.)

### Correctness

#### `GATE-PATH-1` — the fleet gate-manifest location is a convention, not a contract

**Wrong:** all three renderers hard-code the relative path
`../output/aggregate/gate_manifest.json` as the boundary at which the registry
stops being an unmeasured seed and becomes measured fact:

- `scripts/status_report.py:39` (`FLEET_GATE_MANIFEST`)
- `scripts/build_situation_room.py:48`
- `scripts/z_generate_manuscript_variables.py:40`

Nothing binds `bond-ops` to keep writing that path.  On the other side,
`../bond-ops/src/bond_ops/gates.py:424` `write_manifest(report, path)` takes the
destination from *its* caller and exports no constant, so the agreed location
exists only as two matching string literals in two repositories.  If `bond-ops` renames or
relocates its aggregate, every consumer here silently falls back to the
`scaffolded` / `coverage=None` seed.  The fallback is *announced* — stderr
carries `no gate manifest at …` and each renderer's provenance line says
`none applied` (asserted by
`tests/test_scripts_smoke.py:108` `test_absent_gate_manifest_is_reported_not_silent`)
— so this is a degradation, not a silent lie.  But it degrades to a
never-failing state: a fleet where nothing is measured looks exactly like a
fleet whose sibling moved a file.  No test can catch the difference, and
writing one that reads `bond-ops` internals is forbidden by this package's
layer doctrine (see *Known limitations*).

**Done looks like:** `bond-ops` exposes the aggregate through an importable
probe or a published path constant, and `scripts/*` consume that instead of a
literal relative path; renaming the artifact then breaks a `bond-ops` test
rather than quietly emptying this package's measurements.

**Demonstrate:**

```bash
# from bond-ops: the location is exported, not implied
uv run python -c "from bond_ops.gates import AGGREGATE_MANIFEST_PATH; print(AGGREGATE_MANIFEST_PATH)"
# from here: no literal aggregate path left in the orchestrators
! grep -rn 'output" / "aggregate"' scripts/
```

### Verification

#### `SCRIPTS-COV-1` — `scripts/` is outside the measured coverage scope

**Missing:** `pyproject.toml:47-56` sets `source = ["src"]`, so the 100.00%
figure describes the pure core only.  The five orchestrators —
`scripts/status_report.py`, `scripts/build_situation_room.py`,
`scripts/reconcile.py`, `scripts/advance_mission.py`,
`scripts/z_generate_manuscript_variables.py` — are exercised only by the 15
subprocess smoke tests in `tests/test_scripts_smoke.py`, which assert exit
codes and output substrings.  Their branch coverage is unknown and unenforced.
That includes the gate-application and provenance-source wiring
(`build_situation_room.py:69-102`), which is precisely the code that decides
whether a dashboard row is measured.

This is pre-existing scope, not a regression from the audit pass — but it means
"100% coverage" and "this package is fully covered" are different statements,
and only the first is true.

**Done looks like:** either `source = ["src", "scripts"]` with a stated floor
the orchestrators actually meet, or an explicit written decision in
`docs/testing_philosophy.md` that the scripts layer is smoke-tested by design
with the coverage figure scoped accordingly in `README.md`/`AGENTS.md`.  Either
resolution is acceptable; the current state — unmeasured and unstated — is not.

**Demonstrate:**

```bash
uv run pytest tests/ --cov=src --cov=scripts --cov-report=term-missing
```

#### `PROVENANCE-TEST-1` — the provenance-defaults guard is a wording check

**Weak:** `tests/test_scripts_smoke.py:157`
(`test_unreconciled_unmeasured_build_says_so`) closes the "a seed run must not
look reconciled or measured" claim by asserting two substrings —
`"registry seed — provisional codenames"` and `"status/coverage unmeasured"` —
against the constants at `src/bond_coordinator/situation.py:29-34`
(`DEFAULT_CODENAME_SOURCE`, `DEFAULT_MEASUREMENT_SOURCE`).  It fails on a benign
rewording of a string literal, and it passes on any regression that still emits
those words.  The behavioural siblings around it
(`test_reconciled_codenames_reach_the_dashboard:174`,
`test_measured_coverage_reaches_the_dashboard:208`) are strictly stronger:
they assert film-declared codenames and measured coverage values reach the
rendered HTML.

**Done looks like:** the negative case is bound the same behavioural way as the
positive ones — a seed-run dashboard is asserted to contain **zero** occurrences
of any film-declared codename and **zero** numeric coverage cells, rather than
being asserted to contain a particular sentence.

**Demonstrate:**

```bash
# The test must fail when the guarantee breaks, not when the wording changes.
uv run pytest tests/test_scripts_smoke.py::TestBuildSituationRoom -v
# Negative control: reword the two constants in situation.py (keeping behaviour
# identical) — the reworked test must still pass; today's test does not.
```

#### `LEDGER-BRANCH-1` — the `_transition` defensive branch is unreachable and unbound

**Weak:** `src/bond_coordinator/ledger.py:293` carries
`else:  # pragma: no cover — defensive; jump is only 0/-1 from the public API`.
The invariant it names is real but is enforced only by reading the three call
sites — `advance` passes `0` (`ledger.py:252`), `jump` passes a target
(`ledger.py:263`), `touch` passes `-1` (`ledger.py:271`).  Nothing fails if a
fourth caller is added with an out-of-range `jump`.  The pragma is honest
(marked, not hidden) — but an excluded line is an unverified line.

**Done looks like:** the three callers pass a small typed intent (enum or
literal union) so the invalid case is a type error and the branch disappears,
*or* the branch is kept and reached by a test that constructs the invalid
intent directly, removing the pragma.

**Demonstrate:**

```bash
# Either the pragma is gone…
! grep -n "pragma: no cover" src/bond_coordinator/ledger.py
# …and coverage stays at 100% with no excluded lines:
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100
```

### Extension

#### `LEDGER-IO-1` — route ledger provenance through `bond-utilities` `mission_io`

**Missing:** `MissionLedger.to_json` / `from_json` and the persistence in
`scripts/advance_mission.py:32,72` are local stdlib equivalents of the Layer-0
provenance convention.  `bond-utilities` **is built** and ships the convention
at `../bond-utilities/src/bond_utilities/mission_io.py`:
`record_provenance_outcome` (line 153), `save_record` (92) / `load_record`
(126), `validate_record` (61), `verify_provenance` (212), `hash_payload` (45).
This package has simply not adopted it, so a coordinator ledger file carries no
payload hash and cannot be verified by the fleet's own verifier.

The pure-core JSON codecs stay regardless — the layer contract forbids `src/`
importing a sibling.  Only `scripts/advance_mission.py` changes.

**Done looks like:** `scripts/advance_mission.py` writes the ledger through
`mission_io.save_record` with a provenance record, and a persisted ledger file
satisfies `mission_io.verify_provenance`.

**Demonstrate:**

```bash
uv run python scripts/advance_mission.py --slug goldfinger --phase recon \
    --by agent-007 --version 0.1.0 --note "adoption check"
uv run python -c "
import json, sys; sys.path.insert(0, '../bond-utilities/src')
from bond_utilities.mission_io import verify_provenance
assert verify_provenance(json.load(open('output/data/mission_ledger.json')))
print('provenance verified')"
```

#### `LAYER-PROBE-1` — per-layer infra readiness is never actually probed

**Missing:** `build_status(..., layer_ready=...)`
(`src/bond_coordinator/status.py:198-208`) accepts injected readiness, and
`_layer_summaries` (`status.py:145-177`) infers `layer1` from the `bond_api`
importability probe.  No shipped caller supplies the rest, so `layer0`,
`layer2`, `layer3`, and `layer4` render as `None` — the "not probed" tri-state —
in every status report and every dashboard, including for `bond-utilities`
(Layer 0) and this package itself (Layer 2), both of which are built and gated.

The display is honest today (it says *not probed*, not *not ready*), so this is
an extension rather than a defect.  The probe itself belongs in `bond-ops`,
which runs the per-package gates; the coordinator should consume its output
rather than re-implement gate running.  This item therefore unblocks only after
`GATE-PATH-1` gives it a contract to consume.

**Done looks like:** `scripts/status_report.py` and
`scripts/build_situation_room.py` pass a `layer_ready` mapping derived from the
fleet gate output, and a default run reports a boolean per infra layer.

**Demonstrate:**

```bash
uv run python scripts/status_report.py --json \
  | python3 -c "import json,sys; L={l['layer']: l['ready'] for l in json.load(sys.stdin)['layers']}; print(L); assert None not in L.values()"
```

## Known limitations (not bugs)

- **No `mission.py`, no `MissionProvider`.**  This is Layer 2 — the *consumer*
  of film providers, not one of them.  A synthetic provider here would inject a
  non-film into the fleet's discovery surface and make the registry a member of
  the roster it governs.  See `docs/architecture.md`, "Consuming the bond-api
  MissionProvider".
- **`src/bond_coordinator/types.py` mirrors `bond-api` shapes** even though
  `bond-api` is built.  That is the layer contract — the pure core imports no
  sibling — not an unfinished migration.
- **The shipped `ROSTER` literal stays `scaffolded` / `coverage=None`.**  A
  literal is not a measurement.  `gates.py` is the only path by which a row
  becomes `ready`/`building`/`red` with a real number, and every renderer states
  which of the two it is showing.  This was forced by the audit: the earlier
  claim that the fleet *was* at phase-0 scaffold was false (all 27 film packages
  are gated at 96.58–100.00% in `../output/aggregate/gate_manifest.json`), and
  the honest scope is now "the literal is an unmeasured seed", not "the fleet is
  unbuilt".
- **Live-fleet tests assert this package's contract, never a sibling's
  internals.**  Sibling packages are developed concurrently and may be mid-edit;
  a test pinning another package's codename, gadget name, or file layout turns
  this suite red for someone else's work in progress.  This is the reason
  `GATE-PATH-1` cannot be closed by a test written here — it needs a contract
  published from the other side.
- **`scripts/` are thin orchestrators verified by subprocess smoke tests.**
  Accepted today; `SCRIPTS-COV-1` exists to make that either measured or
  explicitly stated, not to relitigate the pattern.
- **Standalone repository, independent gates.**  The coordinator has its own
  `origin` (`docxology/bond-coordinator`, default branch `main`) and its own
  `uv.lock`; it is not a member of a shared `uv` workspace, so every gate below
  runs from this directory and resolves `bond-api` from the vendored copy
  (`vendor/bond-api`).
- **Three reconcile CLI tests assume the checkout keeps its own name under the
  fleet root.**  `tests/test_reconcile.py` resolves the CLI as
  `<parent>/bond-coordinator/scripts/reconcile.py` (`BOND = parents[2]`), so a
  checkout renamed in place fails those three with `FileNotFoundError` while
  lock, sync and the rest of the suite pass.  Measured 2026-11-04: identical at
  the pre-vendoring head `239a415` (sibling `bond-api` present) and at the
  vendored head in a parent holding no siblings, so this is a test-harness
  convention, not a dependency on a sibling.  Fix shape: resolve the CLI from
  `Path(__file__).resolve().parents[1]`, which is the same path in the fleet.

## Verification

The gates that govern this package.  Run all four from **inside** this
directory (it is not a member of the template `uv` workspace).

```bash
uv sync --extra dev

# 1. Suite + coverage gate — expect: 233 tests (232 passed; the real-films CLI
#    test skips when no slug-named fleet sibling is checked out), 100.00%,
#    "Required test coverage of 90% reached."
uv run pytest tests/ --cov=src --cov-fail-under=90

# 2. Lint — expect: "All checks passed!"
uv run ruff check src scripts tests

# 3. Format — expect: "32 files already formatted"
uv run ruff format --check src scripts tests

# 4. Types — expect: "Success: no issues found in 15 source files"
uv run mypy
```

Zero mocks, zero skips, deterministic (fixed UTC clock in `tests/conftest.py`;
the situation room is asserted byte-identical across repeated builds).

Persistent guardrails, unchanged: pure `src/` core (stdlib + `pyyaml`, no
`infrastructure.*`, no sibling imports, no filesystem side-effects);
interpretation lives in `src/` not `scripts/` (see `reconcile.gadget_purpose`);
cross-package reads guarded per film with `except Exception` and reported on
stderr, never silent; ≥90% line + branch on `src/`.

## Round-2 (2026-08-06) — hostile review + manuscript deepening

Steady state on entry: **221 tests passing, 0 skipped, 100.00% branch+line on
`src/`** (604 stmts / 172 branches / 0 missed) at `--cov-fail-under=90`, ruff
check + format + mypy clean (`TODO.md` states 221).

### Findings & fixes (each with a regression/negative-control test)

1. **`GATE-DATAVALID-1` — `parse_gate_manifest` accepted `NaN` / `inf` and
   out-of-range coverage, and negative gate counts (data-validation gap).**
   Python's `json.loads` parses the bare literals `NaN`/`Infinity` by default,
   and `_coerce_coverage` only checked `isinstance(value, (int, float))` — so a
   manifest row with `coverage: NaN` round-tripped into a `GateResult` whose
   coverage was `nan`, then propagated into `CoverageSummary.mean`,
   `formatted_mean()` (→ `"nan%"`), and the situation-room heat + manuscript
   token.  Coverage outside `[0, 100]` (negative, or >100) and negative
   `passed`/`failed`/`rc` counts were likewise silently accepted.  A
   malformed measurement became the fleet's reported mean.
   **Fix:** `GateResult.__post_init__` now rejects, with a single `ValueError`
   contract, any coverage that is not finite in `[0, 100]`, any negative
   count, and a blank `package` (raised on construction — so it applies to
   *programmatic* `GateResult(...)` and to manifest rows alike).
   **Evidence:** added to
   `tests/test_gates.py::TestParseGateManifest::test_malformed_manifest_raises`
   the payloads `coverage=float("nan")`, `float("inf")`, `-float("inf")`,
   `-1.0`, `101.5`, `1000.0`, and `passed=-1`/`failed=-5`/`rc=-3`, each
   asserting `ValueError`; plus
   `test_gate_result_rejects_empty_package_on_construction`.  Before the fix
   the `nan` row parsed successfully (verified by running `parse_gate_manifest`
   against `json.loads` of a `NaN` literal — it returned a `nan` coverage).

2. **`LEDGER-BRANCH-1` — reached the previously `# pragma: no cover`
   defensive branch, removed the pragma (the branch was real, unverified
   code).**  The TODO listed this as an unreachable, excluded line whose
   invariant ("jump is only -1/0") was enforced only by reading three call
   sites.  Rather than weakening it, the branch is now *covered*: a test drives
   `_transition(..., jump=7)` and asserts the `ValueError`.
   **Fix:** comment `# pragma: no cover` removed from `ledger.py:293`.
   **Evidence:** `tests/test_ledger.py::...::test_transition_with_invalid_jump_intent_raises`
   (raises `ValueError`, match `"invalid jump"`).  `grep -n "pragma: no cover"`
   over `src/` now returns nothing; coverage holds at 100% with the branch hit.

3. **`SCRIPTS-MSG-1` — `scripts/advance_mission.py` claimed every transition
   starts at `brief`.**  The success line hard-coded `"{slug}: brief → {phase}"`,
   which was wrong for any multi-step `jump` (e.g. `plan → debrief` would print
   `brief → debrief`), misrepresenting the audit message.
   **Fix:** report the true source phase: capture `prior = ledger.get(slug).phase`
   before the jump and print `"{slug}: {prior.value} → {entry.phase.value}"`.
   **Evidence:** existing smoke test still asserts `recon` appears and the
   transition persists; the fixed line reads the real prior phase.

### Finding that proved a non-issue (recorded)

I tested whether `json.loads` could smuggle `nan`/`inf` coverage past
`parse_gate_manifest` — **it could, hence fix 1**.  I also re-checked that
`gadget_purpose` still never borrows a builtin docstring for any plain-data
shape (unchanged, covered by
`TestGadgetPurpose::test_plain_data_never_returns_a_builtin_docstring`).

### Gate numbers (Round-2 close, on disk)

- **232 tests passing, 0 skipped, 100.00%** line + branch on `src/`
  (615 stmts / 180 branches / 0 missed) at `--cov-fail-under=90`.
- `ruff check` clean, `ruff format --check` clean ("30 files already
  formatted" — now includes the new regression lines).
- `mypy` clean (`Success: no issues found in 14 source files`).
- Manuscript hydration: `z_generate_manuscript_variables.py --no-gate-manifest`
  resolves all 31 tokens into 13 numbered files; the guide files
  (`AGENTS/README/SYNTAX.md`) retain literal `{{...}}` by design and are ruled
  out of the cross-reference scan.

### Manuscript deepening (Round-2)

- **New `manuscript/08_limitations_and_uncertainty.md`** — honest section
  covering: the seeded registry is not a measurement; measured values are only
  as good as the manifest (convention-path provenance, bounded-percentage
  coverage, absence = absence of evidence); ledger truth is bounded by its
  inputs (same-phase re-entries, staleness heuristic); gadget purposes are
  derived shapes not film confessions; reconciliation is partial by design; the
  situation room reflects its inputs exactly; and an uncertainty statement
  (qualitative provenance/model uncertainties, not spurious precision).
- **`03_results.md`** gained a live-generated "Summary table" — every figure a
  `{{TOKEN}}`, none hand-authored — plus a pointer to §[sec:limitations].
- **`references.bib`** +2 scholarly entries (**sandve2013tensimplerules**,
  **peng2011reproducibleresearch**), both real/DOI-verifiable, cited from
  `06_reproducibility.md` and the new limitations section.  All cited keys
  resolve.
- **`SYNTAX.md`**, **`01_introduction.md`**, **`manuscript/AGENTS.md`**,
  **`manuscript/README.md`**, top-level **`AGENTS.md`** updated for the new
  `{#sec:limitations}` section label and section range (00–08 + 99).
- Fixed the two `TODO.md item 1` positional cross-references (`README.md`,
  `docs/faq.md`) → `TODO.md#ledger-io-1` (closes the positional part of
  `DOC-XREF-1` for shipped files; the manuscript `(see TODO.md)` pointers are
  non-positional and correct as-is).

### Still open for a future round (unchanged / not regressed)

- `SCRIPTS-COV-1` (scripts/ outside measured coverage scope) — still a
  pre-existing scope decision; doc either `source = ["src","scripts"]` with a
  stated floor or an explicit "scripts are smoke-tested by design" note in
  `docs/testing_philosophy.md`.  Not regressed this round; scripts changes were
  covered by subprocess smoke tests.
- `LEDGER-IO-1` — route ledger persistence through `bond-utilities` `mission_io`
  (needs the Layer-0 adoption; `src/` codecs stay, `scripts/advance_mission.py`
  is the touch point).  Unchanged.
- `LAYER-PROBE-1` — block on `GATE-PATH-1` (a contract to consume).
- `GATE-PATH-1`, `PROVENANCE-TEST-1`, `DOC-XREF-1` (manuscript side) — see above.
- No `mission.py` / `MissionProvider` — by design (Layer 2 consumer, not
  implementer); `src/bond_coordinator/types.py` stays a pure-core mirror.
