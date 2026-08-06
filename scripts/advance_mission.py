"""Thin orchestrator: advance one film package's mission phase in the ledger.

Loads (or creates) the persisted mission ledger, applies a forward-only phase
transition via the pure-core ``MissionLedger``, and writes the audit-trail
JSON back.  Illegal (backwards) transitions exit non-zero.

Usage::

    uv run python scripts/advance_mission.py --slug goldfinger --phase recon \\
        --by agent-007 --version 0.1.0 --note "watching Fort Knox"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bond_coordinator import (
    MissionLedger,
    MissionPhase,
    PackageRecord,
    build_roster,
)


def _load_or_create(path: Path, roster: tuple[PackageRecord, ...]) -> MissionLedger:
    if path.is_file():
        return MissionLedger.from_json(path.read_text(encoding="utf-8"), roster=roster)
    return MissionLedger(roster)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Advance a package's mission phase.")
    parser.add_argument(
        "--slug", required=True, help="film package slug (e.g. goldfinger)"
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=[phase.value for phase in MissionPhase],
        help="target phase (brief|recon|plan|execute|debrief)",
    )
    parser.add_argument(
        "--by", default="operator", help="agent/identity making the change"
    )
    parser.add_argument(
        "--version", default="0.1.0", help="package version being progressed"
    )
    parser.add_argument("--note", default=None, help="optional audit note")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "mission_ledger.json",
    )
    args = parser.parse_args(argv)

    roster = build_roster()
    ledger = _load_or_create(args.ledger, roster)
    # Report the *actual* source phase of the move (a jump can come from any
    # later phase — the message must not claim every move starts at brief).
    prior = ledger.get(args.slug).phase
    try:
        entry = ledger.jump(
            args.slug, args.phase, args.by, args.version, note=args.note
        )
    except (KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(ledger.to_json(), encoding="utf-8")
    print(
        f"{entry.slug}: {prior.value} → {entry.phase.value}  "
        f"(by {entry.updated_by} @ {entry.version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
