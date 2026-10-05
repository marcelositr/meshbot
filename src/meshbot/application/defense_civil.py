"""Defense Civil alert service boundaries and alert data."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DefenseCivilAlert:
    """Alert data published by the official Defense Civil feed."""

    event: str
    severity: str
    area: str
    headline: str
    description: str
    expires: str | None


class DefenseCivilServiceError(RuntimeError):
    """Base error for Defense Civil service failures."""


class DefenseCivilServiceUnavailableError(DefenseCivilServiceError):
    """Raised when the external alert feed cannot be reached or parsed."""


class DefenseCivilService(Protocol):
    """Interface used by the Defense Civil command."""

    def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
        """Return active alerts matching the requested location."""
        ...
