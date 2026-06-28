"""
models.py
---------
Defines the Student data model used across the application.

Keeping this as a plain dataclass (instead of tying it to any specific
database library) means the same model can be reused later with
Oracle/PostgreSQL via SQLAlchemy, cx_Oracle, psycopg2, etc.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Student:
    """Represents a single student record (i.e., one row in the 'students' table)."""

    id: Optional[int]      # Primary key. None until assigned by the DB layer.
    name: str
    age: int
    email: str
    course: str

    def to_dict(self) -> dict:
        """Convert the Student object to a dictionary (useful for display/serialization)."""
        return asdict(self)
