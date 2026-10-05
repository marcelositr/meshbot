"""Command-line entry point for the local MeshBot simulator."""

from pathlib import Path

from meshbot.bot import MeshBot
from meshbot.config import ConfigurationError, load_settings
from meshbot.simulator import SimulatorTransport


def main() -> None:
    """Run the local simulator chat."""
    config_path = Path("config/config.toml")

    try:
        settings = load_settings(config_path)
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    if settings.transport != "simulator":
        raise SystemExit(
            "The local chat requires transport = \"simulator\" in config/config.toml."
        )

    transport = SimulatorTransport()
    bot = MeshBot(transport, command_prefix=settings.command_prefix)

    print(f"{settings.name} - simulator")
    print("Digite uma mensagem no formato '<node_id> <mensagem>'.")
    print("Exemplo: !12345678 /ping")
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

        if transport.sent_messages:
            response = transport.sent_messages.pop(0)
            print(f"{response.node_id} <- {response.text}")
