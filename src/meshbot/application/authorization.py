"""Authorization policy for incoming bot messages."""

from datetime import UTC, datetime
from typing import Protocol

from meshbot.domain.users import User


class UserLookup(Protocol):
    """Read-only access to registered users."""

    def get(self, node_id: str) -> User | None:
        """Return a registered user, if present."""
        ...


class AuthorizationResult:
    """Result of checking whether a user may use the bot."""

    def __init__(self, allowed: bool, reason: str | None = None) -> None:
        self.allowed = allowed
        self.reason = reason


class AuthorizationPolicy:
    """Apply registration and moderation rules to incoming users."""

    def __init__(self, users: UserLookup) -> None:
        self._users = users

    def check(self, node_id: str, now: datetime | None = None) -> AuthorizationResult:
        """Return whether the node may interact with the bot."""
        user = self._users.get(node_id)

        if user is None:
            return AuthorizationResult(False, "not_registered")

        if user.blocked:
            return AuthorizationResult(False, "blocked")

        current_time = now if now is not None else datetime.now(UTC)
        if user.is_silenced(current_time):
            return AuthorizationResult(False, "silenced")

        return AuthorizationResult(True)
