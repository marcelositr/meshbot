"""Defense Civil alert lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from meshbot.application.defense_civil import DefenseCivilAlert

DefenseCivilEventType = Literal["new", "updated", "deactivated"]


@dataclass(frozen=True, slots=True)
class StoredDefenseCivilAlert:
    """An alert together with its local lifecycle state."""

    alert: DefenseCivilAlert
    active: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DefenseCivilAlertEvent:
    """A lifecycle change detected while synchronizing the feed."""

    type: DefenseCivilEventType
    alert: DefenseCivilAlert


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
    """Apply feed snapshots and detect alert lifecycle changes."""

    def __init__(self, repository: DefenseCivilAlertRepository) -> None:
        self._repository = repository

    def synchronize(
        self,
        alerts: tuple[DefenseCivilAlert, ...],
    ) -> tuple[DefenseCivilAlertEvent, ...]:
        """Persist a successful snapshot and return detected lifecycle events."""
        events: list[DefenseCivilAlertEvent] = []
        seen = {alert.identifier for alert in alerts}

        for alert in alerts:
            previous = self._repository.get(alert.identifier)
            if previous is None or not previous.active:
                event_type: DefenseCivilEventType = "new"
            elif previous.alert != alert:
                event_type = "updated"
            else:
                continue

            self._repository.upsert(alert, active=True)
            events.append(DefenseCivilAlertEvent(event_type, alert))

        for stored in self._repository.list_active():
            if stored.alert.identifier in seen:
                continue

            self._repository.upsert(stored.alert, active=False)
            events.append(DefenseCivilAlertEvent("deactivated", stored.alert))

        return tuple(events)
