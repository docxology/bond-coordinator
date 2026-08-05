"""Measured gate output → registry rows (real data, real JSON, zero mocks).

These tests exist because the registry used to carry ``scaffolded`` /
``coverage=None`` as *literals* with no code path able to change them, while
the docs called that state a measurement.  Every assertion below is against a
transition the code performs on real gate rows, so each one can fail: change
the status rule, the floor comparison, or the "absent row is left alone"
behaviour and a test goes red.

Payloads are the real aggregate shape ``bond-ops`` writes
(``{"packages": [{"package", "coverage", "passed", "failed", "rc",
"verdict"}, ...]}``), round-tripped through real JSON files where a file is
what the orchestrator would read.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bond_coordinator import (
    GateResult,
    PackageStatus,
    apply_gate_results,
    measurement_summary,
    parse_gate_manifest,
)
from bond_coordinator.gates import UNMEASURED_SUMMARY, measured_row_summary
from bond_coordinator.status import COVERAGE_FLOOR


def _row(
    package: str,
    coverage: float | None = 100.0,
    passed: int = 10,
    failed: int = 0,
    rc: int = 0,
    verdict: str = "ok",
) -> dict[str, object]:
    return {
        "package": package,
        "coverage": coverage,
        "passed": passed,
        "failed": failed,
        "rc": rc,
        "verdict": verdict,
    }


class TestParseGateManifest:
    def test_parses_the_aggregate_mapping_shape(self) -> None:
        results = parse_gate_manifest(
            {"packages": [_row("goldfinger", 99.5, passed=167)]}
        )
        assert set(results) == {"goldfinger"}
        result = results["goldfinger"]
        assert result == GateResult(
            package="goldfinger",
            coverage=99.5,
            passed=167,
            failed=0,
            returncode=0,
            verdict="ok",
        )
        assert result.ok is True

    def test_parses_a_bare_list_of_rows(self) -> None:
        results = parse_gate_manifest([_row("skyfall", 91.0)])
        assert results["skyfall"].coverage == 91.0

    def test_parses_from_a_real_json_file(self, tmp_path: Path) -> None:
        path = tmp_path / "gate_manifest.json"
        path.write_text(json.dumps({"packages": [_row("dr_no", 98.0)]}), "utf-8")
        results = parse_gate_manifest(json.loads(path.read_text(encoding="utf-8")))
        assert results["dr_no"].coverage == 98.0

    def test_missing_coverage_is_unknown_not_zero(self) -> None:
        results = parse_gate_manifest([_row("dr_no", coverage=None)])
        assert results["dr_no"].coverage is None

    def test_integer_coverage_is_widened_to_float(self) -> None:
        results = parse_gate_manifest([_row("dr_no", coverage=100)])
        assert results["dr_no"].coverage == pytest.approx(100.0)

    def test_failed_row_is_not_ok(self) -> None:
        results = parse_gate_manifest([_row("dr_no", 95.0, failed=3, verdict="fail")])
        assert results["dr_no"].ok is False

    @pytest.mark.parametrize(
        "payload",
        [
            {"no_packages_key": []},
            {"packages": "not-a-list"},
            "a string",
            [{"coverage": 90.0}],  # row with no package name
            [{"package": ""}],
            [["not", "a", "mapping"]],
            [_row("dr_no", coverage="high")],
            [_row("dr_no", coverage=True)],
            [_row("dr_no", passed="many")],
            [_row("dr_no", failed=True)],
            [_row("dr_no", rc=None)],
        ],
    )
    def test_malformed_manifest_raises(self, payload: object) -> None:
        """A malformed manifest must be loud.

        Parsing it to ``{}`` would leave every row unmeasured — visually
        identical to an honest seed state, which is exactly how a broken
        measurement pipeline hides.
        """
        with pytest.raises(ValueError):
            parse_gate_manifest(payload)


class TestApplyGateResults:
    def test_passing_row_at_or_above_floor_becomes_ready(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger", COVERAGE_FLOOR)])
        applied = apply_gate_results(sample_roster, results)
        row = next(r for r in applied if r.slug == "goldfinger")
        assert row.status is PackageStatus.READY
        assert row.coverage == COVERAGE_FLOOR

    def test_passing_row_below_floor_is_building_not_ready(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger", COVERAGE_FLOOR - 0.01)])
        applied = apply_gate_results(sample_roster, results)
        row = next(r for r in applied if r.slug == "goldfinger")
        assert row.status is PackageStatus.BUILDING
        assert row.coverage == pytest.approx(COVERAGE_FLOOR - 0.01)

    def test_passing_row_without_coverage_is_building(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger", coverage=None)])
        applied = apply_gate_results(sample_roster, results)
        assert (
            next(r for r in applied if r.slug == "goldfinger").status
            is PackageStatus.BUILDING
        )

    @pytest.mark.parametrize(
        "row",
        [
            _row("goldfinger", 100.0, failed=1),
            _row("goldfinger", 100.0, rc=1),
            _row("goldfinger", 100.0, verdict="fail"),
            _row("goldfinger", 100.0, verdict=""),
        ],
    )
    def test_failing_row_is_red_even_at_full_coverage(
        self, sample_roster, row: dict[str, object]
    ) -> None:
        applied = apply_gate_results(sample_roster, parse_gate_manifest([row]))
        record = next(r for r in applied if r.slug == "goldfinger")
        assert record.status is PackageStatus.RED
        assert record.coverage == 100.0

    def test_row_without_a_gate_result_keeps_the_seed_state(
        self, sample_roster
    ) -> None:
        """Absence of measurement is never reported as a measurement."""
        applied = apply_gate_results(
            sample_roster, parse_gate_manifest([_row("goldfinger", 100.0)])
        )
        untouched = next(r for r in applied if r.slug == "dr_no")
        assert untouched.status is PackageStatus.SCAFFOLDED
        assert untouched.coverage is None

    def test_infrastructure_rows_are_ignored(self, sample_roster) -> None:
        results = parse_gate_manifest(
            [_row("bond-api", 100.0), _row("bond-utilities", 100.0)]
        )
        applied = apply_gate_results(sample_roster, results)
        assert [r.slug for r in applied] == [r.slug for r in sample_roster]
        assert all(r.coverage is None for r in applied)

    def test_input_roster_is_not_mutated(self, sample_roster) -> None:
        before = tuple((r.slug, r.status, r.coverage) for r in sample_roster)
        apply_gate_results(
            sample_roster, parse_gate_manifest([_row("goldfinger", 100.0)])
        )
        assert tuple((r.slug, r.status, r.coverage) for r in sample_roster) == before

    def test_order_and_other_fields_are_preserved(self, sample_roster) -> None:
        applied = apply_gate_results(
            sample_roster, parse_gate_manifest([_row("skyfall", 97.0)])
        )
        assert [r.slug for r in applied] == [r.slug for r in sample_roster]
        skyfall_before = next(r for r in sample_roster if r.slug == "skyfall")
        skyfall_after = next(r for r in applied if r.slug == "skyfall")
        assert skyfall_after.film == skyfall_before.film
        assert skyfall_after.year == skyfall_before.year
        assert skyfall_after.codename == skyfall_before.codename
        assert skyfall_after.concepts == skyfall_before.concepts

    def test_custom_floor_changes_the_verdict(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger", 80.0)])
        assert (
            next(
                r
                for r in apply_gate_results(sample_roster, results, floor=75.0)
                if r.slug == "goldfinger"
            ).status
            is PackageStatus.READY
        )
        assert (
            next(
                r
                for r in apply_gate_results(sample_roster, results, floor=85.0)
                if r.slug == "goldfinger"
            ).status
            is PackageStatus.BUILDING
        )

    def test_applying_is_idempotent(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger", 100.0)])
        once = apply_gate_results(sample_roster, results)
        twice = apply_gate_results(once, results)
        assert once == twice


class TestSummaries:
    def test_measurement_summary_counts_only_roster_rows(self, sample_roster) -> None:
        results = parse_gate_manifest([_row("goldfinger"), _row("bond-api")])
        summary = measurement_summary(sample_roster, results)
        assert (
            summary == f"measured gate output applied to 1 of {len(sample_roster)} rows"
        )

    def test_measurement_summary_says_unmeasured_when_empty(
        self, sample_roster
    ) -> None:
        assert measurement_summary(sample_roster, {}) == UNMEASURED_SUMMARY

    def test_measured_row_summary_reads_the_records(self, sample_roster) -> None:
        assert measured_row_summary(sample_roster) == UNMEASURED_SUMMARY
        applied = apply_gate_results(
            sample_roster, parse_gate_manifest([_row("goldfinger", 100.0)])
        )
        assert measured_row_summary(applied) == (
            f"measured gate output on 1 of {len(sample_roster)} registry rows"
        )


class TestStatusIntegration:
    """Measured rows must flow all the way into the aggregate snapshot."""

    def test_coverage_summary_reports_measured_values(self, sample_roster) -> None:
        from bond_coordinator import build_status

        results = parse_gate_manifest(
            [_row("goldfinger", 100.0), _row("skyfall", 80.0), _row("dr_no", 95.0)]
        )
        status = build_status(apply_gate_results(sample_roster, results))
        assert status.coverage.known == 3
        assert status.coverage.unknown == len(sample_roster) - 3
        assert status.coverage.minimum == 80.0
        assert status.coverage.maximum == 100.0
        assert status.coverage.at_or_above_floor == 2
        assert status.counts_by_status[PackageStatus.READY] == 2
        assert status.counts_by_status[PackageStatus.BUILDING] == 1
