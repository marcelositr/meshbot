from datetime import UTC, datetime

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_state import (
    DefenseCivilStateService,
    StoredDefenseCivilAlert,
)


class MemoryRepository:
    def __init__(self) -> None:
        self.items: dict[str, tuple[DefenseCivilAlert, bool]] = {}

    def upsert(self, alert: DefenseCivilAlert, *, active: bool) -> None:
        self.items[alert.identifier] = (alert, active)

    def get(self, identifier: str) -> StoredDefenseCivilAlert | None:
        item = self.items.get(identifier)
        if item is None:
            return None
        return StoredDefenseCivilAlert(item[0], item[1], datetime.now(UTC))

    def list_active(self) -> tuple[StoredDefenseCivilAlert, ...]:
        return tuple(
            StoredDefenseCivilAlert(alert, active, datetime.now(UTC))
            for alert, active in self.items.values()
            if active
        )


def make_alert(identifier: str) -> DefenseCivilAlert:
    return DefenseCivilAlert(
        identifier=identifier,
        sender="defesa@example.gov.br",
        sent="2026-10-05T10:00:00-03:00",
        status="Actual",
        msg_type="Alert",
        scope="Public",
        references=(),
        event="Chuva intensa",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        area="Ituverava/SP",
        headline="Chuva intensa",
        description="",
        instruction="",
        onset=None,
        expires="2099-01-01T00:00:00-03:00",
    )


def test_synchronize_adds_new_alerts() -> None:
    repository = MemoryRepository()
    service = DefenseCivilStateService(repository)

    service.synchronize((make_alert("alert-1"),))

    assert repository.items["alert-1"][1]


def test_synchronize_deactivates_alerts_missing_from_snapshot() -> None:
    repository = MemoryRepository()
    repository.upsert(make_alert("alert-1"), active=True)
    repository.upsert(make_alert("alert-2"), active=True)
    service = DefenseCivilStateService(repository)

    service.synchronize((make_alert("alert-1"),))

    assert repository.items["alert-1"][1]
    assert not repository.items["alert-2"][1]


def test_synchronize_updates_existing_alert() -> None:
    repository = MemoryRepository()
    service = DefenseCivilStateService(repository)
    first = make_alert("alert-1")
    updated = make_alert("alert-1")
    updated = DefenseCivilAlert(
        identifier=updated.identifier,
        sender=updated.sender,
        sent=updated.sent,
        status=updated.status,
        msg_type=updated.msg_type,
        scope=updated.scope,
        references=updated.references,
        event="Alerta atualizado",
        severity=updated.severity,
        urgency=updated.urgency,
        certainty=updated.certainty,
        area=updated.area,
        headline=updated.headline,
        description=updated.description,
        instruction=updated.instruction,
        onset=updated.onset,
        expires=updated.expires,
    )

    service.synchronize((first,))
    service.synchronize((updated,))

    assert repository.items["alert-1"][0].event == "Alerta atualizado"
