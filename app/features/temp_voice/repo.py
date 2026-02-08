from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.db.connect import get_connection


class TempVoiceRepository:
    def __init__(self, db_path: str) -> None:
        self._conn = get_connection(db_path)

    def _utc_now(self) -> str:
        return datetime.now(UTC).isoformat()

    def is_hub_channel(self, guild_id: int, channel_id: int) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM hub_channels WHERE guild_id = ? AND channel_id = ?",
            (str(guild_id), str(channel_id)),
        ).fetchone()
        return row is not None

    def list_hub_channels(self, guild_id: int) -> list[int]:
        rows = self._conn.execute(
            "SELECT channel_id FROM hub_channels WHERE guild_id = ? ORDER BY created_at",
            (str(guild_id),),
        ).fetchall()
        return [int(row["channel_id"]) for row in rows]

    def add_hub_channel(self, guild_id: int, channel_id: int, created_by_user_id: int) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO hub_channels (guild_id, channel_id, created_by_user_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (str(guild_id), str(channel_id), str(created_by_user_id), self._utc_now()),
            )

    def remove_hub_channel(self, guild_id: int, channel_id: int) -> bool:
        with self._conn:
            result = self._conn.execute(
                "DELETE FROM hub_channels WHERE guild_id = ? AND channel_id = ?",
                (str(guild_id), str(channel_id)),
            )
        return result.rowcount > 0

    def set_temp_category(self, guild_id: int, category_id: int | None) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO guild_config (guild_id, temp_category_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET temp_category_id = excluded.temp_category_id
                """,
                (str(guild_id), str(category_id) if category_id is not None else None),
            )

    def get_temp_category(self, guild_id: int) -> int | None:
        row = self._conn.execute(
            "SELECT temp_category_id FROM guild_config WHERE guild_id = ?",
            (str(guild_id),),
        ).fetchone()
        if row is None or row["temp_category_id"] is None:
            return None
        return int(row["temp_category_id"])

    def upsert_managed_channel(
        self,
        guild_id: int,
        channel_id: int,
        owner_user_id: int,
        hub_channel_id: int,
        name: str,
    ) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO managed_voice_channels (
                    guild_id, channel_id, owner_user_id, hub_channel_id, created_at, pending_delete_at, name
                ) VALUES (?, ?, ?, ?, ?, NULL, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    guild_id = excluded.guild_id,
                    owner_user_id = excluded.owner_user_id,
                    hub_channel_id = excluded.hub_channel_id,
                    name = excluded.name,
                    pending_delete_at = NULL
                """,
                (
                    str(guild_id),
                    str(channel_id),
                    str(owner_user_id),
                    str(hub_channel_id),
                    self._utc_now(),
                    name,
                ),
            )

    def get_managed_channel(self, channel_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM managed_voice_channels WHERE channel_id = ?",
            (str(channel_id),),
        ).fetchone()
        return dict(row) if row else None

    def list_managed_channels(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM managed_voice_channels").fetchall()
        return [dict(row) for row in rows]

    def set_pending_delete_at(self, channel_id: int, pending_delete_at: str | None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE managed_voice_channels SET pending_delete_at = ? WHERE channel_id = ?",
                (pending_delete_at, str(channel_id)),
            )

    def update_managed_owner(self, channel_id: int, owner_user_id: int) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE managed_voice_channels SET owner_user_id = ? WHERE channel_id = ?",
                (str(owner_user_id), str(channel_id)),
            )

    def update_managed_name(self, channel_id: int, name: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE managed_voice_channels SET name = ? WHERE channel_id = ?",
                (name, str(channel_id)),
            )

    def remove_managed_channel(self, channel_id: int) -> bool:
        with self._conn:
            result = self._conn.execute(
                "DELETE FROM managed_voice_channels WHERE channel_id = ?",
                (str(channel_id),),
            )
        return result.rowcount > 0

