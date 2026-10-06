from datetime import UTC, datetime
from threading import Event

import pytest

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_poller import DefenseCivilPoller
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
        return StoredDefenseCivilAlert(
            alert=item[0],
            active=item[1],
            updated_at=datetime.now(UTC),
        )

    def list_active(self) -> tuple[StoredDefenseCivilAlert, ...]:
        return tuple(
            StoredDefenseCivilAlert(
                alert=alert,
                active=active,
                updated_at=datetime.now(UTC),
            )
            for alert, active in self.items.values()
            if active
        )


class FakeFeed:
    def __init__(self, alerts: tuple[DefenseCivilAlert, ...]) -> None:
        self.alerts = alerts
        self.calls = 0

    def get_all_alerts(self) -> tuple[DefenseCivilAlert, ...]:
        self.calls += 1
        return self.alerts


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


def test_poll_once_synchronizes_feed_snapshot() -> None:
    repository = MemoryRepository()
    feed = FakeFeed((make_alert("alert-1"),))
    poller = DefenseCivilPoller(
        feed,
        DefenseCivilStateService(repository),
    )

    events = poller.poll_once()

    assert len(events) == 1
    assert events[0].type == "new"
    assert events[0].alert == feed.alerts[0]
    assert feed.calls == 1
    assert repository.items["alert-1"][1]


def test_poll_once_does_not_change_state_when_feed_fails() -> None:
    class FailingFeed(FakeFeed):
        def get_all_alerts(self) -> tuple[DefenseCivilAlert, ...]:
            raise RuntimeError("feed unavailable")

    repository = MemoryRepository()
    existing = make_alert("alert-1")
    repository.upsert(existing, active=True)
    poller = DefenseCivilPoller(
        FailingFeed(()),
        DefenseCivilStateService(repository),
    )

    with pytest.raises(RuntimeError, match="feed unavailable"):
        poller.poll_once()

    assert repository.items["alert-1"][1]


def test_run_polls_until_stop() -> None:
    stop_event = Event()
    repository = MemoryRepository()
    feed = FakeFeed((make_alert("alert-1"),))

    def stop_after_poll(_seconds: float) -> None:
        stop_event.set()

    poller = DefenseCivilPoller(
        feed,
        DefenseCivilStateService(repository),
        sleep=stop_after_poll,
    )

    poller.run(stop_event)

    assert feed.calls == 1


def test_run_retries_failed_feed_with_bounded_backoff() -> None:
    stop_event = Event()
    repository = MemoryRepository()
    calls = 0
    sleeps: list[float] = []

    class FlakyFeed(FakeFeed):
        def get_all_alerts(self) -> tuple[DefenseCivilAlert, ...]:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise RuntimeError("temporary failure")
            stop_event.set()
            return self.alerts

    poller = DefenseCivilPoller(
        FlakyFeed((make_alert("alert-1"),)),
        DefenseCivilStateService(repository),
        poll_interval_seconds=300,
        sleep=sleeps.append,
        retry_initial_delay_seconds=5,
        retry_max_delay_seconds=10,
    )

    poller.run(stop_event)

    assert calls == 3
    assert sleeps == [5, 10]
    assert repository.items["alert-1"][1]


def test_rejects_invalid_retry_delays() -> None:
    repository = MemoryRepository()
    feed = FakeFeed(())

    with pytest.raises(ValueError, match="retry_initial_delay_seconds"):
        DefenseCivilPoller(
            feed,
            DefenseCivilStateService(repository),
            retry_initial_delay_seconds=0,
        )

    with pytest.raises(ValueError, match="retry_max_delay_seconds"):
        DefenseCivilPoller(
            feed,
            DefenseCivilStateService(repository),
            retry_initial_delay_seconds=10,
            retry_max_delay_seconds=5,
        )
