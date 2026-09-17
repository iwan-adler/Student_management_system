"""Database connection and first-run initialization functions."""

import sqlite3
from pathlib import Path

from config.config import (
    DATABASE_PATH,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_ATTENDANCE_THRESHOLD,
)
from database.schema import SCHEMA_SQL
from utils.security import hash_password


def get_connection(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Open an SQLite connection with foreign-key enforcement enabled."""
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """Create tables and first-run defaults without overwriting existing data."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("attendance_threshold", str(DEFAULT_ATTENDANCE_THRESHOLD)),
        )
        existing_user = connection.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USERNAME,)
        ).fetchone()
        if existing_user is None:
            connection.execute(
                "INSERT INTO users (username, password_hash, must_change_password) "
                "VALUES (?, ?, ?)",
                (DEFAULT_ADMIN_USERNAME, hash_password(DEFAULT_ADMIN_PASSWORD), 1),
            )


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DATABASE_PATH}")
