"""Tests for the simulator transport."""

from meshbot.domain.messages import Message
from meshbot.infrastructure.simulator import SimulatorTransport


def test_send_stores_message_and_calls_observer() -> None:
    sent: list[Message] = []

    transport = SimulatorTransport(on_send=sent.append)
    message = Message(node_id="!12345678", text="pong")

    transport.send(message)

    assert transport.sent_messages == [message]
    assert sent == [message]
