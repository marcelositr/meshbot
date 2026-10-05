"""MeshBot application core."""

import time
from collections.abc import Callable

from meshbot.application.commands import CommandHandler
from meshbot.application.ports import MessageTransport


class MeshBot:
    """Process incoming messages and produce bot responses."""

    def __init__(
        self,
        transport: MessageTransport,
        command_handler: CommandHandler,
        message_delay_seconds: float = 0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._transport = transport
        self._commands = command_handler
        self._message_delay_seconds = message_delay_seconds
        self._sleep = sleep

    def process_next_message(self) -> bool:
        """Process one queued message."""
        message = self._transport.receive()
        if message is None:
            return False

        responses = self._commands.handle(message)

        for index, response in enumerate(responses):
            if index:
                self._sleep(self._message_delay_seconds)
            self._transport.send(response)

        return True
