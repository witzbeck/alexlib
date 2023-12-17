from os import name
from random import choice
from string import ascii_lowercase
from alexlib.auth import getauth
from alexlib.config import Settings

from unittest import TestCase, main

vowels = "aeiou"


class TestAuth(TestCase):
    def _rand_database(self) -> str:
        return choice(self.databases)

    def _rand_locale(self) -> str:
        return choice(self.locales)

    def _rand_env(self) -> str:
        return choice(self.envs)

    def setUp(self):
        self.settings = Settings()
        self.databases = ["learning", "headlines", "finance"]
        self.locales = ["local", "remote"]
        self.ndevs = 4
        self.devs = [
            f"dev{x}" if self.ndevs > 1 else "dev"
            for x in ascii_lowercase[-self.ndevs:]
        ]
        self.envs = self.devs + ["test", "prod"]
        self.list_name = [
            self._rand_locale(),
            self._rand_env(),
            self._rand_database(),
        ]
        self.concat_name = ".".join([
            self._rand_locale(),
            self._rand_env(),
            self._rand_database(),
        ])

    def test_concat_getauth(self):
        return getauth(self.concat_name)

    def test_list_getauth(self):
        return getauth(*self.list_name)

    def tearDown(self):
        pass


if name == "__main__":
    main()
