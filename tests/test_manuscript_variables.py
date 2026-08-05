"""Manuscript-variable tests: config parsing, identity tokens, ledger-derived
counts, and {{TOKEN}} tree resolution.

Config reading and token generation are fully deterministic — a small
in-memory config fixture plus the real registry drive every assertion.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bond_coordinator import (
    MISSION_LIFECYCLE,
    ROSTER,
    generate_variables,
    load_config,
    resolve_manuscript_tree,
    subset_roster,
)
from tests.conftest import SAMPLE_SLUGS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_CONFIG = PROJECT_ROOT / "manuscript" / "config.yaml"

MINIMAL_CONFIG = {
    "paper": {
        "title": "BOND-COORDINATOR",
        "subtitle": "Mission control for the BOND suite",
        "version": "0.1.0",
    },
    "mission": {"codename": "MISSION CONTROL"},
    "keywords": ["registry", "ledger", "situation room"],
}


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(MINIMAL_CONFIG), encoding="utf-8")
    return path


class TestLoadConfig:
    def test_loads_real_config(self) -> None:
        config = load_config(REAL_CONFIG)
        assert config["paper"]["title"] == "BOND-COORDINATOR"
        assert config["mission"]["codename"] == "MISSION CONTROL"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "does_not_exist.yaml")

    def test_non_mapping_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ValueError, match="mapping"):
            load_config(path)


class TestGenerateVariables:
    def test_identity_tokens_from_config(self, config_path: Path) -> None:
        variables = generate_variables(config_path)
        assert variables["CONFIG_TITLE"] == "BOND-COORDINATOR"
        assert variables["CONFIG_SUBTITLE"] == "Mission control for the BOND suite"
        assert variables["CONFIG_VERSION"] == "0.1.0"
        assert variables["CONFIG_CODENAME"] == "MISSION CONTROL"
        assert variables["CONFIG_KEYWORDS"] == "registry, ledger, situation room"
        assert variables["CONFIG_MISSION_LIFECYCLE"] == MISSION_LIFECYCLE

    def test_registry_tokens_full_fleet(self, config_path: Path) -> None:
        variables = generate_variables(config_path)
        assert variables["REGISTRY_TOTAL"] == "27"
        assert variables["REGISTRY_SCAFFOLDED"] == "27"
        assert variables["REGISTRY_READY"] == "0"
        assert variables["REGISTRY_BUILDING"] == "0"
        assert variables["REGISTRY_RED"] == "0"
        assert variables["REGISTRY_COVERAGE_MEAN"] == "N/A"
        assert variables["REGISTRY_COVERAGE_KNOWN"] == "0"
        assert variables["REGISTRY_COVERAGE_AT_90"] == "0"
        assert len(variables["REGISTRY_PACKAGES_CSV"].split(", ")) == 27

    def test_seed_roster_declares_itself_unmeasured(self, config_path: Path) -> None:
        variables = generate_variables(config_path)
        assert variables["REGISTRY_MEASUREMENT_SOURCE"] == (
            "none — registry seed defaults (status/coverage unmeasured)"
        )

    def test_measured_roster_moves_the_status_tokens(self, config_path: Path) -> None:
        """Gate output must reach the manuscript, and be labelled as measured.

        The prose in `03_results.md` describes these tokens; if applying real
        gate results could not change them, that description would be
        decorative.
        """
        from bond_coordinator import apply_gate_results, build_roster
        from bond_coordinator.gates import parse_gate_manifest

        results = parse_gate_manifest(
            {
                "packages": [
                    {"package": "goldfinger", "coverage": 100.0, "verdict": "ok"},
                    {"package": "skyfall", "coverage": 92.0, "verdict": "ok"},
                    {
                        "package": "dr_no",
                        "coverage": 88.0,
                        "failed": 1,
                        "rc": 1,
                        "verdict": "fail",
                    },
                ]
            }
        )
        variables = generate_variables(
            config_path, roster=apply_gate_results(build_roster(), results)
        )
        assert variables["REGISTRY_READY"] == "2"
        assert variables["REGISTRY_RED"] == "1"
        assert variables["REGISTRY_SCAFFOLDED"] == "24"
        assert variables["REGISTRY_COVERAGE_KNOWN"] == "3"
        assert variables["REGISTRY_COVERAGE_AT_90"] == "2"
        assert variables["REGISTRY_MEASUREMENT_SOURCE"] == (
            "measured gate output on 3 of 27 registry rows"
        )

    def test_registry_tokens_with_fixture_subset(self, config_path: Path) -> None:
        roster = subset_roster(SAMPLE_SLUGS)
        variables = generate_variables(config_path, roster=roster)
        assert variables["REGISTRY_TOTAL"] == "5"
        assert variables["REGISTRY_SCAFFOLDED"] == "5"
        assert variables["REGISTRY_PACKAGES_CSV"] == ", ".join(SAMPLE_SLUGS)

    def test_layer_and_ledger_tokens(self, config_path: Path) -> None:
        variables = generate_variables(config_path)
        assert variables["REGISTRY_LAYER_COUNT"] == "6"
        assert "layer0 (Q-branch primitives)" in variables["REGISTRY_LAYER_CSV"]
        assert "layer4 (Front door & fleet ops)" in variables["REGISTRY_LAYER_CSV"]
        assert "films (Film packages)" in variables["REGISTRY_LAYER_CSV"]
        assert variables["LEDGER_TRANSITION_TOTAL"] == "27"

    def test_layer_and_ledger_tokens_subset(self, config_path: Path) -> None:
        roster = subset_roster(SAMPLE_SLUGS)
        variables = generate_variables(config_path, roster=roster)
        assert variables["LEDGER_TRANSITION_TOTAL"] == "5"

    def test_roster_span_tokens_full_fleet(self, config_path: Path) -> None:
        """First/last roster rows are derived, so prose never types a year."""
        variables = generate_variables(config_path)
        assert variables["REGISTRY_FIRST_SLUG"] == ROSTER[0].slug
        assert variables["REGISTRY_FIRST_YEAR"] == str(ROSTER[0].year)
        assert variables["REGISTRY_LAST_SLUG"] == ROSTER[-1].slug
        assert variables["REGISTRY_LAST_YEAR"] == str(ROSTER[-1].year)

    def test_roster_span_tokens_follow_the_roster(self, config_path: Path) -> None:
        """Change the roster and the span tokens change with it."""
        roster = subset_roster(("skyfall", "dr_no"))
        variables = generate_variables(config_path, roster=roster)
        assert variables["REGISTRY_FIRST_SLUG"] == "skyfall"
        assert variables["REGISTRY_FIRST_YEAR"] == "2012"
        assert variables["REGISTRY_LAST_SLUG"] == "dr_no"
        assert variables["REGISTRY_LAST_YEAR"] == "1962"

    def test_roster_span_tokens_degrade_on_empty_roster(
        self, config_path: Path
    ) -> None:
        variables = generate_variables(config_path, roster=())
        assert variables["REGISTRY_FIRST_SLUG"] == "—"
        assert variables["REGISTRY_LAST_YEAR"] == "—"
        assert variables["REGISTRY_TOTAL"] == "0"

    def test_gate_tokens_track_the_enforcing_modules(self, config_path: Path) -> None:
        """Threshold tokens are read from the code that enforces them."""
        from bond_coordinator import COVERAGE_FLOOR, DEFAULT_STALE_DAYS, MissionPhase

        variables = generate_variables(config_path)
        assert variables["GATE_COVERAGE_FLOOR"] == f"{COVERAGE_FLOOR:.0f}%"
        assert variables["GATE_STALE_DAYS"] == str(DEFAULT_STALE_DAYS)
        assert variables["LEDGER_PHASE_COUNT"] == str(len(MissionPhase))

    def test_infra_package_count_excludes_the_films_layer(
        self, config_path: Path
    ) -> None:
        """Infra count is derived from SUITE_LAYERS, not typed into prose."""
        from bond_coordinator import SUITE_LAYERS

        expected = sum(
            len(packages) for layer, _, packages in SUITE_LAYERS if layer != "films"
        )
        variables = generate_variables(config_path)
        assert variables["REGISTRY_INFRA_PACKAGE_COUNT"] == str(expected)
        # It counts packages, not layers, and excludes the 27 films entirely.
        assert variables["REGISTRY_INFRA_PACKAGE_COUNT"] != variables["REGISTRY_TOTAL"]
        assert int(variables["REGISTRY_INFRA_PACKAGE_COUNT"]) >= len(SUITE_LAYERS) - 1

    def test_require_outputs_flag_accepted(self, config_path: Path) -> None:
        # The coordinator has no analysis-output dependency; the flag is
        # accepted for pipeline parity and never gates.
        variables = generate_variables(config_path, require_outputs=True)
        assert variables["REGISTRY_TOTAL"] == "27"

    def test_missing_paper_title_raises(self, tmp_path: Path) -> None:
        config = {
            "paper": {"subtitle": "x"},
            "mission": {"codename": "MISSION CONTROL"},
        }
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        with pytest.raises(ValueError, match="paper.title"):
            generate_variables(path)

    def test_missing_mission_codename_raises(self, tmp_path: Path) -> None:
        config = {
            "paper": {"title": "X", "subtitle": "x", "version": "1"},
            "mission": {},
        }
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        with pytest.raises(ValueError, match="mission.codename"):
            generate_variables(path)

    def test_missing_keywords_yields_empty(self, tmp_path: Path) -> None:
        config = {
            "paper": {"title": "X", "subtitle": "x", "version": "1"},
            "mission": {"codename": "MISSION CONTROL"},
        }
        path = tmp_path / "config.yaml"
        path.write_text(yaml.safe_dump(config), encoding="utf-8")
        variables = generate_variables(path)
        assert variables["CONFIG_KEYWORDS"] == ""


class TestResolveManuscriptTree:
    def _templates(self, tmp_path: Path, *names: str) -> Path:
        templates = tmp_path / "templates"
        templates.mkdir()
        for name in names:
            (templates / name).write_text(
                "Title: {{CONFIG_TITLE}}\nCode: {{CONFIG_CODENAME}}\nUnknown: {{UNKNOWN_TOKEN}}\n",
                encoding="utf-8",
            )
        return templates

    def test_resolves_known_tokens_and_leaves_unknown(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        templates = self._templates(tmp_path, "00_abstract.md", "01_introduction.md")
        variables = generate_variables(config_path)
        written = resolve_manuscript_tree(templates, Path(tmp_path) / "out", variables)
        assert len(written) == 2
        resolved = (Path(tmp_path) / "out" / "00_abstract.md").read_text(
            encoding="utf-8"
        )
        assert "Title: BOND-COORDINATOR" in resolved
        assert "Code: MISSION CONTROL" in resolved
        # Unknown tokens are left untouched and remain grep-able.
        assert "{{UNKNOWN_TOKEN}}" in resolved

    def test_writes_sorted_and_creates_output_dir(
        self, tmp_path: Path, config_path: Path
    ) -> None:
        templates = self._templates(tmp_path, "99_references.md", "00_abstract.md")
        variables = generate_variables(config_path)
        written = resolve_manuscript_tree(templates, Path(tmp_path) / "out", variables)
        assert [path.name for path in written] == ["00_abstract.md", "99_references.md"]
        assert all(path.is_file() for path in written)


class TestManuscriptCrossReference:
    def test_every_prose_token_is_generated(self) -> None:
        """Live gate: every {{TOKEN}} in numbered prose sections is produced.

        Globs only numbered manuscript sections ([0-9]*.md) — guide files
        (SYNTAX.md, AGENTS.md, README.md) legitimately illustrate literal
        placeholders and are excluded.
        """
        import re

        variables = generate_variables(REAL_CONFIG)
        used: set[str] = set()
        sections = sorted(PROJECT_ROOT.glob("manuscript/[0-9]*.md"))
        assert sections, "no numbered prose sections found"
        for section in sections:
            text = section.read_text(encoding="utf-8")
            used |= {match[2:-2] for match in re.findall(r"\{\{[A-Z0-9_]+\}\}", text)}
        assert used, "no {{TOKEN}}s found in numbered prose sections"
        missing = used - set(variables)
        assert not missing, f"prose tokens not generated: {sorted(missing)}"
