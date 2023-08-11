from random import randint, choice
from unittest import TestCase, main

from ..alexlib.mystdlib import datetime as dt, td
from ..alexlib.mystdlib import mk_date, mk_delta


class TestMyStdLib(TestCase):
    @property
    def epoch(self):
        return dt(2, 1, 1, 0, 0, 0, 0)

    @property
    def rdate(self):
        return mk_date()

    @property
    def rdelta(self):
        return mk_delta()

    def setUp(self) -> None:
        return super().setUp()

    @property
    def now(self):
        return dt.now()

    def test_round_dt(self):
        now = dt.now()
        delta = td(hours=36)
        self.assertEqual(round(now, delta), dt(2020, 1, 2, 12, 0))

    def tearDown(self) -> None:
        return super().tearDown()

if __name__ == "__main__":
    for i in range(5):
        print(mk_date())
        print(mk_delta())
    # main()