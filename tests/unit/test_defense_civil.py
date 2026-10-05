from meshbot.application.commands import DefenseCivilCommand
from meshbot.application.defense_civil import (
    DefenseCivilAlert,
    DefenseCivilAmbiguousCityError,
    DefenseCivilCityNotFoundError,
    DefenseCivilServiceUnavailableError,
)
from meshbot.domain.messages import IncomingMessage, OutgoingMessage
from meshbot.infrastructure.fake_defense_civil import FakeDefenseCivilService


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
    alert = DefenseCivilAlert(
        event="Chuva intensa",
        severity="Severo",
        area="Ituverava/SP",
        headline="Chuva intensa em Ituverava",
        description="Evite áreas de risco.",
        expires="2026-10-05T23:00:00-03:00",
    )
    command = DefenseCivilCommand(FakeDefenseCivilService((alert,)))

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
            text="Chuva intensa em Ituverava — severidade: Severo.",
        ),
    )


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
