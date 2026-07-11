"""
student_service.py
-------------------
Business logic / validation layer, sitting between the UI (main.py) and
the data layer (StudentRepository implementations).

This layer doesn't care whether the underlying DB is in-memory, Oracle,
or PostgreSQL -- it only talks to the StudentRepository interface. This
keeps validation rules (e.g. "email must be unique", "age must be
positive") centralized and reusable regardless of the storage backend.
"""

import re
from typing import List, Optional

from .db_interface import StudentRepository
from .models import Student


class ValidationError(Exception):
    """Raised when student input data fails validation rules."""
    pass


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StudentService:
    """Encapsulates validation + CRUD operations for students."""

    def __init__(self, repository: StudentRepository):
        self.repository = repository

    # ---------- Validation helpers ----------

    @staticmethod
    def _validate_name(name: str) -> str:
        name = (name or "").strip()
        if not name:
            raise ValidationError("Name cannot be empty.")
        if len(name) > 100:
            raise ValidationError("Name is too long (max 100 characters).")
        return name

    @staticmethod
    def _validate_semester(semester: str) -> str:
        semester = (semester or "").strip()
        if not semester:
            raise ValidationError("Semester cannot be empty.")
        return semester

    @staticmethod
    def _validate_email(email: str) -> str:
        email = (email or "").strip()
        if not email or not EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email format.")
        return email

    @staticmethod
    def _validate_course(course: str) -> str:
        course = (course or "").strip()
        if not course:
            raise ValidationError("Course cannot be empty.")
        return course

    @staticmethod
    def _validate_city(city: str) -> str:
        city = (city or "").strip()
        if not city:
            raise ValidationError("City cannot be empty.")
        return city

    # ---------- CRUD operations ----------

    def add_student(self, name: str, semester, email: str, course: str, city: str) -> Student:
        name = self._validate_name(name)
        semester = self._validate_semester(semester)
        email = self._validate_email(email)
        course = self._validate_course(course)
        city = self._validate_city(city)

        if self.repository.exists_email(email):
            raise ValidationError(f"A student with email '{email}' already exists.")

        student = Student(id=None, name=name, semester=semester, email=email, course=course, city=city)
        return self.repository.add(student)

    def list_students(self) -> List[Student]:
        return self.repository.get_all()

    def get_student(self, student_id: int) -> Optional[Student]:
        return self.repository.get_by_id(student_id)

    def update_student(
        self,
        student_id: int,
        name: Optional[str] = None,
        semester=None,
        email: Optional[str] = None,
        course: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Student:
        existing = self.repository.get_by_id(student_id)
        if existing is None:
            raise ValidationError(f"No student found with ID {student_id}.")

        fields = {}
        if name is not None and name.strip() != "":
            fields["name"] = self._validate_name(name)
        if semester is not None and str(semester).strip() != "":
            fields["semester"] = self._validate_semester(semester)
        if email is not None and email.strip() != "":
            email_clean = self._validate_email(email)
            if self.repository.exists_email(email_clean, exclude_id=student_id):
                raise ValidationError(f"A student with email '{email_clean}' already exists.")
            fields["email"] = email_clean
        if course is not None and course.strip() != "":
            fields["course"] = self._validate_course(course)
        if city is not None and city.strip() != "":
            fields["city"] = self._validate_city(city)

        if not fields:
            raise ValidationError("No valid fields provided to update.")

        updated = self.repository.update(student_id, **fields)
        return updated

    def delete_student(self, student_id: int) -> bool:
        return self.repository.delete(student_id)
