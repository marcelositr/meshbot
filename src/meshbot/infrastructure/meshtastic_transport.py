"""Meshtastic transport implementation."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import Event, Lock, Thread
from typing import Any

from meshbot.domain.messages import IncomingMessage, OutgoingMessage


class MeshtasticTransport:
    """Adapt the Meshtastic Python client to the MessageTransport contract."""

    def __init__(
        self,
        transport: str,
        channel_index: int = 0,
        device: str | None = None,
        interface_factory: Callable[[str, str | None], Any] | None = None,
        pubsub_module: Any | None = None,
        reconnect_initial_delay: float = 1.0,
        reconnect_max_delay: float = 30.0,
    ) -> None:
        if transport not in {"usb", "wifi", "bluetooth"}:
            raise ValueError("Meshtastic transport must be usb, wifi, or bluetooth.")

        self._channel_index = channel_index
        self._incoming: deque[IncomingMessage] = deque()
        self._connected = False
        self._closed = False
        self._reconnect_lock = Lock()
        self._reconnect_stop = Event()
        self._reconnected = Event()
        self._reconnect_initial_delay = reconnect_initial_delay
        self._reconnect_max_delay = reconnect_max_delay
        self._interface_factory = interface_factory
        self._transport = transport
        self._device = device
        self._pub = pubsub_module or self._load_pubsub()
        self._pub.subscribe(
            self._on_connection_established, "meshtastic.connection.established"
        )
        self._pub.subscribe(self._on_connection_lost, "meshtastic.connection.lost")
        self._pub.subscribe(self._on_text, "meshtastic.receive.text")
        self._interface = self._create_interface(
            transport, device, interface_factory
        )

    @property
    def is_connected(self) -> bool:
        """Return whether the Meshtastic client reports an active connection."""
        return self._connected

    def receive(self) -> IncomingMessage | None:
        """Return the oldest received text message, if available."""
        if not self._incoming:
            return None
        return self._incoming.popleft()

    def send(self, message: OutgoingMessage) -> None:
        """Send a text message through the configured Meshtastic channel."""
        self._interface.sendText(
            message.text,
            destinationId=message.recipient_id,
            channelIndex=self._channel_index,
        )

    def close(self) -> None:
        """Unsubscribe callbacks and close the radio interface."""
        self._closed = True
        self._reconnect_stop.set()
        self._pub.unsubscribe(
            self._on_connection_established, "meshtastic.connection.established"
        )
        self._pub.unsubscribe(self._on_connection_lost, "meshtastic.connection.lost")
        self._pub.unsubscribe(self._on_text, "meshtastic.receive.text")
        close = getattr(self._interface, "close", None)
        if close is not None:
            close()
        self._connected = False

    def _on_connection_established(self, *_: Any, **__: Any) -> None:
        self._connected = True
        self._reconnected.set()

    def _on_connection_lost(self, *_: Any, **__: Any) -> None:
        self._connected = False
        self._reconnected.clear()
        self._start_reconnect()

    def _start_reconnect(self) -> None:
        if self._closed or not self._reconnect_lock.acquire(blocking=False):
            return
        try:
            Thread(
                target=self._reconnect_loop,
                name="MeshBotMeshtasticReconnect",
                daemon=True,
            ).start()
        except Exception:
            self._reconnect_lock.release()
            raise

    def _reconnect_loop(self) -> None:
        try:
            delay = self._reconnect_initial_delay
            while not self._closed and not self._connected:
                if self._reconnect_stop.wait(delay):
                    return
                try:
                    old_interface = self._interface
                    close = getattr(old_interface, "close", None)
                    if close is not None:
                        close()
                    new_interface = self._create_interface(
                        self._transport, self._device, self._interface_factory
                    )
                    if self._closed:
                        close = getattr(new_interface, "close", None)
                        if close is not None:
                            close()
                        return
                    self._interface = new_interface
                except Exception:
                    delay = min(delay * 2, self._reconnect_max_delay)
                    continue

                self._reconnected.clear()
                if self._reconnected.wait(self._reconnect_max_delay):
                    return
                delay = min(delay * 2, self._reconnect_max_delay)
        finally:
            self._reconnect_lock.release()

    def _on_text(self, packet: dict[str, Any], **_: Any) -> None:
        decoded = packet.get("decoded")
        if not isinstance(decoded, dict):
            return

        text = decoded.get("text")
        sender_id = packet.get("fromId")
        if not isinstance(text, str) or not isinstance(sender_id, str):
            return

        self._incoming.append(IncomingMessage(sender_id=sender_id, text=text))

    @staticmethod
    def _load_pubsub() -> Any:
        try:
            from pubsub import pub
        except ImportError as exc:
            raise RuntimeError(
                "Meshtastic support requires the 'meshtastic' package."
            ) from exc
        return pub

    @staticmethod
    def _create_interface(
        transport: str,
        device: str | None,
        factory: Callable[[str, str | None], Any] | None,
    ) -> Any:
        if factory is not None:
            return factory(transport, device)

        try:
            if transport == "usb":
                from meshtastic.serial_interface import SerialInterface

                return SerialInterface(devPath=device or None)

            if transport == "wifi":
                from meshtastic.tcp_interface import TCPInterface

                return TCPInterface(hostname=device or None)

            from meshtastic.ble_interface import BLEInterface

            return BLEInterface(address=device or None)
        except ImportError as exc:
            raise RuntimeError(
                "Meshtastic support requires the 'meshtastic' package."
            ) from exc
