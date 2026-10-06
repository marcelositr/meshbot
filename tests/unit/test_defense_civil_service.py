from xml.etree import ElementTree as ET

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.infrastructure.defense_civil import DefenseCivilAlertService
from meshbot.infrastructure.inmet_weather import Municipality


def make_xml_alert(
    *,
    identifier: str,
    msg_type: str = "Alert",
    references: str = "",
    event: str = "Chuva intensa",
    area: str = "Ituverava/SP",
    expires: str = "2099-01-01T00:00:00-03:00",
) -> str:
    return f"""
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>{identifier}</identifier>
      <sender>defesa@example.gov.br</sender>
      <sent>2026-10-05T10:00:00-03:00</sent>
      <status>Actual</status>
      <msgType>{msg_type}</msgType>
      <scope>Public</scope>
      <references>{references}</references>
      <info>
        <event>{event}</event>
        <urgency>Immediate</urgency>
        <severity>Severe</severity>
        <certainty>Observed</certainty>
        <area><areaDesc>{area}</areaDesc></area>
        <headline>{event} em Ituverava</headline>
        <description>Evite áreas de risco.</description>
        <instruction>Procure abrigo.</instruction>
        <onset>2026-10-05T12:00:00-03:00</onset>
        <expires>{expires}</expires>
      </info>
    </alert>
    """


def test_defense_civil_matches_city_and_uf() -> None:
    assert DefenseCivilAlertService._matches_location(
        "Ituverava/SP, Guará/SP",
        "Ituverava",
        "SP",
    )


def test_defense_civil_does_not_match_other_city() -> None:
    assert not DefenseCivilAlertService._matches_location(
        "Guará/SP",
        "Ituverava",
        "SP",
    )


def test_defense_civil_parses_namespaced_cap_info() -> None:
    root = ET.fromstring(make_xml_alert(identifier="alert-1"))
    info = next(child for child in root if child.tag.endswith("info"))

    parsed = DefenseCivilAlertService._parse_info(
        info=info,
        identifier="alert-1",
        sender="defesa@example.gov.br",
        sent="2026-10-05T10:00:00-03:00",
        status="Actual",
        msg_type="Alert",
        scope="Public",
        references=(),
    )

    assert parsed == DefenseCivilAlert(
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
        area="Ituverava/SP",
        headline="Chuva intensa em Ituverava",
        description="Evite áreas de risco.",
        instruction="Procure abrigo.",
        onset="2026-10-05T12:00:00-03:00",
        expires="2099-01-01T00:00:00-03:00",
    )


def test_defense_civil_parses_references() -> None:
    references = DefenseCivilAlertService._parse_references(
        "sender@example.gov.br,alert-1,2026-10-05T10:00:00-03:00 "
        "sender@example.gov.br,alert-2,2026-10-05T11:00:00-03:00"
    )
    assert references == ("alert-1", "alert-2")


def test_defense_civil_rejects_expired_alert() -> None:
    assert not DefenseCivilAlertService._is_active("2020-01-01T00:00:00+00:00")


def test_defense_civil_accepts_future_alert() -> None:
    assert DefenseCivilAlertService._is_active("2099-01-01T00:00:00+00:00")


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


class FakeResolver:
    def resolve(self, query: str) -> Municipality:
        return Municipality(code=123, name="Ituverava", uf="SP")


def test_defense_civil_update_supersedes_previous_alert(monkeypatch) -> None:
    previous = make_xml_alert(identifier="alert-1", event="Alerta antigo")
    update = make_xml_alert(
        identifier="alert-2",
        msg_type="Update",
        references="defesa@example.gov.br,alert-1,2026-10-05T10:00:00-03:00",
        event="Alerta atualizado",
    )
    xml = f"<feed>{previous}{update}</feed>".encode()

    monkeypatch.setattr(
        "meshbot.infrastructure.defense_civil.requests.get",
        lambda *args, **kwargs: FakeResponse(xml),
    )
    service = DefenseCivilAlertService(resolver=FakeResolver())

    alerts = service.get_alerts("Ituverava/SP")

    assert tuple(alert.identifier for alert in alerts) == ("alert-2",)


def test_defense_civil_cancel_removes_previous_alert(monkeypatch) -> None:
    previous = make_xml_alert(identifier="alert-1", event="Alerta cancelado")
    cancel = """
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <identifier>alert-cancel</identifier>
      <sender>defesa@example.gov.br</sender>
      <sent>2026-10-05T12:00:00-03:00</sent>
      <status>Actual</status>
      <msgType>Cancel</msgType>
      <scope>Public</scope>
      <references>defesa@example.gov.br,alert-1,2026-10-05T10:00:00-03:00</references>
    </alert>
    """
    xml = f"<feed>{previous}{cancel}</feed>".encode()

    monkeypatch.setattr(
        "meshbot.infrastructure.defense_civil.requests.get",
        lambda *args, **kwargs: FakeResponse(xml),
    )
    service = DefenseCivilAlertService(resolver=FakeResolver())

    alerts = service.get_alerts("Ituverava/SP")

    assert alerts == ()


def test_defense_civil_ignores_non_public_scope(monkeypatch) -> None:
    private_alert = make_xml_alert(identifier="private-1").replace(
        "<scope>Public</scope>",
        "<scope>Private</scope>",
    )
    xml = f"<feed>{private_alert}</feed>".encode()

    monkeypatch.setattr(
        "meshbot.infrastructure.defense_civil.requests.get",
        lambda *args, **kwargs: FakeResponse(xml),
    )
    service = DefenseCivilAlertService(resolver=FakeResolver())

    assert service.get_alerts("Ituverava/SP") == ()
