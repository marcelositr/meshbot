"""User entities and authorization roles."""

import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

MAX_USER_NAME_LENGTH = 24
DEFAULT_USER_NAME = "Sem nome"


def normalize_node_id(value: str) -> str:
    """Normalize and validate a standard Meshtastic node ID."""
    value = value.strip().lower()
    if len(value) != 9 or value[0] != "!" or any(char not in "0123456789abcdef" for char in value[1:]):
        raise ValueError("node_id must use ! followed by 8 hexadecimal characters.")
    return value


def normalize_user_name(value: str) -> str:
    """Normalize and validate a registered user's display name."""
    value = unicodedata.normalize("NFC", " ".join(value.strip().split()))

    if not value:
        raise ValueError("name must not be empty.")

    if len(value) > MAX_USER_NAME_LENGTH:
        raise ValueError(
            f"name must not exceed {MAX_USER_NAME_LENGTH} characters."
        )

    for char in value:
        if char == " ":
            continue

        category = unicodedata.category(char)

        # Unicode letters (L*) and decimal digits (Nd).
        # This accepts accented letters and preserves case,
        # while rejecting punctuation, symbols and emojis.
        if not category.startswith("L") and category != "Nd":
            raise ValueError(
                "name must contain only letters, numbers, and spaces."
            )

    return value


class UserRole(StrEnum):
    """Roles available to MeshBot users."""

    USER = "user"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class User:
    """A registered Meshtastic user."""

    node_id: str
    name: str = DEFAULT_USER_NAME
    role: UserRole = UserRole.USER
    blocked: bool = False
    silenced_until: datetime | None = None

    def __post_init__(self) -> None:
        normalized_node_id = normalize_node_id(self.node_id)
        object.__setattr__(self, "node_id", normalized_node_id)

        normalized_name = normalize_user_name(self.name)
        object.__setattr__(self, "name", normalized_name)

    def is_silenced(self, now: datetime) -> bool:
        """Return whether the user is currently silenced."""
        return self.silenced_until is not None and self.silenced_until > now
