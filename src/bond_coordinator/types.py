"""Protocol types for the BOND suite (Layer 1 mirror).

bond-coordinator is Layer 2 (mission control) and works with the protocol
shapes ``bond-api`` (Layer 1) defines: :class:`Asset`, :class:`Gadget`, and
:class:`GadgetRegistry`.  This module carries a *pure-core mirror* of those
shapes — same field names, same semantics — so the core keeps its zero-sibling
import rule.

``bond-api`` **is built**; the mirror is a deliberate architectural boundary
rather than a placeholder waiting on it.  Importing ``bond_api`` here would
make the pure core depend on a sibling package, so the real protocol types are
touched only by the thin orchestrator ``scripts/reconcile.py``, which converts
them to plain data before calling into :mod:`bond_coordinator.reconcile`.  See
``docs/architecture.md``, "Consuming the bond-api MissionProvider".

Nothing in this module imports from the rest of the suite; it is stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AssetKind(str, Enum):
    """Kinds of assets a mission can carry, per the BOND protocol."""

    GADGET = "gadget"
    TRANSPORT = "transport"
    COVER = "cover"


@dataclass(frozen=True)
class Asset:
    """A single mission asset (gadget, transport, or cover identity).

    Mirrors ``bond_api.Asset``.  Frozen so registry snapshots can be shared
    without accidental mutation.
    """

    name: str
    kind: AssetKind
    description: str


@dataclass(frozen=True)
class Gadget:
    """A Q-branch gadget: a named piece of equipment attached to a film package.

    Mirrors ``bond_api`` gadget records.  ``film`` is the owning package slug
    (e.g. ``"goldfinger"``); ``assets`` are the optional hardware/cover details
    a mission brief can reference.
    """

    name: str
    film: str
    purpose: str
    assets: tuple[Asset, ...] = field(default_factory=tuple)


class GadgetRegistry:
    """Q-branch lookup table: gadgets registered per film package.

    Deterministic container — no external state.  Registration is idempotency-
    checked: registering the same (film, gadget-name) twice raises
    :class:`ValueError`; looking up an unknown gadget raises :class:`KeyError`.
    """

    def __init__(self, gadgets: list[Gadget] | tuple[Gadget, ...] = ()) -> None:
        self._gadgets: dict[tuple[str, str], Gadget] = {}
        for gadget in gadgets:
            self.register(gadget)

    def register(self, gadget: Gadget) -> Gadget:
        """Register ``gadget`` under its ``(film, name)`` key; returns it."""
        key = (gadget.film, gadget.name)
        if key in self._gadgets:
            raise ValueError(
                f"gadget {gadget.name!r} already registered for film {gadget.film!r}"
            )
        self._gadgets[key] = gadget
        return gadget

    def lookup(self, film: str, name: str) -> Gadget:
        """Return the gadget registered for ``film`` under ``name``."""
        try:
            return self._gadgets[(film, name)]
        except KeyError:
            raise KeyError(f"no gadget {name!r} registered for film {film!r}") from None

    def for_film(self, film: str) -> list[Gadget]:
        """All gadgets registered for ``film``, sorted by name."""
        return sorted(
            (g for (f, _), g in self._gadgets.items() if f == film),
            key=lambda g: g.name,
        )

    def all(self) -> list[Gadget]:
        """All registered gadgets, sorted by (film, name)."""
        return [self._gadgets[key] for key in sorted(self._gadgets)]

    def count(self) -> int:
        """Number of registered gadgets."""
        return len(self._gadgets)


class PackageStatus(str, Enum):
    """Lifecycle status of a film package in the suite registry.

    Mirrors the ROSTER conventions in :mod:`bond_coordinator.registry` / the quality
    guardrails: a package is ``scaffolded``, ``building``, ``ready``, or
    ``red`` (gate failures / blocked).
    """

    SCAFFOLDED = "scaffolded"
    BUILDING = "building"
    READY = "ready"
    RED = "red"


class MissionPhase(str, Enum):
    """Mission lifecycle phases, in strict forward order.

    brief → recon → plan → execute → debrief.  The integer value is the phase
    index used by the ledger's transition rules.
    """

    BRIEF = "brief"
    RECON = "recon"
    PLAN = "plan"
    EXECUTE = "execute"
    DEBRIEF = "debrief"

    @property
    def phase_index(self) -> int:
        """Ordinal position of the phase in the lifecycle (0..4)."""
        return list(MissionPhase).index(self)
