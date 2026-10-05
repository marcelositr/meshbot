from meshbot.application.commands import (
    BlockCommand,
    CommandHandler,
    PingCommand,
    SilenceCommand,
    TempoCommand,
    UnblockCommand,
)
from meshbot.application.moderation import ModerationService
from meshbot.application.moderation_notifications import ModerationNotifier
from meshbot.application.weather import WeatherForecast
from meshbot.domain.messages import IncomingMessage, OutgoingMessage
from meshbot.domain.users import User, UserRole
from meshbot.infrastructure.weather import FakeWeatherService


def test_ping_command_returns_pong() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="!ping"))

    assert response == (OutgoingMessage(recipient_id="!12345678", text="pong"),)


def test_unknown_command_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="!unknown"))

    assert response == ()


def test_non_command_message_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="hello"))

    assert response == ()


def test_tempo_command_formats_four_compact_messages() -> None:
    service = FakeWeatherService(
        WeatherForecast(
            city="Ituverava/SP",
            summary="Nublado c/ pancadas de chuva e trovoadas isoladas.",
            temperature_min=19,
            temperature_max=31,
            humidity_min=50,
            humidity_max=90,
            wind_direction="NE-N",
            wind_intensity="fracos",
        )
    )
    handler = CommandHandler([TempoCommand(service)])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="!tempo Ituverava"))

    assert [message.text for message in response] == [
        "Ituverava/SP: Nublado c/ pancadas de chuva e trovoadas isoladas.",
        "Temperatura: 19°C a 31°C",
        "Umidade: 50% a 90%",
        "Vento: NE-N, fracos",
    ]


def test_tempo_command_requires_city() -> None:
    handler = CommandHandler([TempoCommand(FakeWeatherService())])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="!tempo"))

    assert response[0].text == "Use: !tempo <cidade>"


def test_tempo_command_accepts_city_and_uf() -> None:
    service = FakeWeatherService(
        WeatherForecast(
            city="Ituverava/SP",
            summary="Tempo estável.",
            temperature_min=18,
            temperature_max=30,
            humidity_min=45,
            humidity_max=85,
            wind_direction="NE",
            wind_intensity="fraco",
        )
    )
    handler = CommandHandler([TempoCommand(service)])

    response = handler.handle(IncomingMessage(sender_id="!12345678", text="!tempo Ituverava/SP"))

    assert response[0].text == "Ituverava/SP: Tempo estável."


class InMemoryUsers:
    """Small repository fake for command tests."""

    def __init__(self, users: tuple[User, ...]) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        """Return a registered user."""
        return self._users.get(node_id)

    def save(self, user: User) -> None:
        """Store a user."""
        self._users[user.node_id] = user

    def list_all(self) -> tuple[User, ...]:
        """Return all users."""
        return tuple(self._users.values())


def test_block_command_blocks_user() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
        )
    )
    handler = CommandHandler(
        [BlockCommand(ModerationService(repository), ModerationNotifier(repository))]
    )

    response = handler.handle(IncomingMessage(sender_id="!11111111", text="!bloquear !22222222"))

    assert [message.recipient_id for message in response] == ["!22222222", "!11111111"]
    assert response[0].text == "MeshBot: Você foi bloqueado."
    assert response[1].text == "MeshBot: Admin !11111111 bloqueou !22222222."
    assert repository.get("!22222222") == User("!22222222", blocked=True)


def test_unblock_command_unblocks_user() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222", blocked=True),
        )
    )
    handler = CommandHandler(
        [UnblockCommand(ModerationService(repository), ModerationNotifier(repository))]
    )

    response = handler.handle(IncomingMessage(sender_id="!11111111", text="!desbloquear !22222222"))

    assert [message.recipient_id for message in response] == ["!22222222", "!11111111"]
    assert response[0].text == "MeshBot: Seu acesso ao MeshBot foi desbloqueado."
    assert response[1].text == "MeshBot: Admin !11111111 desbloqueou !22222222."
    assert repository.get("!22222222") == User("!22222222")


def test_silence_command_accepts_custom_duration() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
        )
    )
    handler = CommandHandler(
        [SilenceCommand(ModerationService(repository), ModerationNotifier(repository))]
    )

    response = handler.handle(IncomingMessage(sender_id="!11111111", text="!silenciar !22222222 15"))

    assert [message.recipient_id for message in response] == ["!22222222", "!11111111"]
    assert response[0].text == "MeshBot: Você foi silenciado por 15 minutos."
    assert response[1].text == "MeshBot: Admin !11111111 silenciou !22222222 por 15 minutos."
