"""Central configuration for the Student Management System."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "student_management.db"
APP_NAME = "Student Management System"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ATTENDANCE_THRESHOLD = 75.0

