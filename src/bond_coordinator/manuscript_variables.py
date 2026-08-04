"""Manuscript variable hydration for bond-coordinator.

The manuscript identity (title, subtitle, codename, version, keywords) is
loaded from ``manuscript/config.yaml`` — never hand-authored in prose.  Fleet
metrics (registry counts, coverage summary, lifecycle) are derived from the
pure core (:mod:`bond_coordinator.registry`, :mod:`bond_coordinator.status`)
so the manuscript can never drift from the code.

Determinism: no wall-clock tokens are emitted.  Every value is a function of
the config file and the registry/ledger state only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .ledger import MissionLedger
from .registry import ROSTER, SUITE_NAME, PackageRecord
from .status import SUITE_LAYERS, build_status
from .types import PackageStatus

#: Lifecycle shown in prose; kept in sync with :class:`MissionPhase`.
MISSION_LIFECYCLE = "brief → recon → plan → execute → debrief"


def load_config(config_path: Path) -> dict[str, Any]:
    """Load ``manuscript/config.yaml`` (raises :class:`FileNotFoundError`)."""
    if not Path(config_path).is_file():
        raise FileNotFoundError(f"manuscript config not found: {config_path}")
    with Path(config_path).open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        # ValueError (not TypeError): load_config keeps a single exception
        # contract for every config-validity problem a caller may encounter.
        raise ValueError(f"manuscript config must be a YAML mapping: {config_path}")  # noqa: TRY004
    return loaded


def _paper_token(config: dict[str, Any], key: str) -> str:
    paper = config.get("paper")
    if not isinstance(paper, dict) or key not in paper:
        raise ValueError(f"manuscript config is missing paper.{key}")
    return str(paper[key])


def _mission_token(config: dict[str, Any], key: str) -> str:
    mission = config.get("mission")
    if not isinstance(mission, dict) or key not in mission:
        raise ValueError(f"manuscript config is missing mission.{key}")
    return str(mission[key])


def generate_variables(
    config_path: Path | str,
    roster: tuple[PackageRecord, ...] = ROSTER,
    require_outputs: bool = False,
) -> dict[str, str]:
    """Return the ``{{TOKEN}}`` substitution map for the manuscript.

    ``require_outputs`` is accepted for parity with the exemplar's strict
    pipeline contract; the coordinator has no analysis-output dependency, so
    it never gates on generated files (documented in ``docs/architecture.md``).

    Values are computed fresh from ``roster`` (defaults to the full 27-film
    registry) so counts can never go stale.
    """
    config = load_config(Path(config_path))
    ledger = MissionLedger(roster)
    status = build_status(roster, ledger=ledger)

    ready = status.counts_by_status[PackageStatus.READY]
    building = status.counts_by_status[PackageStatus.BUILDING]
    scaffolded = status.counts_by_status[PackageStatus.SCAFFOLDED]
    red = status.counts_by_status[PackageStatus.RED]

    keywords = config.get("keywords")
    keyword_csv = (
        ", ".join(str(item) for item in keywords) if isinstance(keywords, list) else ""
    )
    layer_csv = ", ".join(f"{layer} ({label})" for layer, label, _ in SUITE_LAYERS)

    return {
        # Identity — from manuscript/config.yaml, never hand-authored in prose.
        "CONFIG_TITLE": _paper_token(config, "title"),
        "CONFIG_SUBTITLE": _paper_token(config, "subtitle"),
        "CONFIG_VERSION": _paper_token(config, "version"),
        "CONFIG_CODENAME": _mission_token(config, "codename"),
        "CONFIG_SUITE_NAME": SUITE_NAME,
        "CONFIG_KEYWORDS": keyword_csv,
        "CONFIG_MISSION_LIFECYCLE": MISSION_LIFECYCLE,
        # Fleet metrics — derived from the registry/ledger, never hand-authored.
        "REGISTRY_TOTAL": str(status.total),
        "REGISTRY_READY": str(ready),
        "REGISTRY_BUILDING": str(building),
        "REGISTRY_SCAFFOLDED": str(scaffolded),
        "REGISTRY_RED": str(red),
        "REGISTRY_COVERAGE_KNOWN": str(status.coverage.known),
        "REGISTRY_COVERAGE_UNKNOWN": str(status.coverage.unknown),
        "REGISTRY_COVERAGE_MEAN": status.coverage.formatted_mean(),
        "REGISTRY_COVERAGE_AT_90": str(status.coverage.at_or_above_floor),
        "REGISTRY_BLOCKED_COUNT": str(len(status.blocked_packages)),
        "REGISTRY_STALE_COUNT": str(len(status.stale_packages)),
        "REGISTRY_PACKAGES_CSV": ", ".join(record.slug for record in roster),
        # Suite topology + audit trail — derived, never hand-authored.
        "REGISTRY_LAYER_COUNT": str(len(SUITE_LAYERS)),
        "REGISTRY_LAYER_CSV": layer_csv,
        "LEDGER_TRANSITION_TOTAL": str(len(ledger.history)),
    }


def resolve_manuscript_tree(
    templates_dir: Path | str,
    output_dir: Path | str,
    variables: dict[str, str],
) -> list[Path]:
    """Substitute ``{{TOKEN}}`` in every ``manuscript/*.md`` template.

    Writes the resolved copies to ``output_dir`` and returns the written
    paths.  Unknown ``{{...}}`` tokens are left untouched (so unresolved
    tokens stay grep-able, per the exemplar contract).
    """
    source_dir = Path(templates_dir)
    target_dir = Path(output_dir)
    written: list[Path] = []
    for template in sorted(source_dir.glob("*.md")):
        text = template.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        target = target_dir / template.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(target)
    return written
