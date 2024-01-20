"""Test the round_datetime function."""
from datetime import datetime
from unittest import main
from unittest import TestCase

from alexlib.constants import EPOCH
from alexlib.time import CustomDatetime
from alexlib.time import CustomTimedelta
from alexlib.time import get_rand_datetime
from alexlib.time import get_rand_timedelta


class TestRoundDatetime(TestCase):
    """Test the round_datetime function."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.dt = get_rand_datetime()
        self.td = get_rand_timedelta()

    def test_epoch_is_datetime(self) -> None:
        """Test that epoch is a datetime object."""
        self.assertIsInstance(EPOCH, datetime)

    def test_makes_rand_datetime(self) -> None:
        """Test that get_rand_datetime makes a CustomDatetime object."""
        self.assertIsInstance(self.dt, CustomDatetime)

    def test_makes_rand_timedelta(self) -> None:
        """Test that get_rand_timedelta makes a CustomTimedelta object."""
        self.assertIsInstance(self.td, CustomTimedelta)


if __name__ == "__main__":
    main()
