"""MeshBot application core."""

from meshbot.application.commands import CommandHandler, PingCommand
from meshbot.application.ports import MessageTransport


class MeshBot:
    """Process incoming messages and produce bot responses."""

    def __init__(self, transport: MessageTransport, command_prefix: str = "/") -> None:
        self._transport = transport
        self._commands = CommandHandler([PingCommand()], prefix=command_prefix)

    def process_next_message(self) -> bool:
        """Process one queued message.

        Returns True when a message was processed and False when the
        transport had nothing available.
        """
        message = self._transport.receive()
        if message is None:
            return False

        response = self._commands.handle(message)
        if response is not None:
            self._transport.send(response)

        return True
