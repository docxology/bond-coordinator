"""Smoke tests: each thin orchestrator runs end-to-end and exits 0.

Scripts are invoked as real subprocesses (project dir is the cwd, and each
script bootstraps its own ``sys.path``), so no mocks and no PYTHONPATH hacks.
Generated artifacts land under the gitignored ``output/`` tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"


def _run(
    script: str, *args: str, tmp_ledger: Path | None = None
) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(
        cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )


class TestStatusReport:
    def test_human_report_exits_zero(self) -> None:
        result = _run("status_report.py")
        assert result.returncode == 0, result.stderr
        assert "BOND — MISSION CONTROL" in result.stdout
        assert "Packages: 27 total" in result.stdout

    def test_json_report(self) -> None:
        result = _run("status_report.py", "--json")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["total"] == 27
        assert payload["counts_by_status"]["scaffolded"] == 27
        # Per-layer summary is part of the machine-readable contract.
        assert len(payload["layers"]) == 6
        assert payload["layers"][-1]["layer"] == "films"
        assert payload["layers"][-1]["total"] == 27

    def test_persists_status_snapshot(self) -> None:
        result = _run("status_report.py")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (PROJECT_ROOT / "output" / "data" / "suite_status.json").read_text(
                encoding="utf-8"
            )
        )
        assert snapshot["total"] == 27
        assert "layers" in snapshot


class TestBuildSituationRoom:
    def test_builds_html_dashboard(self) -> None:
        result = _run("build_situation_room.py")
        assert result.returncode == 0, result.stderr
        target = PROJECT_ROOT / "output" / "situation_room.html"
        assert target.is_file()
        html = target.read_text(encoding="utf-8")
        assert "BOND-COORDINATOR" in html
        assert "MISSION CONTROL" in html
        assert "goldfinger" in html  # every slug present
        assert "never_say_never_again" in html
        # Deepened situation room: layers, timeline, per-film gadgets, audit.
        assert "Suite layers" in html
        assert "Recent transitions" in html
        assert "coverage heat" in html.lower()


class TestAdvanceMission:
    def test_advance_and_persist(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.json"
        result = _run(
            "advance_mission.py",
            "--slug",
            "goldfinger",
            "--phase",
            "recon",
            "--by",
            "agent-007",
            "--version",
            "0.1.0",
            "--ledger",
            str(ledger),
        )
        assert result.returncode == 0, result.stderr
        assert "recon" in result.stdout
        payload = json.loads(ledger.read_text(encoding="utf-8"))
        assert payload["current"]["goldfinger"]["phase"] == "recon"

    def test_illegal_backwards_transition_exits_nonzero(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.json"
        _run(
            "advance_mission.py",
            "--slug",
            "goldfinger",
            "--phase",
            "recon",
            "--ledger",
            str(ledger),
        )
        result = _run(
            "advance_mission.py",
            "--slug",
            "goldfinger",
            "--phase",
            "brief",
            "--ledger",
            str(ledger),
        )
        assert result.returncode == 1
        assert "backwards" in result.stderr or "backwards" in result.stdout

    def test_unknown_slug_exits_nonzero(self, tmp_path: Path) -> None:
        result = _run(
            "advance_mission.py",
            "--slug",
            "not_a_film",
            "--phase",
            "recon",
            "--ledger",
            str(tmp_path / "l.json"),
        )
        assert result.returncode == 1


class TestGenerateManuscriptVariables:
    @pytest.mark.skipif(
        not (PROJECT_ROOT / "manuscript" / "config.yaml").is_file(),
        reason="requires the real manuscript config",
    )
    def test_hydrates_manuscript_tree(self) -> None:
        result = _run("z_generate_manuscript_variables.py")
        assert result.returncode == 0, result.stderr

        variables = json.loads(
            (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").read_text(
                encoding="utf-8"
            )
        )
        assert variables["CONFIG_CODENAME"] == "MISSION CONTROL"
        assert variables["REGISTRY_TOTAL"] == "27"

        abstract = (
            PROJECT_ROOT / "output" / "manuscript" / "00_abstract.md"
        ).read_text(encoding="utf-8")
        assert "BOND-COORDINATOR" in abstract
        assert "MISSION CONTROL" in abstract
