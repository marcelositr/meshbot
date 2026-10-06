"""MeshBot application core."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.application.commands import CommandHandler
from meshbot.application.ports import MessageTransport
from meshbot.domain.messages import OutgoingMessage

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BotStats:
    """Basic counters for bot operation."""

    received: int = 0
    processed: int = 0
    sent: int = 0
    rejected: int = 0
    failures: int = 0


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
        self._received = 0
        self._processed = 0
        self._sent = 0
        self._rejected = 0
        self._failures = 0

    @property
    def stats(self) -> BotStats:
        """Return a snapshot of basic operational counters."""
        return BotStats(
            received=self._received,
            processed=self._processed,
            sent=self._sent,
            rejected=self._rejected,
            failures=self._failures,
        )

    def process_next_message(self) -> bool:
        """Process one queued message."""
        message = self._transport.receive()
        if message is None:
            return False

        self._received += 1
        logger.debug("Received message from %s.", message.sender_id)

        try:
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
                        self._sent += 1
                        self._rejected += 1
                        logger.info(
                            "Rejected message from unregistered sender %s.",
                            message.sender_id,
                        )
                        return True
                    else:
                        self._rejected += 1
                        logger.info(
                            "Rejected message from %s: %s.",
                            message.sender_id,
                            authorization.reason,
                        )
                        return True

            responses = self._commands.handle(message)

            for index, response in enumerate(responses):
                if index:
                    self._sleep(self._message_delay_seconds)
                self._transport.send(response)
                self._sent += 1
                logger.debug("Sent response to %s.", response.recipient_id)

            self._processed += 1
            logger.debug(
                "Processed message from %s with %d response(s).",
                message.sender_id,
                len(responses),
            )
            return True
        except Exception:
            self._failures += 1
            logger.exception("Failed to process message from %s.", message.sender_id)
            raise
