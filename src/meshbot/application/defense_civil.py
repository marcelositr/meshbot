"""Defense Civil alert service boundaries and alert data."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DefenseCivilAlert:
    """Alert data published by the official Defense Civil feed."""

    identifier: str
    sender: str
    sent: str
    status: str
    msg_type: str
    references: tuple[str, ...]
    event: str
    severity: str
    urgency: str
    certainty: str
    area: str
    headline: str
    description: str
    instruction: str
    onset: str | None
    expires: str | None


@dataclass(frozen=True, slots=True)
class DefenseCivilSettings:
    """Presentation and operational policy for Defense Civil responses."""

    enabled: bool
    mode: str
    max_alerts: int
    max_message_length: int
    show_severity: bool
    show_description: bool
    show_instruction: bool
    show_urgency: bool
    show_certainty: bool


class DefenseCivilServiceError(RuntimeError):
    """Base error for Defense Civil service failures."""


class DefenseCivilServiceUnavailableError(DefenseCivilServiceError):
    """Raised when the external alert feed cannot be reached or parsed."""


class DefenseCivilCityNotFoundError(DefenseCivilServiceError):
    """Raised when the requested municipality does not exist."""


class DefenseCivilAmbiguousCityError(DefenseCivilServiceError):
    """Raised when a city name matches multiple municipalities."""

    def __init__(self, matches: tuple[str, ...]) -> None:
        self.matches = matches
        super().__init__("City name is ambiguous.")


class DefenseCivilService(Protocol):
    """Interface used by the Defense Civil command."""

    def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
        """Return active alerts matching the requested location."""
        ...
