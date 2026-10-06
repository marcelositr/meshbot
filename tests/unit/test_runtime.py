"""Tests for the production runtime."""

from threading import Event

import pytest

from meshbot.application.runtime import ProductionRuntime


class FakeBot:
    def __init__(self, stop_event: Event) -> None:
        self.calls = 0
        self._stop_event = stop_event

    def process_next_message(self) -> bool:
        self.calls += 1
        self._stop_event.set()
        return True


class FakeTransport:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_run_processes_messages_until_stop_and_closes_transport() -> None:
    stop_event = Event()
    bot = FakeBot(stop_event)
    transport = FakeTransport()
    runtime = ProductionRuntime(
        bot,  # type: ignore[arg-type]
        transport,  # type: ignore[arg-type]
        sleep=lambda _seconds: None,
    )

    runtime.run(stop_event)

    assert bot.calls == 1
    assert transport.closed


def test_run_closes_transport_when_bot_fails() -> None:
    class FailingBot:
        def process_next_message(self) -> bool:
            raise RuntimeError("boom")

    transport = FakeTransport()
    runtime = ProductionRuntime(
        FailingBot(),  # type: ignore[arg-type]
        transport,  # type: ignore[arg-type]
        sleep=lambda _seconds: None,
    )

    with pytest.raises(RuntimeError, match="boom"):
        runtime.run()

    assert transport.closed


def test_rejects_non_positive_poll_interval() -> None:
    transport = FakeTransport()

    with pytest.raises(ValueError, match="poll_interval_seconds"):
        ProductionRuntime(
            FakeBot(Event()),  # type: ignore[arg-type]
            transport,  # type: ignore[arg-type]
            poll_interval_seconds=0,
        )
