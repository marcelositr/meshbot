"""Direct notifications for moderation actions."""

from meshbot.application.users import UserRepository
from meshbot.domain.messages import OutgoingMessage
from meshbot.domain.users import DEFAULT_USER_NAME


class ModerationNotifier:
    """Build direct messages for moderation actions."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def _display_name(self, node_id: str) -> str:
        """Return the friendly name, or the node ID when no name is set."""
        user = self._repository.get(node_id)
        if user is not None and user.name != DEFAULT_USER_NAME:
            return user.name
        return node_id

    def notify(
        self,
        action: str,
        actor_id: str,
        target_id: str,
        duration_minutes: int | None = None,
    ) -> tuple[OutgoingMessage, ...]:
        """Return the target notification followed by admin notifications."""
        target_name = self._display_name(target_id)
        actor_name = self._display_name(actor_id)

        target_texts = {
            "blocked": f"{target_name}, você foi bloqueado.",
            "unblocked": f"{target_name}, você foi desbloqueado.",
            "silenced": (
                f"{target_name}, você foi silenciado "
                f"por {duration_minutes} minuto{"" if duration_minutes == 1 else "s"}."
            ),
        }
        admin_texts = {
            "blocked": f"O administrador {actor_name} bloqueou {target_name}.",
            "unblocked": f"O administrador {actor_name} desbloqueou {target_name}.",
            "silenced": (
                f"O administrador {actor_name} silenciou "
                f"{target_name} por {duration_minutes} minutos."
            ),
        }

        target_text = target_texts[action]
        admin_text = admin_texts[action]
        messages = [OutgoingMessage(recipient_id=target_id, text=target_text)]

        for user in self._repository.list_all():
            if user.role.value == "admin":
                messages.append(
                    OutgoingMessage(recipient_id=user.node_id, text=admin_text)
                )

        return tuple(messages)
