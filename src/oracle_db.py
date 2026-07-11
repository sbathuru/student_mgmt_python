import os
import threading
from typing import List, Optional

try:
    import oracledb
except ImportError:  # pragma: no cover - optional dependency
    oracledb = None

from .db_interface import StudentRepository
from .models import Student


class OracleStudentDB(StudentRepository):
    """Oracle-backed implementation of the student repository."""

    def __init__(self):
        self._user = os.getenv("ORACLE_USER")
        self._password = os.getenv("ORACLE_PASSWORD")
        self._dsn = os.getenv("ORACLE_DSN")
        if not self._user or not self._password or not self._dsn:
            raise ValueError(
                "Oracle configuration is incomplete. Set ORACLE_USER, ORACLE_PASSWORD, and ORACLE_DSN."
            )
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self):
        if oracledb is None:
            raise RuntimeError("Oracle support requires the 'oracledb' package to be installed.")
        return oracledb.connect(user=self._user, password=self._password, dsn=self._dsn)

    def _ensure_schema(self):
        conn = self._connect()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    BEGIN
                      EXECUTE IMMEDIATE 'CREATE TABLE students (
                        id NUMBER PRIMARY KEY,
                        name VARCHAR2(100) NOT NULL,
                        semester VARCHAR2(50) NOT NULL,
                        email VARCHAR2(255) NOT NULL UNIQUE,
                        course VARCHAR2(100) NOT NULL,
                        city VARCHAR2(100) NOT NULL
                      )';
                    EXCEPTION
                      WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                          RAISE;
                        END IF;
                    END;
                    """
                )
                cursor.execute(
                    """
                    BEGIN
                      EXECUTE IMMEDIATE 'CREATE SEQUENCE students_seq START WITH 1 INCREMENT BY 1';
                    EXCEPTION
                      WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                          RAISE;
                        END IF;
                    END;
                    """
                )
        finally:
            conn.close()

    def _row_to_student(self, row) -> Student:
        return Student(id=row[0], name=row[1], semester=row[2], email=row[3], course=row[4], city=row[5])

    def add(self, student: Student) -> Student:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT students_seq.NEXTVAL FROM dual")
                    student.id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO students (id, name, semester, email, course, city) VALUES (:1, :2, :3, :4, :5, :6)",
                        (student.id, student.name, student.semester, student.email, student.course, student.city),
                    )
            finally:
                conn.close()
            return student

    def get_all(self) -> List[Student]:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, semester, email, course, city FROM students ORDER BY id")
                rows = cursor.fetchall()
            finally:
                conn.close()
            return [self._row_to_student(row) for row in rows]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, semester, email, course, city FROM students WHERE id = :1",
                    (student_id,),
                )
                row = cursor.fetchone()
            finally:
                conn.close()
            if row is None:
                return None
            return self._row_to_student(row)

    def update(self, student_id: int, **fields) -> Optional[Student]:
        with self._lock:
            if not fields:
                return self.get_by_id(student_id)

            assignments = []
            values = []
            for key, value in fields.items():
                if value is not None:
                    values.append(value)
                    assignments.append(f"{key} = :{len(values)}")
            values.append(student_id)

            conn = self._connect()
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"UPDATE students SET {', '.join(assignments)} WHERE id = :{len(values)}",
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
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students WHERE id = :1", (student_id,))
                    deleted = cursor.rowcount > 0
            finally:
                conn.close()
            return deleted

    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                if exclude_id is None:
                    cursor.execute(
                        "SELECT 1 FROM students WHERE LOWER(email) = LOWER(:1) AND ROWNUM = 1",
                        (email,),
                    )
                else:
                    cursor.execute(
                        "SELECT 1 FROM students WHERE LOWER(email) = LOWER(:1) AND id != :2 AND ROWNUM = 1",
                        (email, exclude_id),
                    )
                row = cursor.fetchone()
            finally:
                conn.close()
            return row is not None
