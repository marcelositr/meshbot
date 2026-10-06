"""Production runtime orchestration."""

from __future__ import annotations

from collections.abc import Callable
from threading import Event

from meshbot.application.bot import MeshBot
from meshbot.infrastructure.meshtastic_transport import MeshtasticTransport


class ProductionRuntime:
    """Run MeshBot continuously against the real Meshtastic transport."""

    def __init__(
        self,
        bot: MeshBot,
        transport: MeshtasticTransport,
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
