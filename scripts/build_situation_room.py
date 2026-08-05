"""Thin orchestrator: regenerate the situation-room HTML dashboard.

Reads the persisted mission ledger, the gadget inventory, the reconciled
manifest (film-declared codenames) and the fleet gate manifest (measured
status/coverage) if present, and writes ``output/situation_room.html`` from
the pure-core renderer.  All HTML-building lives in
``bond_coordinator.situation``; all merge/derivation logic lives in
``bond_coordinator.reconcile`` and ``bond_coordinator.gates``.

Codenames and measured coverage are **inputs**, not assumptions: whichever of
the two manifests is absent, the rendered provenance block says so in words,
so a provisional codename or an unmeasured row is never displayed as a
reconciled or measured one.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOND_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bond_coordinator import (
    Gadget,
    GadgetRegistry,
    MissionLedger,
    PackageRecord,
    apply_gate_results,
    build_roster,
    build_situation_room,
    build_status,
    measurement_summary,
    override_codenames,
    parse_gate_manifest,
    write_situation_room,
)
from bond_coordinator.situation import (
    DEFAULT_CODENAME_SOURCE,
    DEFAULT_MEASUREMENT_SOURCE,
)

#: Where ``bond-ops`` writes the fleet-wide gate aggregate.
FLEET_GATE_MANIFEST = BOND_ROOT / "output" / "aggregate" / "gate_manifest.json"


def _load_ledger(path: Path, roster: tuple[PackageRecord, ...]) -> MissionLedger:
    if path.is_file():
        return MissionLedger.from_json(path.read_text(encoding="utf-8"), roster=roster)
    return MissionLedger(roster)


def _load_gadgets(path: Path) -> GadgetRegistry:
    registry = GadgetRegistry()
    if not path.is_file():
        return registry
    records = json.loads(path.read_text(encoding="utf-8"))
    for record in records:
        registry.register(
            Gadget(name=record["name"], film=record["film"], purpose=record["purpose"])
        )
    return registry


def _apply_reconciled(
    path: Path, roster: tuple[PackageRecord, ...]
) -> tuple[tuple[PackageRecord, ...], str]:
    """Merge film-declared codenames from a reconcile manifest, if present."""
    if not path.is_file():
        return roster, DEFAULT_CODENAME_SOURCE
    payload = json.loads(path.read_text(encoding="utf-8"))
    declared = payload.get("film_declared") or {}
    briefs = {slug: {"codename": str(name)} for slug, name in declared.items()}
    merged = override_codenames(roster, briefs)
    changed = sum(
        1 for before, after in zip(roster, merged) if before.codename != after.codename
    )
    return merged, (
        f"reconciled from {path.name}: {len(declared)} film declaration(s), "
        f"{changed} provisional codename(s) overridden"
    )


def _apply_gates(
    path: Path | None, roster: tuple[PackageRecord, ...]
) -> tuple[tuple[PackageRecord, ...], str]:
    """Apply measured gate output, if a manifest was supplied and exists."""
    if path is None:
        return roster, DEFAULT_MEASUREMENT_SOURCE
    if not path.is_file():
        print(
            f"[situation] no gate manifest at {path}; rows stay unmeasured",
            file=sys.stderr,
        )
        return roster, DEFAULT_MEASUREMENT_SOURCE
    results = parse_gate_manifest(json.loads(path.read_text(encoding="utf-8")))
    merged = apply_gate_results(roster, results)
    return merged, f"{measurement_summary(roster, results)} (source: {path})"


def _api_probe() -> bool:
    """True when the Layer 1 protocol package (bond-api) is importable."""
    return importlib.util.find_spec("bond_api") is not None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the situation-room dashboard."
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "mission_ledger.json",
    )
    parser.add_argument(
        "--gadgets",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "gadgets.json",
    )
    parser.add_argument(
        "--reconciled",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "reconciled.json",
        help="manifest written by scripts/reconcile.py --write (film-declared codenames)",
    )
    parser.add_argument(
        "--gate-manifest",
        type=Path,
        default=FLEET_GATE_MANIFEST,
        help="fleet gate aggregate supplying measured status/coverage",
    )
    parser.add_argument(
        "--no-gate-manifest",
        action="store_true",
        help="render the unmeasured registry seed (deterministic, fleet-independent)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "output" / "situation_room.html",
    )
    args = parser.parse_args(argv)

    roster = build_roster()
    roster, codename_source = _apply_reconciled(args.reconciled, roster)
    roster, measurement_source = _apply_gates(
        None if args.no_gate_manifest else args.gate_manifest, roster
    )
    ledger = _load_ledger(args.ledger, roster)
    gadgets = _load_gadgets(args.gadgets)
    status = build_status(roster, ledger, dependency_ready=_api_probe())

    html = build_situation_room(
        status,
        roster,
        ledger,
        gadgets,
        codename_source=codename_source,
        measurement_source=measurement_source,
    )
    target = write_situation_room(html, args.out)
    print(f"situation room written to {target}")
    print(f"  codenames  : {codename_source}")
    print(f"  measurement: {measurement_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
