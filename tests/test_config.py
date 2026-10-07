import pytest
from auditor.config import load_config


def test_load_config():
    """Verify the project configuration can be loaded."""
    config = load_config()

    assert config is not None
    assert "project" in config
    assert "reporting" in config


def test_project_configuration():
    """Verify required project configuration values."""
    config = load_config()

    assert config["project"]["name"] == "cloud-infrastructure-auditor"
    assert config["project"]["environment"] == "development"


def test_reporting_configuration():
    """Verify reporting configuration values."""
    config = load_config()

    assert config["reporting"]["format"] == "console"
    assert config["reporting"]["enabled"] is True
def test_load_config_missing_file():
    """Verify a missing configuration file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("missing_config.yaml")


def test_load_config_invalid_yaml(tmp_path):
    """Verify invalid YAML raises a parsing error."""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text("project: [invalid", encoding="utf-8")

    with pytest.raises(Exception):
        load_config(str(config_file))    