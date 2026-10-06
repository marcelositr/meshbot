"""Tests for the simulator transport."""

from meshbot.domain.messages import OutgoingMessage
from meshbot.infrastructure.simulator import SimulatorTransport


def test_send_stores_message_and_calls_observer() -> None:
    sent: list[OutgoingMessage] = []

    transport = SimulatorTransport(on_send=sent.append)
    message = OutgoingMessage(recipient_id="!12345678", text="pong")

    transport.send(message)

    assert transport.sent_messages == [message]
    assert sent == [message]


def test_set_observer_replaces_callback() -> None:
    first: list[OutgoingMessage] = []
    second: list[OutgoingMessage] = []
    transport = SimulatorTransport(on_send=first.append)

    transport.set_observer(second.append)
    message = OutgoingMessage(recipient_id="!12345678", text="pong")
    transport.send(message)

    assert first == []
    assert second == [message]
