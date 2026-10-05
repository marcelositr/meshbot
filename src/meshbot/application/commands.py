"""Command handling for MeshBot."""

from typing import Protocol

from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherService,
)
from meshbot.domain.messages import Message


class Command(Protocol):
    """Interface implemented by bot commands."""

    name: str

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Execute the command for an incoming message."""
        ...


class PingCommand:
    """Respond to /ping with pong."""

    name = "ping"

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Return the pong response."""
        return (Message(node_id=message.node_id, text="pong"),)


class TempoCommand:
    """Return a compact weather forecast for a requested city."""

    name = "tempo"

    def __init__(self, weather_service: WeatherService) -> None:
        self._weather_service = weather_service

    def execute(self, message: Message) -> tuple[Message, ...]:
        """Resolve the requested city and format the forecast."""
        city = message.text[len("/tempo") :].strip()
        if not city:
            return (Message(node_id=message.node_id, text="Use: /tempo <cidade>"),)

        try:
            forecast = self._weather_service.get_forecast(city)
        except CityNotFoundError:
            return (
                Message(
                    node_id=message.node_id,
                    text=f'Não encontrei "{city}". Use /tempo ibge <codigo>.',
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
                    text="Use /tempo <cidade> - <UF>.",
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

    def __init__(self, commands: list[Command], prefix: str = "/") -> None:
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
