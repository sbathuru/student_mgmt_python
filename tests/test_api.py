import unittest

from src.app import create_app
from src.models import Student


class FakeService:
    def __init__(self):
        self.students = [Student(id=1, name="Ava", semester="3rd", email="ava@example.com", course="CS", city="Delhi")]

    def list_students(self):
        return self.students

    def get_student(self, student_id):
        return next((s for s in self.students if s.id == student_id), None)

    def add_student(self, name, semester, email, course, city):
        student = Student(id=len(self.students) + 1, name=name, semester=semester, email=email, course=course, city=city)
        self.students.append(student)
        return student

    def update_student(self, student_id, name=None, semester=None, email=None, course=None, city=None):
        student = self.get_student(student_id)
        if student is None:
            raise ValueError("not found")
        if name is not None:
            student.name = name
        if semester is not None:
            student.semester = semester
        if email is not None:
            student.email = email
        if course is not None:
            student.course = course
        if city is not None:
            student.city = city
        return student

    def delete_student(self, student_id):
        self.students = [s for s in self.students if s.id != student_id]
        return True


class StudentApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(FakeService())
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

    def test_list_students_api(self):
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsInstance(payload, list)
        self.assertGreaterEqual(len(payload), 1)

    def test_create_and_delete_student_via_api(self):
        response = self.client.post(
            "/api/students",
            json={
                "name": "API Test Student",
                "semester": "5th",
                "email": "api-test@example.com",
                "course": "Physics",
                "city": "Mumbai",
            },
        )
        self.assertEqual(response.status_code, 201)
        created = response.get_json()
        self.assertEqual(created["name"], "API Test Student")
        self.assertIn("id", created)

        delete_response = self.client.delete(f"/api/students/{created['id']}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.get_json()["message"], "Student deleted")


if __name__ == "__main__":
    unittest.main()
