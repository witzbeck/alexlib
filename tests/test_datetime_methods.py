"""Test the new datetime methods."""
from datetime import datetime
from datetime import timedelta
from unittest import main
from unittest import TestCase

from alexlib.times import CustomDatetime, CustomTimedelta
from alexlib.times import get_rand_datetime
from alexlib.times import get_rand_timedelta


class TestNewDatetimeMethods(TestCase):
    """Test the new datetime methods."""

    @property
    def rand_datetime(self) -> CustomDatetime:
        """Return random datetime."""
        return CustomDatetime.rand()

    def setUp(self) -> None:
        """Set up the test case."""
        self.now = datetime.now()
        self.thisyear = self.now.year
        self.xmas = CustomDatetime(self.thisyear, 12, 25)
        self.oneday = timedelta(days=1)
        self.td = CustomTimedelta.rand()

    def test_isholiday(self) -> None:
        """Test isholiday method."""
        self.assertIsInstance(self.rand_datetime.isholiday, bool)
        self.assertTrue(self.xmas.isholiday)
        notxmas = self.xmas + self.oneday
        self.assertFalse(notxmas.isholiday)

    def test_isweekday(self) -> None:
        """Test isweekday method."""
        for _ in range(10):
            dt = self.rand_datetime
            self.assertIsInstance(dt.isweekday, bool)
            self.assertIsNot(dt.isweekday, dt.isweekend)

    def test_isbusinessday(self) -> None:
        """Test isbusinessday method."""
        for _ in range(10):
            dt = self.rand_datetime
            last_busday = dt.get_last_busday()
            self.assertIsInstance(last_busday, datetime)
            self.assertIsInstance(self.rand_datetime.isbusinessday, bool)
            if dt.isbusinessday:
                self.assertFalse(dt.isholiday or dt.isweekend)
            else:
                self.assertTrue(dt.isholiday or dt.isweekend)

    def test_tomorrow(self) -> None:
        """Test tomorrow method."""
        dt = self.rand_datetime
        self.assertIsInstance(dt.tomorrow, datetime)
        self.assertEqual(dt.tomorrow, dt + self.oneday)

    def test_yesterday(self) -> None:
        """Test yesterday method."""
        dt = self.rand_datetime
        self.assertIsInstance(dt.yesterday, datetime)
        self.assertEqual(dt.yesterday, dt - self.oneday)

    def test_get_last_busday(self) -> None:
        """Test get_last_busday method."""
        dt = self.rand_datetime
        last_busday = dt.get_last_busday()
        self.assertIsInstance(last_busday, CustomDatetime)
        if dt.yesterday.isbusinessday:
            self.assertEqual(last_busday, dt.yesterday)
        else:
            self.assertLess(last_busday, dt)

    def test_get_rand_datetime(self) -> None:
        """Test get_rand_datetime function."""
        self.assertIsInstance(get_rand_datetime(), datetime)

    def test_get_rand_timedelta(self) -> None:
        """Test get_rand_timedelta function."""
        self.assertIsInstance(get_rand_timedelta(), timedelta)


if __name__ == "__main__":
    main()
