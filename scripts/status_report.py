"""Thin orchestrator: print (and persist) the aggregate suite-status report.

Reads the persisted mission ledger if present, else reports every mission at
``brief``.  Registry status/coverage come from the fleet gate manifest
(``--gate-manifest``, written by ``bond-ops``) when it exists; with
``--no-gate-manifest``, or when the file is absent, the report shows the
registry's unmeasured seed defaults and says so on the ``gates`` line rather
than presenting them as a measurement.  Uses the pure core
(``bond_coordinator.status``, ``bond_coordinator.gates``) for all aggregation
and all derivation — no business logic here.
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
    COORDINATOR_CODENAME,
    SUITE_NAME,
    MissionLedger,
    PackageRecord,
    SuiteStatus,
    apply_gate_results,
    build_roster,
    build_status,
    measurement_summary,
    parse_gate_manifest,
)

#: Where ``bond-ops`` writes the fleet-wide gate aggregate.
FLEET_GATE_MANIFEST = BOND_ROOT / "output" / "aggregate" / "gate_manifest.json"

#: Wording used when no measured gate output was applied.
UNMEASURED = "none applied — registry seed defaults (status/coverage unmeasured)"


def _api_probe() -> bool:
    """True when the Layer 1 protocol package (bond-api) is importable.

    Uses ``find_spec`` rather than ``import`` so the probe never raises and
    mypy sees a static, resolvable call.
    """
    return importlib.util.find_spec("bond_api") is not None


def _load_ledger(path: Path, roster: tuple[PackageRecord, ...]) -> MissionLedger:
    if path.is_file():
        return MissionLedger.from_json(path.read_text(encoding="utf-8"), roster=roster)
    return MissionLedger(roster)


def _apply_gates(
    path: Path | None, roster: tuple[PackageRecord, ...]
) -> tuple[tuple[PackageRecord, ...], str]:
    """Apply measured gate output, if a manifest was supplied and exists."""
    if path is None:
        return roster, UNMEASURED
    if not path.is_file():
        print(
            f"[status] no gate manifest at {path}; rows stay unmeasured",
            file=sys.stderr,
        )
        return roster, UNMEASURED
    results = parse_gate_manifest(json.loads(path.read_text(encoding="utf-8")))
    return apply_gate_results(roster, results), (
        f"{measurement_summary(roster, results)} (source: {path})"
    )


def _status_to_dict(status: SuiteStatus, measurement_source: str) -> dict[str, object]:
    return {
        "total": status.total,
        "counts_by_status": {k.value: v for k, v in status.counts_by_status.items()},
        "counts_by_phase": {k.value: v for k, v in status.counts_by_phase.items()},
        "coverage": {
            "known": status.coverage.known,
            "unknown": status.coverage.unknown,
            "mean": status.coverage.formatted_mean(),
            "min": status.coverage.minimum,
            "max": status.coverage.maximum,
            "at_or_above_90": status.coverage.at_or_above_floor,
        },
        "stale_packages": list(status.stale_packages),
        "blocked_packages": [
            {"slug": item.slug, "reason": item.reason}
            for item in status.blocked_packages
        ],
        "layers": [
            {
                "layer": layer.layer,
                "label": layer.label,
                "packages": list(layer.packages),
                "ready": layer.ready,
                "ready_count": layer.ready_count,
                "total": layer.total,
                "coverage_mean": layer.coverage_mean,
            }
            for layer in status.layers
        ],
        "dependency_ready": status.dependency_ready,
        "measurement_source": measurement_source,
        "generated_at": status.generated_at.isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the BOND suite status report.")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=PROJECT_ROOT / "output" / "data" / "mission_ledger.json",
        help="path to the persisted mission ledger (optional)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON"
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
        help="report the unmeasured registry seed (deterministic, fleet-independent)",
    )
    args = parser.parse_args(argv)

    roster = build_roster()
    roster, measurement_source = _apply_gates(
        None if args.no_gate_manifest else args.gate_manifest, roster
    )
    ledger = _load_ledger(args.ledger, roster)
    status = build_status(roster, ledger, dependency_ready=_api_probe())

    # Persist the snapshot for the situation room and provenance (gitignored).
    out_path = PROJECT_ROOT / "output" / "data" / "suite_status.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(_status_to_dict(status, measurement_source), indent=2),
        encoding="utf-8",
    )

    if args.json:
        print(
            json.dumps(
                _status_to_dict(status, measurement_source), indent=2, sort_keys=True
            )
        )
        return 0

    by_status = status.counts_by_status
    by_phase = status.counts_by_phase
    print(
        f"{SUITE_NAME} — {COORDINATOR_CODENAME}  ·  {status.generated_at.isoformat()}"
    )
    print(f"Packages: {status.total} total")
    print("  by status: " + "  ".join(f"{k.value}={v}" for k, v in by_status.items()))
    print("  by phase : " + "  ".join(f"{k.value}={v}" for k, v in by_phase.items()))
    print(
        f"  coverage : {status.coverage.known} measured, mean {status.coverage.formatted_mean()}"
    )
    print(
        "  by layer : "
        + "  ".join(
            f"{layer.layer}={layer.ready_count}/{layer.total}"
            for layer in status.layers
        )
    )
    print(f"  gates    : {measurement_source}")
    print(
        f"  stale    : {len(status.stale_packages)}  blocked: {len(status.blocked_packages)}"
    )
    print(
        f"  layer-1  : {'bond-api importable' if status.dependency_ready else 'bond-api not importable here (pure-core mirror in use)'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
