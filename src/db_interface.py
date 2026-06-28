"""
db_interface.py
----------------
Defines the abstract contract (interface) for any Student database backend.

WHY THIS EXISTS:
This is the key piece that makes the database swappable later. Today
'InMemoryStudentDB' implements this interface using a Python dict.
Tomorrow, you can create 'PostgresStudentDB' or 'OracleStudentDB' classes
that implement the SAME methods using real SQL (via psycopg2, cx_Oracle,
SQLAlchemy, etc.) -- and the rest of the application (service layer, UI)
will not need to change AT ALL.

To migrate later:
    1. Create a new class, e.g. PostgresStudentDB(StudentRepository)
    2. Implement add/get_all/get_by_id/update/delete/exists_email using SQL
    3. In main.py, change ONE line:
           db = InMemoryStudentDB()   -->   db = PostgresStudentDB(connection_params)
    Everything else (StudentService, CLI menu) keeps working unchanged.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Student


class StudentRepository(ABC):
    """Abstract base class (interface) for student data access."""

    @abstractmethod
    def add(self, student: Student) -> Student:
        """Insert a new student record. Returns the student with its assigned ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Student]:
        """Return a list of all students."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, student_id: int) -> Optional[Student]:
        """Return a single student by ID, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def update(self, student_id: int, **fields) -> Optional[Student]:
        """Update one or more fields of a student. Returns the updated student or None."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, student_id: int) -> bool:
        """Delete a student by ID. Returns True if deleted, False if not found."""
        raise NotImplementedError

    @abstractmethod
    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check whether a given email is already used by another student."""
        raise NotImplementedError
