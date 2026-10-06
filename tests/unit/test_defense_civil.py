from meshbot.application.commands import DefenseCivilCommand
from meshbot.application.defense_civil import (
    DefenseCivilAlert,
    DefenseCivilAmbiguousCityError,
    DefenseCivilCityNotFoundError,
    DefenseCivilServiceUnavailableError,
    DefenseCivilSettings,
)
from meshbot.domain.messages import IncomingMessage, OutgoingMessage
from meshbot.infrastructure.fake_defense_civil import FakeDefenseCivilService


def make_alert(**overrides: object) -> DefenseCivilAlert:
    values: dict[str, object] = {
        "identifier": "alert-1",
        "sender": "defesa@example.gov.br",
        "sent": "2026-10-05T10:00:00-03:00",
        "status": "Actual",
        "msg_type": "Alert",
        "references": (),
        "event": "Chuva intensa",
        "severity": "Severo",
        "urgency": "Immediate",
        "certainty": "Observed",
        "area": "Ituverava/SP",
        "headline": "Chuva intensa em Ituverava",
        "description": "Evite áreas de risco.",
        "instruction": "Procure abrigo em local seguro.",
        "onset": "2026-10-05T12:00:00-03:00",
        "expires": "2026-10-05T23:00:00-03:00",
    }
    values.update(overrides)
    return DefenseCivilAlert(**values)  # type: ignore[arg-type]


def test_defense_civil_requires_location() -> None:
    command = DefenseCivilCommand(FakeDefenseCivilService())

    result = command.execute(IncomingMessage(sender_id="!12345678", text="!defesacivil"))

    assert result == (
        OutgoingMessage(
            recipient_id="!12345678",
            text="Use: !defesacivil <cidade>.",
        ),
    )


def test_defense_civil_reports_no_active_alerts() -> None:
    command = DefenseCivilCommand(FakeDefenseCivilService())

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert result == (
        OutgoingMessage(
            recipient_id="!12345678",
            text="⚠️ ALERTAS DEFESA CIVIL",
        ),
        OutgoingMessage(
            recipient_id="!12345678",
            text="Nenhum alerta ativo.",
        ),
    )


def test_defense_civil_formats_active_alert() -> None:
    command = DefenseCivilCommand(FakeDefenseCivilService((make_alert(),)))

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert result == (
        OutgoingMessage(
            recipient_id="!12345678",
            text="⚠️ ALERTAS DEFESA CIVIL",
        ),
        OutgoingMessage(
            recipient_id="!12345678",
            text="Chuva intensa em Ituverava",
        ),
        OutgoingMessage(
            recipient_id="!12345678",
            text="Severidade: Severo.",
        ),
    )


def test_defense_civil_attention_mode_includes_instruction() -> None:
    settings = DefenseCivilSettings(
        enabled=True,
        mode="attention",
        max_alerts=5,
        max_message_length=180,
        show_severity=True,
        show_description=False,
        show_instruction=True,
        show_urgency=True,
        show_certainty=False,
    )
    command = DefenseCivilCommand(FakeDefenseCivilService((make_alert(),)), settings)

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert result[1].text == "Chuva intensa em Ituverava"
    assert result[2].text == "Severidade: Severo."
    assert result[3].text == "Urgência: Immediate."
    assert result[4].text == "Procure abrigo em local seguro."


def test_defense_civil_does_not_deduplicate_new_queries() -> None:
    alert = make_alert()
    service = FakeDefenseCivilService((alert,))
    command = DefenseCivilCommand(service)

    first = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )
    second = command.execute(
        IncomingMessage(sender_id="!87654321", text="!defesacivil Ituverava/SP")
    )

    assert first == second
    assert len(second) == 3


def test_defense_civil_respects_alert_limit() -> None:
    alerts = tuple(make_alert(identifier=f"alert-{index}") for index in range(7))
    settings = DefenseCivilSettings(
        enabled=True,
        mode="normal",
        max_alerts=2,
        max_message_length=180,
        show_severity=True,
        show_description=False,
        show_instruction=False,
        show_urgency=False,
        show_certainty=False,
    )
    command = DefenseCivilCommand(FakeDefenseCivilService(alerts), settings)

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert result[-1].text == "Há mais 5 alerta(s) ativo(s) nesta localidade."


def test_defense_civil_splits_long_messages() -> None:
    alert = make_alert(instruction="palavra " * 100)
    settings = DefenseCivilSettings(
        enabled=True,
        mode="emergency",
        max_alerts=5,
        max_message_length=80,
        show_severity=True,
        show_description=True,
        show_instruction=True,
        show_urgency=True,
        show_certainty=True,
    )
    command = DefenseCivilCommand(FakeDefenseCivilService((alert,)), settings)

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert len(result) > 3
    assert all(len(message.text) <= 80 for message in result[1:])


def test_defense_civil_can_be_disabled() -> None:
    settings = DefenseCivilSettings(
        enabled=False,
        mode="normal",
        max_alerts=5,
        max_message_length=180,
        show_severity=True,
        show_description=False,
        show_instruction=False,
        show_urgency=False,
        show_certainty=False,
    )
    command = DefenseCivilCommand(FakeDefenseCivilService(), settings)

    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava/SP")
    )

    assert result[0].text == "Consulta de Defesa Civil desativada."


def test_defense_civil_handles_city_errors() -> None:
    class FailingService:
        def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
            raise DefenseCivilCityNotFoundError(location)

    command = DefenseCivilCommand(FailingService())
    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Cidade")
    )

    assert result[0].text == "Cidade não encontrada."


def test_defense_civil_handles_ambiguous_city() -> None:
    class FailingService:
        def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
            raise DefenseCivilAmbiguousCityError(("Santa Rita/MG", "Santa Rita/PB"))

    command = DefenseCivilCommand(FailingService())
    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Santa Rita")
    )

    assert result[0].text == "Informe a cidade e o estado."


def test_defense_civil_handles_unavailable_service() -> None:
    class FailingService:
        def get_alerts(self, location: str) -> tuple[DefenseCivilAlert, ...]:
            raise DefenseCivilServiceUnavailableError("unavailable")

    command = DefenseCivilCommand(FailingService())
    result = command.execute(
        IncomingMessage(sender_id="!12345678", text="!defesacivil Ituverava")
    )

    assert result[0].text == "Não consegui consultar os alertas."
