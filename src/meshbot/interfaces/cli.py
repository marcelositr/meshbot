"""Command-line interface for MeshBot."""

from pathlib import Path
from threading import Event, Thread

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.application.bot import MeshBot
from meshbot.application.commands import (
    BlockCommand,
    CommandHandler,
    DefenseCivilCommand,
    NameCommand,
    PingCommand,
    RegisterCommand,
    SilenceCommand,
    TempoCommand,
    UnblockCommand,
)
from meshbot.application.defense_civil_delivery import (
    CompactDefenseCivilAlertFormatter,
    DefenseCivilDelivery,
    DefenseCivilEventDispatcher,
    LocationDefenseCivilTargetResolver,
)
from meshbot.application.defense_civil_poller import DefenseCivilPoller
from meshbot.application.defense_civil_state import DefenseCivilStateService
from meshbot.application.logging import configure_logging
from meshbot.application.moderation import ModerationService
from meshbot.application.moderation_notifications import ModerationNotifier
from meshbot.application.runtime import ProductionRuntime
from meshbot.application.users import UserService
from meshbot.config import ConfigurationError, load_settings
from meshbot.domain.messages import OutgoingMessage
from meshbot.domain.users import User, UserRole
from meshbot.infrastructure.defense_civil import DefenseCivilAlertService
from meshbot.infrastructure.inmet_weather import InmetWeatherService
from meshbot.infrastructure.meshtastic_transport import MeshtasticTransport
from meshbot.infrastructure.simulator import SimulatorTransport
from meshbot.infrastructure.sqlite_defense_civil import SQLiteDefenseCivilAlertRepository
from meshbot.infrastructure.sqlite_users import SQLiteUserRepository


def main() -> None:
    """Run the local simulator chat."""
    config_path = Path("config/config.toml")

    try:
        settings = load_settings(config_path)
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    configure_logging(settings.log_level)

    def display_message(message: OutgoingMessage) -> None:
        print(f"{message.recipient_id} <- {message.text}")

    user_repository = SQLiteUserRepository(Path(settings.database_path))
    for node_id in settings.admins:
        existing = user_repository.get(node_id)
        if existing is None:
            user_repository.save(User(node_id=node_id, role=UserRole.ADMIN))
        elif existing.role is not UserRole.ADMIN:
            user_repository.save(
                User(
                    node_id=existing.node_id,
                    name=existing.name,
                    role=UserRole.ADMIN,
                    blocked=existing.blocked,
                    silenced_until=existing.silenced_until,
                )
            )

    moderation_service = ModerationService(
        user_repository,
        default_silence_minutes=settings.default_silence_minutes,
    )
    moderation_notifier = ModerationNotifier(user_repository)

    transport: SimulatorTransport | MeshtasticTransport
    workers = (defense_civil_worker,) if defense_civil_worker is not None else ()

    if settings.transport == "simulator":
        print(f"{settings.name} - simulator")
        print("Digite uma mensagem no formato '<node_id> <mensagem>'.")
        print("Exemplos: !12345678 !ping  |  !12345678 !tempo Ituverava/SP")
        print("          !12345678 !defesacivil Ituverava/SP")
        print("Digite 'exit' para sair.")
        assert isinstance(transport, SimulatorTransport)
        _run_simulator(transport, bot, workers)
        return

    assert isinstance(transport, MeshtasticTransport)
    print(f"{settings.name} - Meshtastic ({settings.transport})")
    try:
        ProductionRuntime(bot, transport, workers=workers).run()
    except (KeyboardInterrupt, EOFError):
        return

def _run_simulator(
    transport: SimulatorTransport,
    bot: MeshBot,
    workers: tuple[object, ...] = (),
) -> None:
    stop_event = Event()
    threads: list[Thread] = []
    for worker in workers:
        thread = Thread(
            target=worker.run,
            args=(stop_event,),
            name="MeshBotBackgroundWorker",
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    try:
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
            transport.sent_messages.clear()
    finally:
        stop_event.set()
        for thread in threads:
            thread.join()
