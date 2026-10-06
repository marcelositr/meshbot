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

def test_close_during_reconnect_closes_new_interface() -> None:
    from threading import Event

    pub = FakePubSub()
    first = FakeInterface()
    second = FakeInterface()
    factory_started = Event()
    release_factory = Event()
    interfaces = iter([first, second])

    def factory(_transport: str, _device: str | None) -> FakeInterface:
        interface = next(interfaces)
        if interface is second:
            factory_started.set()
            release_factory.wait(1)
        return interface

    transport = MeshtasticTransport(
        "usb",
        interface_factory=factory,
        pubsub_module=pub,
        reconnect_initial_delay=0,
        reconnect_max_delay=1,
    )

    pub.emit("meshtastic.connection.established")
    pub.emit("meshtastic.connection.lost")

    assert factory_started.wait(1)
    transport.close()
    release_factory.set()

    for _ in range(100):
        if second.closed:
            break
        Event().wait(0.01)

    assert second.closed


def test_connection_established_during_interface_creation_is_not_lost() -> None:
    from threading import Event

    pub = FakePubSub()
    first = FakeInterface()
    second = FakeInterface()
    created = Event()
    interfaces = iter([first, second])

    def factory(_transport: str, _device: str | None) -> FakeInterface:
        interface = next(interfaces)
        if interface is second:
            pub.emit("meshtastic.connection.established")
            created.set()
        return interface

    transport = MeshtasticTransport(
        "usb",
        interface_factory=factory,
        pubsub_module=pub,
        reconnect_initial_delay=0,
        reconnect_max_delay=1,
    )

    pub.emit("meshtastic.connection.established")
    pub.emit("meshtastic.connection.lost")

    assert created.wait(1)
    assert transport.is_connected

    transport.close()


def test_connection_loss_recreates_interface_and_recovers() -> None:
    from threading import Event

    pub = FakePubSub()
    first = FakeInterface()
    second = FakeInterface()
    created = Event()
    interfaces = iter([first, second])

    def factory(_transport: str, _device: str | None) -> FakeInterface:
        interface = next(interfaces)
        if interface is second:
            created.set()
            pub.emit("meshtastic.connection.established")
        return interface

    transport = MeshtasticTransport(
        "usb",
        interface_factory=factory,
        pubsub_module=pub,
        reconnect_initial_delay=0,
        reconnect_max_delay=1,
    )

    pub.emit("meshtastic.connection.established")
    assert transport.is_connected

    pub.emit("meshtastic.connection.lost")

    assert created.wait(1)
    assert transport.is_connected
    assert first.closed
    assert not second.closed

    transport.close()


def test_rejects_unknown_transport() -> None:
    pub = FakePubSub()
    interface = FakeInterface()

    try:
        MeshtasticTransport(
            "serial",
            interface_factory=lambda _transport, _device: interface,
            pubsub_module=pub,
        )
    except ValueError as exc:
        assert "usb, wifi, or bluetooth" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_close_is_idempotent() -> None:
    pub = FakePubSub()
    interface = FakeInterface()
    transport = MeshtasticTransport(
        "usb",
        interface_factory=lambda _transport, _device: interface,
        pubsub_module=pub,
    )

    transport.close()
    transport.close()

    assert interface.closed
    assert pub.callbacks == {}


def test_send_propagates_interface_failure() -> None:
    pub = FakePubSub()

    class FailingInterface(FakeInterface):
        def sendText(self, text: str, **kwargs: Any) -> None:
            raise RuntimeError("radio unavailable")

    transport = MeshtasticTransport(
        "usb",
        interface_factory=lambda _transport, _device: FailingInterface(),
        pubsub_module=pub,
    )

    try:
        transport.send(OutgoingMessage("!12345678", "pong"))
    except RuntimeError as exc:
        assert str(exc) == "radio unavailable"
    else:
        raise AssertionError("Expected RuntimeError")


def test_connection_loss_recreates_interface_after_failed_attempt() -> None:
    from threading import Event

    pub = FakePubSub()
    first = FakeInterface()
    second = FakeInterface()
    attempts = 0
    recovered = Event()

    def factory(_transport: str, _device: str | None) -> FakeInterface:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise RuntimeError("temporary radio failure")
        if attempts == 3:
            pub.emit("meshtastic.connection.established")
            recovered.set()
            return second
        return first

    transport = MeshtasticTransport(
        "usb",
        interface_factory=factory,
        pubsub_module=pub,
        reconnect_initial_delay=0,
        reconnect_max_delay=0.01,
    )

    pub.emit("meshtastic.connection.established")
    pub.emit("meshtastic.connection.lost")

    assert recovered.wait(1)
    assert transport.is_connected
    assert attempts >= 3

    transport.close()
