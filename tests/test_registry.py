"""Registry tests: the authoritative 27-film ROSTER and the gadget registry.

Uses the deterministic 5-film fixture for behavior, plus direct assertions
on the full roster for completeness/identity guarantees.
"""

from __future__ import annotations

import re

import pytest

from bond_coordinator import (
    FILM_SLUGS,
    ROSTER,
    Asset,
    AssetKind,
    Gadget,
    GadgetRegistry,
    PackageStatus,
    build_roster,
    find_by_status,
    get_package,
    subset_roster,
)
from bond_coordinator.registry import COORDINATOR_CODENAME, SUITE_NAME


class TestRosterCompleteness:
    """The ROSTER must be exactly SCOPE.md §2.1: 27 unique, canon-ordered."""

    def test_roster_has_27_packages(self) -> None:
        assert len(ROSTER) == 27

    def test_roster_ranks_are_sequential(self) -> None:
        assert [record.rank for record in ROSTER] == list(range(1, 28))

    def test_slugs_unique_and_well_formed(self) -> None:
        slugs = [record.slug for record in ROSTER]
        assert len(slugs) == len(set(slugs))
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for slug in slugs:
            assert pattern.match(slug), f"slug {slug!r} is not well-formed"

    def test_film_slugs_match_roster_order(self) -> None:
        assert FILM_SLUGS == tuple(record.slug for record in ROSTER)

    def test_canon_bookends(self) -> None:
        assert ROSTER[0].slug == "dr_no"
        assert ROSTER[0].year == 1962
        assert ROSTER[-1].slug == "never_say_never_again"

    def test_every_record_has_identity_fields(self) -> None:
        for record in ROSTER:
            assert record.film
            assert 1960 <= record.year <= 2025
            assert record.codename
            assert record.concepts

    def test_all_records_start_scaffolded_without_measured_coverage(self) -> None:
        for record in ROSTER:
            assert record.status is PackageStatus.SCAFFOLDED
            assert record.coverage is None

    def test_codenames_are_assigned_and_plot_anchored(self) -> None:
        by_slug = {record.slug: record for record in ROSTER}
        assert by_slug["goldfinger"].codename == "GRAND SLAM"
        assert by_slug["no_time_to_die"].codename == "HERACLES"
        assert by_slug["skyfall"].codename == "SKYFALL"

    def test_known_roster_membership(self) -> None:
        slugs = set(FILM_SLUGS)
        for expected in (
            "dr_no",
            "goldfinger",
            "goldeneye",
            "skyfall",
            "no_time_to_die",
            "casino_royale_1967",
            "on_her_majestys_secret_service",
        ):
            assert expected in slugs


class TestRosterAccessors:
    def test_build_roster_returns_full_registry(self) -> None:
        assert build_roster() == ROSTER
        assert isinstance(build_roster(), tuple)

    def test_get_package_found(self) -> None:
        record = get_package("goldfinger")
        assert record.film == "Goldfinger"
        assert record.codename == "GRAND SLAM"

    def test_get_package_missing_raises(self) -> None:
        with pytest.raises(KeyError):
            get_package("blofeld_unknown")

    def test_find_by_status_all_scaffolded(self) -> None:
        matches = find_by_status(PackageStatus.SCAFFOLDED)
        assert len(matches) == 27
        assert all(record.status is PackageStatus.SCAFFOLDED for record in matches)

    def test_find_by_status_string_coercion(self) -> None:
        assert len(find_by_status("ready")) == 0

    def test_find_by_status_empty_ready(self) -> None:
        assert find_by_status(PackageStatus.READY) == ()


class TestSubsetRoster:
    def test_five_representative_films(self, sample_roster, sample_slugs) -> None:
        assert tuple(record.slug for record in sample_roster) == sample_slugs
        assert len(sample_roster) == 5

    def test_subset_preserves_real_record_data(self, sample_roster) -> None:
        goldfinger = sample_roster[1]
        assert goldfinger.film == "Goldfinger"
        assert goldfinger.codename == "GRAND SLAM"
        assert "macroeconomic attack" in goldfinger.concepts

    def test_subset_unknown_slug_raises(self) -> None:
        with pytest.raises(KeyError):
            subset_roster(["goldfinger", "not_a_film"])

    def test_subset_empty(self) -> None:
        assert subset_roster([]) == ()


class TestCoordinatorIdentity:
    def test_codename(self) -> None:
        assert COORDINATOR_CODENAME == "MISSION CONTROL"

    def test_suite_name(self) -> None:
        assert SUITE_NAME == "PROJECT BOND"


class TestGadgetRegistry:
    def test_constructor_seeds_from_iterable(self) -> None:
        gadgets = [
            Gadget(name="DB5", film="goldfinger", purpose="transport"),
            Gadget(name="Lektor", film="from_russia_with_love", purpose="decryption"),
        ]
        registry = GadgetRegistry(gadgets)
        assert registry.count() == 2
        assert registry.lookup("goldfinger", "DB5").name == "DB5"

    def test_register_and_lookup(self, sample_gadgets) -> None:
        gadget = sample_gadgets.lookup("goldfinger", "Aston Martin DB5")
        assert gadget.film == "goldfinger"
        assert "countermeasures" in gadget.purpose
        assert sample_gadgets.count() == 3

    def test_lookup_missing_raises(self, sample_gadgets) -> None:
        with pytest.raises(KeyError):
            sample_gadgets.lookup("goldfinger", "nonexistent")

    def test_duplicate_register_raises(self, sample_gadgets) -> None:
        with pytest.raises(ValueError):
            sample_gadgets.register(
                Gadget(name="Aston Martin DB5", film="goldfinger", purpose="duplicate")
            )

    def test_for_film_sorted(self, sample_gadgets) -> None:
        assert [g.name for g in sample_gadgets.for_film("goldfinger")] == [
            "Aston Martin DB5"
        ]
        assert sample_gadgets.for_film("dr_no") == []

    def test_all_sorted_by_film_then_name(self, sample_gadgets) -> None:
        names = [(g.film, g.name) for g in sample_gadgets.all()]
        assert names == sorted(names)

    def test_gadget_carries_assets(self) -> None:
        gadget = Gadget(
            name="Ejector Seat",
            film="goldfinger",
            purpose="escape",
            assets=(Asset("seat", AssetKind.TRANSPORT, "ejects pilot"),),
        )
        assert gadget.assets[0].kind is AssetKind.TRANSPORT

    def test_asset_kind_values(self) -> None:
        assert AssetKind.GADGET.value == "gadget"
        assert AssetKind.TRANSPORT.value == "transport"
        assert AssetKind.COVER.value == "cover"
