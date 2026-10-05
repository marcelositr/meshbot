"""Direct notifications for moderation actions."""

from meshbot.application.users import UserRepository
from meshbot.domain.messages import OutgoingMessage


class ModerationNotifier:
    """Build direct messages for moderation actions."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def notify(
        self,
        action: str,
        actor_id: str,
        target_id: str,
        duration_minutes: int | None = None,
    ) -> tuple[Message, ...]:
        """Return the target notification followed by admin notifications."""
        target_texts = {
            "blocked": "MeshBot: Você foi bloqueado.",
            "unblocked": "MeshBot: Seu acesso ao MeshBot foi desbloqueado.",
            "silenced": (
                f"MeshBot: Você foi silenciado por {duration_minutes} minutos."
            ),
        }
        admin_texts = {
            "blocked": f"MeshBot: Admin {actor_id} bloqueou {target_id}.",
            "unblocked": f"MeshBot: Admin {actor_id} desbloqueou {target_id}.",
            "silenced": (
                f"MeshBot: Admin {actor_id} silenciou "
                f"{target_id} por {duration_minutes} minutos."
            ),
        }

        target_text = target_texts[action]
        admin_text = admin_texts[action]
        messages = [OutgoingMessage(recipient_id=target_id, text=target_text)]

        for user in self._repository.list_all():
            if user.role.value == "admin":
                messages.append(OutgoingMessage(recipient_id=user.node_id, text=admin_text))

        return tuple(messages)
