"""Scheduled automatic weather bulletin worker."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, time
from threading import Event
from typing import Protocol

from meshbot.application.weather import WeatherForecast, WeatherService
from meshbot.domain.messages import OutgoingMessage

logger = logging.getLogger(__name__)

_BULLETIN_WINDOW_SECONDS = 60.0


class WeatherBulletinTransport(Protocol):
    """Transport contract used to publish automatic weather bulletins."""

    def send(self, message: OutgoingMessage) -> None:
        """Send a weather bulletin."""


class WeatherBulletinWorker:
    """Publish one weather bulletin during each configured time window."""

    def __init__(
        self,
        weather_service: WeatherService,
        transport: WeatherBulletinTransport,
        location: str,
        recipient_id: str,
        periods: tuple[tuple[str, str], ...],
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if not location.strip():
            raise ValueError("Weather bulletin location must not be empty.")
        if not recipient_id.strip():
            raise ValueError("Weather bulletin recipient_id must not be empty.")
        if not periods:
            raise ValueError("At least one weather bulletin period is required.")

        self._weather_service = weather_service
        self._transport = transport
        self._location = location.strip()
        self._recipient_id = recipient_id.strip()
        self._periods = tuple(
            (label, datetime.strptime(start, "%H:%M").time())
            for label, start in periods
        )
        self._now = now or datetime.now
        self._sleep = sleep or Event().wait
        self._last_slot: tuple[str, str] | None = None

    def run(self, stop_event: Event | None = None) -> None:
        """Run until stopped, publishing at most once per configured window."""
        event = stop_event or Event()
        logger.info("Automatic weather bulletin worker started.")
        while not event.is_set():
            current = self._now()
            slot = self._active_slot(current)
            if slot is not None:
                slot_key = (current.date().isoformat(), slot[0])
                if slot_key != self._last_slot and self._publish(slot[0]):
                    self._last_slot = slot_key

            self._sleep(1.0)
        logger.info("Automatic weather bulletin worker stopped.")

    def _active_slot(self, current: datetime) -> tuple[str, time] | None:
        seconds_since_midnight = (
            current.hour * 3600 + current.minute * 60 + current.second
        )
        for label, start in self._periods:
            start_seconds = start.hour * 3600 + start.minute * 60
            if start_seconds <= seconds_since_midnight < start_seconds + _BULLETIN_WINDOW_SECONDS:
                return label, start
        return None

    def _publish(self, period: str) -> bool:
        try:
            forecast = self._weather_service.get_forecast(self._location)
            text = self._format(period, forecast)
            self._transport.send(
                OutgoingMessage(recipient_id=self._recipient_id, text=text)
            )
            logger.info(
                "Automatic weather bulletin sent: period=%s location=%s recipient=%s.",
                period,
                self._location,
                self._recipient_id,
            )
            return True
        except Exception:
            logger.exception(
                "Automatic weather bulletin failed: period=%s location=%s.",
                period,
                self._location,
            )
            return False

    @staticmethod
    def _format(period: str, forecast: WeatherForecast) -> str:
        return (
            f"🌦️ BOLETIM DO TEMPO ({period}) "
            f"{forecast.city}: {forecast.summary} "
            f"{forecast.temperature_min}°C a {forecast.temperature_max}°C. "
            f"Umidade {forecast.humidity_min}% a {forecast.humidity_max}%. "
            f"Vento {forecast.wind_direction}, {forecast.wind_intensity}."
        )
