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