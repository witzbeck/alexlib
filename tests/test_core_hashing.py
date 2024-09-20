""""""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryFile
from unittest import TestCase, main

from alexlib.files.objects import Directory
from alexlib.files.utils import sha256sum


class TestSha256(TestCase):
    """Test the `sha256` function."""

    def setUp(self) -> None:
        self.here = Directory.from_path(Path(__file__).parent)
        self.real_file = self.here.randchildfile

    def test_with_string(self) -> None:
        """Test with a string."""
        result = sha256("test".encode()).hexdigest()
        self.assertEqual(
            result, "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        )

    def test_with_file(self) -> None:
        """Test with a file."""
        with TemporaryFile() as f:
            f.write(b"test")
            f.seek(0)
            result = sha256(f.read()).hexdigest()
            self.assertEqual(
                result,
                "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            )

    def test_gets_real_file_shasum(self) -> None:
        self.assertIsInstance(sha256sum(self.real_file.path), str)


if __name__ == "__main__":
    main()
