from os import getenv
from unittest import TestCase, main

from alexlib.config import DotEnv


class TestConfigFile(TestCase):
    def setUp(self):
        self.dotenv = DotEnv()
        self.rand_key = self.dotenv.rand_key
        self.rand_val = getenv(self.rand_key)

    def test_dotenv_init(self):
        self.assertEqual(self.dotenv.name, ".env")
        self.assertIsInstance(self.dotenv, DotEnv)

    def test_envdict_init(self):
        self.assertTrue(issubclass(self.dotenv.envdict.__class__, dict))
        self.assertGreater(len(self.dotenv.envdict), 0)

    def test_gets_rand_env(self):
        self.assertEqual(self.dotenv.envdict[self.rand_key], self.rand_val)


if __name__ == "__main__":
    main()
