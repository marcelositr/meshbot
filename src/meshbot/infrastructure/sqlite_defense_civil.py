"""SQLite persistence for Defense Civil alert state."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from meshbot.application.defense_civil import DefenseCivilAlert
from meshbot.application.defense_civil_state import StoredDefenseCivilAlert


class SQLiteDefenseCivilAlertRepository:
    """Persist Defense Civil alerts in the local SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def upsert(self, alert: DefenseCivilAlert, *, active: bool) -> None:
        updated_at = datetime.now().astimezone().isoformat()
        references = "\n".join(alert.references)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO defense_civil_alerts (
                    identifier, sender, sent, status, msg_type, scope,
                    references_text, event, severity, urgency, certainty,
                    area, headline, description, instruction, onset,
                    expires, active, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(identifier) DO UPDATE SET
                    sender = excluded.sender,
                    sent = excluded.sent,
                    status = excluded.status,
                    msg_type = excluded.msg_type,
                    scope = excluded.scope,
                    references_text = excluded.references_text,
                    event = excluded.event,
                    severity = excluded.severity,
                    urgency = excluded.urgency,
                    certainty = excluded.certainty,
                    area = excluded.area,
                    headline = excluded.headline,
                    description = excluded.description,
                    instruction = excluded.instruction,
                    onset = excluded.onset,
                    expires = excluded.expires,
                    active = excluded.active,
                    updated_at = excluded.updated_at
                """,
                (
                    alert.identifier,
                    alert.sender,
                    alert.sent,
                    alert.status,
                    alert.msg_type,
                    alert.scope,
                    references,
                    alert.event,
                    alert.severity,
                    alert.urgency,
                    alert.certainty,
                    alert.area,
                    alert.headline,
                    alert.description,
                    alert.instruction,
                    alert.onset,
                    alert.expires,
                    int(active),
                    updated_at,
                ),
            )

    def get(self, identifier: str) -> StoredDefenseCivilAlert | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM defense_civil_alerts WHERE identifier = ?",
                (identifier,),
            ).fetchone()

        return self._row_to_stored(row) if row is not None else None

    def list_active(self) -> tuple[StoredDefenseCivilAlert, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM defense_civil_alerts
                WHERE active = 1
                ORDER BY sent, identifier
                """
            ).fetchall()

        return tuple(self._row_to_stored(row) for row in rows)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS defense_civil_alerts (
                    identifier TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    sent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    msg_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    references_text TEXT NOT NULL,
                    event TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    certainty TEXT NOT NULL,
                    area TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    description TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    onset TEXT,
                    expires TEXT,
                    active INTEGER NOT NULL CHECK(active IN (0, 1)),
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._database_path)

    @staticmethod
    def _row_to_stored(row: tuple[object, ...]) -> StoredDefenseCivilAlert:
        (
            identifier,
            sender,
            sent,
            status,
            msg_type,
            scope,
            references_text,
            event,
            severity,
            urgency,
            certainty,
            area,
            headline,
            description,
            instruction,
            onset,
            expires,
            active,
            updated_at,
        ) = row

        values = (
            identifier, sender, sent, status, msg_type, scope,
            event, severity, urgency, certainty, area, headline,
            description, instruction,
        )
        if not all(isinstance(value, str) for value in values):
            raise ValueError("Invalid Defense Civil alert stored in database.")
        if not isinstance(references_text, str):
            raise ValueError("Invalid Defense Civil references stored in database.")
        if onset is not None and not isinstance(onset, str):
            raise ValueError("Invalid Defense Civil onset stored in database.")
        if expires is not None and not isinstance(expires, str):
            raise ValueError("Invalid Defense Civil expires stored in database.")
        if not isinstance(active, int) or not isinstance(updated_at, str):
            raise ValueError("Invalid Defense Civil state stored in database.")

        alert = DefenseCivilAlert(
            identifier=identifier,
            sender=sender,
            sent=sent,
            status=status,
            msg_type=msg_type,
            scope=scope,
            references=tuple(filter(None, references_text.split("\n"))),
            event=event,
            severity=severity,
            urgency=urgency,
            certainty=certainty,
            area=area,
            headline=headline,
            description=description,
            instruction=instruction,
            onset=onset,
            expires=expires,
        )
        return StoredDefenseCivilAlert(
            alert=alert,
            active=bool(active),
            updated_at=datetime.fromisoformat(updated_at),
        )
