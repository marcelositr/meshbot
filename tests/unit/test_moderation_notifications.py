"""Tests for moderation direct notifications."""

from meshbot.application.moderation_notifications import ModerationNotifier
from meshbot.domain.users import User, UserRole


class InMemoryUsers:
    """Small repository fake for notification tests."""

    def __init__(self, users: tuple[User, ...]) -> None:
        self._users = {user.node_id: user for user in users}

    def get(self, node_id: str) -> User | None:
        """Return a registered user."""
        return self._users.get(node_id)

    def save(self, user: User) -> None:
        """Store a user."""
        self._users[user.node_id] = user

    def list_all(self) -> tuple[User, ...]:
        """Return all users."""
        return tuple(self._users.values())


def test_block_notification_targets_user_then_all_admins() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
            User("!33333333", role=UserRole.ADMIN),
        )
    )
    notifier = ModerationNotifier(repository)

    messages = notifier.notify("blocked", "!11111111", "!22222222")

    assert [message.recipient_id for message in messages] == [
        "!22222222",
        "!11111111",
        "!33333333",
    ]
    assert messages[0].recipient_id == "!22222222"
    assert messages[0].text == "!22222222, você foi bloqueado."
    assert [message.recipient_id for message in messages[1:]] == ["!11111111", "!33333333"]
    assert all(
        message.text == "O administrador !11111111 bloqueou !22222222."
        for message in messages[1:]
    )


def test_silence_notification_includes_duration() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222"),
        )
    )
    notifier = ModerationNotifier(repository)

    messages = notifier.notify("silenced", "!11111111", "!22222222", 15)

    assert messages[0].recipient_id == "!22222222"
    assert messages[0].text == "!22222222, você foi silenciado por 15 minutos."
    assert messages[1].recipient_id == "!11111111"
    assert messages[1].text == "O administrador !11111111 silenciou !22222222 por 15 minutos."


def test_moderation_preserves_target_name() -> None:
    repository = InMemoryUsers(
        (
            User("!11111111", role=UserRole.ADMIN),
            User("!22222222", name="Ana Clara"),
        )
    )
    notifier = ModerationNotifier(repository)
    assert notifier.notify("blocked", "!11111111", "!22222222")[0].text == "!22222222, você foi bloqueado."
