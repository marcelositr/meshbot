"""Integration tests for SQLite user persistence."""

from datetime import UTC, datetime

from meshbot.domain.users import User, UserRole
from meshbot.infrastructure.sqlite_users import SQLiteUserRepository


def test_sqlite_repository_round_trips_user(tmp_path) -> None:
    repository = SQLiteUserRepository(tmp_path / "meshbot.db")
    user = User(
        node_id="!12345678",
        role=UserRole.ADMIN,
        blocked=True,
        silenced_until=datetime(2026, 10, 5, 15, 30, tzinfo=UTC),
    )

    repository.save(user)

    assert repository.get("!12345678") == user


def test_sqlite_repository_updates_existing_user(tmp_path) -> None:
    repository = SQLiteUserRepository(tmp_path / "meshbot.db")
    repository.save(User(node_id="!12345678"))
    repository.save(User(node_id="!12345678", role=UserRole.ADMIN))

    assert repository.get("!12345678") == User(
        node_id="!12345678",
        role=UserRole.ADMIN,
    )


def test_sqlite_repository_lists_users_by_node_id(tmp_path) -> None:
    repository = SQLiteUserRepository(tmp_path / "meshbot.db")
    repository.save(User(node_id="!22222222"))
    repository.save(User(node_id="!11111111"))

    assert repository.list_all() == (
        User(node_id="!11111111"),
        User(node_id="!22222222"),
    )


def test_sqlite_repository_returns_none_for_unknown_user(tmp_path) -> None:
    repository = SQLiteUserRepository(tmp_path / "meshbot.db")

    assert repository.get("!99999999") is None
