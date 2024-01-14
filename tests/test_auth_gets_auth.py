from unittest import TestCase, main
from random import choice
from functools import partial

from alexlib.auth import Auth
from alexlib.config import Settings
from alexlib.constants import creds

settings = Settings()

databases = settings.envdict["databases"]
systems = settings.envdict["systems"]
envs = settings.envdict["envs"]
locales = settings.envdict["locales"]

rand_system = partial(choice, systems)
rand_env = partial(choice, envs)
rand_db = partial(choice, databases)
rand_locale = partial(choice, locales)


class TestAuth(TestCase):
    def setUp(self):
        self.list_name = [
            rand_locale(),
            rand_env(),
            rand_db(),
        ]
        self.concat_name = ".".join(
            [
                rand_locale(),
                rand_env(),
                rand_db(),
            ]
        )

    def test_concat_getauth(self):
        if (creds / f"{self.concat_name}.store").exists():
            auth = Auth(self.concat_name)
            self.assertIsInstance(auth, Auth)
        else:
            with self.assertRaises(ValueError):
                Auth(self.concat_name)

    def test_list_getauth(self):
        if (creds / f"{self.list_name}.store").exists():
            auth = Auth(self.list_name)
            self.assertIsInstance(auth, Auth)
        else:
            with self.assertRaises(ValueError):
                Auth(self.list_name)


if __name__ == "__main__":
    main()
