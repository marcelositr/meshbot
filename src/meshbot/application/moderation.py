"""Application services for user moderation."""

from datetime import UTC, datetime, timedelta

from meshbot.application.users import UserRepository
from meshbot.domain.users import User, UserRole


class ModerationService:
    """Apply administrative moderation rules to registered users."""

    def __init__(
        self,
        repository: UserRepository,
        default_silence_minutes: int = 30,
    ) -> None:
        if default_silence_minutes <= 0:
            raise ValueError("default_silence_minutes must be positive.")

        self._repository = repository
        self._default_silence_minutes = default_silence_minutes

    @property
    def default_silence_minutes(self) -> int:
        """Return the configured default silence duration."""
        return self._default_silence_minutes

    def block(self, requester_id: str, target_id: str) -> str:
        """Block a registered user."""
        _, target, error = self._authorize_target(requester_id, target_id)
        if error is not None:
            return error
        assert target is not None

        if target.blocked:
            return "already_blocked"

        self._repository.save(
            User(
                node_id=target.node_id,
                name=target.name,
                role=target.role,
                blocked=True,
                silenced_until=target.silenced_until,
            )
        )
        return "blocked"

    def unblock(self, requester_id: str, target_id: str) -> str:
        """Unblock a registered user."""
        _, target, error = self._authorize_target(requester_id, target_id)
        if error is not None:
            return error
        assert target is not None

        if not target.blocked:
            return "not_blocked"

        self._repository.save(
            User(
                node_id=target.node_id,
                name=target.name,
                role=target.role,
                blocked=False,
                silenced_until=target.silenced_until,
            )
        )
        return "unblocked"

    def silence(
        self,
        requester_id: str,
        target_id: str,
        minutes: int | None = None,
        now: datetime | None = None,
    ) -> str:
        """Silence a registered user for a number of minutes."""
        _, target, error = self._authorize_target(requester_id, target_id)
        if error is not None:
            return error
        assert target is not None

        duration = self._default_silence_minutes if minutes is None else minutes
        if duration <= 0:
            return "invalid_minutes"

        current_time = now if now is not None else datetime.now(UTC)
        self._repository.save(
            User(
                node_id=target.node_id,
                name=target.name,
                role=target.role,
                blocked=target.blocked,
                silenced_until=current_time + timedelta(minutes=duration),
            )
        )
        return "silenced"

    def _authorize_target(
        self,
        requester_id: str,
        target_id: str,
    ) -> tuple[User | None, User | None, str | None]:
        requester = self._repository.get(requester_id)
        if requester is None:
            return None, None, "requester_not_registered"

        if requester.role is not UserRole.ADMIN:
            return requester, None, "admin_required"

        target = self._repository.get(target_id)
        if target is None:
            return requester, None, "target_not_registered"

        if target.role is UserRole.ADMIN:
            return requester, target, "cannot_moderate_admin"

        return requester, target, None
