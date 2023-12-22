from datetime import datetime as std_datetime
from unittest import TestCase, main

from alexlib.constants import epoch
from alexlib.time import datetime, timedelta


class TestRoundDatetime(TestCase):
    def setUp(self) -> None:
        self.dt = datetime.rand()
        self.td = timedelta.rand()

    def test_round_dt(self):
        now = datetime.now()
        delta = timedelta(hours=36)
        print(delta)
        rounded = round(now, delta)
        self.assertIsInstance(rounded, datetime)
        print(rounded)
        self.assertIn(rounded.strftime("%H"), ["00", "12"])

    def test_epoch_is_datetime(self) -> None:
        self.assertIsInstance(epoch, std_datetime)

    def test_makes_rand_datetime(self) -> None:
        self.assertIsInstance(self.dt, datetime)

    def test_makes_rand_timedelta(self) -> None:
        self.assertIsInstance(self.td, timedelta)

    def tearDown(self) -> None:
        return super().tearDown()


if __name__ == "__main__":
    main()
