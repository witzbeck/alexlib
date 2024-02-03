"""Test the round_datetime function."""
from datetime import datetime, timedelta
from unittest import main
from unittest import TestCase

from alexlib.constants import EPOCH
from alexlib.times import ONEDAY, CustomDatetime
from alexlib.times import CustomTimedelta
from alexlib.times import get_rand_datetime
from alexlib.times import get_rand_timedelta


class TestRoundDatetime(TestCase):
    """Test the round_datetime function."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.dt = get_rand_datetime()
        self.td = get_rand_timedelta()
        self.cdt = CustomDatetime(self.dt)
        self.ctd = CustomTimedelta(self.td)

    def test_epoch_is_datetime(self) -> None:
        """Test that epoch is a datetime object."""
        self.assertIsInstance(EPOCH, datetime)

    def test_makes_rand_datetime(self) -> None:
        """Test that get_rand_datetime makes a CustomDatetime object."""
        self.assertIsInstance(self.dt, datetime)
        self.assertIsInstance(self.dt, datetime)

    def test_makes_rand_timedelta(self) -> None:
        """Test that get_rand_timedelta makes a CustomTimedelta object."""
        self.assertIsInstance(self.td, timedelta)
        self.assertIsInstance(self.td, timedelta)

    def test_rounds_datetime(self) -> None:
        """Test that round_datetime rounds a datetime object."""
        self.assertIsInstance(round(self.cdt, ONEDAY), datetime)

    def test_can_get_custom_datetime(self) -> None:
        """Test that CustomDatetime can be created from a datetime object."""
        self.assertIsInstance(self.cdt, CustomDatetime)

    def test_can_get_custom_timedelta(self) -> None:
        """Test that CustomTimedelta can be created from a timedelta object."""
        self.assertIsInstance(self.ctd, CustomTimedelta)


if __name__ == "__main__":
    main()
