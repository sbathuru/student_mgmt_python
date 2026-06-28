import os
import tempfile
import unittest

from src.models import Student
from src.sqlite_db import SQLiteStudentDB


class SQLiteStudentDBTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.addCleanup(lambda: os.remove(self.temp_db.name) if os.path.exists(self.temp_db.name) else None)
        os.environ["SQLITE_DB_PATH"] = self.temp_db.name
        self.db = SQLiteStudentDB()

    def test_add_and_fetch_student(self):
        student = self.db.add(Student(id=None, name="Ada", age=21, email="ada@example.com", course="CS"))

        self.assertIsNotNone(student.id)
        fetched = self.db.get_by_id(student.id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Ada")
        self.assertEqual(fetched.email, "ada@example.com")


if __name__ == "__main__":
    unittest.main()
