"""Tests for user management application rules."""

from meshbot.application.users import UserService
from meshbot.domain.users import User, UserRole


class InMemoryUsers:
    """Small repository fake for user service tests."""

    def __init__(self, users: tuple[User, ...] = ()) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        return self._users.get(node_id)

    def save(self, user: User) -> None:
        self._users[user.node_id] = user

    def list_all(self) -> tuple[User, ...]:
        return tuple(self._users.values())


def test_admin_can_register_user() -> None:
    repository = InMemoryUsers((User("!11111111", role=UserRole.ADMIN),))
    service = UserService(repository)

    assert service.register("!11111111", "!22222222") == "registered"
    assert repository.get("!22222222") == User("!22222222")


def test_normal_user_cannot_register_when_admin_required() -> None:
    repository = InMemoryUsers((User("!11111111"),))
    service = UserService(repository)

    assert service.register("!11111111", "!22222222") == "admin_required"
    assert repository.get("!22222222") is None


def test_registration_can_be_open_when_configured() -> None:
    repository = InMemoryUsers((User("!11111111"),))
    service = UserService(repository, registration_requires_admin=False)

    assert service.register("!11111111", "!22222222") == "registered"


def test_duplicate_registration_is_rejected() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
        )
    )
    service = UserService(repository)

    assert service.register("!11111111", "!22222222") == "already_registered"


def test_unknown_requester_cannot_register() -> None:
    service = UserService(InMemoryUsers())

    assert service.register("!99999999", "!22222222") == "requester_not_registered"
