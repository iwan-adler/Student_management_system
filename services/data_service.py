"""Small, parameterized data-access service for all application modules."""

import sqlite3
from pathlib import Path

from database.database import get_connection
from utils.calculations import attendance_percentage, fee_details, grade_for


class DataService:
    """Keeps SQL out of the user-interface layer."""

    def __init__(self, database_path: Path | None = None):
        self.database_path = database_path

    def connection(self):
        return get_connection(self.database_path) if self.database_path else get_connection()

    def rows(self, query: str, parameters=()):
        with self.connection() as conn:
            return conn.execute(query, parameters).fetchall()

    def row(self, query: str, parameters=()):
        with self.connection() as conn:
            return conn.execute(query, parameters).fetchone()

    def execute(self, query: str, parameters=()):
        with self.connection() as conn:
            cursor = conn.execute(query, parameters)
            return cursor.lastrowid

    def students(self, search="", department="", year="", semester="", gender=""):
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        if search:
            query += " AND (student_id LIKE ? OR roll_number LIKE ? OR name LIKE ? OR department LIKE ? OR course LIKE ?)"
            params.extend([f"%{search}%"] * 5)
        for field, value in (("department", department), ("year", year), ("semester", semester), ("gender", gender)):
            if value and value != "All":
                query += f" AND {field} = ?"
                params.append(value)
        return self.rows(query + " ORDER BY name", params)

    def save_student(self, data: dict, record_id=None):
        fields = ("student_id", "roll_number", "name", "dob", "gender", "email", "phone", "address", "department", "course", "year", "semester", "admission_date")
        values = [data[field] for field in fields]
        if record_id:
            set_sql = ", ".join(f"{field} = ?" for field in fields) + ", updated_at = CURRENT_TIMESTAMP"
            self.execute(f"UPDATE students SET {set_sql} WHERE id = ?", values + [record_id])
        else:
            self.execute(f"INSERT INTO students ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})", values)

    def delete_student(self, record_id):
        self.execute("DELETE FROM students WHERE id = ?", (record_id,))

    def subjects(self, search=""):
        return self.rows("SELECT * FROM subjects WHERE subject_code LIKE ? OR subject_name LIKE ? OR department LIKE ? ORDER BY subject_code", [f"%{search}%"] * 3)

    def save_subject(self, data, record_id=None):
        fields = ("subject_code", "subject_name", "department", "semester", "credits")
        values = [data[field] for field in fields]
        if record_id:
            self.execute("UPDATE subjects SET " + ", ".join(f"{f} = ?" for f in fields) + " WHERE id = ?", values + [record_id])
        else:
            self.execute(f"INSERT INTO subjects ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})", values)

    def delete_subject(self, record_id):
        self.execute("DELETE FROM subjects WHERE id = ?", (record_id,))

    def student_choices(self):
        return self.rows("SELECT id, student_id || ' — ' || name AS label FROM students ORDER BY name")

    def subject_choices(self):
        return self.rows("SELECT id, subject_code || ' — ' || subject_name AS label FROM subjects ORDER BY subject_code")

    def save_mark(self, student_id, subject_id, internal, external, academic_year, semester):
        total = internal + external
        grade, _ = grade_for(total)
        self.execute("INSERT INTO marks (student_id, subject_id, internal_marks, external_marks, total_marks, grade, academic_year, semester) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(student_id, subject_id, academic_year, semester) DO UPDATE SET internal_marks=excluded.internal_marks, external_marks=excluded.external_marks, total_marks=excluded.total_marks, grade=excluded.grade", (student_id, subject_id, internal, external, total, grade, academic_year, semester))

    def mark_rows(self):
        return self.rows("SELECT m.*, st.student_id, st.name, su.subject_code, su.subject_name, su.credits FROM marks m JOIN students st ON st.id=m.student_id JOIN subjects su ON su.id=m.subject_id ORDER BY st.name, m.academic_year")

    def save_attendance(self, student_id, subject_id, total, attended, academic_year, semester):
        percentage = attendance_percentage(attended, total)
        self.execute("INSERT INTO attendance (student_id, subject_id, total_classes, attended_classes, attendance_percentage, academic_year, semester) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(student_id, subject_id, academic_year, semester) DO UPDATE SET total_classes=excluded.total_classes, attended_classes=excluded.attended_classes, attendance_percentage=excluded.attendance_percentage", (student_id, subject_id, total, attended, percentage, academic_year, semester))

    def attendance_rows(self):
        return self.rows("SELECT a.*, st.student_id, st.name, su.subject_code FROM attendance a JOIN students st ON st.id=a.student_id JOIN subjects su ON su.id=a.subject_id ORDER BY st.name")

    def save_fee(self, student_id, year, total, paid, last_payment_date):
        pending, status = fee_details(total, paid)
        self.execute("INSERT INTO fees (student_id, academic_year, total_fee, paid_amount, pending_amount, payment_status, last_payment_date) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(student_id, academic_year) DO UPDATE SET total_fee=excluded.total_fee, paid_amount=excluded.paid_amount, pending_amount=excluded.pending_amount, payment_status=excluded.payment_status, last_payment_date=excluded.last_payment_date", (student_id, year, total, paid, pending, status, last_payment_date or None))

    def fee_rows(self):
        return self.rows("SELECT f.*, st.student_id, st.name FROM fees f JOIN students st ON st.id=f.student_id ORDER BY st.name")

    def dashboard(self):
        stats = {}
        stats["Total Students"] = self.row("SELECT COUNT(*) AS value FROM students")["value"]
        stats["Total Subjects"] = self.row("SELECT COUNT(*) AS value FROM subjects")["value"]
        stats["Average GPA"] = self.row("SELECT COALESCE(AVG(total_marks) / 10, 0) AS value FROM marks")["value"]
        stats["Average Attendance"] = self.row("SELECT COALESCE(AVG(attendance_percentage), 0) AS value FROM attendance")["value"]
        threshold = float(self.row("SELECT value FROM settings WHERE key='attendance_threshold'")["value"])
        stats["Low Attendance"] = self.row("SELECT COUNT(DISTINCT student_id) AS value FROM attendance WHERE attendance_percentage < ?", (threshold,))["value"]
        stats["Pending Fees"] = self.row("SELECT COALESCE(SUM(pending_amount), 0) AS value FROM fees")["value"]
        return stats

    def profile(self, student_db_id):
        student = self.row("SELECT * FROM students WHERE id=?", (student_db_id,))
        marks = self.rows("SELECT su.subject_code, su.subject_name, su.credits, m.total_marks, m.grade, m.academic_year, m.semester FROM marks m JOIN subjects su ON su.id=m.subject_id WHERE m.student_id=?", (student_db_id,))
        attendance = self.rows("SELECT su.subject_code, a.total_classes, a.attended_classes, a.attendance_percentage FROM attendance a JOIN subjects su ON su.id=a.subject_id WHERE a.student_id=?", (student_db_id,))
        fees = self.rows("SELECT * FROM fees WHERE student_id=?", (student_db_id,))
        return student, marks, attendance, fees

    def populate_sample_data(self):
        if self.row("SELECT id FROM students LIMIT 1"):
            return False
        subjects = [("CS101", "Programming Fundamentals", "Computer Science", 1, 4), ("CS102", "Data Structures", "Computer Science", 2, 4), ("MA101", "Discrete Mathematics", "Computer Science", 1, 3), ("EN101", "Communication Skills", "Computer Science", 1, 2), ("DB201", "Database Systems", "Computer Science", 3, 4)]
        for values in subjects:
            self.execute("INSERT INTO subjects (subject_code, subject_name, department, semester, credits) VALUES (?, ?, ?, ?, ?)", values)
        for number in range(1, 11):
            self.save_student({"student_id": f"STU{number:03d}", "roll_number": f"CS2026{number:03d}", "name": f"Student {number}", "dob": "2005-01-15", "gender": "Female" if number % 2 else "Male", "email": f"student{number}@example.edu", "phone": f"987650{number:04d}", "address": "Campus Residence", "department": "Computer Science", "course": "BSc Computer Science", "year": 1, "semester": 1, "admission_date": "2026-08-01"})
        students, subjects = self.student_choices(), self.subject_choices()
        for index, student in enumerate(students):
            for subject in subjects[:3]:
                internal, external = 25 + index % 12, 40 + index % 18
                self.save_mark(student["id"], subject["id"], internal, external, "2026-27", 1)
                self.save_attendance(student["id"], subject["id"], 50, 32 + index % 19, "2026-27", 1)
            self.save_fee(student["id"], "2026-27", 50000, 50000 if index < 4 else 30000 if index < 7 else 0, "2026-09-01" if index < 7 else "")
        return True

    def clear_demo_data(self):
        """Remove operational records while preserving the administrator and settings."""
        with self.connection() as conn:
            conn.execute("DELETE FROM students")
            conn.execute("DELETE FROM subjects")
