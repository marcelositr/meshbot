"""Fake Defense Civil service for development and tests."""

from meshbot.application.defense_civil import DefenseCivilAlert


class FakeDefenseCivilService:
    """Return deterministic Defense Civil alerts without network access."""

    def __init__(
        self,
        alerts: tuple[DefenseCivilAlert, ...] = (),
    ) -> None:
        self._alerts = alerts

    def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
        """Return the configured alerts."""
        return self._alerts
