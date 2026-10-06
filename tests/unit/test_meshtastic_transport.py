"""Tests for the Meshtastic transport."""

from typing import Any

from meshbot.domain.messages import IncomingMessage, OutgoingMessage
from meshbot.infrastructure.meshtastic_transport import MeshtasticTransport


class FakePubSub:
    def __init__(self) -> None:
        self.callbacks: dict[str, Any] = {}

    def subscribe(self, callback: Any, topic: str) -> None:
        self.callbacks[topic] = callback

    def unsubscribe(self, callback: Any, topic: str) -> None:
        assert self.callbacks.pop(topic) == callback

    def emit(self, topic: str, packet: dict[str, Any] | None = None) -> None:
        self.callbacks[topic](packet or {})


class FakeInterface:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def sendText(self, text: str, **kwargs: Any) -> None:
        self.sent.append({"text": text, **kwargs})

    def close(self) -> None:
        self.closed = True


def test_connection_lifecycle_tracks_established_and_lost() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    assert not transport.is_connected

    pub.emit("meshtastic.connection.established")
    assert transport.is_connected

    pub.emit("meshtastic.connection.lost")
    assert not transport.is_connected


def test_receive_converts_meshtastic_text_packet() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        channel_index=2,
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    pub.emit(
        "meshtastic.receive.text",
        {"fromId": "!12345678", "decoded": {"text": "!ping"}},
    )

    assert transport.receive() == IncomingMessage("!12345678", "!ping")


def test_receive_ignores_malformed_packets() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    pub.emit("meshtastic.receive.text", {"fromId": "!12345678"})
    pub.emit("meshtastic.receive.text", {"decoded": {"text": "!ping"}})

    assert transport.receive() is None


def test_send_uses_destination_and_channel() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        channel_index=3,
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    transport.send(OutgoingMessage("!12345678", "pong"))

    assert interface.sent == [
        {
            "text": "pong",
            "destinationId": "!12345678",
            "channelIndex": 3,
        }
    ]


def test_close_unsubscribes_and_closes_interface() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    transport.close()

    assert not transport.is_connected
    assert interface.closed
    assert pub.callbacks == {}
