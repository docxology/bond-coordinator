"""Reconcile the coordinator's registry against REAL film packages (pure core).

This is the merge half of the declared bond-api integration point
(``registry.py`` codename policy): when a film package is built and declares
its own codename via its ``MissionBrief``, mission control's provisional
codename is overridden at merge time.  Gadgets registered by a film's
``GadgetRegistry`` are harvested into the coordinator's Q-branch table for
the situation room.

The module is deliberately pure: it takes plain data (a roster and plain
dicts of brief/gadget information) and returns updated data.  It imports
nothing from ``bond-api`` or the filesystem — the thin orchestrator in
``scripts/reconcile.py`` performs discovery and I/O, then calls these
functions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .registry import PackageRecord
from .types import Gadget, GadgetRegistry

__all__ = ["harvest_gadgets", "override_codenames", "reconcile_report"]


def override_codenames(
    roster: tuple[PackageRecord, ...],
    briefs: Mapping[str, Mapping[str, str]],
) -> tuple[PackageRecord, ...]:
    """Return ``roster`` with provisional codenames replaced by real ones.

    Args:
        roster: The coordinator's canon-ordered registry.
        briefs: slug → {"codename": str, "objectives": str} as discovered from
            each film's ``MissionBrief``.  Only non-empty codenames override;
            slugs absent from ``briefs`` (or with an empty codename) keep
            their provisional codename.

    Returns:
        A new tuple of records (frozen dataclasses are replaced, never
        mutated); record order and every other field are preserved.
    """
    updated: list[PackageRecord] = []
    for record in roster:
        brief = briefs.get(record.slug)
        codename = (brief or {}).get("codename", "")
        if brief is not None and codename and codename != record.codename:
            updated.append(replace(record, codename=codename))
        else:
            updated.append(record)
    return tuple(updated)


def harvest_gadgets(
    registry: GadgetRegistry,
    film_gadgets: Mapping[str, Mapping[str, str]],
) -> GadgetRegistry:
    """Merge films' gadget name → purpose maps into a coordinator registry.

    Args:
        registry: The target Q-branch table (usually the coordinator's shared
            instance; merging is deterministic and idempotent).
        film_gadgets: slug → {gadget_name: purpose}.  Purpose may be an empty
            string when the film registered an opaque payload with no
            description; the gadget is still recorded (presence matters).

    Returns:
        A new ``registry`` instance with the merge applied.  Reconcile uses
        refresh semantics: re-registering an existing ``(film, name)`` in a
        later call replaces its purpose (a film's latest build wins), so the
        merge is deterministic and idempotent.
    """
    merged: dict[tuple[str, str], Gadget] = {
        (gadget.film, gadget.name): gadget for gadget in registry.all()
    }
    for slug, gadgets in film_gadgets.items():
        for name, purpose in gadgets.items():
            merged[(slug, name)] = Gadget(name=name, film=slug, purpose=purpose)
    return GadgetRegistry(tuple(merged.values()))


def reconcile_report(
    roster: tuple[PackageRecord, ...],
    briefs: Mapping[str, Mapping[str, str]],
) -> str:
    """Render a plain-text reconciliation report for the thin CLI.

    Shows, per film: provisional codename → real codename (when overridden),
    and the number of gadgets harvested.
    """
    lines = ["PROJECT BOND — registry reconciliation", ""]
    overridden = 0
    for record in roster:
        brief = briefs.get(record.slug)
        codename = (brief or {}).get("codename", "")
        if codename and codename != record.codename:
            lines.append(
                f"* {record.slug}: {record.codename} -> {codename} (film-declared)"
            )
            overridden += 1
        else:
            lines.append(f"* {record.slug}: {record.codename}")
    lines.append("")
    lines.append(f"codenames overridden by film declarations: {overridden}")
    return "\n".join(lines)
