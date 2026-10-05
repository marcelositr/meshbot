"""Communication boundaries required by the application layer."""

from typing import Protocol

from meshbot.domain.messages import Message


class MessageTransport(Protocol):
    """Interface required by the bot to communicate."""

    def receive(self) -> Message | None:
        """Return the next incoming message, if one is available."""
        ...

    def send(self, message: Message) -> None:
        """Send a message to a node."""
        ...
