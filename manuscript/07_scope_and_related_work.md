# Scope, Related Work, and Positioning {#sec:scope}

## Scope

{{CONFIG_TITLE}} is **Layer 2 (mission control)** of {{CONFIG_SUITE_NAME}}.
Its scope is exactly the four modules under `src/bond_coordinator/` and their
thin `scripts/` orchestrators.  It implements **no film algorithms** and makes
**no cross-film computation**: those belong to the 27 film packages.  It does
not orchestrate missions across packages (that is Layer 3, `bond-orchestrator`)
and does not expose a front door (that is Layer 4, `bond-cli`).

Within that boundary this package is deliberately standalone.  Its `src/` core
is pure — no `infrastructure.*`, no sibling-package imports — so the registry,
ledger, status, and situation room can run in any Python 3.10+ environment with
`pyyaml` installed, exactly as the exemplar's mathematical core could.

## Related work

The package inherits the research-exemplar's standards — ≥90% zero-mock
coverage, pure tested cores, thin orchestrators, injected manuscript variables
[@hunt1999pragmatic; @gamma1995designpatterns] — and applies the design-pattern
vocabulary of software architecture [@bass2012softwarearchitecture] and
enterprise registries [@fowler2002patterns] to a multi-package fleet.  The
central claim — that a machine-checkable registry and append-only ledger make
fleet health an executable fact — follows the "essence vs. accidents" framing
of software complexity [@brooks1987nosilverbullet].

## Positioning within the fleet

| Concern | Package |
|---|---|
| Q-branch primitives (ciphers, clocks, seeds) | `bond-utilities` (Layer 0) |
| Protocol types (`MissionBrief`, `Asset`, `GadgetRegistry`) | `bond-api` (Layer 1) |
| **Registry, ledger, status, situation room** | **`bond-coordinator` (this package, Layer 2)** |
| Multi-package mission DAG | `bond-orchestrator` (Layer 3) |
| CLI front door / fleet ops | `bond-cli` / `bond-ops` (Layer 4) |

Because Layers 0–1 are not yet built, this package carries a pure-core mirror
of the protocol shapes (`src/bond_coordinator/types.py`) with a documented
swap point; the swap is mechanical and does not change the public API (see
`TODO.md`).
