"""Tests for the clipboard funcs in the core module."""
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

from alexlib.core import (
    copy_file_to_clipboard,
    chkcmd,
    get_clipboard_cmd,
    to_clipboard,
)


class TestToClipboard(TestCase):
    def setUp(self) -> None:
        try:
            self.cmd = get_clipboard_cmd()
        except OSError:
            self.cmd = None
        self.hascmd = chkcmd(self.cmd[0]) if self.cmd is not None else False

    @patch("subprocess.Popen")
    def test_to_clipboard_success(self, mock_popen):
        if not self.hascmd:
            with self.assertRaises(OSError):
                to_clipboard("Test string")
        else:
            mock_process = mock_popen.return_value
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0

            result = to_clipboard("Test string")
            self.assertEqual(result, "Text copied to clipboard successfully.")

    def test_to_clipboard_typeerror(self):
        with self.assertRaises(TypeError):
            to_clipboard(123)
        with self.assertRaises(TypeError):
            to_clipboard(1.123)
        with self.assertRaises(TypeError):
            to_clipboard(None)
        with self.assertRaises(TypeError):
            to_clipboard(False)


class TestCopyFileToClipboard(TestCase):
    def setUp(self) -> None:
        try:
            self.cmd = get_clipboard_cmd()
        except OSError:
            self.cmd = None
        self.hascmd = chkcmd(self.cmd[0]) if self.cmd is not None else False

    @patch(
        "alexlib.core.to_clipboard",
        return_value="File content from /fake/path.txt copied to clipboard.",
    )
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_file", return_value=True)
    @patch("pathlib.Path.read_text", return_value="File content")
    def test_copy_existing_file(self, *mocks):
        path = Path("/fake/path.txt")
        if not self.hascmd:
            with self.assertRaises(OSError):
                copy_file_to_clipboard(path)
        else:
            result = copy_file_to_clipboard(path)
            self.assertEqual(
                result, "File content from /fake/path.txt copied to clipboard."
            )

    @patch("alexlib.core.to_clipboard")
    def test_copy_non_existing_file(self, mock_to_clipboard):
        path = Path("/non/existing/path")
        if not self.hascmd:
            self.skipTest("Clipboard command not found.")
        else:
            with self.assertRaises(FileExistsError):
                copy_file_to_clipboard(path)

    @patch("alexlib.core.to_clipboard")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.is_file", return_value=True)
    def test_copy_path_not_a_file(self, *mocks):
        path = Path("/not/a/file")
        if not self.hascmd:
            with self.assertRaises(OSError):
                copy_file_to_clipboard(path)
        else:
            with self.assertRaises(FileNotFoundError):
                copy_file_to_clipboard(path)


if __name__ == "__main__":
    main()
