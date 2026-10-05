"""Command handling for MeshBot."""

from typing import Protocol

from meshbot.domain.messages import Message


class Command(Protocol):
    """Interface implemented by bot commands."""

    name: str

    def execute(self, message: Message) -> Message | None:
        """Execute the command for an incoming message."""
        ...


class PingCommand:
    """Respond to /ping with pong."""

    name = "ping"

    def execute(self, message: Message) -> Message:
        """Return the pong response."""
        return Message(node_id=message.node_id, text="pong")


class CommandHandler:
    """Resolve and execute registered bot commands."""

    def __init__(self, commands: list[Command], prefix: str = "/") -> None:
        self._commands = {command.name: command for command in commands}
        self._prefix = prefix

    def handle(self, message: Message) -> Message | None:
        """Execute a matching command or return no response."""
        command_name = message.text.strip()

        if not command_name.startswith(self._prefix):
            return None

        command_name = command_name[len(self._prefix) :]
        command = self._commands.get(command_name)

        if command is None:
            return None

        return command.execute(message)
