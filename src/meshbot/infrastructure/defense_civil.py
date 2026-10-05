"""Official Defense Civil alert feed integration."""

from __future__ import annotations

import unicodedata
import xml.etree.ElementTree as ET

import requests

from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherServiceUnavailableError,
)
from meshbot.application.defense_civil import (
    DefenseCivilAlert,
    DefenseCivilAmbiguousCityError,
    DefenseCivilCityNotFoundError,
    DefenseCivilServiceUnavailableError,
)
from meshbot.infrastructure.inmet_weather import IBGECityResolver

URL = "https://idapfile.mdr.gov.br/idap/api/rss/cap"
TIMEOUT_SECONDS = 10


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.casefold().split())


class DefenseCivilAlertService:
    """Read active Defense Civil alerts from the official CAP feed."""

    def __init__(
        self,
        timeout_seconds: int = TIMEOUT_SECONDS,
        resolver: IBGECityResolver | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._resolver = resolver or IBGECityResolver(timeout_seconds)

    def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
        """Resolve the municipality and return matching active alerts."""
        municipality = self._resolve(location)

        try:
            response = requests.get(URL, timeout=self._timeout_seconds)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            raise DefenseCivilServiceUnavailableError(
                "Defense Civil feed is unavailable."
            ) from exc

        alerts: list[DefenseCivilAlert] = []
        for info in root.iter():
            if self._local_name(info.tag) != "info":
                continue

            alert = self._parse_info(info)
            if alert is None:
                continue

            if self._matches_location(
                alert.area,
                municipality.name,
                municipality.uf,
            ):
                alerts.append(alert)

        return tuple(alerts)

    def _resolve(self, location: str):
        try:
            return self._resolver.resolve(location)
        except CityNotFoundError as exc:
            raise DefenseCivilCityNotFoundError(str(exc)) from exc
        except AmbiguousCityError as exc:
            raise DefenseCivilAmbiguousCityError(exc.matches) from exc
        except WeatherServiceUnavailableError as exc:
            raise DefenseCivilServiceUnavailableError(str(exc)) from exc

    @staticmethod
    def _matches_location(area: str, city: str, uf: str) -> bool:
        normalized_area = _normalize(area)
        return _normalize(city) in normalized_area and _normalize(uf) in normalized_area

    @classmethod
    def _parse_info(cls, info: ET.Element) -> DefenseCivilAlert | None:
        event = cls._find_text(info, "event")
        severity = cls._find_text(info, "severity")
        area = cls._find_text(info, "areaDesc")
        headline = cls._find_text(info, "headline")
        description = cls._find_text(info, "description")
        expires = cls._find_text(info, "expires", required=False)

        if not event or not area:
            return None

        return DefenseCivilAlert(
            event=event,
            severity=severity,
            area=area,
            headline=headline,
            description=description,
            expires=expires,
        )

    @classmethod
    def _find_text(
        cls,
        parent: ET.Element,
        name: str,
        *,
        required: bool = True,
    ) -> str | None:
        for child in parent.iter():
            if child is parent or cls._local_name(child.tag) != name:
                continue
            text = "".join(child.itertext()).strip()
            if text:
                return text
        return "" if required else None

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", maxsplit=1)[-1]
