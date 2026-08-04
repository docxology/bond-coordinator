"""Thin orchestrator: regenerate the situation-room HTML dashboard.

Reads the persisted mission ledger and gadget inventory (if present) and
writes ``output/situation_room.html`` from the pure-core renderer.  All
HTML-building lives in ``bond_coordinator.situation``.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bond_coordinator import (
    Gadget,
    GadgetRegistry,
    MissionLedger,
    PackageRecord,
    build_roster,
    build_situation_room,
    build_status,
    write_situation_room,
)


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
        "--out",
        type=Path,
        default=PROJECT_ROOT / "output" / "situation_room.html",
    )
    args = parser.parse_args(argv)

    roster = build_roster()
    ledger = _load_ledger(args.ledger, roster)
    gadgets = _load_gadgets(args.gadgets)
    status = build_status(roster, ledger, dependency_ready=_api_probe())

    html = build_situation_room(status, roster, ledger, gadgets)
    target = write_situation_room(html, args.out)
    print(f"situation room written to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
