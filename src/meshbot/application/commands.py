"""Command handling for MeshBot."""

from typing import Protocol

from meshbot.application.moderation import ModerationService
from meshbot.application.moderation_notifications import ModerationNotifier
from meshbot.application.users import UserService
from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherService,
    WeatherServiceUnavailableError,
)
from meshbot.domain.messages import Message


class Command(Protocol):
    """Interface implemented by bot commands."""

    name: str

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Execute the command for an incoming message."""
        ...


class PingCommand:
    """Respond to !ping with pong."""

    name = "ping"

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Return the pong response."""
        return (Message(node_id=message.node_id, text="pong"),)


class RegisterCommand:
    """Register a node as a normal user."""

    name = "registrar"

    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Register the requested node."""
        parts = message.text.strip().split(maxsplit=1)
        node_id = parts[1].strip() if len(parts) == 2 else ""

        result = self._user_service.register(message.node_id, node_id)
        responses = {
            "registered": f"Usuário {node_id} cadastrado.",
            "already_registered": f"Usuário {node_id} já está cadastrado.",
            "admin_required": "Apenas administradores podem cadastrar usuários.",
            "requester_not_registered": "Usuário não cadastrado.",
            "invalid_node_id": "Use: !registrar <node_id>",
        }
        return (Message(node_id=message.node_id, text=responses[result]),)


class TempoCommand:
    """Return a compact weather forecast for a requested city."""

    name = "tempo"

    def __init__(self, weather_service: WeatherService) -> None:
        self._weather_service = weather_service

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Resolve the requested city and format the forecast."""
        parts = message.text.strip().split(maxsplit=1)
        city = parts[1].strip() if len(parts) == 2 else ""

        if not city:
            return (Message(node_id=message.node_id, text="Use: !tempo <cidade>"),)

        try:
            forecast = self._weather_service.get_forecast(city)
        except CityNotFoundError:
            return (
                Message(
                    node_id=message.node_id,
                    text=f'Não encontrei "{city}". Use !tempo ibge <codigo>.',
                ),
            )
        except AmbiguousCityError as exc:
            choices = ", ".join(exc.matches)
            return (
                Message(
                    node_id=message.node_id,
                    text=f"Encontrei mais de uma cidade: {choices}",
                ),
                Message(
                    node_id=message.node_id,
                    text="Use !tempo <cidade>/<UF>.",
                ),
            )
        except WeatherServiceUnavailableError:
            return (
                Message(
                    node_id=message.node_id,
                    text="Serviço de previsão indisponível no momento.",
                ),
            )

        return (
            Message(node_id=message.node_id, text=f"{forecast.city}: {forecast.summary}"),
            Message(
                node_id=message.node_id,
                text=f"Temperatura: {forecast.temperature_min}°C a {forecast.temperature_max}°C",
            ),
            Message(
                node_id=message.node_id,
                text=f"Umidade: {forecast.humidity_min}% a {forecast.humidity_max}%",
            ),
            Message(
                node_id=message.node_id,
                text=f"Vento: {forecast.wind_direction}, {forecast.wind_intensity}",
            ),
        )


class CommandHandler:
    """Resolve and execute registered bot commands."""

    def __init__(self, commands: list[Command], prefix: str = "!") -> None:
        self._commands = {command.name: command for command in commands}
        self._prefix = prefix

    def handle(self, message: Message) -> tuple[Message, ...]:
        """Execute a matching command or return no responses."""
        command_text = message.text.strip()

        if not command_text.startswith(self._prefix):
            return ()

        command_text = command_text[len(self._prefix) :]
        command_name = command_text.split(maxsplit=1)[0] if command_text else ""
        command = self._commands.get(command_name)

        if command is None:
            return ()

        return command.execute(message)


class BlockCommand:
    """Block a registered user."""

    name = "bloquear"

    def __init__(
        self,
        moderation_service: ModerationService,
        notifier: ModerationNotifier,
    ) -> None:
        self._moderation_service = moderation_service
        self._notifier = notifier

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Block the requested user."""
        parts = message.text.strip().split(maxsplit=1)
        target_id = parts[1].strip() if len(parts) == 2 else ""

        if not target_id:
            return (
                Message(
                    node_id=message.node_id,
                    text="Use: !bloquear <node_id>",
                ),
            )

        result = self._moderation_service.block(message.node_id, target_id)
        if result == "blocked":
            return self._notifier.notify("blocked", message.node_id, target_id)

        responses = {
            "already_blocked": f"Usuário {target_id} já está bloqueado.",
            "admin_required": "Apenas administradores podem moderar usuários.",
            "requester_not_registered": "Usuário não cadastrado.",
            "target_not_registered": f"Usuário {target_id} não está cadastrado.",
            "cannot_moderate_admin": "Administradores não podem moderar administradores.",
        }
        return (Message(node_id=message.node_id, text=responses[result]),)


class UnblockCommand:
    """Unblock a registered user."""

    name = "desbloquear"

    def __init__(
        self,
        moderation_service: ModerationService,
        notifier: ModerationNotifier,
    ) -> None:
        self._moderation_service = moderation_service
        self._notifier = notifier

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Unblock the requested user."""
        parts = message.text.strip().split(maxsplit=1)
        target_id = parts[1].strip() if len(parts) == 2 else ""

        if not target_id:
            return (
                Message(
                    node_id=message.node_id,
                    text="Use: !desbloquear <node_id>",
                ),
            )

        result = self._moderation_service.unblock(message.node_id, target_id)
        if result == "unblocked":
            return self._notifier.notify("unblocked", message.node_id, target_id)

        responses = {
            "not_blocked": f"Usuário {target_id} não está bloqueado.",
            "admin_required": "Apenas administradores podem moderar usuários.",
            "requester_not_registered": "Usuário não cadastrado.",
            "target_not_registered": f"Usuário {target_id} não está cadastrado.",
            "cannot_moderate_admin": "Administradores não podem moderar administradores.",
        }
        return (Message(node_id=message.node_id, text=responses[result]),)


class SilenceCommand:
    """Silence a registered user."""

    name = "silenciar"

    def __init__(
        self,
        moderation_service: ModerationService,
        notifier: ModerationNotifier,
    ) -> None:
        self._moderation_service = moderation_service
        self._notifier = notifier

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Silence the requested user."""
        parts = message.text.strip().split()
        target_id = parts[1] if len(parts) >= 2 else ""
        minutes_text = parts[2] if len(parts) >= 3 else ""

        if not target_id:
            return (
                Message(
                    node_id=message.node_id,
                    text="Use: !silenciar <node_id> [minutos]",
                ),
            )

        minutes: int | None = None
        if minutes_text:
            try:
                minutes = int(minutes_text)
            except ValueError:
                return (
                    Message(
                        node_id=message.node_id,
                        text="Informe um número inteiro de minutos.",
                    ),
                )

        result = self._moderation_service.silence(
            message.node_id,
            target_id,
            minutes,
        )
        duration = (
            minutes
            if minutes is not None
            else self._moderation_service.default_silence_minutes
        )
        if result == "silenced":
            return self._notifier.notify(
                "silenced",
                message.node_id,
                target_id,
                duration,
            )

        responses = {
            "invalid_minutes": "O tempo de silêncio deve ser maior que zero.",
            "admin_required": "Apenas administradores podem moderar usuários.",
            "requester_not_registered": "Usuário não cadastrado.",
            "target_not_registered": f"Usuário {target_id} não está cadastrado.",
            "cannot_moderate_admin": "Administradores não podem moderar administradores.",
        }
        return (Message(node_id=message.node_id, text=responses[result]),)
