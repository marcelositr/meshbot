"""Production runtime orchestration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Event, Thread
from typing import Protocol

logger = logging.getLogger(__name__)


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


class RuntimeWorker(Protocol):
    """Background worker managed by the production runtime."""

    def run(self, stop_event: Event) -> None:
        """Run until the shared stop event is set."""
        ...


class ProductionRuntime:
    """Run MeshBot continuously against a closable transport."""

    def __init__(
        self,
        bot: BotRunner,
        transport: ClosableTransport,
        poll_interval_seconds: float = 0.1,
        sleep: Callable[[float], None] | None = None,
        workers: tuple[RuntimeWorker, ...] = (),
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be greater than zero.")

        self._bot = bot
        self._transport = transport
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep = sleep or Event().wait
        self._workers = workers

    def run(self, stop_event: Event | None = None) -> None:
        """Process messages until the stop event is set, then close transport."""
        event = stop_event or Event()
        threads: list[Thread] = []
        logger.info("Production runtime started.")
        try:
            for worker in self._workers:
                thread = Thread(
                    target=worker.run,
                    args=(event,),
                    name="MeshBotBackgroundWorker",
                    daemon=True,
                )
                thread.start()
                threads.append(thread)
            while not event.is_set():
                self._bot.process_next_message()
                self._sleep(self._poll_interval_seconds)
        finally:
            event.set()
            for thread in threads:
                thread.join()
            logger.info("Production runtime stopping; closing transport.")
            self._transport.close()
