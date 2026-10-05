"""Local transport used for development and testing."""

from collections import deque
from collections.abc import Callable

from meshbot.domain.messages import IncomingMessage, OutgoingMessage


class SimulatorTransport:
    """In-memory fake chat that behaves like a message transport."""

    def __init__(
        self,
        on_send: Callable[[OutgoingMessage], None] | None = None,
    ) -> None:
        self._incoming: deque[IncomingMessage] = deque()
        self.sent_messages: list[OutgoingMessage] = []
        self._on_send = on_send

    def receive(self) -> IncomingMessage | None:
        """Return the oldest queued incoming message."""
        if not self._incoming:
            return None
        return self._incoming.popleft()

    def send(self, message: OutgoingMessage) -> None:
        """Store an outgoing message and notify the simulator observer."""
        self.sent_messages.append(message)
        if self._on_send is not None:
            self._on_send(message)

    def inject_message(self, node_id: str, text: str) -> None:
        """Inject a virtual node message into the simulated network."""
        self._incoming.append(IncomingMessage(sender_id=node_id, text=text))
