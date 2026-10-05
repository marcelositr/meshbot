"""Integration tests for MeshBot authorization and registration flow."""

from datetime import UTC, datetime, timedelta

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.application.bot import MeshBot
from meshbot.application.commands import (
    CommandHandler,
    NameCommand,
    PingCommand,
    RegisterCommand,
)
from meshbot.application.users import UserService
from meshbot.domain.messages import OutgoingMessage
from meshbot.domain.users import User
from meshbot.infrastructure.simulator import SimulatorTransport


class InMemoryUsers:
    def __init__(self, users: tuple[User, ...] = ()) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        return self._users.get(node_id)

    def save(self, user: User) -> None:
        self._users[user.node_id] = user

    def list_all(self) -> tuple[User, ...]:
        return tuple(self._users.values())


def make_bot(repository: InMemoryUsers) -> tuple[MeshBot, SimulatorTransport]:
    transport = SimulatorTransport()
    user_service = UserService(repository)
    handler = CommandHandler(
        [RegisterCommand(user_service), NameCommand(user_service), PingCommand()]
    )
    bot = MeshBot(
        transport,
        handler,
        authorization=AuthorizationPolicy(repository),
    )
    return bot, transport


def test_unregistered_user_is_told_how_to_register() -> None:
    bot, transport = make_bot(InMemoryUsers())
    transport.inject_message("!12345678", "!ping")
    assert bot.process_next_message() is True
    assert transport.sent_messages == [
        OutgoingMessage(
            recipient_id="!12345678",
            text="Você não está cadastrado. Use !registrar.",
        )
    ]


def test_unregistered_user_can_register_and_then_use_commands() -> None:
    repository = InMemoryUsers()
    bot, transport = make_bot(repository)
    transport.inject_message("!12345678", "!registrar")
    assert bot.process_next_message() is True
    assert transport.sent_messages == [
        OutgoingMessage(
            recipient_id="!12345678",
            text="Cadastro realizado.",
        )
    ]
    transport.sent_messages.clear()
    transport.inject_message("!12345678", "!nome João da Silva")
    assert bot.process_next_message() is True
    assert transport.sent_messages == [
        OutgoingMessage(
            recipient_id="!12345678",
            text="Seu nome agora é João da Silva.",
        )
    ]
    transport.sent_messages.clear()
    transport.inject_message("!12345678", "!ping")
    assert bot.process_next_message() is True
    assert transport.sent_messages == [
        OutgoingMessage(recipient_id="!12345678", text="pong")
    ]


def test_blocked_user_is_silently_rejected() -> None:
    bot, transport = make_bot(InMemoryUsers((User("!12345678", blocked=True),)))
    transport.inject_message("!12345678", "!ping")
    assert bot.process_next_message() is True
    assert transport.sent_messages == []


def test_silenced_user_is_silently_rejected() -> None:
    user = User(
        "!12345678",
        silenced_until=datetime.now(UTC) + timedelta(minutes=5),
    )
    bot, transport = make_bot(InMemoryUsers((user,)))
    transport.inject_message("!12345678", "!ping")
    assert bot.process_next_message() is True
    assert transport.sent_messages == []
