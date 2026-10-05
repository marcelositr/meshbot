from meshbot.application.bot import MeshBot
from meshbot.application.commands import CommandHandler, PingCommand
from meshbot.infrastructure.simulator import SimulatorTransport


def test_simulator_ping_round_trip() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(transport, CommandHandler([PingCommand()]))

    transport.inject_message("!12345678", "!ping")

    assert bot.process_next_message() is True
    assert len(transport.sent_messages) == 1
    assert transport.sent_messages[0].recipient_id == "!12345678"
    assert transport.sent_messages[0].text == "pong"


def test_unknown_command_does_not_generate_response() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(transport, CommandHandler([PingCommand()]))

    transport.inject_message("!12345678", "!unknown")

    assert bot.process_next_message() is True
    assert transport.sent_messages == []


def test_empty_transport_reports_no_message() -> None:
    transport = SimulatorTransport()
    bot = MeshBot(transport, CommandHandler([PingCommand()]))

    assert bot.process_next_message() is False
