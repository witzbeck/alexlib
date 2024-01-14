"""Test the new datetime methods."""
from datetime import datetime
from datetime import timedelta
from unittest import main
from unittest import TestCase

from alexlib.time import CustomDatetime
from alexlib.time import get_rand_datetime
from alexlib.time import get_rand_timedelta


class TestNewDatetimeMethods(TestCase):
    """Test the new datetime methods."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.dt = get_rand_datetime()
        self.now = datetime.now()
        self.thisyear = self.now.year
        self.xmas = CustomDatetime(self.thisyear, 12, 25)
        self.oneday = timedelta(days=1)
        self.td = get_rand_timedelta()

    def test_isholiday(self) -> None:
        """Test isholiday method."""
        self.assertIsInstance(self.dt.isholiday, bool)
        self.assertTrue(self.xmas.isholiday)
        notxmas = self.xmas + self.oneday
        self.assertFalse(notxmas.isholiday)

    def test_isweekday(self) -> None:
        """Test isweekday method."""
        for _ in range(10):
            self.assertIsInstance(self.dt.isweekday, bool)
            self.assertIsNot(self.dt.isweekday, self.dt.isweekend)

    def test_isbusinessday(self) -> None:
        """Test isbusinessday method."""
        self.assertIsInstance(self.dt.get_last_busday(), datetime)
        for _ in range(10):
            self.assertIsInstance(self.dt.isbusinessday, bool)
            self.assertIsNot(self.dt.isbusinessday, self.dt.isholiday)
            self.assertIsNot(self.dt.isbusinessday, self.dt.isweekend)

    def test_tomorrow(self) -> None:
        """Test tomorrow method."""
        self.assertIsInstance(self.dt.tomorrow, datetime)
        self.assertEqual(self.dt.tomorrow, self.dt + self.oneday)

    def test_yesterday(self) -> None:
        """Test yesterday method."""
        self.assertIsInstance(self.dt.yesterday, datetime)
        self.assertEqual(self.dt.yesterday, self.dt - self.oneday)


if __name__ == "__main__":
    main()
