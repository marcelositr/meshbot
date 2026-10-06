"""Persistent state boundaries for Defense Civil alerts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from meshbot.application.defense_civil import DefenseCivilAlert


@dataclass(frozen=True, slots=True)
class StoredDefenseCivilAlert:
    """An alert together with its local lifecycle state."""

    alert: DefenseCivilAlert
    active: bool
    updated_at: datetime


class DefenseCivilAlertRepository(Protocol):
    """Persistence boundary for Defense Civil alert state."""

    def upsert(self, alert: DefenseCivilAlert, *, active: bool) -> None:
        """Create or update an alert and its active state."""
        ...

    def get(self, identifier: str) -> StoredDefenseCivilAlert | None:
        """Return one stored alert by identifier."""
        ...

    def list_active(self) -> tuple[StoredDefenseCivilAlert, ...]:
        """Return currently active stored alerts."""
        ...


class DefenseCivilStateService:
    """Apply feed snapshots to persistent Defense Civil state."""

    def __init__(self, repository: DefenseCivilAlertRepository) -> None:
        self._repository = repository

    def synchronize(self, alerts: tuple[DefenseCivilAlert, ...]) -> None:
        """Persist the current effective alert snapshot."""
        seen = {alert.identifier for alert in alerts}

        for alert in alerts:
            self._repository.upsert(alert, active=True)

        for stored in self._repository.list_active():
            if stored.alert.identifier not in seen:
                self._repository.upsert(stored.alert, active=False)

    @staticmethod
    def now() -> datetime:
        """Return a timezone-aware UTC timestamp for state transitions."""
        return datetime.now(UTC)
