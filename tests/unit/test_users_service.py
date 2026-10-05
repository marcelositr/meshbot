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


def test_user_can_register_themselves() -> None:
    repository = InMemoryUsers()
    service = UserService(repository)

    assert service.register("!22222222") == "registered"
    assert repository.get("!22222222") == User("!22222222")


def test_duplicate_registration_is_rejected() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
        )
    )
    service = UserService(repository)

    assert service.register("!22222222") == "already_registered"


def test_registered_user_can_set_name() -> None:
    repository = InMemoryUsers((User("!11111111"),))
    service = UserService(repository)

    assert service.set_name("!11111111", "  Ana   Clara  ") == "name_updated"
    assert repository.get("!11111111") == User("!11111111", name="Ana Clara")


def test_registered_user_can_rename() -> None:
    repository = InMemoryUsers((User("!11111111", name="Ana Clara"),))
    service = UserService(repository)

    assert service.set_name("!11111111", "João Pedro") == "name_updated"
    assert repository.get("!11111111") == User("!11111111", name="João Pedro")


def test_unregistered_user_cannot_set_name() -> None:
    service = UserService(InMemoryUsers())

    assert service.set_name("!99999999", "Ana Clara") == "requester_not_registered"


def test_user_name_limit_is_24_characters() -> None:
    repository = InMemoryUsers((User("!11111111"),))
    service = UserService(repository)

    assert service.set_name("!11111111", "123456789012345678901234") == "name_updated"
    assert service.set_name("!11111111", "1234567890123456789012345") == "invalid_name"
