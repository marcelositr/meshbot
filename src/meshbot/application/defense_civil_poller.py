"""Continuous Defense Civil feed synchronization."""

from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Event
from typing import Protocol

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_state import (
    DefenseCivilAlertEvent,
    DefenseCivilStateService,
)

logger = logging.getLogger(__name__)


class DefenseCivilFeed(Protocol):
    """Source of current effective Defense Civil alerts."""

    def get_all_alerts(self) -> tuple[DefenseCivilAlert, ...]:
        """Return the current active alert snapshot."""
        ...


class DefenseCivilPoller:
    """Synchronize the Defense Civil feed at a fixed interval."""

    def __init__(
        self,
        feed: DefenseCivilFeed,
        state: DefenseCivilStateService,
        poll_interval_seconds: float = 300.0,
        sleep: Callable[[float], None] | None = None,
        on_events: Callable[[DefenseCivilAlertEvent], None] | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        self._feed = feed
        self._state = state
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep = sleep or Event().wait
        self._on_events = on_events

    def poll_once(self) -> tuple[DefenseCivilAlertEvent, ...]:
        """Fetch and persist one successful feed snapshot."""
        alerts = self._feed.get_all_alerts()
        events = self._state.synchronize(alerts)
        logger.info(
            "Defense Civil feed synchronized: %d active alerts, %d lifecycle events.",
            len(alerts),
            len(events),
        )
        if self._on_events is not None:
            for event in events:
                self._on_events(event)
        return events

    def run(self, stop_event: Event | None = None) -> None:
        """Poll until stopped; failed polls leave the previous state untouched."""
        event = stop_event or Event()
        logger.info("Defense Civil poller started.")
        while not event.is_set():
            try:
                self.poll_once()
            except Exception:
                logger.exception("Defense Civil feed synchronization failed.")
            if not event.is_set():
                self._sleep(self._poll_interval_seconds)
        logger.info("Defense Civil poller stopped.")
