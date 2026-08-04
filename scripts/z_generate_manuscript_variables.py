"""Thin orchestrator: hydrate manuscript {{TOKEN}}s, runs last (z_ prefix).

Loads the manuscript identity + fleet metrics from ``manuscript/config.yaml``
via the pure core, writes the resolved mapping to
``output/data/manuscript_variables.json``, and substitutes every template in
``manuscript/*.md`` into ``output/manuscript/*.md``.

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
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bond_coordinator import (
    build_roster,
    generate_variables,
    resolve_manuscript_tree,
)


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
    args = parser.parse_args(argv)

    variables = generate_variables(
        args.config, roster=build_roster(), require_outputs=args.allow_draft
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
