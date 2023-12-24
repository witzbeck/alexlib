from os import name
from random import choice
from string import ascii_lowercase
from unittest import TestCase, main

from alexlib.auth import Auth


class TestAuth(TestCase):
    def _rand_database(self) -> str:
        return choice(self.databases)

    def _rand_locale(self) -> str:
        return choice(self.locales)

    def _rand_env(self) -> str:
        return choice(self.envs)

    def setUp(self):
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
        auth = Auth(self.concat_name)
        self.assertIsInstance(auth, Auth)

    def test_list_getauth(self):
        auth = Auth(*self.list_name)
        self.assertIsInstance(auth, Auth)


if name == "__main__":
    main()
