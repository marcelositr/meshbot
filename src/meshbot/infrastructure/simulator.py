"""Local transport used for development and testing."""

from collections import deque
from collections.abc import Callable

from meshbot.domain.messages import Message


class SimulatorTransport:
    """In-memory fake chat that behaves like a message transport."""

    def __init__(
        self,
        on_send: Callable[[Message], None] | None = None,
    ) -> None:
        self._incoming: deque[Message] = deque()
        self.sent_messages: list[Message] = []
        self._on_send = on_send

    def receive(self) -> Message | None:
        """Return the oldest queued incoming message."""
        if not self._incoming:
            return None
        return self._incoming.popleft()

    def send(self, message: Message) -> None:
        """Store an outgoing message and notify the simulator observer."""
        self.sent_messages.append(message)
        if self._on_send is not None:
            self._on_send(message)

    def inject_message(self, node_id: str, text: str) -> None:
        """Inject a virtual node message into the simulated network."""
        self._incoming.append(Message(node_id=node_id, text=text))
