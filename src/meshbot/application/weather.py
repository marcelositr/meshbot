"""Weather service boundaries and forecast data."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class WeatherForecast:
    """Compact weather data needed by the bot."""

    city: str
    summary: str
    temperature_min: int
    temperature_max: int
    humidity_min: int
    humidity_max: int
    wind_direction: str
    wind_intensity: str


class WeatherServiceError(RuntimeError):
    """Base error for weather service failures."""


class WeatherServiceUnavailableError(WeatherServiceError):
    """Raised when an external weather dependency cannot be reached."""


class CityNotFoundError(WeatherServiceError):
    """Raised when a city cannot be resolved."""


class AmbiguousCityError(WeatherServiceError):
    """Raised when a city name matches multiple municipalities."""

    def __init__(self, matches: tuple[str, ...]) -> None:
        self.matches = matches
        super().__init__("City name is ambiguous.")


class WeatherService(Protocol):
    """Interface used by weather commands."""

    def get_forecast(self, city: str) -> WeatherForecast:
        """Return the forecast for the requested city."""
        ...
