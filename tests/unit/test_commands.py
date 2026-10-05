from meshbot.application.commands import CommandHandler, PingCommand, TempoCommand
from meshbot.application.weather import WeatherForecast
from meshbot.domain.messages import Message
from meshbot.infrastructure.weather import FakeWeatherService


def test_ping_command_returns_pong() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="!ping"))

    assert response == (Message(node_id="!12345678", text="pong"),)


def test_unknown_command_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="!unknown"))

    assert response == ()


def test_non_command_message_returns_no_response() -> None:
    handler = CommandHandler([PingCommand()])

    response = handler.handle(Message(node_id="!12345678", text="hello"))

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

    response = handler.handle(Message(node_id="!12345678", text="!tempo Ituverava"))

    assert [message.text for message in response] == [
        "Ituverava/SP: Nublado c/ pancadas de chuva e trovoadas isoladas.",
        "Temperatura: 19°C a 31°C",
        "Umidade: 50% a 90%",
        "Vento: NE-N, fracos",
    ]


def test_tempo_command_requires_city() -> None:
    handler = CommandHandler([TempoCommand(FakeWeatherService())])

    response = handler.handle(Message(node_id="!12345678", text="!tempo"))

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

    response = handler.handle(Message(node_id="!12345678", text="!tempo Ituverava/SP"))

    assert response[0].text == "Ituverava/SP: Tempo estável."
