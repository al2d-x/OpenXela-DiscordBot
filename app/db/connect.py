import sqlite3
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATHS = [
    Path(__file__).with_name("schema.sql"),
    APP_ROOT / "features" / "temp_voice" / "schema.sql",
]


def get_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as connection:
        for schema_path in SCHEMA_PATHS:
            if not schema_path.exists():
                continue
            schema_sql = schema_path.read_text(encoding="utf-8")
            connection.executescript(schema_sql)
        connection.commit()
