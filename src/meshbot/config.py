"""Application configuration loading and validation."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when the MeshBot configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated settings used by the application."""

    environment: str
    name: str
    transport: str
    channel_name: str
    channel_index: int
    admins: tuple[str, ...]
    registration_requires_admin: bool
    default_silence_minutes: int
    command_prefix: str
    message_delay_seconds: float
    weather_provider: str
    weather_timeout_seconds: int
    weather_morning_start: str
    weather_afternoon_start: str
    weather_night_start: str
    log_level: str


_ALLOWED_ENVIRONMENTS = {"development", "production"}
_ALLOWED_TRANSPORTS = {"simulator", "wifi", "bluetooth", "usb"}
_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
_ALLOWED_WEATHER_PROVIDERS = {"inmet"}


def load_settings(path: Path) -> Settings:
    """Load and validate settings from a TOML file."""
    try:
        with path.open("rb") as file:
            raw = tomllib.load(file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Invalid TOML in configuration file: {path}") from exc

    return _build_settings(raw)


def _build_settings(raw: dict[str, Any]) -> Settings:
    try:
        messaging = _required_table(raw, "messaging")
        weather = _required_table(raw, "weather")
        periods = _required_table(weather, "periods")
        settings = Settings(
            environment=_required_string(raw, "environment"),
            name=_required_string(raw, "name"),
            transport=_required_string(raw, "transport"),
            channel_name=_required_string(raw, "channel_name"),
            channel_index=_required_int(raw, "channel_index"),
            admins=_required_admins(raw),
            registration_requires_admin=_required_bool(raw, "registration_requires_admin"),
            default_silence_minutes=_required_int(raw, "default_silence_minutes"),
            command_prefix=_required_string(raw, "command_prefix"),
            message_delay_seconds=_required_number(messaging, "message_delay_seconds"),
            weather_provider=_required_string(weather, "provider"),
            weather_timeout_seconds=_required_int(weather, "timeout_seconds"),
            weather_morning_start=_required_string(periods, "morning_start"),
            weather_afternoon_start=_required_string(periods, "afternoon_start"),
            weather_night_start=_required_string(periods, "night_start"),
            log_level=_required_string(raw, "log_level").upper(),
        )
    except KeyError as exc:
        raise ConfigurationError(f"Missing configuration option: {exc.args[0]}") from exc

    _validate(settings)
    return settings


def _validate(settings: Settings) -> None:
    if settings.environment not in _ALLOWED_ENVIRONMENTS:
        raise ConfigurationError(
            f"Invalid environment: {settings.environment!r}. "
            f"Expected one of {sorted(_ALLOWED_ENVIRONMENTS)}."
        )

    if settings.transport not in _ALLOWED_TRANSPORTS:
        raise ConfigurationError(
            f"Invalid transport: {settings.transport!r}. "
            f"Expected one of {sorted(_ALLOWED_TRANSPORTS)}."
        )

    if settings.environment == "development" and settings.transport != "simulator":
        raise ConfigurationError("Development environment must use the simulator transport.")

    if settings.channel_index < 0:
        raise ConfigurationError("channel_index must be zero or greater.")

    if settings.default_silence_minutes <= 0:
        raise ConfigurationError("default_silence_minutes must be greater than zero.")

    if not settings.command_prefix:
        raise ConfigurationError("command_prefix must not be empty.")

    if settings.message_delay_seconds < 0:
        raise ConfigurationError("message_delay_seconds must be zero or greater.")

    if settings.weather_provider not in _ALLOWED_WEATHER_PROVIDERS:
        raise ConfigurationError(f"Invalid weather provider: {settings.weather_provider!r}.")

    if settings.weather_timeout_seconds <= 0:
        raise ConfigurationError("weather_timeout_seconds must be greater than zero.")

    for name, value in (
        ("weather_morning_start", settings.weather_morning_start),
        ("weather_afternoon_start", settings.weather_afternoon_start),
        ("weather_night_start", settings.weather_night_start),
    ):
        _validate_time(name, value)

    if settings.log_level not in _ALLOWED_LOG_LEVELS:
        raise ConfigurationError(
            f"Invalid log_level: {settings.log_level!r}. "
            f"Expected one of {sorted(_ALLOWED_LOG_LEVELS)}."
        )


def _required_table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw[key]
    if not isinstance(value, dict):
        raise ConfigurationError(f"{key} must be a table.")
    return value


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{key} must be a non-empty string.")
    return value.strip()


def _required_int(raw: dict[str, Any], key: str) -> int:
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{key} must be an integer.")
    return value


def _required_number(raw: dict[str, Any], key: str) -> float:
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{key} must be a number.")
    return float(value)


def _required_bool(raw: dict[str, Any], key: str) -> bool:
    value = raw[key]
    if not isinstance(value, bool):
        raise ConfigurationError(f"{key} must be true or false.")
    return value


def _required_admins(raw: dict[str, Any]) -> tuple[str, ...]:
    value = raw["admins"]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigurationError("admins must be a list of strings.")
    return tuple(item.strip() for item in value if item.strip())


def _validate_time(name: str, value: str) -> None:
    parts = value.split(":")
    if len(parts) != 2:
        raise ConfigurationError(f"{name} must use HH:MM format.")
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ConfigurationError(f"{name} must use HH:MM format.") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ConfigurationError(f"{name} must use HH:MM format.")
