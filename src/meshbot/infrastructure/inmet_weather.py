"""INMET weather service and IBGE municipality resolution."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

import requests

from meshbot.application.weather import (
    AmbiguousCityError,
    CityNotFoundError,
    WeatherForecast,
    WeatherServiceUnavailableError,
)

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) "
        "Gecko/20100101 Firefox/142.0"
    ),
    "Accept": "application/json,text/plain,*/*",
}


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
        """Resolve a city name, optionally followed by '/UF'."""
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
            choices = tuple(f"{item.name}/{item.uf}" for item in matches)
            raise AmbiguousCityError(choices)

        return matches[0]

    def _load(self) -> tuple[Municipality, ...]:
        if self._municipalities is not None:
            return self._municipalities

        try:
            response = requests.get(
                self.URL,
                headers=_HTTP_HEADERS,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise WeatherServiceUnavailableError(
                "Unable to retrieve the IBGE municipality list."
            ) from exc

        if not isinstance(data, list):
            raise WeatherServiceUnavailableError(
                "IBGE returned an unexpected municipality response."
            )

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
        """Resolve a city or IBGE code and return the current period."""
        code, requested_city, uf = self._resolve_code(city)

        try:
            data = self._fetch(code)
            daily = data[str(code)][datetime.now().strftime("%d/%m/%Y")]
            forecast = daily.get(self._current_period(), daily)
            return WeatherForecast(
                city=f"{forecast.get('entidade', requested_city)}/{uf}",
                summary=str(forecast["resumo"]).rstrip(".") + ".",
                temperature_min=int(forecast["temp_min"]),
                temperature_max=int(forecast["temp_max"]),
                humidity_min=int(forecast["umidade_min"]),
                humidity_max=int(forecast["umidade_max"]),
                wind_direction=str(forecast["dir_vento"]),
                wind_intensity=_format_wind_intensity(str(forecast["int_vento"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherServiceUnavailableError(
                "INMET returned an unexpected forecast response."
            ) from exc

    def _resolve_code(self, city: str) -> tuple[int, str, str]:
        match = re.fullmatch(r"ibge\s+(\d+)", city.strip(), flags=re.IGNORECASE)
        if match:
            code = int(match.group(1))
            uf = _UF_BY_IBGE_CODE.get(code // 100_000)
            if uf is None:
                raise CityNotFoundError(match.group(1))
            return code, match.group(1), uf

        municipality = self._resolver.resolve(city)
        return municipality.code, municipality.name, municipality.uf

    def _fetch(self, code: int) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.URL}/{code}",
                headers=_HTTP_HEADERS,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise WeatherServiceUnavailableError(
                "Unable to retrieve the INMET forecast."
            ) from exc

        if not isinstance(data, dict):
            raise WeatherServiceUnavailableError(
                "INMET returned an unexpected response."
            )

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
    match = re.fullmatch(r"\s*(.*?)\s*/\s*([A-Za-z]{2})\s*", value)
    if match is None:
        return value.strip(), None
    return match.group(1).strip(), match.group(2).upper()


def _parse_municipality(data: Any) -> Municipality:
    try:
        code = int(data["id"])
        name = str(data["nome"])
        uf = _extract_uf(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherServiceUnavailableError(
            "IBGE returned an unexpected municipality response."
        ) from exc
    return Municipality(code=code, name=name, uf=uf)


def _extract_uf(data: dict[str, Any]) -> str:
    """Extract the municipality UF from the available IBGE hierarchy."""
    microrregiao = data.get("microrregiao")
    if isinstance(microrregiao, dict):
        mesorregiao = microrregiao.get("mesorregiao")
        if isinstance(mesorregiao, dict):
            uf = mesorregiao.get("UF")
            if isinstance(uf, dict):
                sigla = uf.get("sigla")
                if isinstance(sigla, str):
                    return sigla

    regiao_imediata = data.get("regiao-imediata")
    if isinstance(regiao_imediata, dict):
        regiao_intermediaria = regiao_imediata.get("regiao-intermediaria")
        if isinstance(regiao_intermediaria, dict):
            uf = regiao_intermediaria.get("UF")
            if isinstance(uf, dict):
                sigla = uf.get("sigla")
                if isinstance(sigla, str):
                    return sigla

    code = int(data["id"])
    uf_code = code // 100_000
    uf = _UF_BY_IBGE_CODE.get(uf_code)
    if uf is not None:
        return uf

    raise ValueError("IBGE municipality response does not contain a UF.")


_UF_BY_IBGE_CODE = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}


def _parse_time(value: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Invalid weather period time: {value!r}") from exc


def _format_wind_intensity(value: str) -> str:
    normalized = value.strip().lower()
    return normalized[:-1] if normalized.endswith("s") else normalized
