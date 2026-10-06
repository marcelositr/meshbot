from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_delivery import (
    CompactDefenseCivilAlertFormatter,
    DefenseCivilDelivery,
    LocationDefenseCivilTargetResolver,
)


def make_alert(area: str = "Ituverava/SP") -> DefenseCivilAlert:
    return DefenseCivilAlert(
        identifier="alert-1",
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
        area=area,
        headline="Chuva intensa",
        description="",
        instruction="Evite áreas de risco.",
        onset=None,
        expires="2099-01-01T00:00:00-03:00",
    )


def test_formatter_builds_compact_alert() -> None:
    messages = CompactDefenseCivilAlertFormatter(180).format(make_alert())

    assert messages == (
        "⚠️ DEFESA CIVIL Chuva intensa Severidade: Severe. Urgência: Immediate. "
        "Evite áreas de risco.",
    )


def test_formatter_splits_long_alert() -> None:
    alert = make_alert()
    alert = DefenseCivilAlert(
        **{**alert.__dict__, "instruction": "palavra " * 100},
    )

    messages = CompactDefenseCivilAlertFormatter(60).format(alert)

    assert len(messages) > 1
    assert all(len(message) <= 60 for message in messages)


def test_target_resolver_matches_configured_location() -> None:
    resolver = LocationDefenseCivilTargetResolver("ituverava/sp")

    assert resolver.matches(make_alert("Ituverava/SP"))


def test_target_resolver_rejects_other_location() -> None:
    resolver = LocationDefenseCivilTargetResolver("Ribeirão Preto/SP")

    assert not resolver.matches(make_alert("Ituverava/SP"))


def test_delivery_targets_matching_alert() -> None:
    delivery = DefenseCivilDelivery(
        CompactDefenseCivilAlertFormatter(),
        LocationDefenseCivilTargetResolver("Ituverava/SP"),
        "!12345678",
    )

    messages = delivery.deliver(make_alert())

    assert len(messages) == 1
    assert messages[0].recipient_id == "!12345678"


def test_delivery_ignores_non_matching_alert() -> None:
    delivery = DefenseCivilDelivery(
        CompactDefenseCivilAlertFormatter(),
        LocationDefenseCivilTargetResolver("Ribeirão Preto/SP"),
        "!12345678",
    )

    assert delivery.deliver(make_alert()) == ()
