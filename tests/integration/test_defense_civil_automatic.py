"""Integration tests for automatic Defense Civil delivery."""

from pathlib import Path

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_delivery import (
    CompactDefenseCivilAlertFormatter,
    DefenseCivilDelivery,
    DefenseCivilEventDispatcher,
    LocationDefenseCivilTargetResolver,
)
from meshbot.application.defense_civil_poller import DefenseCivilPoller
from meshbot.application.defense_civil_state import DefenseCivilStateService
from meshbot.domain.messages import OutgoingMessage
from meshbot.infrastructure.simulator import SimulatorTransport
from meshbot.infrastructure.sqlite_defense_civil import (
    SQLiteDefenseCivilAlertRepository,
)


class FakeDefenseCivilFeed:
    def __init__(self, alerts: tuple[DefenseCivilAlert, ...]) -> None:
        self._alerts = alerts

    def get_all_alerts(self) -> tuple[DefenseCivilAlert, ...]:
        return self._alerts


def make_alert() -> DefenseCivilAlert:
    return DefenseCivilAlert(
        identifier="alert-automatic-1",
        sender="defesa@example.gov.br",
        sent="2026-10-06T10:00:00-03:00",
        status="Actual",
        msg_type="Alert",
        scope="Public",
        references=(),
        event="Chuva intensa",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        area="Ribeirão Preto/SP",
        headline="Chuva intensa",
        description="",
        instruction="Evite áreas de risco.",
        onset=None,
        expires="2099-01-01T00:00:00-03:00",
    )


def test_automatic_defense_civil_delivery_end_to_end(tmp_path: Path) -> None:
    transport = SimulatorTransport()
    repository = SQLiteDefenseCivilAlertRepository(
        tmp_path / "defense-civil.sqlite3"
    )
    state = DefenseCivilStateService(repository)
    delivery = DefenseCivilDelivery(
        CompactDefenseCivilAlertFormatter(180),
        LocationDefenseCivilTargetResolver("Ribeirão Preto/SP"),
        "^all",
    )
    dispatcher = DefenseCivilEventDispatcher(delivery, transport)
    poller = DefenseCivilPoller(
        FakeDefenseCivilFeed((make_alert(),)),
        state,
        on_events=dispatcher.dispatch,
    )

    first_events = poller.poll_once()
    second_events = poller.poll_once()

    assert [event.type for event in first_events] == ["new"]
    assert second_events == ()
    assert transport.sent_messages == [
        OutgoingMessage(
            recipient_id="^all",
            text=(
                "⚠️ DEFESA CIVIL Chuva intensa Severidade: Severe. "
                "Urgência: Immediate. Evite áreas de risco."
            ),
        )
    ]
