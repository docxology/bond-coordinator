"""Apply measured gate output to the registry (pure core).

The ``ROSTER`` constant in :mod:`bond_coordinator.registry` is a *seed*: every
row ships with ``status=scaffolded`` and ``coverage=None`` because a literal in
a source file is not a measurement.  Measured values enter the registry only
here, from gate output produced by an actual test run — the fleet aggregate
manifest that ``bond-ops`` writes (``output/aggregate/gate_manifest.json``),
whose rows look like::

    {"package": "goldfinger", "coverage": 100.0, "passed": 167,
     "failed": 0, "rc": 0, "verdict": "ok"}

This module is deliberately pure: :func:`parse_gate_manifest` takes an already
decoded JSON payload and :func:`apply_gate_results` takes a roster plus those
results and returns a new roster.  Reading the file is the thin orchestrators'
job (``scripts/status_report.py``, ``scripts/build_situation_room.py``,
``scripts/z_generate_manuscript_variables.py``).

Status derivation is a *rule*, not a hand-assertion:

* a package with no gate row keeps the seed state (``scaffolded`` / unknown
  coverage) — absence of measurement is never reported as a measurement;
* a row that failed (non-zero ``rc``, any failed test, or a verdict other than
  ``ok``) is ``red``, and its measured coverage is still recorded;
* a passing row at or above the coverage floor is ``ready``;
* a passing row below the floor — or one that reports no coverage number at
  all — is ``building``.

Coverage is treated as a *bounded measurement*, not an arbitrary float: only a
finite value in ``[0, 100]`` percent is a valid coverage, and the test/exit
counts must be non-negative.  A row that violates this is rejected loudly by
:func:`parse_gate_manifest` (a ``ValueError``), never coerced or silently
clamped — a malformed measurement must not become the fleet's ``mean``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace

from .registry import PackageRecord
from .status import COVERAGE_FLOOR
from .types import PackageStatus

__all__ = [
    "GateResult",
    "apply_gate_results",
    "measured_row_summary",
    "measurement_summary",
    "parse_gate_manifest",
]

#: Wording for a roster carrying no measured values at all.  Shared by the
#: dashboard, the status report, and the manuscript token so the three can
#: never disagree about what "unmeasured" looks like.
UNMEASURED_SUMMARY = "none — registry seed defaults (status/coverage unmeasured)"

#: Lower bound of a valid coverage percentage.
MIN_COVERAGE = 0.0
#: Upper bound of a valid coverage percentage (a percentage cannot exceed 100).
MAX_COVERAGE = 100.0


@dataclass(frozen=True)
class GateResult:
    """One package's measured gate outcome."""

    package: str
    coverage: float | None
    passed: int
    failed: int
    returncode: int
    verdict: str

    def __post_init__(self) -> None:
        """Validate the outcome in place (frozen dataclass: raises, no mutation).

        Coverage must be a finite percentage in ``[0, 100]`` or ``None``;
        counts are non-negative.  This runs on construction via
        :func:`parse_gate_manifest` *and* on any programmatic construction,
        so no ``GateResult`` with ``nan``/``inf``/out-of-range coverage or a
        negative count can ever flow into ``apply_gate_results``.
        """
        if self.coverage is not None and not (
            MIN_COVERAGE <= self.coverage <= MAX_COVERAGE
            and math.isfinite(self.coverage)
        ):
            # ValueError (not TypeError): a single exception contract for every
            # data-validity problem a caller may hit.
            raise ValueError(
                f"gate row coverage must be a finite percentage in "
                f"[{MIN_COVERAGE:.0f}, {MAX_COVERAGE:.0f}], got {self.coverage!r}"
            )
        if self.passed < 0 or self.failed < 0 or self.returncode < 0:
            raise ValueError(
                f"gate row counts must be non-negative (passed={self.passed}, "
                f"failed={self.failed}, rc={self.returncode})"
            )
        if not self.package.strip():
            raise ValueError("gate row package must be a non-empty string")

    @property
    def ok(self) -> bool:
        """True when the gate run passed outright (no failures, verdict ok)."""
        return self.failed == 0 and self.returncode == 0 and self.verdict == "ok"


def _coerce_coverage(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):  # bool is an int subclass; not a coverage number
        # ValueError, not TypeError: parse_gate_manifest keeps ONE exception
        # contract for every manifest-validity problem a caller must handle.
        raise ValueError(f"gate row coverage must be a number, got {value!r}")  # noqa: TRY004
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"gate row coverage must be a number or null, got {value!r}")


def _coerce_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(  # noqa: TRY004 — single exception contract, see above
            f"gate row {field} must be an integer, got {value!r}"
        )
    return value


def parse_gate_manifest(payload: object) -> dict[str, GateResult]:
    """Return ``package slug -> GateResult`` from a decoded gate manifest.

    Accepts either the aggregate mapping (``{"packages": [row, ...]}``) or a
    bare list of rows.  Raises :class:`ValueError` for any other shape, for a
    row that is not a mapping, for a row with no ``package`` key, and for a row
    whose numeric fields are not numbers — a malformed manifest must be loud,
    because silently parsing to ``{}`` would report the whole fleet as
    unmeasured and look exactly like an honest seed state.  Range/sanity
    validation (finite coverage in ``[0, 100]``, non-negative counts) is
    applied in :class:`GateResult.__post_init__`.
    """
    if isinstance(payload, Mapping):
        rows: object = payload.get("packages")
        if rows is None:
            raise ValueError("gate manifest mapping has no 'packages' key")
    else:
        rows = payload
    if not isinstance(rows, list):
        raise ValueError(  # noqa: TRY004 — single exception contract, see above
            f"gate manifest 'packages' must be a list, got {type(rows).__name__}"
        )

    results: dict[str, GateResult] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(  # noqa: TRY004 — single exception contract
                f"gate manifest row must be a mapping, got {row!r}"
            )
        name = row.get("package")
        if not isinstance(name, str) or not name:
            raise ValueError(f"gate manifest row has no 'package' name: {row!r}")
        verdict = row.get("verdict", "")
        results[name] = GateResult(
            package=name,
            coverage=_coerce_coverage(row.get("coverage")),
            passed=_coerce_int(row.get("passed", 0), "passed"),
            failed=_coerce_int(row.get("failed", 0), "failed"),
            returncode=_coerce_int(row.get("rc", 0), "rc"),
            verdict=str(verdict),
        )
    return results


def _status_for(result: GateResult, floor: float) -> PackageStatus:
    if not result.ok:
        return PackageStatus.RED
    if result.coverage is not None and result.coverage >= floor:
        return PackageStatus.READY
    return PackageStatus.BUILDING


def apply_gate_results(
    roster: tuple[PackageRecord, ...],
    results: Mapping[str, GateResult],
    floor: float = COVERAGE_FLOOR,
) -> tuple[PackageRecord, ...]:
    """Return ``roster`` with measured status/coverage applied.

    Rows without a matching gate result are returned unchanged, so a partial
    fleet run never overwrites a package's state with a guess.  Gate results
    for packages that are not registry rows (the infrastructure packages share
    the same manifest) are ignored here — they are reported by the layer
    summary, not the film roster.  The input roster is never mutated.
    """
    updated: list[PackageRecord] = []
    for record in roster:
        result = results.get(record.slug)
        if result is None:
            updated.append(record)
            continue
        updated.append(
            replace(
                record,
                status=_status_for(result, floor),
                coverage=result.coverage,
            )
        )
    return tuple(updated)


def measurement_summary(
    roster: tuple[PackageRecord, ...],
    results: Mapping[str, GateResult],
) -> str:
    """One line naming how much of ``roster`` the given results measure.

    Rendered by the situation room and emitted as a manuscript token so a
    reader can always tell whether a status/coverage figure came from a gate
    run or from the registry's unmeasured seed defaults.
    """
    measured = sum(1 for record in roster if record.slug in results)
    if measured == 0:
        return UNMEASURED_SUMMARY
    return f"measured gate output applied to {measured} of {len(roster)} rows"


def measured_row_summary(roster: tuple[PackageRecord, ...]) -> str:
    """One line describing how much of ``roster`` carries measured coverage.

    Derived from the records themselves rather than from a caller-supplied
    label, so a manuscript token can state the provenance of its own numbers
    without anyone being able to hand-author a friendlier answer.
    """
    measured = sum(1 for record in roster if record.coverage is not None)
    if measured == 0:
        return UNMEASURED_SUMMARY
    return f"measured gate output on {measured} of {len(roster)} registry rows"
