# Scope, Related Work, and Positioning {#sec:scope}

## Scope

{{CONFIG_TITLE}} is **Layer 2 (mission control)** of {{CONFIG_SUITE_NAME}}.
Its scope is exactly the pure core under `src/bond_coordinator/` — `types.py`,
`registry.py`, `reconcile.py`, `ledger.py`, `status.py`, `situation.py`, and
`manuscript_variables.py` — and their thin `scripts/` orchestrators.  It
implements **no film algorithms** and makes **no cross-film computation**: those
belong to the 27 film packages.  It does not orchestrate missions across
packages (that is Layer 3, `bond-orchestrator`) and does not expose a front
door (that is Layer 4, `bond-cli`).

Within that boundary this package is deliberately standalone.  Its `src/` core
is pure — no `infrastructure.*`, no sibling-package imports (the `reconcile`
**script** discovers films through `bond-api`, but the pure merge functions
take plain data) — so the registry, ledger, status, and situation room can run
in any Python 3.10+ environment with `pyyaml` installed, exactly as the
exemplar's mathematical core could.

## Related work

The package inherits the research-exemplar's standards — ≥90% zero-mock
coverage, pure tested cores, thin orchestrators, injected manuscript variables
[@hunt1999pragmatic; @gamma1995designpatterns] — and applies the design-pattern
vocabulary of software architecture [@bass2012softwarearchitecture] and
enterprise registries [@fowler2002patterns] to a multi-package fleet.  The
layered topology (strict downward dependency, per-layer readiness) follows the
layered-architecture guidance in the software-engineering body of knowledge
[@swebok2014], and the central claim — that a machine-checkable registry and
append-only, validated ledger make fleet health an executable fact — follows
the "essence vs. accidents" framing of software complexity
[@brooks1987nosilverbullet].

## Positioning within the fleet

The coordinator declares and reports `{{REGISTRY_LAYER_COUNT}}` topology
layers (`{{REGISTRY_LAYER_CSV}}`) and surfaces per-layer readiness in the
status snapshot and situation room:

| Layer | Package(s) | Coordinator report |
|---|---|---|
| Layer 0 (Q-branch primitives) | `bond-utilities` | readiness tri-state |
| Layer 1 (the protocol) | `bond-api` | readiness (tracks the runtime probe) |
| **Layer 2 (mission control)** | **`bond-coordinator` (this package)** | registry, ledger, status, situation room |
| Layer 3 (the DAG runner) | `bond-orchestrator` | readiness tri-state |
| Layer 4 (front door / fleet ops) | `bond-cli`, `bond-ops` | readiness tri-state |
| Films | 27 film packages | tracked count, READY count, mean coverage |

Because Layers 0–1 are not yet built, this package carries a pure-core mirror
of the protocol shapes (`src/bond_coordinator/types.py`) with a documented
swap point; the swap is mechanical and does not change the public API (see
`TODO.md`).
