"""Production runtime orchestration."""

from __future__ import annotations

from collections.abc import Callable
from threading import Event
from typing import Protocol


class BotRunner(Protocol):
    """Application contract for a continuously processed bot."""

    def process_next_message(self) -> bool:
        """Process one queued message."""
        ...


class ClosableTransport(Protocol):
    """Transport contract required by the production runtime."""

    def close(self) -> None:
        """Close the transport."""
        ...


class ProductionRuntime:
    """Run MeshBot continuously against a closable transport."""

    def __init__(
        self,
        bot: BotRunner,
        transport: ClosableTransport,
        poll_interval_seconds: float = 0.1,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        self._bot = bot
        self._transport = transport
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep = sleep or Event().wait

    def run(self, stop_event: Event | None = None) -> None:
        """Process messages until the stop event is set, then close transport."""
        event = stop_event or Event()
        try:
            while not event.is_set():
                self._bot.process_next_message()
                self._sleep(self._poll_interval_seconds)
        finally:
            self._transport.close()
