"""SQLite schema definitions kept separate from database access code."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    must_change_password INTEGER NOT NULL DEFAULT 1 CHECK (must_change_password IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL UNIQUE,
    roll_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    dob TEXT,
    gender TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    department TEXT NOT NULL,
    course TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year > 0),
    semester INTEGER NOT NULL CHECK (semester > 0),
    admission_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT NOT NULL UNIQUE,
    subject_name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK (semester > 0),
    credits INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    internal_marks REAL NOT NULL CHECK (internal_marks BETWEEN 0 AND 40),
    external_marks REAL NOT NULL CHECK (external_marks BETWEEN 0 AND 60),
    total_marks REAL NOT NULL CHECK (total_marks BETWEEN 0 AND 100),
    grade TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK (semester > 0),
    UNIQUE (student_id, subject_id, academic_year, semester),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    total_classes INTEGER NOT NULL CHECK (total_classes >= 0),
    attended_classes INTEGER NOT NULL CHECK (attended_classes BETWEEN 0 AND total_classes),
    attendance_percentage REAL NOT NULL CHECK (attendance_percentage BETWEEN 0 AND 100),
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK (semester > 0),
    UNIQUE (student_id, subject_id, academic_year, semester),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    total_fee REAL NOT NULL CHECK (total_fee >= 0),
    paid_amount REAL NOT NULL CHECK (paid_amount BETWEEN 0 AND total_fee),
    pending_amount REAL NOT NULL CHECK (pending_amount >= 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('PAID', 'PARTIALLY PAID', 'PENDING')),
    last_payment_date TEXT,
    UNIQUE (student_id, academic_year),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department);
CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_fees_student ON fees(student_id);
"""
