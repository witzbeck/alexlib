from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, main
from json import loads as json_loads

from alexlib.core import dump_envs, is_dotenv, is_json


class TestCoreDumpEnvs(TestCase):
    def setUp(self) -> None:
        """Setup for tests."""
        self.test_dir = Path(mkdtemp())

    def tearDown(self) -> None:
        """Cleanup after tests."""
        rmtree(self.test_dir)

    def test_is_json(self):
        self.assertTrue(is_json("test.json"))
        self.assertFalse(is_json("test.txt"))
        self.assertFalse(is_json("test"))
        self.assertTrue(is_json("settings.json"))
        self.assertTrue(is_json("config.json"))
        self.assertTrue(is_json("package.json"))
        self.assertTrue(is_json(Path("test.json")))
        self.assertFalse(is_json(Path("test.txt")))
        self.assertFalse(is_json(Path("test")))
        self.assertTrue(is_json(Path("settings.json")))
        self.assertTrue(is_json(Path("config.json")))
        self.assertTrue(is_json(Path("package.json")))

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

    def test_is_dotenv_true(self):
        # Test to check .env detection
        test_path = Path(self.test_dir) / ".env"
        test_path.touch()
        self.assertTrue(is_dotenv(test_path))

    def test_is_dotenv_false(self):
        # Test to check non-.env files
        test_path = Path(self.test_dir) / "file.txt"
        test_path.touch()
        self.assertFalse(is_dotenv(test_path))

    def test_is_json_true(self):
        # Test to check JSON file detection
        test_path = Path(self.test_dir) / "file.json"
        test_path.touch()
        self.assertTrue(is_json(test_path))

    def test_is_json_false(self):
        # Test to check non-JSON files
        test_path = Path(self.test_dir) / "file.txt"
        test_path.touch()
        self.assertFalse(is_json(test_path))

    def test_dump_dotenv(self):
        # Test dumping to dotenv format
        test_path = Path(self.test_dir) / "output.env"
        pairs = {"KEY": "VALUE"}
        dump_envs(test_path, pairs)
        self.assertTrue(test_path.exists())
        self.assertEqual(test_path.read_text(), "KEY=VALUE")

    def test_dump_envs_json(self):
        # Test dumping to JSON format
        test_path = Path(self.test_dir) / "output.json"
        pairs = {"KEY": "VALUE"}
        dump_envs(test_path, pairs)
        self.assertTrue(test_path.exists())
        data = json_loads(test_path.read_text())
        self.assertDictEqual(data, pairs)

    def test_dump_envs_dotenv(self):
        # Test dump_envs function with dotenv file
        test_path = Path(self.test_dir) / ".env"
        pairs = {"KEY": "VALUE"}
        dump_envs(test_path, pairs, force=True)
        self.assertTrue(test_path.exists())

    def test_dump_envs_json_force(self):
        # Test force overwrite with JSON file
        test_path = Path(self.test_dir) / "output.json"
        test_path.touch()  # Create the file first to trigger force condition
        pairs = {"KEY": "NEW_VALUE"}
        dump_envs(test_path, pairs, force=True)
        self.assertTrue(test_path.exists())
        data = json_loads(test_path.read_text())
        self.assertDictEqual(data, pairs)

    def test_dump_envs_unsupported_type(self):
        # Test error handling for unsupported file types
        test_path = Path(self.test_dir) / "output.unsupported"
        pairs = {"KEY": "VALUE"}
        with self.assertRaises(ValueError):
            dump_envs(test_path, pairs)


if __name__ == "__main__":
    main()
