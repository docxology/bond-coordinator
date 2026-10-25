"""Authoritative registry of the BOND suite's 27 film packages.

Seeded from the BOND fleet roster conventions (film, year, core concepts)
plus coordinator-assigned mission codenames.  This literal is the authority for
the 27-film roster; the fleet-level ``SCOPE.md`` document is not shipped with
this package.

Codename policy
---------------
Mission codenames are **assigned by mission control** (this package) from each
film's canonical plot element (e.g. Goldfinger's Operation Grand Slam → the
``GRAND SLAM`` codename) and are **provisional**: when a film package is built
and declares its own codename via ``bond-api``'s ``MissionBrief``, the
coordinator's codename is overridden at merge time.  Until then the ROSTER is
the single source of truth for the whole fleet.

Status / coverage policy
------------------------
Every row in the shipped ``ROSTER`` literal carries ``status=scaffolded`` and
``coverage=None``.  Those are **seed defaults**, not measurements: they mean
"no gate output has been applied to this record", and they say nothing about
whether the corresponding film package exists, builds, or passes.  A literal
in this file could never be a measurement, which is exactly why measured
values are not written here.

Status and coverage are populated only by
:func:`bond_coordinator.gates.apply_gate_results`, from a ``bond-ops`` gate
aggregate, and every renderer that displays them also states which of the two
it is showing (see ``gates.measurement_summary``).
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import PackageStatus

#: Mission codename of this package (manuscript identity).
COORDINATOR_CODENAME = "MISSION CONTROL"

#: Human-readable suite name.
SUITE_NAME = "PROJECT BOND"


@dataclass(frozen=True)
class PackageRecord:
    """One row of the film-package registry."""

    rank: int  # roster position, 1..27 (canon order)
    slug: str  # directory + git repo + herdr agent name
    film: str  # film title
    year: int  # release year
    codename: str  # coordinator-assigned mission codename (provisional)
    status: PackageStatus  # scaffolded | building | ready | red
    coverage: float | None  # measured line+branch coverage %, or None if unknown
    concepts: tuple[str, ...]  # core concepts → software payload (SCOPE §2.1)


def _record(
    rank: int,
    slug: str,
    film: str,
    year: int,
    codename: str,
    concepts: tuple[str, ...],
) -> PackageRecord:
    """Build a seed record: identity only, status/coverage left unmeasured."""
    return PackageRecord(
        rank=rank,
        slug=slug,
        film=film,
        year=year,
        codename=codename,
        status=PackageStatus.SCAFFOLDED,
        coverage=None,
        concepts=concepts,
    )


#: The 27 film packages, in Eon-canon order (1–25) then non-Eon (26–27),
#: exactly per the fleet roster conventions.
ROSTER: tuple[PackageRecord, ...] = (
    _record(
        1,
        "dr_no",
        "Dr. No",
        1962,
        "CRAB KEY",
        (
            "radiation/isotope forensics",
            "island threat assessment",
        ),
    ),
    _record(
        2,
        "from_russia_with_love",
        "From Russia with Love",
        1963,
        "LEKTOR",
        (
            "entrapment ops",
            "SIGINT interception",
            "defector handoff",
        ),
    ),
    _record(
        3,
        "goldfinger",
        "Goldfinger",
        1964,
        "GRAND SLAM",
        (
            "macroeconomic attack",
            "vault defense",
            "laser threat",
        ),
    ),
    _record(
        4,
        "thunderball",
        "Thunderball",
        1965,
        "THUNDERBALL",
        (
            "underwater ops",
            "nuclear convoy integrity",
        ),
    ),
    _record(
        5,
        "you_only_live_twice",
        "You Only Live Twice",
        1967,
        "BIRD ONE",
        (
            "orbital capture",
            "hidden-base discovery",
        ),
    ),
    _record(
        6,
        "on_her_majestys_secret_service",
        "On Her Majesty's Secret Service",
        1969,
        "BEDLAM",
        (
            "bioweapon dispersion",
            "alpine ops",
            "cover identity",
        ),
    ),
    _record(
        7,
        "diamonds_are_forever",
        "Diamonds Are Forever",
        1971,
        "DIAMOND NET",
        (
            "supply-chain provenance",
            "orbital weapons",
        ),
    ),
    _record(
        8,
        "live_and_let_die",
        "Live and Let Die",
        1973,
        "SAN MONIQUE",
        (
            "narcotics networks",
            "coded comms",
        ),
    ),
    _record(
        9,
        "the_man_with_the_golden_gun",
        "The Man with the Golden Gun",
        1974,
        "SOLEX",
        (
            "solar concentration",
            "lair topology",
            "assassin scheduling",
        ),
    ),
    _record(
        10,
        "the_spy_who_loved_me",
        "The Spy Who Loved Me",
        1977,
        "LIPARUS",
        (
            "submarine tracking",
            "marine forensics",
        ),
    ),
    _record(
        11,
        "moonraker",
        "Moonraker",
        1979,
        "MOONRAKER",
        (
            "orbital logistics",
            "centrifuge ops",
        ),
    ),
    _record(
        12,
        "for_your_eyes_only",
        "For Your Eyes Only",
        1981,
        "ATAC",
        (
            "targeting systems",
            "key recovery",
        ),
    ),
    _record(
        13,
        "octopussy",
        "Octopussy",
        1983,
        "FABERGE",
        (
            "forgery detection",
            "cover logistics",
        ),
    ),
    _record(
        14,
        "a_view_to_a_kill",
        "A View to a Kill",
        1985,
        "MAIN STRIKE",
        (
            "microchip supply chain",
            "urban sabotage",
            "racing analytics",
        ),
    ),
    _record(
        15,
        "the_living_daylights",
        "The Living Daylights",
        1987,
        "LIVING DAYLIGHTS",
        (
            "countersniper optics",
            "defection",
        ),
    ),
    _record(
        16,
        "licence_to_kill",
        "Licence to Kill",
        1989,
        "WAVEKREST",
        (
            "narcotics finance",
            "rogue ops",
        ),
    ),
    _record(
        17,
        "goldeneye",
        "GoldenEye",
        1995,
        "ARKANGEL",
        (
            "orbital EMP",
            "infrastructure resilience",
        ),
    ),
    _record(
        18,
        "tomorrow_never_dies",
        "Tomorrow Never Dies",
        1997,
        "CARVER",
        (
            "media manipulation",
            "stealth",
        ),
    ),
    _record(
        19,
        "the_world_is_not_enough",
        "The World Is Not Enough",
        1999,
        "ELEKTRA",
        (
            "energy infrastructure",
            "hostage psychology",
        ),
    ),
    _record(
        20,
        "die_another_day",
        "Die Another Day",
        2002,
        "ICARUS",
        (
            "identity replacement",
            "extreme-environment ops",
        ),
    ),
    _record(
        21,
        "casino_royale_2006",
        "Casino Royale",
        2006,
        "LE CHIFFRE",
        (
            "game theory",
            "financial crime",
        ),
    ),
    _record(
        22,
        "quantum_of_solace",
        "Quantum of Solace",
        2008,
        "QUANTUM",
        (
            "resource cartels",
            "hydrology",
        ),
    ),
    _record(
        23,
        "skyfall",
        "Skyfall",
        2012,
        "SKYFALL",
        (
            "cyber operations",
            "legacy systems",
        ),
    ),
    _record(
        24,
        "spectre",
        "Spectre",
        2015,
        "NINE EYES",
        (
            "surveillance networks",
            "org intelligence",
        ),
    ),
    _record(
        25,
        "no_time_to_die",
        "No Time to Die",
        2021,
        "HERACLES",
        (
            "DNA-targeted bioweapons",
            "toxicology",
        ),
    ),
    _record(
        26,
        "casino_royale_1967",
        "Casino Royale",
        1967,
        "FIVE BONDS",
        (
            "multi-agent farce",
            "coordination failure",
        ),
    ),
    _record(
        27,
        "never_say_never_again",
        "Never Say Never Again",
        1983,
        "REPLAY",
        (
            "legacy remount",
            "replay",
        ),
    ),
)

#: Slugs of every film package, in roster order.
FILM_SLUGS: tuple[str, ...] = tuple(record.slug for record in ROSTER)


def build_roster() -> tuple[PackageRecord, ...]:
    """Return the full 27-film roster.

    A function (not the bare constant) so callers can never accidentally
    rebind the module-level registry.
    """
    return ROSTER


def subset_roster(slugs: tuple[str, ...] | list[str]) -> tuple[PackageRecord, ...]:
    """Return the roster rows for ``slugs`` in the given order.

    Used to seed deterministic test fixtures from representative films without
    depending on the full 27.  Raises :class:`KeyError` for unknown slugs.
    """
    by_slug = {record.slug: record for record in ROSTER}
    missing = [slug for slug in slugs if slug not in by_slug]
    if missing:
        raise KeyError(f"unknown film package slug(s): {', '.join(sorted(missing))}")
    return tuple(by_slug[slug] for slug in slugs)


def get_package(slug: str) -> PackageRecord:
    """Return the registry record for ``slug`` (raises :class:`KeyError`)."""
    for record in ROSTER:
        if record.slug == slug:
            return record
    raise KeyError(f"no film package with slug {slug!r}")


def find_by_status(status: PackageStatus | str) -> tuple[PackageRecord, ...]:
    """All registry records whose status equals ``status`` (roster order)."""
    target = PackageStatus(status) if isinstance(status, str) else status
    return tuple(record for record in ROSTER if record.status is target)
