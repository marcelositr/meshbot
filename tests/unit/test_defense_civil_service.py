from xml.etree import ElementTree as ET

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.infrastructure.defense_civil import DefenseCivilAlertService


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
    xml = """
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
      <info>
        <event>Chuva intensa</event>
        <severity>Severo</severity>
        <area><areaDesc>Ituverava/SP</areaDesc></area>
        <headline>Chuva intensa em Ituverava</headline>
        <description>Evite áreas de risco.</description>
        <expires>2026-10-05T23:00:00-03:00</expires>
      </info>
    </alert>
    """
    root = ET.fromstring(xml)
    info = next(iter(root))

    alert = DefenseCivilAlertService._parse_info(info)

    assert alert == DefenseCivilAlert(
        event="Chuva intensa",
        severity="Severo",
        area="Ituverava/SP",
        headline="Chuva intensa em Ituverava",
        description="Evite áreas de risco.",
        expires="2026-10-05T23:00:00-03:00",
    )
