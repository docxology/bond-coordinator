"""Thin orchestrator: hydrate manuscript {{TOKEN}}s, runs last (z_ prefix).

Loads the manuscript identity + fleet metrics from ``manuscript/config.yaml``
via the pure core, writes the resolved mapping to
``output/data/manuscript_variables.json``, and substitutes every template in
``manuscript/*.md`` into ``output/manuscript/*.md``.

Registry status/coverage tokens are hydrated from the fleet gate manifest
(``--gate-manifest``) when it exists; otherwise the registry's unmeasured seed
defaults are used and ``REGISTRY_MEASUREMENT_SOURCE`` says so in the rendered
manuscript.  ``--no-gate-manifest`` forces the seed path for a deterministic,
fleet-independent build.

The ``--allow-draft`` flag is accepted for parity with the exemplar pipeline;
the coordinator has no analysis-output dependency, so it never gates on
generated files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOND_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bond_coordinator import (
    PackageRecord,
    apply_gate_results,
    build_roster,
    generate_variables,
    parse_gate_manifest,
    resolve_manuscript_tree,
)

#: Where ``bond-ops`` writes the fleet-wide gate aggregate.
FLEET_GATE_MANIFEST = BOND_ROOT / "output" / "aggregate" / "gate_manifest.json"


def _measured_roster(path: Path | None) -> tuple[PackageRecord, ...]:
    """The registry roster with measured gate output applied where available."""
    roster = build_roster()
    if path is None or not path.is_file():
        if path is not None:
            print(
                f"[manuscript] no gate manifest at {path}; tokens report the "
                "unmeasured registry seed",
                file=sys.stderr,
            )
        return roster
    results = parse_gate_manifest(json.loads(path.read_text(encoding="utf-8")))
    return apply_gate_results(roster, results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hydrate manuscript variables from config + registry."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "manuscript" / "config.yaml",
    )
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="accepted for pipeline parity; coordinator never gates on analysis outputs",
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
        help="hydrate from the unmeasured registry seed (fleet-independent)",
    )
    args = parser.parse_args(argv)

    roster = _measured_roster(None if args.no_gate_manifest else args.gate_manifest)
    variables = generate_variables(
        args.config, roster=roster, require_outputs=args.allow_draft
    )

    data_path = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )

    out_dir = PROJECT_ROOT / "output" / "manuscript"
    written = resolve_manuscript_tree(PROJECT_ROOT / "manuscript", out_dir, variables)
    print(f"resolved {len(variables)} tokens into {len(written)} manuscript files")
    print(f"  variables -> {data_path}")
    print(f"  tree      -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
