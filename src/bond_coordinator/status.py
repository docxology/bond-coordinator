"""Aggregate suite-status reporting for the BOND fleet.

Combines the registry (what exists / measured status) with the ledger (where
each package is in its mission lifecycle) into one deterministic snapshot:
counts by status and phase, a coverage summary, and stale / blocked flags.

All time-dependent inputs are injectable so the report is reproducible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .ledger import MissionLedger, utcnow
from .registry import FILM_SLUGS, ROSTER, PackageRecord
from .types import MissionPhase, PackageStatus

#: Coverage gate shared by the whole suite (matches pyproject fail_under).
COVERAGE_FLOOR = 90.0

#: Default age (days) after which an unfinished mission is flagged stale.
DEFAULT_STALE_DAYS = 30

#: Declared suite topology — (layer id, human label, package
#: slugs).  The ``films`` layer is the registry's 27-film roster; infra layers
#: are the sibling mission-infrastructure packages (not tracked as records,
#: but their readiness is reported by the layer summary).
SUITE_LAYERS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("layer0", "Q-branch primitives", ("bond-utilities",)),
    ("layer1", "The protocol", ("bond-api",)),
    ("layer2", "Mission control", ("bond-coordinator",)),
    ("layer3", "The DAG runner", ("bond-orchestrator",)),
    ("layer4", "Front door & fleet ops", ("bond-cli", "bond-ops")),
    ("films", "Film packages", FILM_SLUGS),
)


@dataclass(frozen=True)
class CoverageSummary:
    """Measured coverage across the fleet (None-valued fields when nothing is measured)."""

    known: int  # packages with a measured coverage value
    unknown: int  # packages without one (scaffolded / not yet gated)
    mean: float | None
    minimum: float | None
    maximum: float | None
    at_or_above_floor: int  # packages meeting the 90% gate

    def formatted_mean(self) -> str:
        """Mean coverage as a display string, or ``"N/A"`` when unmeasured."""
        if self.mean is None:
            return "N/A"
        return f"{self.mean:.1f}%"


@dataclass(frozen=True)
class BlockedPackage:
    """A package currently blocked, with the reason mission control flags."""

    slug: str
    reason: str


@dataclass(frozen=True)
class LayerSummary:
    """One layer of the declared suite topology, summarized for the report.

    Semantics differ per layer kind: infra layers (``layer0``…``layer4``) carry
    a ``ready`` tri-state (``True`` / ``False`` / ``None`` when not probed) and
    a ``ready_count`` of 1 when ready; the ``films`` layer carries ``ready=None``
    plus the registry-derived ``ready_count`` (READY films) and
    ``coverage_mean`` (over measured films only).
    """

    layer: str
    label: str
    packages: tuple[str, ...]
    ready: bool | None
    ready_count: int
    total: int
    coverage_mean: float | None


@dataclass(frozen=True)
class SuiteStatus:
    """One deterministic snapshot of the whole fleet."""

    total: int
    counts_by_status: dict[PackageStatus, int]
    counts_by_phase: dict[MissionPhase, int]
    coverage: CoverageSummary
    stale_packages: tuple[str, ...]
    blocked_packages: tuple[BlockedPackage, ...]
    dependency_ready: bool  # bond-api (Layer 1) available to the fleet
    generated_at: datetime
    layers: tuple[LayerSummary, ...] = ()
    #: The staleness threshold this snapshot was computed with.  Carried on
    #: the snapshot so downstream renderers state the threshold that was
    #: actually applied instead of assuming the default.
    stale_days: int = DEFAULT_STALE_DAYS


def _coverage_summary(roster: tuple[PackageRecord, ...]) -> CoverageSummary:
    known_values = [record.coverage for record in roster if record.coverage is not None]
    if not known_values:
        return CoverageSummary(
            known=0,
            unknown=len(roster),
            mean=None,
            minimum=None,
            maximum=None,
            at_or_above_floor=0,
        )
    return CoverageSummary(
        known=len(known_values),
        unknown=len(roster) - len(known_values),
        mean=sum(known_values) / len(known_values),
        minimum=min(known_values),
        maximum=max(known_values),
        at_or_above_floor=sum(1 for value in known_values if value >= COVERAGE_FLOOR),
    )


def _blocked_packages(
    roster: tuple[PackageRecord, ...], ledger: MissionLedger
) -> tuple[BlockedPackage, ...]:
    blocked: list[BlockedPackage] = []
    by_slug = {record.slug: record for record in roster}
    for slug in sorted(by_slug):
        record = by_slug[slug]
        phase = ledger.get(slug).phase
        if record.status is PackageStatus.RED:
            blocked.append(BlockedPackage(slug, "flagged red"))
        elif phase is MissionPhase.EXECUTE and record.status is not PackageStatus.READY:
            blocked.append(BlockedPackage(slug, "executing before ready"))
        elif phase is MissionPhase.PLAN and record.status is PackageStatus.SCAFFOLDED:
            blocked.append(BlockedPackage(slug, "planning before building"))
    return tuple(blocked)


def _layer_summaries(
    roster: tuple[PackageRecord, ...],
    dependency_ready: bool,
    layer_ready: Mapping[str, bool] | None,
) -> tuple[LayerSummary, ...]:
    """Build one :class:`LayerSummary` per declared suite layer.

    The ``films`` layer aggregates the given ``roster`` (which may be the full
    27 or a subset fixture): tracked count, READY count, and mean coverage over
    measured films.  Infra layers report readiness from ``layer_ready``, with a
    sensible default: ``layer1`` (bond-api) tracks ``dependency_ready``, all
    other infra layers default to ``None`` (not probed).
    """
    film_by_slug = {record.slug: record for record in roster}
    summaries: list[LayerSummary] = []
    for layer, label, packages in SUITE_LAYERS:
        if layer == "films":
            present = [film_by_slug[slug] for slug in packages if slug in film_by_slug]
            ready_count = sum(1 for r in present if r.status is PackageStatus.READY)
            known = [r.coverage for r in present if r.coverage is not None]
            mean = sum(known) / len(known) if known else None
            summaries.append(
                LayerSummary(
                    layer=layer,
                    label=label,
                    packages=tuple(record.slug for record in present),
                    ready=None,
                    ready_count=ready_count,
                    total=len(present),
                    coverage_mean=mean,
                )
            )
        else:
            ready = (layer_ready or {}).get(
                layer, dependency_ready if layer == "layer1" else None
            )
            summaries.append(
                LayerSummary(
                    layer=layer,
                    label=label,
                    packages=packages,
                    ready=ready,
                    ready_count=1 if ready else 0,
                    total=len(packages),
                    coverage_mean=None,
                )
            )
    return tuple(summaries)


def build_status(
    roster: tuple[PackageRecord, ...] = ROSTER,
    ledger: MissionLedger | None = None,
    now: datetime | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
    dependency_ready: bool = False,
    layer_ready: Mapping[str, bool] | None = None,
) -> SuiteStatus:
    """Assemble the fleet snapshot from registry + ledger.

    ``ledger`` defaults to a fresh ledger (every package at ``brief``) — the
    honest state before any mission has been run.  ``now`` and ``stale_days``
    are injectable for deterministic reports.  ``layer_ready`` optionally
    supplies per-layer readiness for the infra layers (see
    :func:`_layer_summaries`); when ``None``, only ``layer1`` is inferred from
    ``dependency_ready``.
    """
    if ledger is None:
        ledger = MissionLedger(roster)
    reference = now if now is not None else utcnow()

    counts_by_status = {status: 0 for status in PackageStatus}
    for record in roster:
        counts_by_status[record.status] += 1

    counts_by_phase = {phase: 0 for phase in MissionPhase}
    for slug in sorted(record.slug for record in roster):
        counts_by_phase[ledger.get(slug).phase] += 1

    stale = tuple(
        slug
        for slug in sorted(record.slug for record in roster)
        if ledger.is_stale(slug, stale_days=stale_days, now=reference)
    )

    return SuiteStatus(
        total=len(roster),
        counts_by_status=counts_by_status,
        counts_by_phase=counts_by_phase,
        coverage=_coverage_summary(roster),
        stale_packages=stale,
        blocked_packages=_blocked_packages(roster, ledger),
        dependency_ready=dependency_ready,
        generated_at=reference,
        layers=_layer_summaries(roster, dependency_ready, layer_ready),
        stale_days=stale_days,
    )


def count_by_status(
    status: PackageStatus | str, roster: tuple[PackageRecord, ...] = ROSTER
) -> int:
    """Number of packages in ``status`` (convenience for thin scripts)."""
    target = PackageStatus(status) if isinstance(status, str) else status
    return sum(1 for record in roster if record.status is target)
