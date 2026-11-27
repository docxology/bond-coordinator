# Reproducibility Certification {#sec:reproducibility}

Reproducibility is a first-order requirement for mission control, because the
suite's provenance story depends on it.  The certification below follows the
reproducibility-in-computational-research guidance of
[@sandve2013tensimplerules; @peng2011reproducibleresearch].

## Determinism

- **Injectable clocks**: every time-dependent path (`MissionLedger`, `build_status`,
  `is_stale`) accepts an injectable `now`; tests pin a fixed UTC reference clock and
  assert exact timestamps and byte-identical outputs.
- **No wall-clock tokens**: `manuscript_variables.py` emits no
  `GENERATION_TIMESTAMP`-style token, so manuscript bytes depend only on the
  config file and registry/ledger state.  A test asserts the situation room is
  byte-identical across repeated builds with identical inputs.
- **Deterministic audit views**: `transition_summary`, `per_agent_summary`,
  and `phase_timeline` are pure functions of the append-only history — their
  output is stable for a given ledger, and the situation room's
  recent-transitions table sorts with a deterministic tie-break
  (`(timestamp, slug)`).
- **Fixed seeds**: no random draws anywhere in `src/` or `tests/`.

## Provenance

- The ledger is **append-only** and validated: every transition must carry a
  non-empty agent and version (a `@require`-style identity check), and a
  non-mutating `validate_transition` gates moves before they commit.  Every
  recorded transition lands in the audit trail, and `to_json()`/`from_json()`
  round-trip state and history losslessly.  A thin CLI
  (`scripts/advance_mission.py`) persists the ledger to
  `output/data/mission_ledger.json` after each move.
- The audit trail is *countable, not just capturable*: at a fresh state it
  holds exactly {{LEDGER_TRANSITION_TOTAL}} entries (one per registered
  package), and every later move is visible in `transition_summary` and
  `per_agent_summary`.
- Generated artifacts — `output/situation_room.html`,
  `output/data/suite_status.json`, `output/data/manuscript_variables.json`, and
  the resolved manuscript tree — are gitignored and understood to be disposable:
  they are always regenerated from source, never hand-edited.

## Verification

The standalone publication replay hydrates from the checked-in registry and
uses the pinned Template renderer. The focused local checks cover the
configuration, manuscript tokens, registry, ledger, and status aggregation.
The seed replay includes no aggregate gate measurements or sibling-package
imports. It cannot certify the readiness or coverage of the larger suite.
See the rendering guide for exact commands and artifact locations.
