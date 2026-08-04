#!/usr/bin/env python3
"""Reconcile the coordinator registry against REAL film packages (thin CLI).

Discovers each built film's ``MissionBrief`` (real codename) and module-level
``GadgetRegistry`` via the frozen bond-api protocol, then applies the pure
merge logic from :mod:`bond_coordinator.reconcile`.  Prints a report and
optionally writes a JSON manifest of the reconciled roster.

Usage (from this directory):
    uv run python scripts/reconcile.py
    uv run python scripts/reconcile.py --write output/data/reconciled.json
    uv run python scripts/reconcile.py --slugs goldfinger spectre
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # -> projects/working/bond
sys.path.insert(0, str(REPO / "bond-coordinator" / "src"))

from bond_coordinator import build_roster
from bond_coordinator.reconcile import (
    harvest_gadgets,
    override_codenames,
    reconcile_report,
)
from bond_coordinator.types import GadgetRegistry


def _discover_briefs(slugs: list[str]) -> dict[str, dict[str, str]]:
    """Return slug -> {codename, objectives} from each film's MissionBrief."""
    from bond_api.discovery import load_provider  # type: ignore[import-untyped]

    briefs: dict[str, dict[str, str]] = {}
    for slug in slugs:
        search = REPO / slug / "src"
        if not (search / slug / "mission.py").is_file():
            continue  # not built yet: keep provisional codename
        provider = load_provider(slug, search_paths=[str(search)])
        brief = provider.brief()
        briefs[slug] = {
            "codename": brief.codename,
            "objectives": " | ".join(brief.objectives),
        }
    return briefs


def _discover_gadgets(slugs: list[str]) -> dict[str, dict[str, str]]:
    """Return slug -> {gadget_name: purpose} from each film's GADGETS registry."""
    import importlib

    film_gadgets: dict[str, dict[str, str]] = {}
    for slug in slugs:
        search = REPO / slug / "src"
        if not (search / slug / "mission.py").is_file():
            continue
        sys.path.insert(0, str(search))
        try:
            module = importlib.import_module(f"{slug}.mission")
            registry = getattr(module, "GADGETS", None)
            if registry is None:
                continue
            for name in registry.gadgets_for(slug):
                payload = registry.lookup(slug, name)
                purpose = ""
                doc = getattr(payload, "__doc__", None)
                if doc:
                    purpose = doc.strip().splitlines()[0]
                film_gadgets.setdefault(slug, {})[name] = purpose
        finally:
            try:
                sys.path.remove(str(search))
            except ValueError:
                pass
    return film_gadgets


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
    args = parser.parse_args()

    slugs = args.slugs or [record.slug for record in build_roster()]
    try:
        briefs = _discover_briefs(slugs)
        film_gadgets = _discover_gadgets(slugs)
    except (
        ImportError,
        RuntimeError,
    ) as exc:  # bond-api probe: degrade gracefully, never crash
        print(f"[reconcile] bond-api discovery unavailable: {exc}", file=sys.stderr)
        return 2

    roster = build_roster()
    reconciled = override_codenames(roster, briefs)
    registry = harvest_gadgets(GadgetRegistry(), film_gadgets)
    print(reconcile_report(reconciled, briefs))

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
        }
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"[reconcile] manifest written -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
