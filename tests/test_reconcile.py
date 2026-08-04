"""Reconcile: registry codename overrides + gadget harvest (pure core tests).

Real-data, zero-mock coverage of :mod:`bond_coordinator.reconcile` plus a
real-films CLI smoke (subprocess) that reconciles against actual film
packages once Phase 2 has built them.  The pure merge tests use synthetic
codename deltas (the coordinator's provisional codenames often already match
the films' real ones); the CLI test asserts real output content.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bond_coordinator import Gadget, GadgetRegistry, subset_roster
from bond_coordinator.reconcile import (
    harvest_gadgets,
    override_codenames,
    reconcile_report,
)

BOND = Path(__file__).resolve().parents[2]


def test_override_codenames_applies_real_codenames(sample_roster) -> None:
    briefs = {
        "goldfinger": {
            "codename": "OVERRIDE-ONE",
            "objectives": "recon the gold market",
        },
        "skyfall": {"codename": "OVERRIDE-TWO", "objectives": "cyber ops"},
    }
    reconciled = override_codenames(sample_roster, briefs)
    by_slug = {record.slug: record for record in reconciled}
    assert by_slug["goldfinger"].codename == "OVERRIDE-ONE"
    assert by_slug["skyfall"].codename == "OVERRIDE-TWO"
    # Unaffected films keep their provisional codenames and every field.
    assert by_slug["dr_no"].codename == "CRAB KEY"
    assert by_slug["dr_no"].year == 1962
    # Order and length preserved.
    assert [r.slug for r in reconciled] == [r.slug for r in sample_roster]


def test_override_codenames_ignores_empty_and_absent(sample_roster) -> None:
    briefs = {"dr_no": {"codename": "", "objectives": "x"}}
    reconciled = override_codenames(sample_roster, briefs)
    assert [r.codename for r in reconciled if r.slug == "dr_no"] == ["CRAB KEY"]
    # No brief at all -> unchanged.
    assert [r.codename for r in reconciled if r.slug == "goldeneye"] == [
        r.codename for r in sample_roster if r.slug == "goldeneye"
    ]


def test_override_codenames_does_not_mutate_input() -> None:
    original = subset_roster(("goldfinger",))
    override_codenames(original, {"goldfinger": {"codename": "NEW", "objectives": "x"}})
    assert original[0].codename == "GRAND SLAM"


def test_harvest_gadgets_merges_and_is_idempotent() -> None:
    source = GadgetRegistry()
    registry = harvest_gadgets(
        source, {"goldfinger": {"market_corner": "corner the gold market"}}
    )
    names = {g.name for g in registry.for_film("goldfinger")}
    assert names == {"market_corner"}
    # Re-running with the same payload replaces in place (no duplicate rows).
    registry = harvest_gadgets(
        registry,
        {
            "goldfinger": {
                "market_corner": "corner the gold market",
                "laser_threat": "burn-through",
            }
        },
    )
    rows = registry.for_film("goldfinger")
    assert {g.name for g in rows} == {"market_corner", "laser_threat"}
    assert all(g.film == "goldfinger" for g in rows)
    # The original source registry is left untouched (pure).
    assert source.count() == 0


def test_harvest_gadgets_empty_purpose_ok() -> None:
    registry = harvest_gadgets(GadgetRegistry(), {"spectre": {"surveillance_net": ""}})
    gadget = registry.lookup("spectre", "surveillance_net")
    assert isinstance(gadget, Gadget)
    assert gadget.purpose == ""


def test_reconcile_report_lists_overrides(sample_roster) -> None:
    briefs = {"goldfinger": {"codename": "OVERRIDE-ONE", "objectives": "o"}}
    text = reconcile_report(sample_roster, briefs)
    assert "goldfinger: GRAND SLAM -> OVERRIDE-ONE (film-declared)" in text
    assert "codenames overridden by film declarations: 1" in text


REAL_FILMS = ("goldfinger", "spectre", "no_time_to_die")
_REAL_FILMS_READY = all(
    (BOND / slug / "src" / slug / "mission.py").is_file() for slug in REAL_FILMS
)


@pytest.mark.skipif(
    not _REAL_FILMS_READY, reason="real film packages not built yet (Phase 2)"
)
def test_reconcile_cli_against_real_films(tmp_path: Path) -> None:
    """The thin CLI reconciles real films: real codenames + gadgets on stdout."""
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            str(BOND / "bond-coordinator" / "scripts" / "reconcile.py"),
            "--slugs",
            *REAL_FILMS,
            "--write",
            str(tmp_path / "reconciled.json"),
        ],
        capture_output=True,
        text=True,
        cwd=str(BOND / "bond-coordinator"),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for slug in REAL_FILMS:
        assert f"{slug}:" in result.stdout
    assert "codenames overridden by film declarations:" in result.stdout

    manifest = (tmp_path / "reconciled.json").read_text()
    assert '"GRAND SLAM"' in manifest  # goldfinger's real codename
    assert "market_corner" in manifest  # goldfinger's harvested gadget
