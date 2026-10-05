"""Messages exchanged between MeshBot and a transport."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Message:
    """A message received from or sent to a node."""

    node_id: str
    text: str
