"""
in_memory_db.py
----------------
In-memory implementation of StudentRepository.

Simulates a SQL "students" TABLE using a Python dict:
    self._table = {
        1: Student(id=1, name="...", age=.., email="...", course="..."),
        2: Student(id=2, ...),
        ...
    }

An auto-increment counter (self._next_id) mimics a database SEQUENCE /
AUTO_INCREMENT / IDENTITY column, so IDs behave the same way they would
in Oracle (SEQUENCE) or PostgreSQL (SERIAL/IDENTITY).

This class fully implements the StudentRepository interface, so it can
be swapped for a real database later without touching any other file.
"""

import threading
from typing import List, Optional

from .db_interface import StudentRepository
from .models import Student


class InMemoryStudentDB(StudentRepository):
    """In-memory 'students' table, backed by a dict for O(1) lookups by ID."""

    def __init__(self):
        # The "table": maps student_id -> Student
        self._table: dict[int, Student] = {}
        # Simulates an auto-increment primary key sequence
        self._next_id: int = 1
        # Lock to keep operations thread-safe (mirrors real DB transaction safety)
        self._lock = threading.Lock()

    def add(self, student: Student) -> Student:
        with self._lock:
            student.id = self._next_id
            self._table[student.id] = student
            self._next_id += 1
            return student

    def get_all(self) -> List[Student]:
        with self._lock:
            # Return sorted by ID for consistent, predictable listing order
            return [self._table[k] for k in sorted(self._table.keys())]

    def get_by_id(self, student_id: int) -> Optional[Student]:
        with self._lock:
            return self._table.get(student_id)

    def update(self, student_id: int, **fields) -> Optional[Student]:
        with self._lock:
            student = self._table.get(student_id)
            if student is None:
                return None
            for key, value in fields.items():
                if value is not None and hasattr(student, key):
                    setattr(student, key, value)
            return student

    def delete(self, student_id: int) -> bool:
        with self._lock:
            if student_id in self._table:
                del self._table[student_id]
                return True
            return False

    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        with self._lock:
            for sid, student in self._table.items():
                if student.email.lower() == email.lower() and sid != exclude_id:
                    return True
            return False
