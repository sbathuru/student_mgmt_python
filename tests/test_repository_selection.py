import os
import unittest
from unittest.mock import patch

from src.app import create_repository
from src.sqlite_db import SQLiteStudentDB


class RepositorySelectionTests(unittest.TestCase):
    def test_uses_sqlite_by_default_when_oracle_is_not_configured(self):
        with patch.dict(os.environ, {}, clear=False):
            repo = create_repository()
            self.assertIsInstance(repo, SQLiteStudentDB)


if __name__ == "__main__":
    unittest.main()
