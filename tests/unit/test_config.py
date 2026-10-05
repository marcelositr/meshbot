from pathlib import Path

import pytest

from meshbot.config import ConfigurationError, Settings, load_settings

VALID_CONFIG = """
environment = "development"
name = "MeshBot"
transport = "simulator"
channel_name = "LongFast"
channel_index = 0
admins = ["!12345678"]
default_silence_minutes = 30
command_prefix = "/"
log_level = "INFO"

[messaging]
message_delay_seconds = 5

[weather]
provider = "inmet"
timeout_seconds = 30

[weather.periods]
morning_start = "06:00"
afternoon_start = "12:00"
night_start = "18:00"
"""


def test_load_settings_returns_validated_settings(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(VALID_CONFIG, encoding="utf-8")

    settings = load_settings(config)

    assert isinstance(settings, Settings)
    assert settings.name == "MeshBot"
    assert settings.transport == "simulator"
    assert settings.admins == ("!12345678",)
    assert settings.database_path == "data/meshbot.db"
    assert settings.default_silence_minutes == 30
    assert settings.message_delay_seconds == 5
    assert settings.weather_provider == "inmet"


def test_development_cannot_use_real_transport(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace('transport = "simulator"', 'transport = "wifi"'),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="must use the simulator"):
        load_settings(config)


def test_invalid_silence_duration_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace("default_silence_minutes = 30", "default_silence_minutes = 0"),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="greater than zero"):
        load_settings(config)


def test_missing_configuration_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_settings(tmp_path / "missing.toml")


def test_negative_message_delay_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace("message_delay_seconds = 5", "message_delay_seconds = -1"),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="zero or greater"):
        load_settings(config)
