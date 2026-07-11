import os
import threading
from typing import List, Optional

import mysql.connector

from .db_interface import StudentRepository
from .models import Student


class MySQLStudentDB(StudentRepository):
    """MySQL-backed implementation of the student repository."""

    def __init__(self):
        self._config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "student_mgmt"),
            "autocommit": True,
        }
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self):
        return mysql.connector.connect(**self._config)

    def _ensure_schema(self):
        conn = self._connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS students (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        semester VARCHAR(50) NOT NULL,
                        email VARCHAR(150) NOT NULL UNIQUE,
                        course VARCHAR(100) NOT NULL,
                        city VARCHAR(100) NOT NULL
                    )
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def add(self, student: Student) -> Student:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO students (name, semester, email, course, city) VALUES (%s, %s, %s, %s, %s)",
                        (student.name, student.semester, student.email, student.course, student.city),
                    )
                    student.id = cursor.lastrowid
                conn.commit()
            finally:
                conn.close()
            return student

    def get_all(self) -> List[Student]:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT id, name, semester, email, course, city FROM students ORDER BY id")
                    rows = cursor.fetchall()
            finally:
                conn.close()
            return [Student(id=row["id"], name=row["name"], semester=row["semester"], email=row["email"], course=row["course"], city=row["city"]) for row in rows]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT id, name, semester, email, course, city FROM students WHERE id = %s", (student_id,))
                    row = cursor.fetchone()
            finally:
                conn.close()
            if row is None:
                return None
            return Student(id=row["id"], name=row["name"], semester=row["semester"], email=row["email"], course=row["course"], city=row["city"])

    def update(self, student_id: int, **fields) -> Optional[Student]:
        with self._lock:
            if not fields:
                return self.get_by_id(student_id)

            assignments = []
            values = []
            for key, value in fields.items():
                if value is not None:
                    assignments.append(f"{key} = %s")
                    values.append(value)
            values.append(student_id)

            conn = self._connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE students SET {', '.join(assignments)} WHERE id = %s",
                        tuple(values),
                    )
                conn.commit()
            finally:
                conn.close()
            return self.get_by_id(student_id)

    def delete(self, student_id: int) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
                conn.commit()
            finally:
                conn.close()
            return cursor.rowcount > 0 if 'cursor' in locals() else False

    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                with conn.cursor() as cursor:
                    if exclude_id is None:
                        cursor.execute("SELECT 1 FROM students WHERE LOWER(email) = LOWER(%s) LIMIT 1", (email,))
                    else:
                        cursor.execute(
                            "SELECT 1 FROM students WHERE LOWER(email) = LOWER(%s) AND id != %s LIMIT 1",
                            (email, exclude_id),
                        )
                    return cursor.fetchone() is not None
            finally:
                conn.close()
