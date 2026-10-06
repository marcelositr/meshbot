"""Tests for operational observability."""

import logging
from contextlib import suppress

from meshbot.application.bot import BotStats, MeshBot
from meshbot.application.logging import configure_logging
from meshbot.domain.messages import IncomingMessage, OutgoingMessage


class FakeTransport:
    def __init__(self) -> None:
        self.incoming: list[IncomingMessage] = []
        self.sent: list[OutgoingMessage] = []

    def receive(self) -> IncomingMessage | None:
        return self.incoming.pop(0) if self.incoming else None

    def send(self, message: OutgoingMessage) -> None:
        self.sent.append(message)


class FakeCommands:
    def handle(self, _message: IncomingMessage) -> list[OutgoingMessage]:
        return [OutgoingMessage("!2", "pong")]


def test_bot_tracks_basic_counters() -> None:
    transport = FakeTransport()
    transport.incoming.append(IncomingMessage("!1", "!ping"))
    bot = MeshBot(transport, FakeCommands())

    assert bot.process_next_message()
    assert bot.stats == BotStats(received=1, processed=1, sent=1)
    assert not bot.process_next_message()
    assert bot.stats.received == 1


def test_bot_counts_failures_and_logs_exception(caplog) -> None:
    class FailingCommands:
        def handle(self, _message: IncomingMessage) -> list[OutgoingMessage]:
            raise RuntimeError("boom")

    transport = FakeTransport()
    transport.incoming.append(IncomingMessage("!1", "!ping"))
    bot = MeshBot(transport, FailingCommands())

    with caplog.at_level(logging.ERROR):
        with suppress(RuntimeError):
            bot.process_next_message()

    assert bot.stats.failures == 1
    assert "Failed to process message from !1." in caplog.text


def test_configure_logging_applies_level() -> None:
    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
