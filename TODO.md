# bond-coordinator TODO

Forward-only backlog for **bond-coordinator** — mission control (Layer 2) of
the BOND suite.  Local-only working tree; no remote.

## Status

Phase 5 (documentation truth + defect sweep) is green.  The gates are the
source of truth for any number, so this file names the gate rather than
quoting a figure that would go stale:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90   # line + branch on src/
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/
```

Zero mocks, zero skips, deterministic.  Reconcile semantics (refresh/replace)
and every public API are unchanged — `bond-cli`, `bond-orchestrator`, and the
film fleet consume them.

## Open work

1. **Route ledger provenance through `bond-utilities` `mission_io`.**
   `MissionLedger.to_json`/`from_json` and `scripts/advance_mission.py`
   persistence are local stdlib equivalents of the Layer-0 conventions.
   `bond-utilities` is not yet built; adopt it when it lands.  The pure-core
   JSON codecs stay regardless — only the *script* changes.
2. **Feed per-layer infra readiness from a real fleet probe.**
   `build_status(layer_ready=...)` accepts injected readiness and `layer1`
   is inferred from the `bond_api` importability probe, but `layer0`,
   `layer2`, `layer3`, and `layer4` report `None` ("not probed") unless a
   caller supplies them.  A real probe belongs in `bond-ops`, which runs the
   per-package gates; the coordinator should consume its output rather than
   re-implement gate running.
3. **Populate measured `status` / `coverage` on `PackageRecord`.**
   Every roster row is still `scaffolded` with `coverage=None`, which is the
   honest state: these fields are only ever written from measured gate output.
   Wire them to the `bond-ops` aggregate run rather than hand-asserting them.
4. **Reconsider the `_transition` defensive branch.**
   `ledger.py::MissionLedger._transition` carries a `# pragma: no cover`
   guard for an invalid `jump` value that no public method can produce
   (`advance` passes 0, `touch` passes -1, `jump` passes a target).  It is
   honestly marked rather than hidden, but it is unreachable code; either
   restructure the three callers to a small enum-typed intent so the branch
   disappears, or leave it and keep the pragma justified.

## Known constraints (not bugs)

- **No `mission.py`, no `MissionProvider`.** This is Layer 2 — the consumer of
  film providers, not one of them. Adding a synthetic provider would put a
  non-film into the fleet's discovery surface. See `docs/architecture.md`,
  "Consuming the bond-api MissionProvider".
- **`src/bond_coordinator/types.py` mirrors `bond-api` shapes** even though
  `bond-api` is built. That is the layer contract (the pure core imports no
  sibling), not an unfinished migration.
- **Live-fleet tests assert this package's contract, never a sibling's
  internals.** Sibling packages are developed concurrently and may be mid-edit;
  a test that pins another package's codename or gadget name makes this
  suite red for someone else's work in progress.

## Guardrails (persistent)

- Zero-mock testing; real data + computation only.
- ≥90% line+branch coverage on `src/` (`--cov-fail-under=90`).
- Deterministic: fixed seeds/clocks; no untracked random reliance.
- Thin orchestrators in `scripts/`; business logic in `src/` — including
  *interpretation* (see `reconcile.gadget_purpose`).
- Cross-package reads guarded per film with `except Exception`, reported on
  stderr, never silent.
- `ruff` + `mypy` clean on `src/bond_coordinator` and `scripts/`.
- Local-only: never push to any remote (there is none).  Commit path-scoped
  inside this package only.
