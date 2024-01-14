from os import getenv
from unittest import TestCase, main

from alexlib.config import Settings


class TestConfigFile(TestCase):
    def setUp(self):
        self.settings = Settings()
        self.rand_key = self.settings.rand_key
        self.rand_val = getenv(self.rand_key)

    def test_settings_init(self):
        self.assertEqual(self.settings.name, "settings.json")
        self.assertIsInstance(self.settings, Settings)

    def test_envdict_init(self):
        self.assertTrue(issubclass(self.settings.envdict.__class__, dict))
        self.assertGreater(len(self.settings.envdict), 0)

    def test_gets_rand_env(self):
        self.assertEqual(str(self.settings.envdict[self.rand_key]), self.rand_val)


if __name__ == "__main__":
    main()
