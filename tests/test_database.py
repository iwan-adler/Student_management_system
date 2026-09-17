"""Basic Phase 1 database tests."""

import tempfile
import unittest
from pathlib import Path

from database.database import get_connection, initialize_database
from utils.security import verify_password


class DatabaseInitializationTests(unittest.TestCase):
    def test_schema_and_default_admin_are_created(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "test.db"
            initialize_database(path)
            with get_connection(path) as connection:
                tables = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
                table_names = {row["name"] for row in tables}
                self.assertTrue({"users", "students", "subjects", "marks", "attendance", "fees", "settings"} <= table_names)
                user = connection.execute(
                    "SELECT password_hash FROM users WHERE username = ?", ("admin",)
                ).fetchone()
                self.assertIsNotNone(user)
                self.assertTrue(verify_password("admin123", user["password_hash"]))

    def test_foreign_keys_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "test.db"
            initialize_database(path)
            with get_connection(path) as connection:
                with self.assertRaises(Exception):
                    connection.execute(
                        "INSERT INTO fees (student_id, academic_year, total_fee, paid_amount, pending_amount, payment_status) VALUES (?, ?, ?, ?, ?, ?)",
                        (999, "2026-27", 1000, 0, 1000, "PENDING"),
                    )


if __name__ == "__main__":
    unittest.main()
