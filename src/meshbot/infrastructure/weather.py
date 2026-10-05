"""Weather service implementations for development and tests."""

from meshbot.application.weather import WeatherForecast


class FakeWeatherService:
    """Return deterministic weather data without network access."""

    def __init__(self, forecast: WeatherForecast | None = None) -> None:
        self._forecast = forecast or WeatherForecast(
            city="Ituverava",
            summary="Nublado c/ pancadas de chuva e trovoadas isoladas.",
            temperature_min=19,
            temperature_max=31,
            humidity_min=50,
            humidity_max=90,
            wind_direction="NE-N",
            wind_intensity="fracos",
        )

    def get_forecast(self, city: str) -> WeatherForecast:
        """Return the configured forecast using the requested city name."""
        return WeatherForecast(
            city=self._forecast.city,
            summary=self._forecast.summary,
            temperature_min=self._forecast.temperature_min,
            temperature_max=self._forecast.temperature_max,
            humidity_min=self._forecast.humidity_min,
            humidity_max=self._forecast.humidity_max,
            wind_direction=self._forecast.wind_direction,
            wind_intensity=self._forecast.wind_intensity,
        )
