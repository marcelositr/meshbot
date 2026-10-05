"""Local transport used for development and testing."""

from collections import deque

from meshbot.domain.messages import Message


class SimulatorTransport:
    """In-memory fake chat that behaves like a message transport."""

    def __init__(self) -> None:
        self._incoming: deque[Message] = deque()
        self.sent_messages: list[Message] = []

    def receive(self) -> Message | None:
        """Return the oldest queued incoming message."""
        if not self._incoming:
            return None
        return self._incoming.popleft()

    def send(self, message: Message) -> None:
        """Store an outgoing message so the simulator can inspect it."""
        self.sent_messages.append(message)

    def inject_message(self, node_id: str, text: str) -> None:
        """Inject a virtual node message into the simulated network."""
        self._incoming.append(Message(node_id=node_id, text=text))
