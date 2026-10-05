"""Communication boundaries required by the application layer."""

from typing import Protocol

from meshbot.domain.messages import IncomingOutgoingMessage, OutgoingOutgoingMessage


class OutgoingMessageTransport(Protocol):
    """Interface required by the bot to communicate."""

    def receive(self) -> IncomingMessage | None:
        """Return the next incoming message, if one is available."""
        ...

    def send(self, message: OutgoingMessage) -> None:
        """Send a message to a node."""
        ...
