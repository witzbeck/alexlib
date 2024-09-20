"""Test core functions."""

from json import JSONDecodeError
from pathlib import Path
from tomllib import TOMLDecodeError
from unittest import TestCase
from unittest.mock import mock_open, patch

from alexlib.files.utils import (
    read_json,
    read_toml,
)


class TestReadFiles(TestCase):
    def test_read_toml_invalid(self):
        """
        Test with invalid TOML content
        """
        with patch("pathlib.Path.open", mock_open(read_data='key = "value')):
            mock_path_instance = Path("/fake/path/to/file")
            with self.assertRaises(TOMLDecodeError):
                read_toml(mock_path_instance, mustexist=False)

    def test_read_toml_valid(self):
        """
        Test with valid content for TOML files.
        """
        with patch("pathlib.Path.open", mock_open(read_data='key = "value"')):
            mock_path_instance = Path("/fake/path/to/file")
            self.assertEqual(
                read_toml(mock_path_instance, mustexist=False),
                {"key": "value"},
                "Failed to read valid TOML.",
            )

    def test_read_json_invalid(self):
        """
        Test with invalid content for JSON files.
        This method uses subTests to iterate over different file types and content scenarios.
        """
        with patch("pathlib.Path.open", mock_open(read_data='{"key": "value"')):
            mock_path_instance = Path("/fake/path/to/file")
            with self.assertRaises(JSONDecodeError):
                read_json(mock_path_instance, mustexist=False)

    def test_read_json_valid(self) -> None:
        """
        Test with valid  content for JSON files.
        """
        with patch("pathlib.Path.open", mock_open(read_data='{"key": "value"}')):
            mock_path_instance = Path("/fake/path/to/file")
            self.assertEqual(
                read_json(mock_path_instance, mustexist=False),
                {"key": "value"},
                "Failed to read valid JSON.",
            )
