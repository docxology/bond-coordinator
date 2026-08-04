"""Aggregate suite-status reporting for the BOND fleet.

Combines the registry (what exists / measured status) with the ledger (where
each package is in its mission lifecycle) into one deterministic snapshot:
counts by status and phase, a coverage summary, and stale / blocked flags.

All time-dependent inputs are injectable so the report is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .ledger import MissionLedger, utcnow
from .registry import ROSTER, PackageRecord
from .types import MissionPhase, PackageStatus

#: Coverage gate shared by the whole suite (matches pyproject fail_under).
COVERAGE_FLOOR = 90.0

#: Default age (days) after which an unfinished mission is flagged stale.
DEFAULT_STALE_DAYS = 30


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


def build_status(
    roster: tuple[PackageRecord, ...] = ROSTER,
    ledger: MissionLedger | None = None,
    now: datetime | None = None,
    stale_days: int = DEFAULT_STALE_DAYS,
    dependency_ready: bool = False,
) -> SuiteStatus:
    """Assemble the fleet snapshot from registry + ledger.

    ``ledger`` defaults to a fresh ledger (every package at ``brief``) — the
    honest state before any mission has been run.  ``now`` and ``stale_days``
    are injectable for deterministic reports.
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
    )


def count_by_status(
    status: PackageStatus | str, roster: tuple[PackageRecord, ...] = ROSTER
) -> int:
    """Number of packages in ``status`` (convenience for thin scripts)."""
    target = PackageStatus(status) if isinstance(status, str) else status
    return sum(1 for record in roster if record.status is target)
