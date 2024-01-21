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

    @property
    def rand_datetime(self) -> CustomDatetime:
        """Return random datetime."""
        return get_rand_datetime()

    def setUp(self) -> None:
        """Set up the test case."""
        self.now = datetime.now()
        self.thisyear = self.now.year
        self.xmas = CustomDatetime(self.thisyear, 12, 25)
        self.oneday = timedelta(days=1)
        self.td = get_rand_timedelta()

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
        self.assertIsInstance(self.rand_datetime.get_last_busday(), datetime)
        for _ in range(10):
            dt = self.rand_datetime
            self.assertIsInstance(self.rand_datetime.isbusinessday, bool)
            self.assertIsNot(
                dt.isbusinessday,
                dt.isholiday or dt.isweekend,
                msg=f"{dt} is a holiday or weekend",
            )
            self.assertIsNot(dt.isbusinessday, dt.isweekend)

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


if __name__ == "__main__":
    main()
