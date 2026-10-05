"""Application services for user management."""

from typing import Protocol

from meshbot.domain.users import User, normalize_user_name


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


class UserService:
    """Apply application rules for registering users."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def register(self, requester_id: str) -> str:
        """Register the requesting node itself."""
        node_id = requester_id.strip()

        if self._repository.get(node_id) is not None:
            return "already_registered"

        self._repository.save(User(node_id=node_id))
        return "registered"

    def set_name(self, requester_id: str, name: str) -> str:
        """Set or replace the requester's display name."""
        requester = self._repository.get(requester_id)
        if requester is None:
            return "requester_not_registered"

        try:
            normalized_name = normalize_user_name(name)
        except ValueError:
            return "invalid_name"

        self._repository.save(
            User(
                node_id=requester.node_id,
                name=normalized_name,
                role=requester.role,
                blocked=requester.blocked,
                silenced_until=requester.silenced_until,
            )
        )
        return "name_updated"
