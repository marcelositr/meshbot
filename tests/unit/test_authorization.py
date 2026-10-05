"""Tests for application authorization."""

from datetime import UTC, datetime

from meshbot.application.authorization import AuthorizationPolicy
from meshbot.domain.users import User


class InMemoryUsers:
    """Small user repository fake for authorization tests."""

    def __init__(self, users: tuple[User, ...] = ()) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        """Return a registered user."""
        return self._users.get(node_id)


def test_unknown_user_is_not_authorized() -> None:
    policy = AuthorizationPolicy(InMemoryUsers())

    result = policy.check("!99999999")

    assert result.allowed is False
    assert result.reason == "not_registered"


def test_registered_user_is_authorized() -> None:
    policy = AuthorizationPolicy(InMemoryUsers((User("!12345678"),)))

    result = policy.check("!12345678")

    assert result.allowed is True
    assert result.reason is None


def test_blocked_user_is_not_authorized() -> None:
    policy = AuthorizationPolicy(InMemoryUsers((User("!12345678", blocked=True),)))

    result = policy.check("!12345678")

    assert result.allowed is False
    assert result.reason == "blocked"


def test_silenced_user_is_not_authorized() -> None:
    until = datetime(2026, 10, 5, 15, 30, tzinfo=UTC)
    policy = AuthorizationPolicy(
        InMemoryUsers((User("!12345678", silenced_until=until),))
    )

    result = policy.check(
        "!12345678",
        now=datetime(2026, 10, 5, 15, 0, tzinfo=UTC),
    )

    assert result.allowed is False
    assert result.reason == "silenced"


def test_expired_silence_allows_user() -> None:
    until = datetime(2026, 10, 5, 15, 30, tzinfo=UTC)
    policy = AuthorizationPolicy(
        InMemoryUsers((User("!12345678", silenced_until=until),))
    )

    result = policy.check(
        "!12345678",
        now=datetime(2026, 10, 5, 15, 30, tzinfo=UTC),
    )

    assert result.allowed is True
