"""Suite-status tests: aggregation, coverage summary, stale/blocked flags.

Builds small deterministic rosters from the 5-film fixture by varying
status/coverage fields via ``dataclasses.replace`` — real records, real rules.
"""

from __future__ import annotations

from dataclasses import replace

from bond_coordinator import (
    ROSTER,
    MissionLedger,
    MissionPhase,
    PackageStatus,
    build_status,
    count_by_status,
    subset_roster,
)
from tests.conftest import FIXED_NOW


def _mixed_roster(sample_roster):
    """5-film roster with 2 ready / 1 building / 1 scaffolded / 1 red."""
    ready_a, ready_b, building, scaffolded, red = sample_roster
    return (
        replace(ready_a, status=PackageStatus.READY, coverage=95.0),
        replace(ready_b, status=PackageStatus.READY, coverage=92.0),
        replace(building, status=PackageStatus.BUILDING, coverage=85.0),
        replace(scaffolded, status=PackageStatus.SCAFFOLDED, coverage=None),
        replace(red, status=PackageStatus.RED, coverage=None),
    )


def _ledger_with(roster, phase_map) -> MissionLedger:
    """Ledger advanced to the given phase per slug, pinned to FIXED_NOW."""
    ledger = MissionLedger(roster, now_fn=lambda: FIXED_NOW)
    for slug, phase in phase_map.items():
        ledger.jump(slug, phase, "operator", "0.1.0")
    return ledger


class TestFreshFleet:
    """Before any work, every package is scaffolded and every mission briefed."""

    def test_default_status(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        assert status.total == 5
        assert status.counts_by_status[PackageStatus.SCAFFOLDED] == 5
        assert status.counts_by_status[PackageStatus.READY] == 0
        assert status.counts_by_phase[MissionPhase.BRIEF] == 5
        assert status.stale_packages == ()
        assert status.blocked_packages == ()
        assert status.dependency_ready is False
        assert status.coverage.known == 0
        assert status.coverage.unknown == 5
        assert status.coverage.mean is None
        assert status.coverage.formatted_mean() == "N/A"

    def test_dependency_ready_passthrough(self, sample_roster) -> None:
        status = build_status(sample_roster, dependency_ready=True)
        assert status.dependency_ready is True


class TestMixedFleet:
    def test_counts_by_status(self, sample_roster) -> None:
        status = build_status(_mixed_roster(sample_roster))
        assert status.counts_by_status[PackageStatus.READY] == 2
        assert status.counts_by_status[PackageStatus.BUILDING] == 1
        assert status.counts_by_status[PackageStatus.SCAFFOLDED] == 1
        assert status.counts_by_status[PackageStatus.RED] == 1

    def test_coverage_summary(self, sample_roster) -> None:
        coverage = build_status(_mixed_roster(sample_roster)).coverage
        assert coverage.known == 3
        assert coverage.unknown == 2
        assert coverage.minimum == 85.0
        assert coverage.maximum == 95.0
        assert coverage.at_or_above_floor == 2  # only 95 and 92 clear the 90 gate
        assert coverage.formatted_mean() == "90.7%"

    def test_red_package_is_blocked(self, sample_roster) -> None:
        status = build_status(_mixed_roster(sample_roster))
        assert any(item.reason == "flagged red" for item in status.blocked_packages)


class TestBlockedRules:
    def test_executing_before_ready_is_blocked(self, sample_roster) -> None:
        roster = _mixed_roster(sample_roster)
        # goldeneye is BUILDING (index 2) in the mixed roster; executing is premature.
        ledger = _ledger_with(roster, {"goldeneye": "execute"})
        status = build_status(roster, ledger)
        assert any(
            item.reason == "executing before ready" for item in status.blocked_packages
        )

    def test_ready_executing_not_blocked(self, sample_roster) -> None:
        roster = _mixed_roster(sample_roster)
        # dr_no is READY in the mixed roster; executing is allowed.
        ledger = _ledger_with(roster, {"dr_no": "execute"})
        status = build_status(roster, ledger)
        assert not any(
            item.reason == "executing before ready" for item in status.blocked_packages
        )

    def test_planning_before_building_is_blocked(self, sample_roster) -> None:
        roster = _mixed_roster(sample_roster)
        # skyfall is scaffolded in the mixed roster; planning is premature.
        ledger = _ledger_with(roster, {"skyfall": "plan"})
        status = build_status(roster, ledger)
        assert any(
            item.reason == "planning before building"
            for item in status.blocked_packages
        )

    def test_phases_counted(self, sample_roster) -> None:
        roster = _mixed_roster(sample_roster)
        ledger = _ledger_with(roster, {"goldfinger": "recon", "dr_no": "debrief"})
        status = build_status(roster, ledger)
        assert status.counts_by_phase[MissionPhase.RECON] == 1
        assert status.counts_by_phase[MissionPhase.DEBRIEF] == 1


class TestStaleFlags:
    def test_stale_flagged_from_age(self, aged_ledger, sample_roster) -> None:
        status = build_status(sample_roster, aged_ledger, now=FIXED_NOW)
        # goldfinger was debriefed (never stale); the other 4 are stale.
        assert status.stale_packages == (
            "dr_no",
            "goldeneye",
            "no_time_to_die",
            "skyfall",
        )

    def test_no_stale_within_threshold(self, fresh_ledger, sample_roster) -> None:
        status = build_status(sample_roster, fresh_ledger)
        assert status.stale_packages == ()


class TestCountByStatus:
    def test_count_convenience_full_registry(self) -> None:
        assert count_by_status(PackageStatus.SCAFFOLDED, ROSTER) == 27
        assert count_by_status("ready", ROSTER) == 0

    def test_count_convenience_subset(self, sample_slugs) -> None:
        roster = subset_roster(sample_slugs)
        assert count_by_status(PackageStatus.SCAFFOLDED, roster) == 5
