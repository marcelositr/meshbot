from meshbot.application.commands import CommandHandler, PingCommand
from meshbot.domain.messages import Message


def test_ping_command_returns_pong() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="/ping"))

    assert response == Message(node_id="!12345678", text="pong")


def test_unknown_command_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="/unknown"))

    assert response is None


def test_non_command_message_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="hello"))

    assert response is None
