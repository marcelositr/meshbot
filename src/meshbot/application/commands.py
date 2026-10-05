"""Command handling for MeshBot."""

from typing import Protocol

from meshbot.application.defense_civil import (
    DefenseCivilAmbiguousCityError,
    DefenseCivilCityNotFoundError,
    DefenseCivilService,
    DefenseCivilServiceUnavailableError,
)
from meshbot.application.moderation import ModerationService
from meshbot.application.moderation_notifications import ModerationNotifier
from meshbot.application.users import UserService
from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherService,
    WeatherServiceUnavailableError,
)
from meshbot.domain.messages import IncomingMessage, OutgoingMessage
from meshbot.domain.users import normalize_user_name


class Command(Protocol):
    """Interface implemented by bot commands."""

    name: str

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Execute the command for an incoming message."""
        ...


class PingCommand:
    """Respond to !ping with pong."""

    name = "ping"

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Return the pong response."""
        return (OutgoingMessage(recipient_id=message.sender_id, text="pong"),)


class RegisterCommand:
    """Register a node as a normal user."""

    name = "registrar"

    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Register the requested node."""
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) != 1:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !registrar.",
                ),
            )

        result = self._user_service.register(message.sender_id)
        responses = {
            "registered": "Cadastro realizado.",
            "already_registered": "Você já está cadastrado.",
            "invalid_node_id": "Não foi possível identificar seu node.",
        }
        return (OutgoingMessage(recipient_id=message.sender_id, text=responses[result]),)


class NameCommand:
    """Set or replace the current user's display name."""

    name = "nome"

    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Set the sender's display name."""
        parts = message.text.strip().split(maxsplit=1)
        name = parts[1].strip() if len(parts) == 2 else ""

        if not name:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !nome <nome>.",
                ),
            )

        try:
            normalized_name = normalize_user_name(name)
        except ValueError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Nome inválido.",
                ),
            )

        result = self._user_service.set_name(message.sender_id, normalized_name)
        responses = {
            "name_updated": f"Seu nome agora é {normalized_name}.",
            "requester_not_registered": "Você não está cadastrado.",
            "invalid_name": "Nome inválido.",
        }
        return (
            OutgoingMessage(
                recipient_id=message.sender_id,
                text=responses[result],
            ),
        )


class TempoCommand:
    """Return a compact weather forecast for a requested city."""

    name = "tempo"

    def __init__(self, weather_service: WeatherService) -> None:
        self._weather_service = weather_service

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Resolve the requested city and format the forecast."""
        parts = message.text.strip().split(maxsplit=1)
        city = parts[1].strip() if len(parts) == 2 else ""

        if not city:
            return (OutgoingMessage(recipient_id=message.sender_id, text="Use: !tempo <cidade>."),)

        try:
            forecast = self._weather_service.get_forecast(city)
        except CityNotFoundError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Cidade não encontrada.",
                ),
            )
        except AmbiguousCityError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Informe a cidade e o estado.",
                ),
            )
        except WeatherServiceUnavailableError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Não consegui consultar o tempo.",
                ),
            )

        return (
            OutgoingMessage(
                recipient_id=message.sender_id,
                text=f"{forecast.city}: {forecast.summary}",
            ),
            OutgoingMessage(
                recipient_id=message.sender_id,
                text=f"Temperatura: {forecast.temperature_min}°C a {forecast.temperature_max}°C",
            ),
            OutgoingMessage(
                recipient_id=message.sender_id,
                text=f"Umidade: {forecast.humidity_min}% a {forecast.humidity_max}%",
            ),
            OutgoingMessage(
                recipient_id=message.sender_id,
                text=f"Vento: {forecast.wind_direction}, {forecast.wind_intensity}",
            ),
        )


class DefenseCivilCommand:
    """Return active Defense Civil alerts for a requested city."""

    name = "defesacivil"

    def __init__(self, service: DefenseCivilService) -> None:
        self._service = service

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Resolve the requested city and return active alerts."""
        parts = message.text.strip().split(maxsplit=1)
        location = parts[1].strip() if len(parts) == 2 else ""

        if not location:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !defesacivil <cidade>.",
                ),
            )

        try:
            alerts = self._service.get_alerts(location)
        except DefenseCivilCityNotFoundError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Cidade não encontrada.",
                ),
            )
        except DefenseCivilAmbiguousCityError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Informe a cidade e o estado.",
                ),
            )
        except DefenseCivilServiceUnavailableError:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Não consegui consultar os alertas.",
                ),
            )

        if not alerts:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="⚠️ ALERTAS DEFESA CIVIL",
                ),
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Nenhum alerta ativo.",
                ),
            )

        responses: list[OutgoingMessage] = [
            OutgoingMessage(
                recipient_id=message.sender_id,
                text="⚠️ ALERTAS DEFESA CIVIL",
            )
        ]
        for alert in alerts:
            title = " ".join((alert.headline or alert.event).split())
            responses.append(
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text=f"{title} — severidade: {alert.severity}.",
                )
            )
        return tuple(responses)


class CommandHandler:
    """Resolve and execute registered bot commands."""

    def __init__(self, commands: list[Command], prefix: str = "!") -> None:
        self._commands = {command.name: command for command in commands}
        self._prefix = prefix

    def handle(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
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

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Block the requested user."""
        parts = message.text.strip().split(maxsplit=1)
        target_id = parts[1].strip() if len(parts) == 2 else ""

        if not target_id:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !bloquear <node_id>.",
                ),
            )

        result = self._moderation_service.block(message.sender_id, target_id)
        if result == "blocked":
            return self._notifier.notify("blocked", message.sender_id, target_id)

        responses = {
            "already_blocked": "Este usuário já está bloqueado.",
            "admin_required": "Apenas administradores podem fazer isso.",
            "requester_not_registered": "Você não está cadastrado.",
            "target_not_registered": "Este usuário não está cadastrado.",
            "cannot_moderate_admin": "Não é possível moderar um administrador.",
        }
        return (OutgoingMessage(recipient_id=message.sender_id, text=responses[result]),)


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

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Unblock the requested user."""
        parts = message.text.strip().split(maxsplit=1)
        target_id = parts[1].strip() if len(parts) == 2 else ""

        if not target_id:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !desbloquear <node_id>.",
                ),
            )

        result = self._moderation_service.unblock(message.sender_id, target_id)
        if result == "unblocked":
            return self._notifier.notify("unblocked", message.sender_id, target_id)

        responses = {
            "not_blocked": "Este usuário não está bloqueado.",
            "admin_required": "Apenas administradores podem fazer isso.",
            "requester_not_registered": "Você não está cadastrado.",
            "target_not_registered": "Este usuário não está cadastrado.",
            "cannot_moderate_admin": "Não é possível moderar um administrador.",
        }
        return (OutgoingMessage(recipient_id=message.sender_id, text=responses[result]),)


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

    def execute(self, message: IncomingMessage) -> tuple[OutgoingMessage, ...]:
        """Silence the requested user."""
        parts = message.text.strip().split()
        target_id = parts[1] if len(parts) >= 2 else ""
        minutes_text = parts[2] if len(parts) >= 3 else ""

        if not target_id:
            return (
                OutgoingMessage(
                    recipient_id=message.sender_id,
                    text="Use: !silenciar <node_id> <minutos>.",
                ),
            )

        minutes: int | None = None
        if minutes_text:
            try:
                minutes = int(minutes_text)
            except ValueError:
                return (
                    OutgoingMessage(
                        recipient_id=message.sender_id,
                        text="Informe o tempo em minutos.",
                    ),
                )

        result = self._moderation_service.silence(
            message.sender_id,
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
                message.sender_id,
                target_id,
                duration,
            )

        responses = {
            "invalid_minutes": "Informe um tempo válido.",
            "admin_required": "Apenas administradores podem fazer isso.",
            "requester_not_registered": "Você não está cadastrado.",
            "target_not_registered": "Este usuário não está cadastrado.",
            "cannot_moderate_admin": "Não é possível moderar um administrador.",
        }
        return (OutgoingMessage(recipient_id=message.sender_id, text=responses[result]),)
