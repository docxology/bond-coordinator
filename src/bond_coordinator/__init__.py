"""bond-coordinator — mission control for the BOND suite.

Layer 2 of the BOND fleet: authoritative registry of the 27 film packages,
the mission-state ledger (brief → recon → plan → execute → debrief), the
aggregate suite-status report, and the situation-room dashboard.

Pure core: no infrastructure imports, stdlib + pyyaml only, deterministic.
"""

from __future__ import annotations

from .ledger import SYSTEM_AGENT, SYSTEM_VERSION, LedgerEntry, MissionLedger, utcnow
from .manuscript_variables import (
    MISSION_LIFECYCLE,
    generate_variables,
    load_config,
    resolve_manuscript_tree,
)
from .reconcile import harvest_gadgets, override_codenames, reconcile_report
from .registry import (
    COORDINATOR_CODENAME,
    FILM_SLUGS,
    ROSTER,
    SUITE_NAME,
    PackageRecord,
    build_roster,
    find_by_status,
    get_package,
    subset_roster,
)
from .situation import build_situation_room, write_situation_room
from .status import (
    COVERAGE_FLOOR,
    DEFAULT_STALE_DAYS,
    SUITE_LAYERS,
    BlockedPackage,
    CoverageSummary,
    LayerSummary,
    SuiteStatus,
    build_status,
    count_by_status,
)
from .types import (
    Asset,
    AssetKind,
    Gadget,
    GadgetRegistry,
    MissionPhase,
    PackageStatus,
)

__version__ = "0.1.0"

__all__ = [
    "COORDINATOR_CODENAME",
    "COVERAGE_FLOOR",
    "DEFAULT_STALE_DAYS",
    "FILM_SLUGS",
    "MISSION_LIFECYCLE",
    "ROSTER",
    "SUITE_LAYERS",
    "SUITE_NAME",
    "SYSTEM_AGENT",
    "SYSTEM_VERSION",
    "Asset",
    "AssetKind",
    "BlockedPackage",
    "CoverageSummary",
    "Gadget",
    "GadgetRegistry",
    "LayerSummary",
    "LedgerEntry",
    "MissionLedger",
    "MissionPhase",
    "PackageRecord",
    "PackageStatus",
    "SuiteStatus",
    "__version__",
    "build_roster",
    "build_situation_room",
    "build_status",
    "count_by_status",
    "find_by_status",
    "generate_variables",
    "get_package",
    "harvest_gadgets",
    "load_config",
    "override_codenames",
    "reconcile_report",
    "resolve_manuscript_tree",
    "subset_roster",
    "utcnow",
    "write_situation_room",
]
