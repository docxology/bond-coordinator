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


def _gate_manifest(path: Path, rows: list[dict[str, object]]) -> Path:
    """Write a real gate-aggregate manifest (the shape bond-ops emits)."""
    path.write_text(json.dumps({"packages": rows}, indent=2), encoding="utf-8")
    return path


def _gate_row(
    package: str, coverage: float, failed: int = 0, verdict: str = "ok"
) -> dict[str, object]:
    return {
        "package": package,
        "coverage": coverage,
        "passed": 100,
        "failed": failed,
        "rc": 0 if failed == 0 else 1,
        "verdict": verdict,
    }


class TestStatusReport:
    """Seed runs use ``--no-gate-manifest`` so assertions are fleet-independent.

    The measured path is exercised against a manifest written by the test
    itself: real JSON, real subprocess, no dependency on whichever packages
    the sibling fleet happens to have gated today.
    """

    def test_human_report_exits_zero(self) -> None:
        result = _run("status_report.py", "--no-gate-manifest")
        assert result.returncode == 0, result.stderr
        assert "BOND — MISSION CONTROL" in result.stdout
        assert "Packages: 27 total" in result.stdout

    def test_seed_run_declares_itself_unmeasured(self) -> None:
        result = _run("status_report.py", "--no-gate-manifest")
        assert result.returncode == 0, result.stderr
        assert "gates    : none applied — registry seed defaults" in result.stdout

    def test_json_report(self) -> None:
        result = _run("status_report.py", "--json", "--no-gate-manifest")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["total"] == 27
        assert sum(payload["counts_by_status"].values()) == 27
        assert payload["counts_by_status"]["scaffolded"] == 27
        assert payload["measurement_source"].startswith("none applied")
        # Per-layer summary is part of the machine-readable contract.
        assert len(payload["layers"]) == 6
        assert payload["layers"][-1]["layer"] == "films"
        assert payload["layers"][-1]["total"] == 27

    def test_measured_manifest_populates_status_and_coverage(
        self, tmp_path: Path
    ) -> None:
        manifest = _gate_manifest(
            tmp_path / "gate_manifest.json",
            [
                _gate_row("goldfinger", 100.0),
                _gate_row("skyfall", 80.0),
                _gate_row("dr_no", 99.0, failed=2, verdict="fail"),
                _gate_row("bond-api", 100.0),  # infra row: not a registry film
            ],
        )
        result = _run("status_report.py", "--json", "--gate-manifest", str(manifest))
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        counts = payload["counts_by_status"]
        assert counts["ready"] == 1
        assert counts["building"] == 1
        assert counts["red"] == 1
        assert counts["scaffolded"] == 24
        assert payload["coverage"]["known"] == 3
        assert payload["coverage"]["min"] == 80.0
        assert payload["coverage"]["max"] == 100.0
        assert payload["measurement_source"].startswith(
            "measured gate output applied to 3 of 27 rows"
        )

    def test_absent_gate_manifest_is_reported_not_silent(self, tmp_path: Path) -> None:
        result = _run(
            "status_report.py",
            "--json",
            "--gate-manifest",
            str(tmp_path / "nope.json"),
        )
        assert result.returncode == 0, result.stderr
        assert "no gate manifest at" in result.stderr
        assert json.loads(result.stdout)["measurement_source"].startswith(
            "none applied"
        )

    def test_persists_status_snapshot(self) -> None:
        result = _run("status_report.py", "--no-gate-manifest")
        assert result.returncode == 0, result.stderr
        snapshot = json.loads(
            (PROJECT_ROOT / "output" / "data" / "suite_status.json").read_text(
                encoding="utf-8"
            )
        )
        assert snapshot["total"] == 27
        assert "layers" in snapshot
        assert "measurement_source" in snapshot


class TestBuildSituationRoom:
    def test_builds_html_dashboard(self, tmp_path: Path) -> None:
        out = tmp_path / "situation_room.html"
        result = _run(
            "build_situation_room.py",
            "--no-gate-manifest",
            "--reconciled",
            str(tmp_path / "absent.json"),
            "--out",
            str(out),
        )
        assert result.returncode == 0, result.stderr
        assert out.is_file()
        html = out.read_text(encoding="utf-8")
        assert "BOND-COORDINATOR" in html
        assert "MISSION CONTROL" in html
        assert "goldfinger" in html  # every slug present
        assert "never_say_never_again" in html
        # Deepened situation room: layers, timeline, per-film gadgets, audit.
        assert "Suite layers" in html
        assert "Recent transitions" in html
        assert "coverage heat" in html.lower()

    def test_unreconciled_unmeasured_build_says_so(self, tmp_path: Path) -> None:
        """No manifests ⇒ the dashboard must not imply reconciled or measured."""
        out = tmp_path / "situation_room.html"
        result = _run(
            "build_situation_room.py",
            "--no-gate-manifest",
            "--reconciled",
            str(tmp_path / "absent.json"),
            "--out",
            str(out),
        )
        assert result.returncode == 0, result.stderr
        html = out.read_text(encoding="utf-8")
        assert "Data provenance" in html
        assert "registry seed — provisional codenames" in html
        assert "status/coverage unmeasured" in html

    def test_reconciled_codenames_reach_the_dashboard(self, tmp_path: Path) -> None:
        """Film-declared codenames must render, replacing the provisional ones.

        The dashboard used to be built from ``build_roster()`` alone, with no
        reconciled input at all, so a film's declared codename could never
        appear no matter how many reconcile runs had happened.
        """
        reconciled = tmp_path / "reconciled.json"
        reconciled.write_text(
            json.dumps(
                {
                    "films": {},
                    "film_declared": {"a_view_to_a_kill": "TEST DECLARED NAME"},
                    "gadgets": {},
                    "skipped": [],
                }
            ),
            encoding="utf-8",
        )
        out = tmp_path / "situation_room.html"
        result = _run(
            "build_situation_room.py",
            "--no-gate-manifest",
            "--reconciled",
            str(reconciled),
            "--out",
            str(out),
        )
        assert result.returncode == 0, result.stderr
        html = out.read_text(encoding="utf-8")
        assert "TEST DECLARED NAME" in html
        assert "MAIN STRIKE" not in html  # the provisional codename is gone
        assert "1 provisional codename(s) overridden" in html

    def test_measured_coverage_reaches_the_dashboard(self, tmp_path: Path) -> None:
        manifest = _gate_manifest(
            tmp_path / "gate_manifest.json", [_gate_row("goldfinger", 93.75)]
        )
        out = tmp_path / "situation_room.html"
        result = _run(
            "build_situation_room.py",
            "--gate-manifest",
            str(manifest),
            "--reconciled",
            str(tmp_path / "absent.json"),
            "--out",
            str(out),
        )
        assert result.returncode == 0, result.stderr
        html = out.read_text(encoding="utf-8")
        assert "93.8%" in html  # rendered to one decimal by _fmt_coverage
        assert "measured gate output applied to 1 of 27 rows" in html


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
        result = _run("z_generate_manuscript_variables.py", "--no-gate-manifest")
        assert result.returncode == 0, result.stderr

        variables = json.loads(
            (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").read_text(
                encoding="utf-8"
            )
        )
        assert variables["CONFIG_CODENAME"] == "MISSION CONTROL"
        assert variables["REGISTRY_TOTAL"] == "27"
        assert variables["REGISTRY_MEASUREMENT_SOURCE"].startswith("none —")

        abstract = (
            PROJECT_ROOT / "output" / "manuscript" / "00_abstract.md"
        ).read_text(encoding="utf-8")
        assert "BOND-COORDINATOR" in abstract
        assert "MISSION CONTROL" in abstract

    @pytest.mark.skipif(
        not (PROJECT_ROOT / "manuscript" / "config.yaml").is_file(),
        reason="requires the real manuscript config",
    )
    def test_measured_manifest_hydrates_measured_tokens(self, tmp_path: Path) -> None:
        """A gate manifest must move the manuscript's own status figures."""
        manifest = _gate_manifest(
            tmp_path / "gate_manifest.json",
            [_gate_row("goldfinger", 100.0), _gate_row("skyfall", 91.0)],
        )
        result = _run(
            "z_generate_manuscript_variables.py", "--gate-manifest", str(manifest)
        )
        assert result.returncode == 0, result.stderr
        variables = json.loads(
            (PROJECT_ROOT / "output" / "data" / "manuscript_variables.json").read_text(
                encoding="utf-8"
            )
        )
        assert variables["REGISTRY_READY"] == "2"
        assert variables["REGISTRY_SCAFFOLDED"] == "25"
        assert variables["REGISTRY_COVERAGE_KNOWN"] == "2"
        assert variables["REGISTRY_COVERAGE_MEAN"] == "95.5%"
        assert variables["REGISTRY_MEASUREMENT_SOURCE"] == (
            "measured gate output on 2 of 27 registry rows"
        )
