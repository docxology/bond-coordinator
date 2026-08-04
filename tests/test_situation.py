"""Situation-room tests: HTML structure, escaping, determinism, persistence.

The dashboard is deterministic given its inputs, so we assert byte equality
on repeated builds and verify HTML escaping on user-controlled strings.
"""

from __future__ import annotations

from pathlib import Path

from bond_coordinator import (
    Gadget,
    GadgetRegistry,
    PackageStatus,
    build_situation_room,
    build_status,
    write_situation_room,
)
from tests.conftest import FIXED_NOW


class TestStructure:
    def test_contains_identity_and_all_slugs(self, sample_roster, fresh_ledger) -> None:
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, fresh_ledger)
        assert "BOND-COORDINATOR" in html
        assert "MISSION CONTROL" in html
        assert "Situation Room" in html
        for record in sample_roster:
            assert record.slug in html
            assert record.film in html
            assert record.codename in html

    def test_counts_rendered(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        assert "Total packages" in html
        assert "<strong>5</strong>" in html or ">5<" in html

    def test_coverage_dash_when_unmeasured(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        assert "—" in html  # unmeasured coverage renders as an em dash

    def test_empty_gadget_section_message(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, gadgets=GadgetRegistry())
        assert "No gadgets registered yet" in html


class TestGadgets:
    def test_gadgets_and_assets_rendered(
        self, sample_roster, fresh_ledger, sample_gadgets
    ) -> None:
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(
            status, sample_roster, fresh_ledger, gadgets=sample_gadgets
        )
        assert "Aston Martin DB5" in html
        assert "goldfinger" in html
        assert "Little Nellie" in html
        assert "No gadgets registered yet" not in html

    def test_unsafe_gadget_purpose_is_escaped(
        self, sample_roster, fresh_ledger
    ) -> None:
        registry = GadgetRegistry()
        registry.register(
            Gadget(
                name="Evil Gadget",
                film="dr_no",
                purpose="<script>alert('xss')</script>",
            )
        )
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(
            status, sample_roster, fresh_ledger, gadgets=registry
        )
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html


class TestBlockedAndStaleRendering:
    def test_blocked_packages_listed(self, sample_roster) -> None:
        from dataclasses import replace

        roster = (replace(sample_roster[0], status=PackageStatus.RED),) + sample_roster[
            1:
        ]
        status = build_status(roster, now=FIXED_NOW)
        html = build_situation_room(status, roster)
        assert "flagged red" in html
        assert roster[0].slug in html

    def test_dependency_not_ready_note(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW, dependency_ready=False)
        html = build_situation_room(status, sample_roster)
        assert "not yet built" in html


class TestDeterminismAndPersistence:
    def test_byte_identical_across_runs(self, sample_roster, fresh_ledger) -> None:
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        first = build_situation_room(status, sample_roster, fresh_ledger)
        second = build_situation_room(status, sample_roster, fresh_ledger)
        assert first == second

    def test_write_situation_room_creates_file(self, tmp_path, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        target = write_situation_room(
            html, Path(tmp_path) / "nested" / "situation_room.html"
        )
        assert target.is_file()
        assert target.read_text(encoding="utf-8") == html

    def test_write_returns_path(self, tmp_path, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        target = write_situation_room(html, Path(tmp_path) / "out.html")
        assert target.name == "out.html"
