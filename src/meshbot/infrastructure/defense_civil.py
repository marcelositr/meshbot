"""Official Defense Civil alert feed integration."""

from __future__ import annotations

import unicodedata
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import requests

from meshbot.application.defense_civil import (
    DefenseCivilAlert,
    DefenseCivilAmbiguousCityError,
    DefenseCivilCityNotFoundError,
    DefenseCivilServiceUnavailableError,
)
from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherServiceUnavailableError,
)
from meshbot.infrastructure.inmet_weather import IBGECityResolver, Municipality

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
        """Resolve the municipality and return the current active alerts."""
        municipality = self._resolve(location)

        try:
            response = requests.get(URL, timeout=self._timeout_seconds)
            response.raise_for_status()
            root = ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as exc:
            raise DefenseCivilServiceUnavailableError(
                "Defense Civil feed is unavailable."
            ) from exc

        parsed_alerts: list[DefenseCivilAlert] = []
        cancelled: set[str] = set()
        superseded: set[str] = set()

        for alert_element in root.iter():
            if self._local_name(alert_element.tag) != "alert":
                continue

            identifier = self._find_text(alert_element, "identifier")
            sender = self._find_text(alert_element, "sender")
            sent = self._find_text(alert_element, "sent")
            status = self._find_text(alert_element, "status")
            msg_type = self._find_text(alert_element, "msgType")
            scope = self._find_text(alert_element, "scope")
            scope = self._find_text(alert_element, "scope")
            references_text = self._find_text(
                alert_element,
                "references",
                required=False,
            )

            if not identifier or not sender or not sent or not status or not msg_type or not scope:
                continue
            if status != "Actual" or scope != "Public":
                continue

            references = self._parse_references(references_text)

            if msg_type == "Cancel":
                cancelled.update(references)
                continue

            if msg_type not in {"Alert", "Update"}:
                continue

            if msg_type == "Update":
                superseded.update(references)

            infos = [
                child
                for child in alert_element
                if self._local_name(child.tag) == "info"
            ]
            for info in infos:
                alert = self._parse_info(
                    info=info,
                    identifier=identifier,
                    sender=sender,
                    sent=sent,
                    status=status,
                    msg_type=msg_type,
                    scope=scope,
                    references=references,
                )
                if alert is not None:
                    parsed_alerts.append(alert)

        alerts: list[DefenseCivilAlert] = []
        for alert in parsed_alerts:
            if alert.identifier in cancelled or alert.identifier in superseded:
                continue
            if not self._is_active(alert.expires):
                continue
            if not self._matches_location(
                alert.area,
                municipality.name,
                municipality.uf,
            ):
                continue
            alerts.append(alert)

        return tuple(alerts)

    def _resolve(self, location: str) -> Municipality:
        try:
            return self._resolver.resolve(location)
        except CityNotFoundError as exc:
            raise DefenseCivilCityNotFoundError(str(exc)) from exc
        except AmbiguousCityError as exc:
            raise DefenseCivilAmbiguousCityError(exc.matches) from exc
        except WeatherServiceUnavailableError as exc:
            raise DefenseCivilServiceUnavailableError(str(exc)) from exc

    @staticmethod
    def _is_active(expires: str | None) -> bool:
        if not expires:
            return True

        try:
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        except ValueError:
            return False

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)

        return expiry > datetime.now(UTC)

    @staticmethod
    def _matches_location(area: str, city: str, uf: str) -> bool:
        normalized_area = _normalize(area)
        return _normalize(city) in normalized_area and _normalize(uf) in normalized_area

    @classmethod
    def _parse_info(
        cls,
        *,
        info: ET.Element,
        identifier: str,
        sender: str,
        sent: str,
        status: str,
        msg_type: str,
        scope: str,
        references: tuple[str, ...],
    ) -> DefenseCivilAlert | None:
        event = cls._find_text(info, "event")
        severity = cls._find_text(info, "severity")
        urgency = cls._find_text(info, "urgency")
        certainty = cls._find_text(info, "certainty")
        area = cls._find_text(info, "areaDesc")
        headline = cls._find_text(info, "headline", required=False)
        description = cls._find_text(info, "description", required=False)
        instruction = cls._find_text(info, "instruction", required=False)
        onset = cls._find_text(info, "onset", required=False)
        expires = cls._find_text(info, "expires", required=False)

        if not event or not severity or not urgency or not certainty or not area:
            return None

        return DefenseCivilAlert(
            identifier=identifier,
            sender=sender,
            sent=sent,
            status=status,
            msg_type=msg_type,
            scope=scope,
            references=references,
            event=event,
            severity=severity,
            urgency=urgency,
            certainty=certainty,
            area=area,
            headline=headline or "",
            description=description or "",
            instruction=instruction or "",
            onset=onset,
            expires=expires,
        )

    @staticmethod
    def _parse_references(value: str | None) -> tuple[str, ...]:
        if not value:
            return ()

        identifiers: list[str] = []
        for reference in value.split():
            parts = reference.split(",", maxsplit=2)
            if len(parts) == 3 and parts[1]:
                identifiers.append(parts[1])
        return tuple(identifiers)

    @classmethod
    def _find_text(
        cls,
        parent: ET.Element,
        name: str,
        *,
        required: bool = True,
    ) -> str | None:
        for child in parent:
            if cls._local_name(child.tag) != name:
                continue
            text = "".join(child.itertext()).strip()
            if text:
                return text
        return "" if required else None

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", maxsplit=1)[-1]
