"""Pytest configuration for bond-coordinator tests.

Zero-mock policy: every test uses real data, real computation, and real
files.  The only "fixture" is a deterministic 5-film subset of the real
27-film registry (representative canon spread: early, mid, and modern
packages), so tests never depend on the whole fleet being built.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Force headless backend (kept for parity with the template contract; the
# coordinator core has no plotting, so this is belt-and-braces).
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_coordinator import Gadget, GadgetRegistry, subset_roster

#: Representative film slugs used by the deterministic test fixture.
SAMPLE_SLUGS: tuple[str, ...] = (
    "dr_no",
    "goldfinger",
    "goldeneye",
    "skyfall",
    "no_time_to_die",
)

#: Fixed reference clock for all time-dependent assertions.
FIXED_NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_slugs() -> tuple[str, ...]:
    """The 5 representative film slugs."""
    return SAMPLE_SLUGS


@pytest.fixture
def sample_roster(sample_slugs: tuple[str, ...]):
    """Deterministic 5-film registry subset (real records, real concepts)."""
    return subset_roster(sample_slugs)


@pytest.fixture
def fixed_clock():
    """A clock function pinned to :data:`FIXED_NOW`."""
    return lambda: FIXED_NOW


@pytest.fixture
def sample_gadgets() -> GadgetRegistry:
    """Q-branch gadgets for two of the representative films."""
    from bond_coordinator import Asset, AssetKind

    registry = GadgetRegistry()
    registry.register(
        Gadget(
            name="Aston Martin DB5",
            film="goldfinger",
            purpose="armored transport with countermeasures",
            assets=(
                Asset("ejector seat", AssetKind.GADGET, "pilot ejection"),
                Asset("machine guns", AssetKind.GADGET, "forward-firing armament"),
            ),
        )
    )
    registry.register(
        Gadget(
            name="Golden Gun",
            film="the_man_with_the_golden_gun",
            purpose="disassembled assassin pistol",
        )
    )
    registry.register(
        Gadget(
            name="Little Nellie",
            film="you_only_live_twice",
            purpose="autogyro reconnaissance platform",
        )
    )
    return registry


@pytest.fixture
def fresh_ledger(sample_roster, fixed_clock):
    """A ledger over the 5-film roster pinned to the fixed clock."""
    from bond_coordinator import MissionLedger

    return MissionLedger(sample_roster, now_fn=fixed_clock)


@pytest.fixture
def aged_ledger(sample_roster):
    """A ledger whose entries were all stamped 45 days before FIXED_NOW."""
    from bond_coordinator import MissionLedger

    def past_clock() -> datetime:
        return FIXED_NOW - timedelta(days=45)

    ledger = MissionLedger(sample_roster, now_fn=past_clock)
    # Move goldfinger to a finished state (debriefed) so staleness logic
    # distinguishes "complete" from "abandoned".
    ledger.jump("goldfinger", "debrief", "operator", "0.1.0")
    return ledger
