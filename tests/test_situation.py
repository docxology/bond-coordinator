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
        """A failed probe reports non-importability, not non-existence."""
        status = build_status(sample_roster, now=FIXED_NOW, dependency_ready=False)
        html = build_situation_room(status, sample_roster)
        assert "not importable in this environment" in html
        assert "pure-core mirror in use" in html
        # The probe measures this interpreter's environment; it must never be
        # rendered as a claim that the sibling package has not been built.
        assert "not yet built" not in html

    def test_dependency_ready_note(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW, dependency_ready=True)
        html = build_situation_room(status, sample_roster)
        assert "importable (protocol available)" in html
        assert "pure-core mirror in use" not in html


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


class TestCoverageHeat:
    def test_heat_buckets_rendered(self, sample_roster) -> None:
        from dataclasses import replace

        roster = (
            (
                replace(sample_roster[0], coverage=95.0),  # >=90 -> ok
                replace(sample_roster[1], coverage=75.0),  # 50..90 -> warn
                replace(sample_roster[2], coverage=40.0),  # <50 -> bad
            )
            + sample_roster[3:]
        )  # remaining coverage None -> unknown
        status = build_status(roster, now=FIXED_NOW)
        html = build_situation_room(status, roster)
        assert 'class="heat-ok"' in html
        assert 'class="heat-warn"' in html
        assert 'class="heat-bad"' in html
        assert 'class="heat-unknown"' in html
        assert "Coverage heat" in html

    def test_unmeasured_coverage_is_unknown(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        assert 'class="heat-unknown"' in html
        assert "—" in html  # unmeasured coverage still renders as an em dash


class TestTimelineBar:
    def test_timeline_column_rendered(self, sample_roster, fresh_ledger) -> None:
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, fresh_ledger)
        assert 'class="timeline"' in html
        assert "tl-now" in html
        assert "tl-todo" in html

    def test_debriefed_package_shows_done_cells(
        self, aged_ledger, sample_roster
    ) -> None:
        status = build_status(sample_roster, aged_ledger, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, aged_ledger)
        assert 'class="tl-done"' in html  # goldfinger is debriefed in aged_ledger


class TestPerFilmGadgets:
    def test_gadgets_grouped_per_film(
        self, sample_roster, fresh_ledger, sample_gadgets
    ) -> None:
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(
            status, sample_roster, fresh_ledger, gadgets=sample_gadgets
        )
        assert 'class="film-group"' in html
        assert "goldfinger — 1 gadget(s)" in html
        assert "have registered gadgets" in html
        # Gadgets for films outside the roster subset are still shown.
        assert "Little Nellie" in html

    def test_empty_gadget_summary(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, gadgets=GadgetRegistry())
        assert "No gadgets registered yet" in html
        assert "tracked films have none" in html


class TestLayersRendering:
    def test_layers_section_rendered(self, sample_roster) -> None:
        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        assert "Suite layers" in html
        assert "layer0" in html
        assert "bond-api" in html
        assert "not probed" in html

    def test_layers_injection_renders_readiness(self, sample_roster) -> None:
        status = build_status(
            sample_roster,
            now=FIXED_NOW,
            dependency_ready=True,
            layer_ready={"layer0": True, "layer4": False},
        )
        html = build_situation_room(status, sample_roster)
        assert "Suite layers" in html
        # films layer shows ready_count/total (no films are READY here).
        assert f"0/{len(sample_roster)} ready" in html
        # Assert the rendered *cell*, not a bare substring: "yes"/"no" occur
        # in ordinary prose, so a substring check here would pass vacuously.
        assert "<td>yes</td>" in html  # layer0 injected True, layer1 inferred True
        assert "<td>no</td>" in html  # layer4 injected False

    def test_empty_layers_omits_the_section(self, sample_roster) -> None:
        """A snapshot carrying no layers renders no layers section at all."""
        from dataclasses import replace as dc_replace

        status = dc_replace(build_status(sample_roster, now=FIXED_NOW), layers=())
        html = build_situation_room(status, sample_roster)
        assert "Suite layers" not in html
        # The rest of the document still renders.
        assert "Film packages" in html
        assert "Recent transitions" in html


class TestStaleThresholdRendering:
    def test_default_threshold_is_reported(self, sample_roster) -> None:
        from bond_coordinator import DEFAULT_STALE_DAYS

        status = build_status(sample_roster, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster)
        assert f"no update in {DEFAULT_STALE_DAYS} days" in html

    def test_custom_threshold_is_reported_not_the_default(self, sample_roster) -> None:
        """The dashboard states the threshold actually applied."""
        status = build_status(sample_roster, now=FIXED_NOW, stale_days=7)
        html = build_situation_room(status, sample_roster)
        assert "no update in 7 days" in html
        assert "no update in 30 days" not in html


class TestAuditTimeline:
    def test_recent_transitions_section(self, sample_roster, fresh_ledger) -> None:
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0", note="recon launch")
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, fresh_ledger)
        assert "Recent transitions" in html
        assert "recon launch" in html
        assert "recorded transitions" in html
        assert "recon" in html

    def test_audit_notes_escaped(self, sample_roster, fresh_ledger) -> None:
        fresh_ledger.advance(
            "goldfinger", "agent-007", "0.1.0", note="<script>x</script>"
        )
        status = build_status(sample_roster, fresh_ledger, now=FIXED_NOW)
        html = build_situation_room(status, sample_roster, fresh_ledger)
        assert "<script>x</script>" not in html
        assert "&lt;script&gt;" in html
