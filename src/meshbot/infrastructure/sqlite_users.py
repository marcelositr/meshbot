"""SQLite persistence for MeshBot users."""

import sqlite3
from datetime import datetime
from pathlib import Path

from meshbot.domain.users import User, UserRole


class SQLiteUserRepository:
    """Persist registered users in a local SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def get(self, node_id: str) -> User | None:
        """Return a registered user, if present."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT node_id, role, blocked, silenced_until
                FROM users
                WHERE node_id = ?
                """,
                (node_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_user(row)

    def save(self, user: User) -> None:
        """Create or update a registered user."""
        silenced_until = (
            user.silenced_until.isoformat() if user.silenced_until is not None else None
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (node_id, role, blocked, silenced_until)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    role = excluded.role,
                    blocked = excluded.blocked,
                    silenced_until = excluded.silenced_until
                """,
                (
                    user.node_id,
                    user.role.value,
                    int(user.blocked),
                    silenced_until,
                ),
            )

    def list_all(self) -> tuple[User, ...]:
        """Return all registered users ordered by node ID."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT node_id, role, blocked, silenced_until
                FROM users
                ORDER BY node_id
                """
            ).fetchall()

        return tuple(self._row_to_user(row) for row in rows)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    node_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
                    blocked INTEGER NOT NULL CHECK(blocked IN (0, 1)),
                    silenced_until TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._database_path)

    @staticmethod
    def _row_to_user(row: tuple[object, ...]) -> User:
        node_id, role, blocked, silenced_until = row
        if not isinstance(node_id, str):
            raise ValueError("Invalid node_id stored in users table.")
        if not isinstance(role, str):
            raise ValueError("Invalid role stored in users table.")
        if not isinstance(blocked, int):
            raise ValueError("Invalid blocked value stored in users table.")
        if silenced_until is not None and not isinstance(silenced_until, str):
            raise ValueError("Invalid silenced_until value stored in users table.")

        return User(
            node_id=node_id,
            role=UserRole(role),
            blocked=bool(blocked),
            silenced_until=(
                datetime.fromisoformat(silenced_until)
                if silenced_until is not None
                else None
            ),
        )
