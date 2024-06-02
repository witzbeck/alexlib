from pathlib import Path
from unittest import TestCase, main

from alexlib.core import is_dotenv, is_json


class TestCoreDumpEnvs(TestCase):
    def test_is_json(self):
        self.assertTrue(is_json("test.json"))
        self.assertFalse(is_json("test.txt"))
        self.assertFalse(is_json("test"))
        self.assertTrue(is_json("settings.json"))
        self.assertTrue(is_json("config.json"))
        self.assertTrue(is_json("package.json"))

    def test_is_dotenv(self) -> None:
        self.assertTrue(is_dotenv(".env"))
        self.assertTrue(is_dotenv(".env.example"))
        self.assertTrue(is_dotenv(".env.local"))
        self.assertTrue(is_dotenv(".env.test"))
        self.assertFalse(is_dotenv("env.development"))
        self.assertFalse(is_dotenv("settings.json"))
        self.assertFalse(is_dotenv("config.json"))
        self.assertFalse(is_dotenv("package.json"))
        self.assertFalse(is_dotenv("test.json"))
        self.assertFalse(is_dotenv("test.txt"))
        self.assertTrue(is_dotenv(Path(".env")))
        self.assertTrue(is_dotenv(Path(".env.example")))
        self.assertTrue(is_dotenv(Path(".env.local")))
        self.assertTrue(is_dotenv(Path(".env.test")))
        self.assertFalse(is_dotenv(Path("env.development")))
        self.assertFalse(is_dotenv(Path("settings.json")))
        self.assertFalse(is_dotenv(Path("config.json")))
        self.assertFalse(is_dotenv(Path("package.json")))
        self.assertFalse(is_dotenv(Path("test.json")))
        self.assertFalse(is_dotenv(Path("test.txt")))


if __name__ == "__main__":
    main()
