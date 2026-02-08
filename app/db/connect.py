import sqlite3
from pathlib import Path


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection(db_path) as connection:
        connection.executescript(schema_sql)
        connection.commit()
