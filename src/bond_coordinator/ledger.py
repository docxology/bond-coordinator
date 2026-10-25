"""Mission-state ledger for the BOND suite.

Tracks every film package's mission lifecycle — brief → recon → plan →
execute → debrief — with strict forward-only transition rules and an
append-only audit trail of who/when/version for every transition.

The ledger is a pure core: it never touches the filesystem itself.  JSON
serialization (:meth:`MissionLedger.to_json` / :meth:`MissionLedger.from_json`)
is provided for provenance persistence by thin orchestrators
(``scripts/advance_mission.py``).  It is a local stdlib equivalent of the
conventions ``bond-utilities`` ``mission_io`` already provides — that package
is built; this one has simply not adopted it yet (see ``TODO.md#ledger-io-1``).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .registry import ROSTER, PackageRecord
from .types import MissionPhase

#: Default identity recorded for system-level transitions (registration).
SYSTEM_AGENT = "bond-coordinator"

#: Version string stamped on entries when the caller does not supply one.
SYSTEM_VERSION = "0.0.0"


def _require_forward(slug: str, current: MissionPhase, desired_index: int) -> None:
    """Raise :class:`ValueError` when ``desired_index`` is out of the lifecycle.

    Two rules: no phase exists past ``debrief`` (an ``advance`` from debrief
    yields index 5), and a transition must never move backwards.  Shared by
    :meth:`MissionLedger._transition` and
    :meth:`MissionLedger.validate_transition` so both paths enforce identical
    semantics.
    """
    if desired_index > len(MissionPhase) - 1:
        raise ValueError(f"cannot advance {slug!r} past {MissionPhase.DEBRIEF.value!r}")
    if desired_index < current.phase_index:
        raise ValueError(
            f"illegal transition for {slug!r}: {current.value!r} → "
            f"{MissionPhase(list(MissionPhase)[desired_index]).value!r} "
            "moves the mission backwards"
        )


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime (determinism anchor)."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LedgerEntry:
    """One audit record: a package's phase at a point in time."""

    slug: str
    phase: MissionPhase
    updated_by: str
    updated_at: datetime
    version: str
    note: str | None = None

    def to_dict(self) -> dict[str, str]:
        """JSON-serializable representation (ISO-8601 timestamp)."""
        return {
            "slug": self.slug,
            "phase": self.phase.value,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "note": self.note or "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> LedgerEntry:
        """Rebuild an entry from :meth:`to_dict` output."""
        updated_at = datetime.fromisoformat(str(data["updated_at"]))
        note = data.get("note")
        return cls(
            slug=str(data["slug"]),
            phase=MissionPhase(str(data["phase"])),
            updated_by=str(data["updated_by"]),
            updated_at=updated_at,
            version=str(data["version"]),
            note=str(note) if note else None,
        )


class MissionLedger:
    """Append-only mission-state ledger for the registered film packages.

    Transition rules
    ----------------
    1. A package must be in the registry (``ROSTER`` or an injected roster).
    2. Phases move strictly forward: brief → recon → plan → execute → debrief.
    3. Re-entering the *current* phase is allowed (an idempotent touch that
       re-stamps who/when/version — e.g. a rebuild inside ``building``).
    4. Moving backwards raises :class:`ValueError`.  No phase may be skipped
       when advancing: ``advance`` moves exactly one step; use ``jump`` for
       multi-step advances (still forward-only, still audited).

    Every transition appends to ``history``; the current state per slug is the
    most recent entry.
    """

    def __init__(
        self,
        roster: tuple[PackageRecord, ...] = ROSTER,
        now_fn: Callable[[], datetime] = utcnow,
    ) -> None:
        self._roster = roster
        self._now_fn = now_fn
        self._current: dict[str, LedgerEntry] = {}
        self._history: list[LedgerEntry] = []
        # Register every package at BRIEF (mission control opens the file).
        for record in roster:
            entry = LedgerEntry(
                slug=record.slug,
                phase=MissionPhase.BRIEF,
                updated_by=SYSTEM_AGENT,
                updated_at=now_fn(),
                version=SYSTEM_VERSION,
                note="package registered (phase-0 scaffold)",
            )
            self._current[record.slug] = entry
            self._history.append(entry)

    # ------------------------------------------------------------------ state

    def get(self, slug: str) -> LedgerEntry:
        """Current ledger entry for ``slug`` (raises :class:`KeyError`)."""
        try:
            return self._current[slug]
        except KeyError:
            raise KeyError(
                f"package {slug!r} is not registered in the ledger"
            ) from None

    def all_entries(self) -> list[LedgerEntry]:
        """Current entry for every registered package, sorted by slug."""
        return [
            self._current[record.slug]
            for record in sorted(self._roster, key=lambda r: r.slug)
        ]

    def audit_trail(self, slug: str) -> list[LedgerEntry]:
        """Full append-only history for ``slug`` (raises :class:`KeyError`)."""
        if slug not in self._current:
            raise KeyError(f"package {slug!r} is not registered in the ledger")
        return [entry for entry in self._history if entry.slug == slug]

    @property
    def history(self) -> list[LedgerEntry]:
        """Every recorded transition across all packages (append-only)."""
        return list(self._history)

    # ----------------------------------------------------- audit summaries

    def transition_summary(self) -> dict[MissionPhase, int]:
        """Number of recorded entries per phase across the whole audit trail.

        Includes the initial registration entries (all ``brief``), so the
        counts are the complete append-only picture, not just net moves.
        """
        counts = {phase: 0 for phase in MissionPhase}
        for entry in self._history:
            counts[entry.phase] += 1
        return counts

    def per_agent_summary(self) -> dict[str, int]:
        """Number of recorded transitions per ``updated_by`` identity.

        Keys appear in first-appearance order (deterministic for a given
        history); the system agent's registration entries are included.
        """
        counts: dict[str, int] = {}
        for entry in self._history:
            counts[entry.updated_by] = counts.get(entry.updated_by, 0) + 1
        return counts

    def phase_timeline(self, slug: str) -> list[tuple[str, str]]:
        """Chronological ``(phase, ISO-timestamp)`` history for ``slug``.

        Backs the situation room's per-film mission timeline: one entry per
        recorded transition, oldest first.  Raises :class:`KeyError` for an
        unknown slug.
        """
        if slug not in self._current:
            raise KeyError(f"package {slug!r} is not registered in the ledger")
        return [
            (entry.phase.value, entry.updated_at.isoformat())
            for entry in self._history
            if entry.slug == slug
        ]

    def is_registered(self, slug: str) -> bool:
        """True when ``slug`` has a ledger entry (i.e. is in the roster)."""
        return slug in self._current

    # ------------------------------------------------------------ validation

    @staticmethod
    def _validate_identity(updated_by: str, version: str, note: str | None) -> None:
        """Reject empty identity fields and non-string notes.

        Every transition must be attributable: ``updated_by`` and ``version``
        are non-empty strings, and an optional note must be a string.  Raises
        :class:`ValueError` with the offending field named.
        """
        if not isinstance(updated_by, str) or not updated_by.strip():
            raise ValueError("updated_by must be a non-empty string")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("version must be a non-empty string")
        if note is not None and not isinstance(note, str):
            raise ValueError("note must be a string or None")

    def validate_transition(
        self,
        slug: str,
        target: MissionPhase | str,
        updated_by: str,
        version: str,
        note: str | None = None,
    ) -> None:
        """Validate a prospective transition **without mutating the ledger**.

        Runs the same checks :meth:`jump` would: the slug must be registered,
        the identity fields must be non-empty, and the target phase must be a
        legal forward move from the package's current phase.  Raises
        :class:`KeyError` for an unknown slug and :class:`ValueError` for rule
        violations — a caller can gate a transition before committing it.
        """
        current = self.get(slug)
        self._validate_identity(updated_by, version, note)
        desired = MissionPhase(target) if isinstance(target, str) else target
        _require_forward(slug, current.phase, desired.phase_index)

    # -------------------------------------------------------------- mutation

    def advance(
        self, slug: str, updated_by: str, version: str, note: str | None = None
    ) -> LedgerEntry:
        """Advance ``slug`` exactly one lifecycle phase forward.

        Re-entering the current phase is a touch (see :meth:`touch`); moving
        backwards or skipping phases raises :class:`ValueError`.
        """
        return self._transition(slug, updated_by, version, note, jump=0)

    def jump(
        self,
        slug: str,
        target: MissionPhase | str,
        updated_by: str,
        version: str,
        note: str | None = None,
    ) -> LedgerEntry:
        """Advance ``slug`` to ``target`` phase (multi-step forward only)."""
        return self._transition(
            slug, updated_by, version, note, jump=None, target=target
        )

    def touch(
        self, slug: str, updated_by: str, version: str, note: str | None = None
    ) -> LedgerEntry:
        """Re-stamp the current phase (same-phase re-entry, idempotent)."""
        return self._transition(slug, updated_by, version, note, jump=-1)

    def _transition(
        self,
        slug: str,
        updated_by: str,
        version: str,
        note: str | None,
        jump: int | None,
        target: MissionPhase | str | None = None,
    ) -> LedgerEntry:
        current = self.get(slug)
        self._validate_identity(updated_by, version, note)
        current_index = current.phase.phase_index

        if target is not None:
            desired = MissionPhase(target) if isinstance(target, str) else target
            desired_index = desired.phase_index
        elif jump == -1:
            desired_index = current_index  # touch: same phase
        elif jump == 0:
            desired_index = current_index + 1  # advance: exactly one step
        else:  # defensive; only reachable when a caller passes an invalid jump
            raise ValueError(f"invalid jump {jump!r}")

        _require_forward(slug, current.phase, desired_index)

        phase = MissionPhase(list(MissionPhase)[desired_index])
        entry = LedgerEntry(
            slug=slug,
            phase=phase,
            updated_by=updated_by,
            updated_at=self._now_fn(),
            version=version,
            note=note,
        )
        self._current[slug] = entry
        self._history.append(entry)
        return entry

    # ------------------------------------------------------------ staleness

    def is_stale(
        self, slug: str, stale_days: int = 30, now: datetime | None = None
    ) -> bool:
        """True when ``slug`` has not advanced in ``stale_days`` and is not debriefed.

        A debriefed mission is complete and therefore never stale.  ``now`` is
        injectable for deterministic tests; defaults to the ledger clock.
        """
        entry = self.get(slug)
        if entry.phase is MissionPhase.DEBRIEF:
            return False
        reference = now if now is not None else self._now_fn()
        return (reference - entry.updated_at) > timedelta(days=stale_days)

    # ------------------------------------------------------------ persistence

    def to_json(self) -> str:
        """Serialize current state + full audit history to JSON."""
        payload = {
            "current": {
                slug: entry.to_dict() for slug, entry in sorted(self._current.items())
            },
            "history": [entry.to_dict() for entry in self._history],
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    @classmethod
    def from_json(
        cls,
        data: str,
        roster: tuple[PackageRecord, ...] = ROSTER,
        now_fn: Callable[[], datetime] = utcnow,
    ) -> MissionLedger:
        """Rebuild a ledger from :meth:`to_json` output.

        Validates that every recorded slug exists in ``roster``; raises
        :class:`ValueError` for unknown packages or malformed payloads.
        """
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed ledger JSON: {exc}") from exc
        if (
            not isinstance(payload, dict)
            or "current" not in payload
            or "history" not in payload
        ):
            raise ValueError("ledger JSON must contain 'current' and 'history'")

        ledger = cls.__new__(cls)
        ledger._roster = roster
        ledger._now_fn = now_fn
        ledger._current = {}
        ledger._history = []

        known = {record.slug for record in roster}
        history_rows: list[dict[str, object]] = []
        for row in payload["history"]:
            if not isinstance(row, dict):
                # ValueError (not TypeError): from_json has a single exception
                # contract for every data-validity problem the caller may hit.
                raise ValueError("ledger history entries must be objects")  # noqa: TRY004
            slug = str(row.get("slug", ""))
            if slug not in known:
                raise ValueError(f"ledger references unknown package {slug!r}")
            history_rows.append(row)

        for row in history_rows:
            entry = LedgerEntry.from_dict(row)
            ledger._history.append(entry)
            ledger._current[entry.slug] = entry

        for record in roster:
            if record.slug not in ledger._current:
                raise ValueError(f"ledger is missing current state for {record.slug!r}")
        return ledger
