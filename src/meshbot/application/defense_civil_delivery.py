"""Defense Civil alert formatting and delivery targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_state import DefenseCivilAlertEvent
from meshbot.domain.messages import OutgoingMessage


@dataclass(frozen=True, slots=True)
class DefenseCivilDeliverySettings:
    """Policy for automatic Defense Civil transmissions."""

    enabled: bool
    location: str
    recipient_id: str
    max_message_length: int


class DefenseCivilAlertFormatter(Protocol):
    """Format one alert into radio-sized messages."""

    def format(self, alert: DefenseCivilAlert) -> tuple[str, ...]:
        """Return the messages for one alert."""
        ...


class DefenseCivilTargetResolver(Protocol):
    """Resolve whether an alert belongs to the configured transmission area."""

    def matches(self, alert: DefenseCivilAlert) -> bool:
        """Return whether the alert should be transmitted."""
        ...


class CompactDefenseCivilAlertFormatter:
    """Format alerts conservatively for automatic radio transmission."""

    def __init__(self, max_message_length: int = 180) -> None:
        if max_message_length <= 0:
            raise ValueError("max_message_length must be greater than zero.")
        self._max_message_length = max_message_length

    def format(self, alert: DefenseCivilAlert) -> tuple[str, ...]:
        """Build compact messages and split them at word boundaries."""
        fields = [
            "⚠️ DEFESA CIVIL",
            " ".join((alert.headline or alert.event).split()),
            f"Severidade: {alert.severity}.",
        ]
        if alert.urgency:
            fields.append(f"Urgência: {alert.urgency}.")
        if alert.instruction:
            fields.append(" ".join(alert.instruction.split()))

        text = " ".join(field for field in fields if field)
        return self._split(text)

    def _split(self, text: str) -> tuple[str, ...]:
        words = text.split()
        parts: list[str] = []
        current = ""

        for word in words:
            candidate = word if not current else f"{current} {word}"
            if len(candidate) <= self._max_message_length:
                current = candidate
                continue

            if current:
                parts.append(current)

            if len(word) > self._max_message_length:
                parts.extend(
                    word[index : index + self._max_message_length]
                    for index in range(0, len(word), self._max_message_length)
                )
                current = ""
            else:
                current = word

        if current:
            parts.append(current)
        return tuple(parts)


class LocationDefenseCivilTargetResolver:
    """Match alerts against a configured municipality/UF text."""

    def __init__(self, location: str) -> None:
        normalized = " ".join(location.casefold().split())
        if not normalized:
            raise ValueError("location must not be empty.")
        self._location = normalized

    def matches(self, alert: DefenseCivilAlert) -> bool:
        """Return whether the CAP area contains the configured location."""
        area = " ".join(alert.area.casefold().split())
        return self._location in area


class DefenseCivilDelivery:
    """Turn one alert into targeted outgoing messages."""

    def __init__(
        self,
        formatter: DefenseCivilAlertFormatter,
        target_resolver: DefenseCivilTargetResolver,
        recipient_id: str,
    ) -> None:
        if not recipient_id.strip():
            raise ValueError("recipient_id must not be empty.")
        self._formatter = formatter
        self._target_resolver = target_resolver
        self._recipient_id = recipient_id

    def deliver(self, alert: DefenseCivilAlert) -> tuple[OutgoingMessage, ...]:
        """Format and target an alert, or return no messages."""
        if not self._target_resolver.matches(alert):
            return ()
        return tuple(
            OutgoingMessage(recipient_id=self._recipient_id, text=text)
            for text in self._formatter.format(alert)
        )


class DefenseCivilEventDispatcher:
    """Deliver only new or changed alerts from lifecycle events."""

    def __init__(
        self,
        delivery: DefenseCivilDelivery,
        send: Protocol,
    ) -> None:
        self._delivery = delivery
        self._send = send

    def dispatch(self, event: DefenseCivilAlertEvent) -> None:
        """Deliver a new or updated alert; ignore deactivation events."""
        if event.type == "deactivated":
            return
        for message in self._delivery.deliver(event.alert):
            self._send.send(message)
