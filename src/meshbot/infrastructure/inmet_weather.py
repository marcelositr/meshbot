"""INMET weather service and IBGE municipality resolution."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherForecast,
)


@dataclass(frozen=True, slots=True)
class Municipality:
    """IBGE municipality identity."""

    code: int
    name: str
    uf: str


class IBGECityResolver:
    """Resolve Brazilian municipality names to IBGE codes."""

    URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

    def __init__(self, timeout_seconds: int = 30) -> None:
        self._timeout_seconds = timeout_seconds
        self._municipalities: tuple[Municipality, ...] | None = None

    def resolve(self, query: str) -> Municipality:
        """Resolve a city name, optionally followed by '- UF'."""
        city_name, uf = _split_city_and_uf(query)
        normalized_name = _normalize(city_name)
        normalized_uf = _normalize(uf) if uf else None

        matches = [
            municipality
            for municipality in self._load()
            if _normalize(municipality.name) == normalized_name
            and (normalized_uf is None or _normalize(municipality.uf) == normalized_uf)
        ]

        if not matches:
            raise CityNotFoundError(city_name)

        if len(matches) > 1:
            choices = tuple(f"{item.name} - {item.uf}" for item in matches)
            raise AmbiguousCityError(choices)

        return matches[0]

    def _load(self) -> tuple[Municipality, ...]:
        if self._municipalities is not None:
            return self._municipalities

        request = Request(
            self.URL,
            headers={"User-Agent": "MeshBot/0.1", "Accept": "application/json"},
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("Unable to retrieve the IBGE municipality list.") from exc

        self._municipalities = tuple(_parse_municipality(item) for item in data)
        return self._municipalities


class InmetWeatherService:
    """Retrieve today's forecast from the INMET PREVMET API."""

    URL = "https://apiprevmet3.inmet.gov.br/previsao"

    def __init__(
        self,
        timeout_seconds: int,
        morning_start: str,
        afternoon_start: str,
        night_start: str,
        resolver: IBGECityResolver | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._morning_start = _parse_time(morning_start)
        self._afternoon_start = _parse_time(afternoon_start)
        self._night_start = _parse_time(night_start)
        self._resolver = resolver or IBGECityResolver(timeout_seconds)

    def get_forecast(self, city: str) -> WeatherForecast:
        """Resolve a city and return the forecast for the current period."""
        municipality = self._resolver.resolve(city)
        data = self._fetch(municipality.code)
        today = datetime.now().strftime("%d/%m/%Y")
        daily = data[str(municipality.code)][today]
        period = self._current_period()
        forecast = daily.get(period, daily)

        return WeatherForecast(
            city=f"{forecast['entidade']} - {forecast['uf']}",
            summary=str(forecast["resumo"]).rstrip(".") + ".",
            temperature_min=int(forecast["temp_min"]),
            temperature_max=int(forecast["temp_max"]),
            humidity_min=int(forecast["umidade_min"]),
            humidity_max=int(forecast["umidade_max"]),
            wind_direction=str(forecast["dir_vento"]),
            wind_intensity=str(forecast["int_vento"]).lower(),
        )

    def _fetch(self, code: int) -> dict[str, Any]:
        request = Request(
            f"{self.URL}/{code}",
            headers={"User-Agent": "MeshBot/0.1", "Accept": "application/json"},
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError("Unable to retrieve the INMET forecast.") from exc

        if not isinstance(data, dict):
            raise RuntimeError("INMET returned an unexpected response.")

        return data

    def _current_period(self) -> str:
        current = datetime.now().time()
        if self._morning_start <= current < self._afternoon_start:
            return "manha"
        if self._afternoon_start <= current < self._night_start:
            return "tarde"
        return "noite"


def _normalize(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(
        character for character in without_accents if not unicodedata.combining(character)
    ).casefold().strip()


def _split_city_and_uf(value: str) -> tuple[str, str | None]:
    match = re.fullmatch(r"\s*(.*?)\s*-\s*([A-Za-z]{2})\s*", value)
    if match is None:
        return value.strip(), None
    return match.group(1).strip(), match.group(2).upper()


def _parse_municipality(data: Any) -> Municipality:
    try:
        code = int(data["id"])
        name = str(data["nome"])
        uf = str(data["microrregiao"]["mesorregiao"]["UF"]["sigla"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("IBGE returned an unexpected municipality response.") from exc
    return Municipality(code=code, name=name, uf=uf)


def _parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Invalid weather period time: {value!r}") from exc
