from meshbot.application.weather import AmbiguousCityError, CityNotFoundError
from meshbot.infrastructure.inmet_weather import IBGECityResolver, Municipality, _parse_municipality


def test_city_resolver_ignores_case_and_accents() -> None:
    resolver = IBGECityResolver()
    resolver._municipalities = (
        Municipality(code=3524105, name="Ituverava", uf="SP"),
    )

    result = resolver.resolve("ituverava")

    assert result.code == 3524105


def test_city_resolver_accepts_uf_for_ambiguous_names() -> None:
    resolver = IBGECityResolver()
    resolver._municipalities = (
        Municipality(code=1, name="Santa Rita", uf="MG"),
        Municipality(code=2, name="Santa Rita", uf="PB"),
    )

    result = resolver.resolve("Santa Rita - PB")

    assert result.code == 2


def test_city_resolver_rejects_ambiguous_name_without_uf() -> None:
    resolver = IBGECityResolver()
    resolver._municipalities = (
        Municipality(code=1, name="Santa Rita", uf="MG"),
        Municipality(code=2, name="Santa Rita", uf="PB"),
    )

    try:
        resolver.resolve("Santa Rita")
    except AmbiguousCityError as exc:
        assert exc.matches == ("Santa Rita - MG", "Santa Rita - PB")
    else:
        raise AssertionError("Expected ambiguous city error")


def test_city_resolver_rejects_unknown_city() -> None:
    resolver = IBGECityResolver()
    resolver._municipalities = ()

    try:
        resolver.resolve("Cidade Inexistente")
    except CityNotFoundError:
        pass
    else:
        raise AssertionError("Expected city not found error")


def test_parse_municipality_falls_back_to_uf_from_ibge_code() -> None:
    data = {
        "id": 3524105,
        "nome": "Ituverava",
        "microrregiao": None,
        "regiao-imediata": None,
    }

    municipality = _parse_municipality(data)

    assert municipality == Municipality(code=3524105, name="Ituverava", uf="SP")
