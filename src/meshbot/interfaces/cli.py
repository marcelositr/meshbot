"""Command-line interface for MeshBot."""

from pathlib import Path

from meshbot.application.bot import MeshBot
from meshbot.application.commands import CommandHandler, PingCommand, TempoCommand
from meshbot.config import ConfigurationError, load_settings
from meshbot.infrastructure.inmet_weather import InmetWeatherService
from meshbot.infrastructure.simulator import SimulatorTransport


def main() -> None:
    """Run the local simulator chat."""
    config_path = Path("config/config.toml")

    try:
        settings = load_settings(config_path)
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    if settings.transport != "simulator":
        raise SystemExit(
            'The local chat requires transport = "simulator" in config/config.toml.'
        )

    transport = SimulatorTransport()
    weather_service = InmetWeatherService(
        timeout_seconds=settings.weather_timeout_seconds,
        morning_start=settings.weather_morning_start,
        afternoon_start=settings.weather_afternoon_start,
        night_start=settings.weather_night_start,
    )
    command_handler = CommandHandler(
        [PingCommand(), TempoCommand(weather_service)],
        prefix=settings.command_prefix,
    )
    bot = MeshBot(
        transport,
        command_handler,
        message_delay_seconds=settings.message_delay_seconds,
    )

    print(f"{settings.name} - simulator")
    print("Digite uma mensagem no formato '<node_id> <mensagem>'.")
    print("Exemplos: !12345678 /ping  |  !12345678 /tempo Ituverava")
    print("Digite 'exit' para sair.")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if line.lower() == "exit":
            return

        if not line:
            continue

        try:
            node_id, text = line.split(maxsplit=1)
        except ValueError:
            print("Formato inválido. Use: <node_id> <mensagem>")
            continue

        transport.inject_message(node_id, text)
        bot.process_next_message()

        while transport.sent_messages:
            response = transport.sent_messages.pop(0)
            print(f"{response.node_id} <- {response.text}")
