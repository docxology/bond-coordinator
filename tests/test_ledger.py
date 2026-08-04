"""Mission-ledger tests: lifecycle transitions, audit trail, staleness, JSON.

Every assertion runs against the deterministic 5-film fixture with an
injected clock — no wall-clock dependence anywhere.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from bond_coordinator import (
    SYSTEM_AGENT,
    SYSTEM_VERSION,
    MissionLedger,
    MissionPhase,
)
from bond_coordinator.ledger import LedgerEntry

FIXED_NOW = __import__("tests.conftest", fromlist=["FIXED_NOW"]).FIXED_NOW


class TestInitialization:
    def test_every_registered_package_starts_at_brief(
        self, fresh_ledger, sample_roster
    ) -> None:
        for record in sample_roster:
            entry = fresh_ledger.get(record.slug)
            assert entry.phase is MissionPhase.BRIEF
            assert entry.updated_by == SYSTEM_AGENT
            assert entry.version == SYSTEM_VERSION

    def test_all_entries_sorted_by_slug(self, fresh_ledger, sample_roster) -> None:
        slugs = [entry.slug for entry in fresh_ledger.all_entries()]
        assert slugs == sorted(record.slug for record in sample_roster)
        assert len(slugs) == 5

    def test_initial_audit_trail_has_one_entry(self, fresh_ledger) -> None:
        assert len(fresh_ledger.audit_trail("goldfinger")) == 1
        assert len(fresh_ledger.history) == 5

    def test_unknown_slug_raises_on_get(self, fresh_ledger) -> None:
        with pytest.raises(KeyError):
            fresh_ledger.get("not_a_film")

    def test_is_registered(self, fresh_ledger) -> None:
        assert fresh_ledger.is_registered("goldfinger")
        assert not fresh_ledger.is_registered("blofeld_unknown")


class TestTransitions:
    def test_advance_moves_exactly_one_phase(self, fresh_ledger) -> None:
        entry = fresh_ledger.advance(
            "goldfinger", "agent-007", "0.1.0", note="recon launched"
        )
        assert entry.phase is MissionPhase.RECON
        assert fresh_ledger.get("goldfinger").phase is MissionPhase.RECON
        assert entry.updated_by == "agent-007"
        assert entry.note == "recon launched"

    def test_full_lifecycle_walk(self, fresh_ledger) -> None:
        phases = [p for p in MissionPhase]
        for index in range(1, len(phases)):
            fresh_ledger.advance("skyfall", "agent-007", "0.1.0")
            assert fresh_ledger.get("skyfall").phase is phases[index]
        assert len(fresh_ledger.audit_trail("skyfall")) == len(phases)

    def test_advance_past_debrief_raises(self, fresh_ledger) -> None:
        fresh_ledger.jump("goldfinger", "debrief", "agent-007", "0.1.0")
        with pytest.raises(ValueError):
            fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")

    def test_touch_re_stamps_same_phase(self, fresh_ledger, fixed_clock) -> None:
        original = fresh_ledger.get("goldfinger")
        touched = fresh_ledger.touch(
            "goldfinger", "agent-007", "0.2.0", note="re-briefed"
        )
        assert touched.phase is MissionPhase.BRIEF
        assert touched.updated_by == "agent-007"
        assert touched.version == "0.2.0"
        assert touched.updated_at == fixed_clock()
        assert len(fresh_ledger.audit_trail("goldfinger")) == 2
        assert fresh_ledger.get("goldfinger") is not original

    def test_jump_to_same_phase_is_allowed(self, fresh_ledger) -> None:
        entry = fresh_ledger.jump("goldfinger", "brief", "agent-007", "0.1.0")
        assert entry.phase is MissionPhase.BRIEF

    def test_jump_allows_multi_step_forward(self, fresh_ledger) -> None:
        entry = fresh_ledger.jump(
            "goldfinger", MissionPhase.EXECUTE, "agent-007", "0.1.0"
        )
        assert entry.phase is MissionPhase.EXECUTE
        assert len(fresh_ledger.audit_trail("goldfinger")) == 2

    def test_jump_accepts_string_phase(self, fresh_ledger) -> None:
        entry = fresh_ledger.jump("goldfinger", "debrief", "agent-007", "0.1.0")
        assert entry.phase is MissionPhase.DEBRIEF

    def test_jump_to_earlier_phase_raises(self, fresh_ledger) -> None:
        fresh_ledger.jump("goldfinger", "plan", "agent-007", "0.1.0")
        with pytest.raises(ValueError, match="backwards"):
            fresh_ledger.jump("goldfinger", "brief", "agent-007", "0.1.0")

    def test_transition_unknown_slug_raises(self, fresh_ledger) -> None:
        with pytest.raises(KeyError):
            fresh_ledger.advance("not_a_film", "agent-007", "0.1.0")

    def test_clock_is_used_for_timestamps(self, fresh_ledger, fixed_clock) -> None:
        entry = fresh_ledger.advance("dr_no", "agent-007", "0.1.0")
        assert entry.updated_at == fixed_clock()


class TestAuditTrail:
    def test_history_is_append_only_and_ordered(self, fresh_ledger) -> None:
        fresh_ledger.advance("dr_no", "agent-007", "0.1.0")
        fresh_ledger.advance("dr_no", "agent-007", "0.1.0")
        trail = fresh_ledger.audit_trail("dr_no")
        assert [entry.phase for entry in trail] == [
            MissionPhase.BRIEF,
            MissionPhase.RECON,
            MissionPhase.PLAN,
        ]
        assert trail[0].updated_at <= trail[-1].updated_at

    def test_audit_trail_unknown_slug_raises(self, fresh_ledger) -> None:
        with pytest.raises(KeyError):
            fresh_ledger.audit_trail("not_a_film")


class TestStaleness:
    def test_fresh_mission_not_stale(self, fresh_ledger) -> None:
        assert not fresh_ledger.is_stale("dr_no", stale_days=30, now=FIXED_NOW)

    def test_aged_unfinished_mission_is_stale(self, aged_ledger) -> None:
        assert aged_ledger.is_stale("dr_no", stale_days=30, now=FIXED_NOW)

    def test_aged_mission_within_threshold_not_stale(self, aged_ledger) -> None:
        assert not aged_ledger.is_stale("dr_no", stale_days=60, now=FIXED_NOW)

    def test_debriefed_mission_never_stale(self, aged_ledger) -> None:
        assert not aged_ledger.is_stale("goldfinger", stale_days=1, now=FIXED_NOW)

    def test_staleness_uses_injected_now(self, fresh_ledger) -> None:
        later = FIXED_NOW + timedelta(days=400)
        assert fresh_ledger.is_stale("dr_no", stale_days=30, now=later)


class TestPersistence:
    def test_json_roundtrip_preserves_state_and_history(
        self, fresh_ledger, sample_roster
    ) -> None:
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")
        fresh_ledger.jump("skyfall", "debrief", "agent-007", "0.1.0", note="done")
        payload = fresh_ledger.to_json()
        restored = MissionLedger.from_json(payload, roster=sample_roster)
        assert restored.get("goldfinger").phase is MissionPhase.RECON
        assert restored.get("skyfall").phase is MissionPhase.DEBRIEF
        assert len(restored.history) == len(fresh_ledger.history)
        assert restored.audit_trail("skyfall")[-1].note == "done"

    def test_from_json_rejects_unknown_package(
        self, fresh_ledger, sample_roster
    ) -> None:
        payload = fresh_ledger.to_json()
        with pytest.raises(ValueError, match="unknown package"):
            MissionLedger.from_json(
                payload, roster=sample_roster[:1] + sample_roster[2:]
            )

    def test_from_json_rejects_malformed_json(self) -> None:
        with pytest.raises(ValueError, match="malformed"):
            MissionLedger.from_json("{not json")

    def test_from_json_rejects_missing_sections(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="current"):
            MissionLedger.from_json('{"history": []}')

    def test_from_json_rejects_non_object_history(self) -> None:
        with pytest.raises(ValueError, match="objects"):
            MissionLedger.from_json('{"current": {}, "history": ["not-an-object"]}')

    def test_from_json_rejects_incomplete_current_state(self, sample_roster) -> None:
        entry = LedgerEntry(
            slug="goldfinger",
            phase=MissionPhase.BRIEF,
            updated_by="system",
            updated_at=FIXED_NOW,
            version="0.1.0",
        )
        payload = json.dumps(
            {"current": {"goldfinger": entry.to_dict()}, "history": [entry.to_dict()]}
        )
        with pytest.raises(ValueError, match="missing current state"):
            MissionLedger.from_json(payload, roster=sample_roster)

    def test_to_json_is_deterministic(self, fresh_ledger) -> None:
        fresh_ledger.advance("dr_no", "agent-007", "0.1.0")
        assert fresh_ledger.to_json() == fresh_ledger.to_json()


class TestEntryCodec:
    def test_entry_roundtrip(self) -> None:
        entry = LedgerEntry(
            slug="goldfinger",
            phase=MissionPhase.RECON,
            updated_by="agent-007",
            updated_at=FIXED_NOW,
            version="0.1.0",
            note="watching Fort Knox",
        )
        restored = LedgerEntry.from_dict(entry.to_dict())
        assert restored == entry
        assert restored.updated_at == FIXED_NOW

    def test_entry_note_defaults_to_none(self) -> None:
        entry = LedgerEntry(
            slug="goldfinger",
            phase=MissionPhase.BRIEF,
            updated_by="system",
            updated_at=FIXED_NOW,
            version="0.0.0",
        )
        assert entry.note is None
        assert entry.to_dict()["note"] == ""


class TestTransitionValidation:
    def test_validate_transition_ok(self, fresh_ledger) -> None:
        fresh_ledger.validate_transition("goldfinger", "recon", "agent-007", "0.1.0")
        # Same-phase target is a legal forward (non-moving) check.
        fresh_ledger.validate_transition("goldfinger", "brief", "agent-007", "0.1.0")
        # Validation never mutates the ledger.
        assert fresh_ledger.get("goldfinger").phase is MissionPhase.BRIEF

    def test_validate_transition_accepts_enum(self, fresh_ledger) -> None:
        fresh_ledger.jump("goldfinger", "recon", "agent-007", "0.1.0")
        fresh_ledger.validate_transition(
            "goldfinger", MissionPhase.PLAN, "agent-007", "0.1.0"
        )

    def test_validate_transition_backwards_raises(self, fresh_ledger) -> None:
        fresh_ledger.jump("goldfinger", "plan", "agent-007", "0.1.0")
        with pytest.raises(ValueError, match="backwards"):
            fresh_ledger.validate_transition(
                "goldfinger", "brief", "agent-007", "0.1.0"
            )

    def test_validate_transition_unknown_slug_raises(self, fresh_ledger) -> None:
        with pytest.raises(KeyError):
            fresh_ledger.validate_transition(
                "not_a_film", "recon", "agent-007", "0.1.0"
            )

    def test_validate_transition_empty_updated_by_raises(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="updated_by"):
            fresh_ledger.validate_transition("goldfinger", "recon", "", "0.1.0")

    def test_validate_transition_blank_version_raises(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="version"):
            fresh_ledger.validate_transition("goldfinger", "recon", "agent-007", "  ")

    def test_validate_transition_non_string_note_raises(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="note"):
            fresh_ledger.validate_transition(
                "goldfinger", "recon", "agent-007", "0.1.0", note=5
            )

    def test_validate_transition_bad_target_raises(self, fresh_ledger) -> None:
        with pytest.raises(ValueError):
            fresh_ledger.validate_transition("goldfinger", "not_a_phase", "a", "0.1.0")


class TestIdentityValidationOnMutation:
    def test_advance_rejects_empty_updated_by(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="updated_by"):
            fresh_ledger.advance("goldfinger", "   ", "0.1.0")

    def test_advance_rejects_empty_version(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="version"):
            fresh_ledger.advance("goldfinger", "agent-007", "")

    def test_touch_rejects_non_string_note(self, fresh_ledger) -> None:
        with pytest.raises(ValueError, match="note"):
            fresh_ledger.touch("goldfinger", "agent-007", "0.1.0", note=123)


class TestAuditSummaries:
    def test_transition_summary_counts_all_entries(self, fresh_ledger) -> None:
        summary = fresh_ledger.transition_summary()
        assert summary[MissionPhase.BRIEF] == 5
        assert summary[MissionPhase.RECON] == 0
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")
        fresh_ledger.jump("skyfall", "debrief", "agent-007", "0.1.0")
        summary = fresh_ledger.transition_summary()
        assert summary[MissionPhase.BRIEF] == 5  # registrations remain
        assert summary[MissionPhase.RECON] == 1
        assert summary[MissionPhase.DEBRIEF] == 1

    def test_per_agent_summary(self, fresh_ledger) -> None:
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")
        fresh_ledger.jump("skyfall", "debrief", "q-branch", "0.1.0")
        summary = fresh_ledger.per_agent_summary()
        assert summary[SYSTEM_AGENT] == 5
        assert summary["agent-007"] == 2
        assert summary["q-branch"] == 1

    def test_phase_timeline_is_chronological(self, fresh_ledger, fixed_clock) -> None:
        fresh_ledger.advance("goldfinger", "agent-007", "0.1.0")
        fresh_ledger.advance("goldfinger", "agent-007", "0.2.0")
        timeline = fresh_ledger.phase_timeline("goldfinger")
        assert [phase for phase, _ in timeline] == ["brief", "recon", "plan"]
        assert all(ts == fixed_clock().isoformat() for _, ts in timeline)

    def test_phase_timeline_unknown_slug_raises(self, fresh_ledger) -> None:
        with pytest.raises(KeyError):
            fresh_ledger.phase_timeline("not_a_film")
