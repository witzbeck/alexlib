"""Test core functions."""
from datetime import timezone
from unittest import main, TestCase

from alexlib.core import (
    concat_lists,
    get_local_tz,
)


class TestCore(TestCase):
    """Test core functions."""

    def test_concat_lists(self):
        """Test with various lists of lists."""
        self.assertEqual(
            concat_lists([[1, 2], [3, 4]]),
            [1, 2, 3, 4],
            "Failed to correctly concatenate lists.",
        )

    def test_get_local_tz(self):
        """Ensure it returns the correct local timezone."""
        self.assertIsInstance(
            get_local_tz(), timezone, "The returned value is not a timezone instance."
        )


if __name__ == "__main__":
    main()
