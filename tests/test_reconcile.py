"""Reconcile: registry codename overrides + gadget harvest (pure core tests).

Real-data, zero-mock coverage of :mod:`bond_coordinator.reconcile` plus a
real-films CLI test (subprocess) that reconciles against every built film
package and asserts the exact override count the run itself reports.  The pure
merge tests use synthetic codename deltas (many of the coordinator's
provisional codenames already match the films' real ones); the CLI test
derives its expectation from the manifest the run wrote, so it pins no
sibling's internals while still being able to fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bond_coordinator import (
    FILM_SLUGS,
    Gadget,
    GadgetRegistry,
    get_package,
    subset_roster,
)
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


#: Every film in the registry, not a hand-picked sample.  The previous version
#: of this test reconciled three films — goldfinger, spectre, no_time_to_die —
#: which happen to be three of the films whose declared codename EQUALS the
#: registry's provisional one, so the override path it claimed to exercise was
#: never entered.  Sampling the roster is what let that go unnoticed; the fix
#: is to stop sampling.
REAL_FILMS: tuple[str, ...] = FILM_SLUGS
_BUILT_FILMS = tuple(
    slug for slug in REAL_FILMS if (BOND / slug / "src" / slug / "mission.py").is_file()
)


@pytest.mark.skipif(not _BUILT_FILMS, reason="no film package is built yet (Phase 2)")
def test_reconcile_cli_against_real_films(tmp_path: Path) -> None:
    """The CLI's reported override count must equal the count in its manifest.

    The assertion that used to live here was ``"codenames overridden by film
    declarations:" in result.stdout`` — the label prefix, which matches for
    every possible count including zero, so it could not fail.  The count is
    now *derived* from the manifest the same run wrote (each film-declared
    codename compared against the registry's provisional one) and asserted
    exactly, so a regression that stops counting overrides — for instance
    rendering the report against the already-reconciled roster, which compares
    every declared codename to itself — turns this red.

    Nothing here pins a sibling's codename: the expectation is computed from
    whatever the fleet declares at run time, so a film may rename freely.
    """
    import json as _json
    import subprocess
    import sys

    manifest_path = tmp_path / "reconciled.json"
    result = subprocess.run(
        [
            sys.executable,
            str(BOND / "bond-coordinator" / "scripts" / "reconcile.py"),
            "--slugs",
            *REAL_FILMS,
            "--write",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(BOND / "bond-coordinator"),
        check=False,
    )
    assert result.returncode == 0, result.stderr

    manifest = _json.loads(manifest_path.read_text())
    assert set(REAL_FILMS) <= set(manifest["films"])
    declared = manifest["film_declared"]
    assert declared, (
        "no built film declared a codename; the override contract below would "
        "be vacuous — check that bond-api discovery still works"
    )

    for slug in REAL_FILMS:
        assert f"{slug}:" in result.stdout
        assert slug in declared or slug in manifest["skipped"], (
            f"{slug} neither declared a codename nor was reported skipped"
        )
        assert manifest["films"][slug]["codename"], f"{slug} has no codename at all"

    # Every film that loaded supplied a non-empty codename, and the reconciled
    # roster carries it (not the provisional one).
    overrides = {
        slug: codename
        for slug, codename in declared.items()
        if codename != get_package(slug).codename
    }
    for slug, codename in declared.items():
        assert codename
        assert manifest["films"][slug]["codename"] == codename

    # The exact count, and every individual diff line, must appear on stdout.
    assert f"codenames overridden by film declarations: {len(overrides)}" in (
        result.stdout
    ), result.stdout
    for slug, codename in overrides.items():
        provisional = get_package(slug).codename
        assert f"* {slug}: {provisional} -> {codename} (film-declared)" in (
            result.stdout
        ), f"{slug} override missing from the report"


def _write_film(root: Path, slug: str, body: str) -> None:
    """Materialise a minimal film package tree at ``root/slug/src/slug``."""
    pkg = root / slug / "src" / slug
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mission.py").write_text(body, encoding="utf-8")


_DECLARING_FILM = '''\
"""Synthetic film declaring its own codename (positive control)."""

from bond_api.protocol import MissionBrief


class MissionProvider:
    film = "dr_no"

    def brief(self):
        return MissionBrief(
            film="dr_no", codename="DECLARED CODENAME", objectives=("o",)
        )

    def recon(self, request): ...
    def plan(self, brief): ...
    def execute(self, plan): ...
    def debrief(self, outcome): ...
'''


def test_reconcile_cli_reports_a_real_codename_override(tmp_path: Path) -> None:
    """Positive control: an override must be *visible and counted* on stdout.

    The CLI previously rendered the report against the already-reconciled
    roster, so every declared codename was compared to itself: the
    ``provisional -> declared`` line was unreachable and the override count
    was structurally pinned to 0 no matter how many films overrode.  This
    materialises a film whose declared codename differs from the registry's
    provisional one and asserts both the diff line and the count.
    """
    import subprocess
    import sys

    root = tmp_path / "bond"
    root.mkdir()
    _write_film(root, "dr_no", _DECLARING_FILM)

    result = subprocess.run(
        [
            sys.executable,
            str(BOND / "bond-coordinator" / "scripts" / "reconcile.py"),
            "--slugs",
            "dr_no",
            "--bond-root",
            str(root),
        ],
        capture_output=True,
        text=True,
        cwd=str(BOND / "bond-coordinator"),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    provisional = get_package("dr_no").codename
    assert (
        f"* dr_no: {provisional} -> DECLARED CODENAME (film-declared)" in result.stdout
    ), result.stdout
    assert "codenames overridden by film declarations: 1" in result.stdout


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
