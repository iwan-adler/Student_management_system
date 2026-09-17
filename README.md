# Student Management System

A desktop-based Student Management System built with Python, Tkinter, and SQLite.

## Features

- Secure administrator login with PBKDF2 password hashing and first-login password change
- Dashboard statistics, grade distribution, configurable attendance threshold
- Student and subject CRUD with validation, search, filters, sortable tables, and deletion safeguards
- Marks, grades, GPA, attendance, and fee management
- Student profile and top-performer reports with text export
- Optional ten-student demonstration dataset and a controlled data-clear action

## Architecture

- `main.py` initializes the application.
- `config/` holds central settings and paths.
- `database/` owns the schema and SQLite access.
- `utils/` provides reusable helpers such as password hashing.
- `services/` separates database-backed business operations from screens.
- `ui/` contains the single-window Tkinter interface and reusable widgets.

## Database relationships

`students` is the central academic record. One student can have many `marks`, `attendance`, and `fees` records. Each mark and attendance entry belongs to one `subject`. Deleting a student cascades to their dependent records; subjects cannot be deleted while referenced by records.

## Run

```bash
python main.py
```

The command creates `database/student_management.db` when it does not exist and never overwrites existing records.

## Default administrator

- Username: `admin`
- Password: `admin123`

The initial account is marked to require a password change when authentication is implemented in Phase 2. This project uses local password hashing and is intended for academic use, not enterprise deployment.

## Test

```bash
python -m unittest discover -s tests
```

## Future enhancements

Student/teacher roles, PDF reports, charts using Matplotlib, backups, notifications, and web/mobile access can be added without changing the core schema.
