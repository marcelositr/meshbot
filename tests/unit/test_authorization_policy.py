"""Integration tests for authorization in the bot."""

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.application.bot import MeshBot
from meshbot.application.commands import CommandHandler, PingCommand
from meshbot.domain.users import User
from meshbot.infrastructure.simulator import SimulatorTransport


class InMemoryUsers:
    """Small user repository fake for integration tests."""

    def __init__(self, users: tuple[User, ...]) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        """Return a registered user."""
        return self._users.get(node_id)


def test_unregistered_user_is_ignored() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(
        transport,
        CommandHandler([PingCommand()]),
        authorization=AuthorizationPolicy(InMemoryUsers(())),
    )

    transport.inject_message("!99999999", "!ping")

    assert bot.process_next_message() is True
    assert transport.sent_messages == []


def test_registered_user_can_use_bot() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(
        transport,
        CommandHandler([PingCommand()]),
        authorization=AuthorizationPolicy(InMemoryUsers((User("!12345678"),))),
    )

    transport.inject_message("!12345678", "!ping")

    assert bot.process_next_message() is True
    assert transport.sent_messages[0].text == "pong"


def test_blocked_user_is_ignored() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(
        transport,
        CommandHandler([PingCommand()]),
        authorization=AuthorizationPolicy(InMemoryUsers((User("!12345678", blocked=True),))),
    )

    transport.inject_message("!12345678", "!ping")

    assert bot.process_next_message() is True
    assert transport.sent_messages == []
