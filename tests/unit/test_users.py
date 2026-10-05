"""Tests for user domain behavior."""

from datetime import UTC, datetime

from meshbot.domain.users import User, UserRole


def test_user_defaults_to_normal_role() -> None:
    user = User(node_id="!12345678")

    assert user.role is UserRole.USER
    assert user.blocked is False
    assert user.silenced_until is None


def test_admin_user_can_be_created() -> None:
    user = User(node_id="!12345678", role=UserRole.ADMIN)

    assert user.role is UserRole.ADMIN


def test_silenced_user_is_silenced_until_expiry() -> None:
    now = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
    user = User(
        node_id="!12345678",
        silenced_until=datetime(2026, 10, 5, 15, 30, tzinfo=UTC),
    )

    assert user.is_silenced(now) is True
    assert user.is_silenced(datetime(2026, 10, 5, 15, 30, tzinfo=UTC)) is False
