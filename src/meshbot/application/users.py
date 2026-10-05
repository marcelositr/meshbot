"""Application boundaries for user persistence."""

from typing import Protocol

from meshbot.domain.users import User


class UserRepository(Protocol):
    """Persistence boundary for registered users."""

    def get(self, node_id: str) -> User | None:
        """Return a registered user, if present."""
        ...

    def save(self, user: User) -> None:
        """Create or update a registered user."""
        ...

    def list_all(self) -> tuple[User, ...]:
        """Return all registered users."""
        ...
