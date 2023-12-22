from unittest import TestCase, main

from alexlib.time import datetime, timedelta


class TestNewDatetimeMethods(TestCase):
    def setUp(self) -> None:
        self.dt = datetime.rand()
        self.now = datetime.now()
        self.thisyear = self.now.year
        self.xmas = datetime(self.thisyear, 12, 25)
        self.oneday = timedelta(days=1)
        self.td = timedelta.rand()

    def test_isholiday(self):
        self.assertIsInstance(self.dt.isholiday, bool)
        self.assertTrue(self.xmas.isholiday)
        notxmas = self.xmas + self.oneday
        self.assertFalse(notxmas.isholiday)

    def test_isweekday(self):
        for _ in range(10):
            self.assertIsInstance(self.dt.isweekday, bool)
            self.assertIsNot(self.dt.isweekday, self.dt.isweekend)

    def test_isbusinessday(self):
        self.assertIsInstance(self.dt.get_last_busday(), datetime)
        for _ in range(10):
            self.assertIsInstance(self.dt.isbusinessday, bool)
            self.assertIsNot(self.dt.isbusinessday, self.dt.isholiday)
            self.assertIsNot(self.dt.isbusinessday, self.dt.isweekend)

    def test_tomorrow(self):
        self.assertIsInstance(self.dt.tomorrow, datetime)
        self.assertEqual(self.dt.tomorrow, self.dt + self.oneday)

    def test_yesterday(self):
        self.assertIsInstance(self.dt.yesterday, datetime)
        self.assertEqual(self.dt.yesterday, self.dt - self.oneday)

    def tearDown(self) -> None:
        return super().tearDown()


if __name__ == "__main__":
    main()
