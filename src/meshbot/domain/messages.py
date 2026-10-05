"""Messages exchanged between MeshBot and a transport."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncomingMessage:
    """A message received from a node."""

    sender_id: str
    text: str


@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    """A message sent to a destination node."""

    recipient_id: str
    text: str
