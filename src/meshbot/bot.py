"""MeshBot application core."""

from meshbot.messages import Message
from meshbot.transport import MessageTransport


class MeshBot:
    """Process incoming messages and produce bot responses."""

    def __init__(self, transport: MessageTransport, command_prefix: str = "/") -> None:
        self._transport = transport
        self._command_prefix = command_prefix

    def process_next_message(self) -> bool:
        """Process one queued message.

        Returns True when a message was processed and False when the
        transport had nothing available.
        """
        message = self._transport.receive()
        if message is None:
            return False

        response = self._handle_message(message)
        if response is not None:
            self._transport.send(response)

        return True

    def _handle_message(self, message: Message) -> Message | None:
        command = message.text.strip()

        if command == f"{self._command_prefix}ping":
            return Message(node_id=message.node_id, text="pong")

        return None
