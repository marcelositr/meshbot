"""User entities and authorization roles."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    """Roles available to MeshBot users."""

    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class User:
    """A registered Meshtastic user."""

    node_id: str
    role: UserRole = UserRole.USER
    blocked: bool = False
    silenced_until: datetime | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must not be empty.")

    def is_silenced(self, now: datetime) -> bool:
        """Return whether the user is currently silenced."""
        return self.silenced_until is not None and self.silenced_until > now
