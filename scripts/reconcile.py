#!/usr/bin/env python3
"""Reconcile the coordinator registry against REAL film packages (thin CLI).

Discovers each built film's ``MissionBrief`` (real codename) and module-level
``GadgetRegistry`` via the frozen bond-api protocol, then applies the pure
merge logic from :mod:`bond_coordinator.reconcile`.  Prints a report and
optionally writes a JSON manifest of the reconciled roster plus the flat
``gadgets.json`` the situation room consumes.

Un-loadable films are skipped per-film (a missing dependency or broken
provider must never abort the whole suite); skipped slugs are listed in the
report.

Usage (from this directory):
    uv run python scripts/reconcile.py
    uv run python scripts/reconcile.py --write output/data/reconciled.json
    uv run python scripts/reconcile.py --gadgets output/data/gadgets.json
    uv run python scripts/reconcile.py --slugs goldfinger spectre
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]  # -> fleet root (sibling repos)
sys.path.insert(0, str(REPO / "bond-coordinator" / "src"))

from bond_coordinator import build_roster
from bond_coordinator.reconcile import (
    gadget_purpose,
    harvest_gadgets,
    override_codenames,
    reconcile_report,
)
from bond_coordinator.types import GadgetRegistry


def _discover_briefs(
    slugs: list[str], root: Path = REPO
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Return (slug -> {codename, objectives}, skipped) from each MissionBrief.

    Un-loadable films (missing deps, broken providers) are SKIPPED, never
    fatal — the probe pattern: a broken film must not crash the suite.

    The guard is deliberately ``Exception``-wide.  Importing a third-party
    film executes arbitrary module-level code, so it can raise anything
    (``NameError`` from a missing import, ``AttributeError``, ``TypeError``,
    ``ValueError`` from a failed constant build).  A narrower guard silently
    fails to deliver the isolation this function promises: one half-edited
    sibling would abort reconciliation for all 27.  Every skip is reported on
    stderr with its cause, so isolation never becomes silence.
    """
    try:
        from bond_api.discovery import load_provider  # type: ignore[import-untyped]
    except ImportError as exc:
        # Layer 1 absent from this environment: degrade to "no film declared a
        # codename" (every film keeps its provisional one) instead of aborting.
        print(
            f"[reconcile] bond-api unavailable ({exc}); no briefs discovered",
            file=sys.stderr,
        )
        return {}, sorted(slugs)

    briefs: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    for slug in slugs:
        search = root / slug / "src"
        if not (search / slug / "mission.py").is_file():
            skipped.append(slug)
            continue  # not built yet: keep provisional codename
        try:
            provider = load_provider(slug, search_paths=[str(search)])
            brief = provider.brief()
            briefs[slug] = {
                "codename": brief.codename,
                "objectives": " | ".join(brief.objectives),
            }
        except Exception as exc:  # noqa: BLE001 — per-film isolation, see docstring
            print(
                f"[reconcile] skipping {slug}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            skipped.append(slug)
    return briefs, skipped


def _discover_gadgets(
    slugs: list[str], root: Path = REPO
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Return (slug -> {gadget_name: purpose}, skipped) from each film's GADGETS.

    Same per-film isolation contract as :func:`_discover_briefs`: importing a
    film runs its module-level code, so any exception is caught, reported on
    stderr, and recorded as a skip rather than aborting the fleet-wide run.
    """
    import importlib

    film_gadgets: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    for slug in slugs:
        search = root / slug / "src"
        if not (search / slug / "mission.py").is_file():
            skipped.append(slug)
            continue
        sys.path.insert(0, str(search))
        try:
            module = importlib.import_module(f"{slug}.mission")
            registry = getattr(module, "GADGETS", None)
            if registry is None:
                # A film with no GADGETS declaration is a legitimate state,
                # not a failure: it contributes nothing and is not "skipped".
                continue
            if callable(registry) and not hasattr(registry, "items"):
                registry = registry()  # a callable factory returning the registry
            if hasattr(registry, "gadgets_for") and hasattr(registry, "lookup"):
                pairs = (
                    (name, registry.lookup(slug, name))
                    for name in registry.gadgets_for(slug)
                )
            elif isinstance(registry, dict):
                pairs = ((name, payload) for name, payload in registry.items())
            else:
                # Unknown container shape — report it rather than dropping the
                # film silently, so an unharvestable registry is visible.
                print(
                    f"[reconcile] {slug}: unrecognised GADGETS shape "
                    f"({type(registry).__name__}); nothing harvested",
                    file=sys.stderr,
                )
                skipped.append(slug)
                continue
            for name, payload in pairs:
                # Purpose derivation is pure business logic and lives in src/:
                # reading payload.__doc__ here would harvest builtin docstrings.
                film_gadgets.setdefault(slug, {})[name] = gadget_purpose(payload)
        except Exception as exc:  # noqa: BLE001 — per-film isolation, see docstring
            print(
                f"[reconcile] skipping gadgets for {slug}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            skipped.append(slug)
        finally:
            try:
                sys.path.remove(str(search))
            except ValueError:
                pass
    return film_gadgets, skipped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile registry against real films"
    )
    parser.add_argument(
        "--slugs", nargs="+", default=None, help="films to reconcile (default: all 27)"
    )
    parser.add_argument(
        "--write", default=None, help="write reconciled roster JSON manifest"
    )
    parser.add_argument(
        "--gadgets", default=None, help="write flat gadgets.json for the situation room"
    )
    parser.add_argument(
        "--bond-root",
        type=Path,
        default=REPO,
        help="directory holding the film packages (default: the BOND suite root); "
        "overridable so the per-film isolation contract is testable",
    )
    args = parser.parse_args()

    slugs = args.slugs or [record.slug for record in build_roster()]
    briefs, skipped = _discover_briefs(slugs, root=args.bond_root)
    film_gadgets, skipped_g = _discover_gadgets(slugs, root=args.bond_root)
    skipped_all = sorted(set(skipped + skipped_g))

    roster = build_roster()
    reconciled = override_codenames(roster, briefs)
    registry = harvest_gadgets(GadgetRegistry(), film_gadgets)
    # The report must be rendered against the PROVISIONAL roster, not the
    # reconciled one: it diffs each record's codename against the film's
    # declaration.  Passing ``reconciled`` compares the declared codename to
    # itself, so every override silently reports as "unchanged" and the count
    # is structurally pinned to 0.
    print(reconcile_report(roster, briefs))
    if skipped_all:
        print(
            f"[reconcile] skipped (unloadable/not built): {', '.join(skipped_all)}",
            file=sys.stderr,
        )

    if args.write:
        manifest = {
            "films": {
                record.slug: {
                    "film": record.film,
                    "year": record.year,
                    "codename": record.codename,
                    "gadgets": [
                        {"name": g.name, "purpose": g.purpose}
                        for g in registry.for_film(record.slug)
                    ],
                }
                for record in reconciled
            },
            "film_declared": {slug: info["codename"] for slug, info in briefs.items()},
            "gadgets": {
                slug: {name: purpose for name, purpose in gadgets.items()}
                for slug, gadgets in film_gadgets.items()
            },
            "skipped": skipped_all,
        }
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"[reconcile] manifest written -> {path}")

    if args.gadgets:
        flat: list[dict[str, Any]] = [
            {"name": gadget.name, "film": gadget.film, "purpose": gadget.purpose}
            for gadget in registry.all()
        ]
        path = Path(args.gadgets)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(flat, indent=2, sort_keys=True) + "\n")
        print(f"[reconcile] gadgets written -> {path} ({len(flat)} gadgets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
