"""Unit tests for scheduled automatic weather bulletins."""

from datetime import datetime
from threading import Event

from meshbot.application.weather import WeatherForecast
from meshbot.application.weather_bulletin import WeatherBulletinWorker
from meshbot.domain.messages import OutgoingMessage


class FakeWeatherService:
    def __init__(self, fail_first: bool = False) -> None:
        self.calls = 0
        self._fail_first = fail_first

    def get_forecast(self, city: str) -> WeatherForecast:
        self.calls += 1
        if self._fail_first and self.calls == 1:
            raise RuntimeError("temporary failure")
        return WeatherForecast(
            city=city,
            summary="Nublado",
            temperature_min=18,
            temperature_max=30,
            humidity_min=45,
            humidity_max=85,
            wind_direction="NE",
            wind_intensity="fracos",
        )


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[OutgoingMessage] = []

    def send(self, message: OutgoingMessage) -> None:
        self.sent.append(message)


def test_bulletin_is_sent_once_inside_configured_window() -> None:
    service = FakeWeatherService()
    transport = FakeTransport()
    stop_event = Event()
    calls = 0

    def sleep(_: float) -> None:
        nonlocal calls
        calls += 1
        if calls >= 3:
            stop_event.set()

    worker = WeatherBulletinWorker(
        service,
        transport,
        "Ribeirão Preto/SP",
        "^all",
        (("manhã", "06:00"),),
        now=lambda: datetime(2026, 10, 6, 6, 0, 30),
        sleep=sleep,
    )

    worker.run(stop_event)

    assert service.calls == 1
    assert len(transport.sent) == 1
    assert transport.sent[0].recipient_id == "^all"
    assert "BOLETIM DO TEMPO (manhã)" in transport.sent[0].text


def test_bulletin_is_not_sent_after_one_minute_window() -> None:
    service = FakeWeatherService()
    transport = FakeTransport()
    stop_event = Event()
    calls = 0

    def sleep(_: float) -> None:
        nonlocal calls
        calls += 1
        if calls >= 2:
            stop_event.set()

    worker = WeatherBulletinWorker(
        service,
        transport,
        "Ribeirão Preto/SP",
        "^all",
        (("manhã", "06:00"),),
        now=lambda: datetime(2026, 10, 6, 6, 1, 1),
        sleep=sleep,
    )

    worker.run(stop_event)

    assert service.calls == 0
    assert transport.sent == []


def test_failed_bulletin_retries_during_same_window() -> None:
    service = FakeWeatherService(fail_first=True)
    transport = FakeTransport()
    stop_event = Event()
    calls = 0

    def sleep(_: float) -> None:
        nonlocal calls
        calls += 1
        if calls >= 2:
            stop_event.set()

    worker = WeatherBulletinWorker(
        service,
        transport,
        "Ribeirão Preto/SP",
        "^all",
        (("manhã", "06:00"),),
        now=lambda: datetime(2026, 10, 6, 6, 0, 10),
        sleep=sleep,
    )

    worker.run(stop_event)

    assert service.calls == 2
    assert len(transport.sent) == 1


def test_bulletin_worker_rejects_invalid_configuration() -> None:
    service = FakeWeatherService()
    transport = FakeTransport()

    for location, recipient_id in (("", "^all"), ("Ribeirão Preto/SP", "")):
        try:
            WeatherBulletinWorker(
                service,
                transport,
                location,
                recipient_id,
                (("manhã", "06:00"),),
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError")
