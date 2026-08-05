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
    gadget_purpose,
    harvest_gadgets,
    override_codenames,
    reconcile_report,
)

BOND = Path(__file__).resolve().parents[2]


class TestGadgetPurpose:
    """Purpose derivation must never borrow a builtin's docstring.

    Regression guard: harvesting once read ``payload.__doc__`` directly, which
    Python resolves to the *type's* docstring for plain-data payloads.  Real
    harvest output carried 19 gadgets whose recorded purpose was
    ``"dict() -> new empty dictionary"`` or ``"Built-in mutable sequence."`` —
    CPython attributes presented as film-declared provenance.
    """

    def test_function_contributes_its_own_first_docstring_line(self) -> None:
        def isotope_library() -> dict[str, float]:
            """Return the immutable isotope library keyed by isotope name.

            Second paragraph is not part of the one-line purpose.
            """
            return {}

        assert (
            gadget_purpose(isotope_library)
            == "Return the immutable isotope library keyed by isotope name."
        )

    def test_class_contributes_its_own_docstring(self) -> None:
        class DispersionModel:
            """Gamma plume dispersion over Crab Key."""

        assert (
            gadget_purpose(DispersionModel) == "Gamma plume dispersion over Crab Key."
        )

    def test_documented_shape_without_docstring_is_empty(self) -> None:
        def undocumented() -> None:
            return None

        assert gadget_purpose(undocumented) == ""

    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            ({"a": 1.0, "b": 2.0}, "data payload: dict of 2 entries"),
            ({"only": 1}, "data payload: dict of 1 entry"),
            ({}, "data payload: dict of 0 entries"),
            (["low", "high"], "data payload: list of 2 entries"),
            (("stable", "unstable", "mixed"), "data payload: tuple of 3 entries"),
            (frozenset({"a"}), "data payload: frozenset of 1 entry"),
            (7, "data payload: int"),
            (3.5, "data payload: float"),
            (None, "data payload: NoneType"),
        ],
    )
    def test_plain_data_gets_a_factual_shape_summary(
        self, payload: object, expected: str
    ) -> None:
        assert gadget_purpose(payload) == expected

    @pytest.mark.parametrize(
        "payload",
        [{"a": 1}, ["x"], ("y",), 7, 3.5, None, frozenset({"z"})],
    )
    def test_plain_data_never_returns_a_builtin_docstring(
        self, payload: object
    ) -> None:
        """The exact failure that produced the fabricated harvest output."""
        borrowed = getattr(payload, "__doc__", None)
        derived = gadget_purpose(payload)
        assert derived != borrowed
        assert "Built-in" not in derived
        assert "-> new empty" not in derived

    def test_string_payload_is_the_films_own_words(self) -> None:
        assert gadget_purpose("decodes voodoo-coded traffic") == (
            "decodes voodoo-coded traffic"
        )

    def test_blank_string_payload_is_empty(self) -> None:
        assert gadget_purpose("   \n  ") == ""

    def test_multiline_string_payload_takes_the_first_line(self) -> None:
        assert gadget_purpose("first line\nsecond line") == "first line"

    def test_module_contributes_its_docstring(self) -> None:
        from bond_coordinator import reconcile as module

        assert gadget_purpose(module).startswith("Reconcile the coordinator")

    def test_purpose_is_deterministic(self) -> None:
        payload = {"a": 1, "b": 2}
        assert gadget_purpose(payload) == gadget_purpose(payload)


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

    # Assert the coordinator's contract against whatever the fleet's real state
    # is right now, rather than pinning a sibling's internals: every requested
    # film appears in the manifest, and each one either loaded (declaring a
    # codename) or was reported as skipped.  A sibling mid-edit must not turn
    # this package's suite red — that is exactly the isolation being tested.
    import json as _json

    manifest = _json.loads((tmp_path / "reconciled.json").read_text())
    assert set(REAL_FILMS) <= set(manifest["films"])
    declared = manifest["film_declared"]
    for slug in REAL_FILMS:
        assert slug in declared or slug in manifest["skipped"], (
            f"{slug} neither declared a codename nor was reported skipped"
        )
        assert manifest["films"][slug]["codename"], f"{slug} has no codename at all"
    for slug, codename in declared.items():
        # A film that loaded must have supplied a real, non-empty codename,
        # and the reconciled roster must carry it.
        assert codename
        assert manifest["films"][slug]["codename"] == codename


def _write_film(root: Path, slug: str, body: str) -> None:
    """Materialise a minimal film package tree at ``root/slug/src/slug``."""
    pkg = root / slug / "src" / slug
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mission.py").write_text(body, encoding="utf-8")


def test_reconcile_isolates_a_broken_film(tmp_path: Path) -> None:
    """A film that explodes on import must not abort the fleet-wide run.

    Positive control for the per-film guard: ``broken`` raises ``NameError``
    at module level — an exception class the guard once did not catch, which
    made a single half-edited sibling abort reconciliation for all 27 films.
    """
    import subprocess
    import sys

    root = tmp_path / "bond"
    root.mkdir()
    _write_film(
        root, "goldfinger", "GADGETS = {'market_corner': 'corner the market'}\n"
    )
    _write_film(
        root, "skyfall", "raise NameError(\"name 'TypedDict' is not defined\")\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(BOND / "bond-coordinator" / "scripts" / "reconcile.py"),
            "--slugs",
            "goldfinger",
            "skyfall",
            "--bond-root",
            str(root),
            "--gadgets",
            str(tmp_path / "gadgets.json"),
        ],
        capture_output=True,
        text=True,
        cwd=str(BOND / "bond-coordinator"),
        check=False,
    )

    # The run completes despite the broken film.
    assert result.returncode == 0, result.stderr
    # The breakage is reported, not swallowed.
    assert "skyfall" in result.stderr
    assert "NameError" in result.stderr
    # The healthy film's gadget still made it through, with the film's own words.
    import json as _json

    gadgets = _json.loads((tmp_path / "gadgets.json").read_text())
    harvested = {(g["film"], g["name"]): g["purpose"] for g in gadgets}
    assert harvested[("goldfinger", "market_corner")] == "corner the market"
    assert not any(film == "skyfall" for film, _ in harvested)


def test_reconcile_harvests_no_builtin_docstrings_from_a_real_film(
    tmp_path: Path,
) -> None:
    """End-to-end guard on the fabricated-purpose defect.

    A film registering plain-data payloads must never have CPython's own
    docstrings recorded as its declared gadget purposes.
    """
    import json as _json
    import subprocess
    import sys

    root = tmp_path / "bond"
    root.mkdir()
    _write_film(
        root,
        "dr_no",
        "GADGETS = {\n"
        "    'inhalation_dcf': {'Cs-137': 1.0, 'Sr-90': 2.0},\n"
        "    'stability_classes': ('A', 'B', 'C'),\n"
        "}\n",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(BOND / "bond-coordinator" / "scripts" / "reconcile.py"),
            "--slugs",
            "dr_no",
            "--bond-root",
            str(root),
            "--gadgets",
            str(tmp_path / "gadgets.json"),
        ],
        capture_output=True,
        text=True,
        cwd=str(BOND / "bond-coordinator"),
        check=False,
    )
    assert result.returncode == 0, result.stderr

    purposes = {
        g["name"]: g["purpose"]
        for g in _json.loads((tmp_path / "gadgets.json").read_text())
    }
    assert purposes["inhalation_dcf"] == "data payload: dict of 2 entries"
    assert purposes["stability_classes"] == "data payload: tuple of 3 entries"
    for purpose in purposes.values():
        assert "Built-in" not in purpose
        assert "new empty dictionary" not in purpose
