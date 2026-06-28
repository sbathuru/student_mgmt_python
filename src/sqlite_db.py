import os
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional

from .db_interface import StudentRepository
from .models import Student


class SQLiteStudentDB(StudentRepository):
    """SQLite-backed implementation of the student repository."""

    def __init__(self):
        self._db_path = Path(os.getenv("SQLITE_DB_PATH", Path(__file__).resolve().parent.parent / "student.db"))
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        course TEXT NOT NULL
                    )
                    """
                )
        finally:
            conn.close()

    def add(self, student: Student) -> Student:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.execute(
                        "INSERT INTO students (name, age, email, course) VALUES (?, ?, ?, ?)",
                        (student.name, student.age, student.email, student.course),
                    )
                    student.id = cursor.lastrowid
            finally:
                conn.close()
            return student

    def get_all(self) -> List[Student]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT id, name, age, email, course FROM students ORDER BY id"
                ).fetchall()
            finally:
                conn.close()
            return [
                Student(id=row["id"], name=row["name"], age=row["age"], email=row["email"], course=row["course"])
                for row in rows
            ]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT id, name, age, email, course FROM students WHERE id = ?",
                    (student_id,),
                ).fetchone()
            finally:
                conn.close()
            if row is None:
                return None
            return Student(id=row["id"], name=row["name"], age=row["age"], email=row["email"], course=row["course"])

    def update(self, student_id: int, **fields) -> Optional[Student]:
        with self._lock:
            if not fields:
                return self.get_by_id(student_id)

            assignments = []
            values = []
            for key, value in fields.items():
                if value is not None:
                    assignments.append(f"{key} = ?")
                    values.append(value)
            values.append(student_id)

            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        f"UPDATE students SET {', '.join(assignments)} WHERE id = ?",
                        tuple(values),
                    )
            finally:
                conn.close()
            return self.get_by_id(student_id)

    def delete(self, student_id: int) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
                    deleted = cursor.rowcount > 0
            finally:
                conn.close()
            return deleted

    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                if exclude_id is None:
                    row = conn.execute(
                        "SELECT 1 FROM students WHERE LOWER(email) = LOWER(?) LIMIT 1",
                        (email,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT 1 FROM students WHERE LOWER(email) = LOWER(?) AND id != ? LIMIT 1",
                        (email, exclude_id),
                    ).fetchone()
            finally:
                conn.close()
            return row is not None
