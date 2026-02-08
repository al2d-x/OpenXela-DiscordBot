from __future__ import annotations

import sqlite3
import threading

from app.db.connect import get_connection


class Repository:
    def __init__(self, db_path: str) -> None:
        self._conn = get_connection(db_path)
        self._lock = threading.Lock()

    def claim_next_counter(self, guild_id: int, key: str) -> int:
        with self._lock:
            cursor = self._conn.cursor()
            try:
                cursor.execute("BEGIN IMMEDIATE")
                row = cursor.execute(
                    "SELECT value FROM counters WHERE guild_id = ? AND key = ?",
                    (str(guild_id), key),
                ).fetchone()
                if row is None:
                    value = 1
                    cursor.execute(
                        "INSERT INTO counters (guild_id, key, value) VALUES (?, ?, ?)",
                        (str(guild_id), key, value),
                    )
                else:
                    value = int(row["value"]) + 1
                    cursor.execute(
                        "UPDATE counters SET value = ? WHERE guild_id = ? AND key = ?",
                        (value, str(guild_id), key),
                    )
                self._conn.commit()
                return value
            except sqlite3.Error:
                self._conn.rollback()
                raise
