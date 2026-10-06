from pathlib import Path

import pytest

from meshbot.config import ConfigurationError, Settings, load_settings

VALID_CONFIG = """
name = "MeshBot"
transport = "simulator"
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
    assert settings.defense_civil_timeout_seconds == 30
    assert settings.defense_civil.mode == "normal"
    assert settings.defense_civil.max_alerts == 5
    assert not settings.weather_automatic_enabled
    assert settings.features.ping
    assert settings.features.weather_command
    assert settings.features.weather_bulletin
    assert settings.features.defense_civil_command
    assert settings.features.defense_civil_monitor


def test_feature_settings_can_disable_optional_features(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[features]
ping = false
weather_command = false
weather_bulletin = false
defense_civil_command = false
defense_civil_monitor = false
""",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert not settings.features.ping
    assert not settings.features.weather_command
    assert not settings.features.weather_bulletin
    assert not settings.features.defense_civil_command
    assert not settings.features.defense_civil_monitor


def test_automatic_weather_requires_weather_bulletin_feature(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace(
            'timeout_seconds = 30',
            'timeout_seconds = 30\nautomatic_enabled = true\n'
            'location = "Ribeirão Preto/SP"\nrecipient_id = "^all"',
        )
        + """
[features]
weather_bulletin = false
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="features.weather_bulletin"):
        load_settings(config)


def test_automatic_defense_civil_requires_monitor_feature(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[features]
defense_civil_monitor = false

[defesa_civil]
automatic_enabled = true
location = "Ribeirão Preto/SP"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="features.defense_civil_monitor"):
        load_settings(config)


def test_defense_civil_mode_changes_default_presentation(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[defesa_civil]
mode = "emergency"
""",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.defense_civil.show_description
    assert settings.defense_civil.show_instruction
    assert settings.defense_civil.show_urgency
    assert settings.defense_civil.show_certainty


def test_defense_civil_options_override_mode(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[defesa_civil]
mode = "emergency"
show_description = false
show_instruction = false
""",
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert not settings.defense_civil.show_description
    assert not settings.defense_civil.show_instruction
    assert settings.defense_civil.show_urgency


def test_real_transport_is_allowed_without_environment_setting(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace('transport = "simulator"', 'transport = "wifi"'),
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.transport == "wifi"


def test_invalid_silence_duration_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace("default_silence_minutes = 30", "default_silence_minutes = 0"),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="greater than zero"):
        load_settings(config)


def test_invalid_defense_civil_timeout_is_rejected(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[defesa_civil]
timeout_seconds = 0
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="defesa_civil.timeout_seconds"):
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


def test_optional_device_is_loaded(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace(
            'admins = ["!12345678"]',
            'admins = ["!12345678"]\ndevice = "/dev/ttyUSB0"',
        ),
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.device == "/dev/ttyUSB0"


def test_empty_optional_device_becomes_none(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace('admins = ["!12345678"]', 'admins = ["!12345678"]\ndevice = ""'),
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.device is None


def test_automatic_defense_civil_requires_feature_enabled(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[defesa_civil]
enabled = false
automatic_enabled = true
location = "Ribeirão Preto/SP"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="enabled is required"):
        load_settings(config)


def test_automatic_defense_civil_requires_location(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG
        + """
[defesa_civil]
enabled = true
automatic_enabled = true
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="location is required"):
        load_settings(config)


def test_automatic_weather_requires_location(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace(
            'timeout_seconds = 30',
            'timeout_seconds = 30\nautomatic_enabled = true',
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="weather.location is required"):
        load_settings(config)


def test_automatic_weather_settings_are_loaded(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        VALID_CONFIG.replace(
            'timeout_seconds = 30',
            'timeout_seconds = 30\nautomatic_enabled = true\n'
            'location = "Ribeirão Preto/SP"\nrecipient_id = "^all"',
        ),
        encoding="utf-8",
    )

    settings = load_settings(config)

    assert settings.weather_automatic_enabled
    assert settings.weather_location == "Ribeirão Preto/SP"
    assert settings.weather_recipient_id == "^all"
