import os
import unittest
from unittest.mock import patch

from src.app import create_repository


class OracleRepositoryConfigurationTests(unittest.TestCase):
    def test_requires_oracle_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                create_repository()


if __name__ == "__main__":
    unittest.main()
