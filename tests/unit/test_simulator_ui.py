"""Tests for the simulator terminal UI helpers."""

from meshbot.interfaces.simulator_ui import parse_input


def test_parse_input_accepts_node_and_message() -> None:
    assert parse_input("!12345678 !ping") == ("!12345678", "!ping")


def test_parse_input_preserves_spaces_inside_message() -> None:
    assert parse_input("!12345678 bom dia Marcelo") == (
        "!12345678",
        "bom dia Marcelo",
    )


def test_parse_input_rejects_blank_or_incomplete_input() -> None:
    assert parse_input("") is None
    assert parse_input("   ") is None
    assert parse_input("!12345678") is None
