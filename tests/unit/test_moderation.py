"""Tests for user moderation service."""

from datetime import UTC, datetime

from meshbot.application.moderation import ModerationService
from meshbot.domain.users import User, UserRole


class InMemoryUsers:
    """Small repository fake for moderation tests."""

    def __init__(self, users: tuple[User, ...]) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        """Return a registered user."""
        return self._users.get(node_id)

    def save(self, user: User) -> None:
        """Store a user."""
        self._users[user.node_id] = user

    def list_all(self) -> tuple[User, ...]:
        """Return all users."""
        return tuple(self._users.values())


def make_service(*users: User, default_silence_minutes: int = 30) -> tuple[
    ModerationService, InMemoryUsers
]:
    repository = InMemoryUsers(tuple(users))
    return ModerationService(repository, default_silence_minutes), repository


def test_admin_can_block_user() -> None:
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222"),
    )

    assert service.block("!11111111", "!22222222") == "blocked"
    assert repository.get("!22222222") == User("!22222222", blocked=True)


def test_admin_can_unblock_user() -> None:
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222", blocked=True),
    )

    assert service.unblock("!11111111", "!22222222") == "unblocked"
    assert repository.get("!22222222") == User("!22222222")


def test_admin_can_silence_user_for_custom_duration() -> None:
    now = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222"),
    )

    assert service.silence("!11111111", "!22222222", 15, now) == "silenced"
    assert repository.get("!22222222") == User(
        "!22222222",
        silenced_until=datetime(2026, 10, 5, 15, 15, tzinfo=UTC),
    )


def test_silence_uses_default_duration() -> None:
    now = datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222"),
        default_silence_minutes=45,
    )

    assert service.silence("!11111111", "!22222222", now=now) == "silenced"
    assert repository.get("!22222222") == User(
        "!22222222",
        silenced_until=datetime(2026, 10, 5, 15, 45, tzinfo=UTC),
    )


def test_normal_user_cannot_moderate() -> None:
    service, repository = make_service(
        User("!11111111"),
        User("!22222222"),
    )

    assert service.block("!11111111", "!22222222") == "admin_required"
    assert repository.get("!22222222") == User("!22222222")


def test_admin_cannot_moderate_admin() -> None:
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222", role=UserRole.ADMIN),
    )

    assert service.block("!11111111", "!22222222") == "cannot_moderate_admin"
    assert service.unblock("!11111111", "!22222222") == "cannot_moderate_admin"
    assert service.silence("!11111111", "!22222222") == "cannot_moderate_admin"
    assert repository.get("!22222222") == User("!22222222", role=UserRole.ADMIN)


def test_moderation_requires_registered_target() -> None:
    service, _ = make_service(User("!11111111", role=UserRole.ADMIN))

    assert service.block("!11111111", "!99999999") == "target_not_registered"


def test_invalid_silence_duration_is_rejected() -> None:
    service, repository = make_service(
        User("!11111111", role=UserRole.ADMIN),
        User("!22222222"),
    )

    assert service.silence("!11111111", "!22222222", 0) == "invalid_minutes"
    assert repository.get("!22222222") == User("!22222222")
