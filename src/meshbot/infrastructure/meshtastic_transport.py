"""Meshtastic transport implementation."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
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
    ) -> None:
        if transport not in {"usb", "wifi", "bluetooth"}:
            raise ValueError("Meshtastic transport must be usb, wifi, or bluetooth.")

        self._channel_index = channel_index
        self._incoming: deque[IncomingMessage] = deque()
        self._connected = False
        self._pub = pubsub_module or self._load_pubsub()
        self._pub.subscribe(self._on_connection_established, "meshtastic.connection.established")
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
        self._pub.unsubscribe(self._on_connection_established, "meshtastic.connection.established")
        self._pub.unsubscribe(self._on_connection_lost, "meshtastic.connection.lost")
        self._pub.unsubscribe(self._on_text, "meshtastic.receive.text")
        close = getattr(self._interface, "close", None)
        if close is not None:
            close()

    def _on_connection_established(self, **_: Any) -> None:
        self._connected = True

    def _on_connection_lost(self, **_: Any) -> None:
        self._connected = False

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
