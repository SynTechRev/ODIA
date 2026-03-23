"""Tests for scripts/setup_jurisdiction.py — interactive configuration wizard."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import the wizard module dynamically (it lives in scripts/, not src/)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_WIZARD_PATH = _SCRIPTS_DIR / "setup_jurisdiction.py"


def _import_wizard():
    spec = importlib.util.spec_from_file_location("setup_jurisdiction", _WIZARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wizard = _import_wizard()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_wizard_with_inputs(tmp_path: Path, inputs: list[str]) -> dict:
    """Run the wizard with *inputs* fed as mocked input() responses."""
    with patch("builtins.input", side_effect=inputs):
        return wizard.run_wizard(config_dir=tmp_path)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class TestValidateStateCode:
    def test_valid_two_letter(self):
        assert wizard.validate_state_code("CA") is True
        assert wizard.validate_state_code("TX") is True
        assert wizard.validate_state_code("NY") is True

    def test_lowercase_accepted(self):
        # validate_state_code checks isalpha() and len == 2; case is caller's responsibility
        assert wizard.validate_state_code("ca") is True

    def test_one_letter_rejected(self):
        assert wizard.validate_state_code("C") is False

    def test_three_letters_rejected(self):
        assert wizard.validate_state_code("CAL") is False

    def test_empty_rejected(self):
        assert wizard.validate_state_code("") is False

    def test_digit_rejected(self):
        assert wizard.validate_state_code("C1") is False

    def test_space_rejected(self):
        assert wizard.validate_state_code("C ") is False


class TestValidateSourcePath:
    def test_empty_string_valid(self):
        assert wizard.validate_source_path("") is True

    def test_existing_dir_valid(self, tmp_path):
        assert wizard.validate_source_path(str(tmp_path)) is True

    def test_nonexistent_path_invalid(self):
        assert wizard.validate_source_path("/no/such/path/xyz") is False

    def test_file_not_dir_invalid(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        assert wizard.validate_source_path(str(f)) is False


# ---------------------------------------------------------------------------
# Config assembly
# ---------------------------------------------------------------------------


class TestBuildJurisdictionConfig:
    def test_required_fields_present(self):
        cfg = wizard.build_jurisdiction_config("Testville", "CA")
        assert cfg["name"] == "Testville"
        assert cfg["state"] == "CA"
        assert cfg["country"] == "US"
        assert "meeting_type" in cfg

    def test_legistar_url_included_when_provided(self):
        cfg = wizard.build_jurisdiction_config(
            "Testville", "CA", "https://example.legistar.com"
        )
        assert cfg["legistar_base_url"] == "https://example.legistar.com"

    def test_legistar_url_omitted_when_empty(self):
        cfg = wizard.build_jurisdiction_config("Testville", "CA", "")
        assert "legistar_base_url" not in cfg

    def test_corpus_manifest_is_empty_dict(self):
        assert wizard.build_corpus_manifest() == {}


class TestBuildAgenciesConfig:
    def test_returns_dict_of_lists(self):
        sample = {"Police Department": ["police", "pd"]}
        result = wizard.build_agencies_config(sample)
        assert result == sample
        assert isinstance(result["Police Department"], list)


# ---------------------------------------------------------------------------
# Full wizard run (mocked input)
# ---------------------------------------------------------------------------


class TestWizardFlow:
    def _inputs_for(
        self,
        name="Riverside County",
        state="CA",
        legistar="",
        agency_selection="",
        source="",
        confirm_save="y",
    ) -> list[str]:
        """Build a list of input() responses matching wizard prompts."""
        return [name, state, legistar, agency_selection, source, confirm_save]

    def test_minimal_valid_flow(self, tmp_path):
        inputs = self._inputs_for()
        result = _run_wizard_with_inputs(tmp_path, inputs)

        assert result["jurisdiction"]["name"] == "Riverside County"
        assert result["jurisdiction"]["state"] == "CA"
        assert result["config_dir"] == str(tmp_path)

    def test_config_files_written(self, tmp_path):
        inputs = self._inputs_for()
        _run_wizard_with_inputs(tmp_path, inputs)

        assert (tmp_path / "jurisdiction.json").exists()
        assert (tmp_path / "agencies.json").exists()
        assert (tmp_path / "corpus_manifest.json").exists()

    def test_jurisdiction_json_content(self, tmp_path):
        inputs = self._inputs_for(name="Bayview City", state="OR")
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads((tmp_path / "jurisdiction.json").read_text(encoding="utf-8"))
        assert data["name"] == "Bayview City"
        assert data["state"] == "OR"
        assert data["country"] == "US"

    def test_agencies_json_is_valid(self, tmp_path):
        inputs = self._inputs_for()
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads((tmp_path / "agencies.json").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        # Every value must be a list of strings
        for v in data.values():
            assert isinstance(v, list)
            for alias in v:
                assert isinstance(alias, str)

    def test_corpus_manifest_is_empty_dict(self, tmp_path):
        inputs = self._inputs_for()
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads(
            (tmp_path / "corpus_manifest.json").read_text(encoding="utf-8")
        )
        assert data == {}

    def test_legistar_url_saved(self, tmp_path):
        inputs = self._inputs_for(legistar="https://mytown.legistar.com")
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads((tmp_path / "jurisdiction.json").read_text(encoding="utf-8"))
        assert data["legistar_base_url"] == "https://mytown.legistar.com"

    def test_specific_agency_selection(self, tmp_path):
        # Select item 1 (Police Department) only
        inputs = self._inputs_for(agency_selection="1")
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads((tmp_path / "agencies.json").read_text(encoding="utf-8"))
        assert "Police Department" in data
        assert "Fire Department" not in data

    def test_select_all_agencies(self, tmp_path):
        # Select "All of the above" — last menu item
        all_idx = str(len(wizard._AGENCY_MENU))
        inputs = self._inputs_for(agency_selection=all_idx)
        _run_wizard_with_inputs(tmp_path, inputs)

        data = json.loads((tmp_path / "agencies.json").read_text(encoding="utf-8"))
        assert len(data) == len(wizard._AGENCY_CATALOGUE)

    def test_default_source_used_when_empty(self, tmp_path):
        inputs = self._inputs_for(source="")
        result = _run_wizard_with_inputs(tmp_path, inputs)
        assert result["source_path"] == wizard._DEFAULT_SOURCE

    def test_custom_source_path(self, tmp_path):
        # Create a subdirectory to use as source
        src = tmp_path / "docs"
        src.mkdir()
        inputs = self._inputs_for(source=str(src))
        result = _run_wizard_with_inputs(tmp_path, inputs)
        assert result["source_path"] == str(src)


# ---------------------------------------------------------------------------
# Overwrite protection
# ---------------------------------------------------------------------------


class TestOverwriteProtection:
    def test_existing_config_prompts_overwrite(self, tmp_path):
        # Create existing jurisdiction.json
        existing = {"name": "Old City", "state": "TX", "country": "US"}
        (tmp_path / "jurisdiction.json").write_text(
            json.dumps(existing), encoding="utf-8"
        )

        # User says yes to overwrite, then provides new inputs
        inputs = [
            "y",  # overwrite?
            "New City",  # name
            "CA",  # state
            "",  # legistar
            "",  # agencies (all)
            "",  # source (default)
            "y",  # save?
        ]
        with patch("builtins.input", side_effect=inputs):
            result = wizard.run_wizard(config_dir=tmp_path)

        data = json.loads((tmp_path / "jurisdiction.json").read_text(encoding="utf-8"))
        assert data["name"] == "New City"

    def test_existing_config_cancel_overwrite(self, tmp_path):
        existing = {"name": "Old City", "state": "TX", "country": "US"}
        (tmp_path / "jurisdiction.json").write_text(
            json.dumps(existing), encoding="utf-8"
        )

        # User says no to overwrite — wizard exits
        with patch("builtins.input", side_effect=["n"]):
            with pytest.raises(SystemExit) as exc_info:
                wizard.run_wizard(config_dir=tmp_path)
        assert exc_info.value.code == 0

        # Original file unchanged
        data = json.loads((tmp_path / "jurisdiction.json").read_text(encoding="utf-8"))
        assert data["name"] == "Old City"


# ---------------------------------------------------------------------------
# State code retry
# ---------------------------------------------------------------------------


class TestStateCodeRetry:
    def test_invalid_then_valid_state(self, tmp_path):
        inputs = [
            "Testville",  # name
            "CALIFORNIA",  # invalid state (too long)
            "CALI",  # still invalid
            "CA",  # valid
            "",  # legistar
            "",  # agencies
            "",  # source
            "y",  # save
        ]
        with patch("builtins.input", side_effect=inputs):
            result = wizard.run_wizard(config_dir=tmp_path)

        assert result["jurisdiction"]["state"] == "CA"


# ---------------------------------------------------------------------------
# Loader compatibility
# ---------------------------------------------------------------------------


class TestLoaderCompatibility:
    def test_generated_config_loads_cleanly(self, tmp_path):
        """Files written by the wizard must be parseable by load_jurisdiction_config."""
        inputs = [
            "Lakeview",
            "WI",
            "",
            "",
            "",
            "y",
        ]
        with patch("builtins.input", side_effect=inputs):
            wizard.run_wizard(config_dir=tmp_path)

        from oraculus_di_auditor.config import load_jurisdiction_config

        cfg = load_jurisdiction_config(tmp_path)
        assert cfg.name == "Lakeview"
        assert cfg.state == "WI"
        assert isinstance(cfg.agencies, dict)
        assert isinstance(cfg.corpus_manifest, dict)
