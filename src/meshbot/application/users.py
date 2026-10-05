"""Application services for user management."""

from typing import Protocol

from meshbot.domain.users import User, UserRole


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

    def __init__(self, repository: UserRepository, registration_requires_admin: bool = True) -> None:
        self._repository = repository
        self._registration_requires_admin = registration_requires_admin

    def register(self, requester_id: str, node_id: str) -> str:
        """Register a node and return the result code."""
        if not node_id.strip():
            return "invalid_node_id"

        requester = self._repository.get(requester_id)
        if requester is None:
            return "requester_not_registered"

        if self._registration_requires_admin and requester.role is not UserRole.ADMIN:
            return "admin_required"

        if self._repository.get(node_id) is not None:
            return "already_registered"

        self._repository.save(User(node_id=node_id))
        return "registered"
