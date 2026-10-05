from meshbot.application.bot import MeshBot
from meshbot.application.commands import CommandHandler, TempoCommand
from meshbot.application.weather import WeatherForecast
from meshbot.infrastructure.simulator import SimulatorTransport
from meshbot.infrastructure.weather import FakeWeatherService


def test_tempo_round_trip_sends_four_messages_with_delay_between_them() -> None:
    transport = SimulatorTransport()
    delays: list[float] = []
    service = FakeWeatherService(
        WeatherForecast(
            city="Ituverava",
            summary="Nublado c/ pancadas de chuva.",
            temperature_min=19,
            temperature_max=31,
            humidity_min=50,
            humidity_max=90,
            wind_direction="NE-N",
            wind_intensity="fracos",
        )
    )
    bot = MeshBot(
        transport,
        CommandHandler([TempoCommand(service)]),
        message_delay_seconds=5,
        sleep=delays.append,
    )

    transport.inject_message("!12345678", "/tempo Ituverava")

    assert bot.process_next_message() is True
    assert [message.text for message in transport.sent_messages] == [
        "Ituverava: Nublado c/ pancadas de chuva.",
        "Temperatura: 19°C a 31°C",
        "Umidade: 50% a 90%",
        "Vento: NE-N, fracos",
    ]
    assert delays == [5, 5, 5]
