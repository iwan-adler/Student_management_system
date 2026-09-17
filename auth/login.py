"""Authentication operations isolated from presentation code."""

from database.database import get_connection
from utils.security import hash_password, verify_password


def authenticate(username: str, password: str):
    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return user if user and verify_password(password, user["password_hash"]) else None


def change_password(user_id: int, password: str) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?", (hash_password(password), user_id))
