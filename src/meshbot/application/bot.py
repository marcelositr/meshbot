"""MeshBot application core."""

import time
from collections.abc import Callable

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.application.commands import CommandHandler
from meshbot.application.ports import MessageTransport
from meshbot.domain.messages import OutgoingMessage


class MeshBot:
    """Process incoming messages and produce bot responses."""

    def __init__(
        self,
        transport: MessageTransport,
        command_handler: CommandHandler,
        authorization: AuthorizationPolicy | None = None,
        message_delay_seconds: float = 0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._transport = transport
        self._commands = command_handler
        self._authorization = authorization
        self._message_delay_seconds = message_delay_seconds
        self._sleep = sleep

    def process_next_message(self) -> bool:
        """Process one queued message."""
        message = self._transport.receive()
        if message is None:
            return False

        if self._authorization is not None:
            authorization = self._authorization.check(message.sender_id)
            if not authorization.allowed:
                is_registration = message.text.strip() == "!registrar"
                if authorization.reason == "not_registered" and is_registration:
                    pass
                elif authorization.reason == "not_registered":
                    self._transport.send(
                        OutgoingMessage(
                            recipient_id=message.sender_id,
                            text="Você não está cadastrado. Use !registrar.",
                        )
                    )
                    return True
                else:
                    return True

        responses = self._commands.handle(message)

        for index, response in enumerate(responses):
            if index:
                self._sleep(self._message_delay_seconds)
            self._transport.send(response)

        return True
