from json import JSONDecodeError
from datetime import timezone
from pathlib import Path
from unittest import TestCase, main
from alexlib.core import (
    get_local_tz,
    isnone,
    istrue,
    isdunder,
    ishidden,
    aslist,
    chktext,
    chktype,
    envcast,
    chkenv,
    concat_lists,
    read_json,
)
from unittest.mock import patch


class TestAlexLibCore(TestCase):
    """Test cases for alexlib.core utility functions."""

    def test_get_local_tz(self):
        """Ensure it returns the correct local timezone."""
        self.assertIsInstance(
            get_local_tz(), timezone, "The returned value is not a timezone instance."
        )

    def test_isnone(self):
        """Test with None, empty string, and the string 'none' in various cases. Test with non-None values."""
        self.assertTrue(isnone(None), "Failed to recognize None as none.")
        self.assertTrue(isnone(""), "Failed to recognize empty string as none.")
        self.assertTrue(isnone("none"), "Failed to recognize 'none' as none.")
        self.assertTrue(
            isnone(" None "), "Failed to recognize ' None ' (with spaces) as none."
        )
        self.assertFalse(
            isnone("text"), "Incorrectly identified non-empty string as none."
        )
        self.assertFalse(isnone(1), "Incorrectly identified number as none.")
        self.assertFalse(isnone(True), "Incorrectly identified boolean as none.")

    def test_istrue_true_values(self):
        """Test with values that should return True, including edge cases."""
        true_values = [True, 1, "true", "t", "1"]
        for value in true_values:
            self.assertTrue(istrue(value), f"Failed to recognize {value} as True.")

    def test_istrue_false_values(self):
        """Test with values that should return False, including edge cases."""
        false_values = [False, 0, "false", "f", "0", "", "text", [], {}]
        for value in false_values:
            self.assertFalse(istrue(value), f"Failed to recognize {value} as False.")

    def test_isdunder(self):
        """Test with strings that are and are not dunder variables."""
        self.assertTrue(
            isdunder("__init__"), "Failed to recognize '__init__' as dunder."
        )
        self.assertFalse(
            isdunder("_hidden"), "Incorrectly identified '_hidden' as dunder."
        )
        self.assertFalse(isdunder("text"), "Incorrectly identified 'text' as dunder.")

    def test_ishidden(self):
        """Test with strings that start with an underscore but are not dunder, and with non-hidden strings."""
        self.assertTrue(ishidden("_hidden"), "Failed to recognize '_hidden' as hidden.")
        self.assertFalse(
            ishidden("__dunder__"), "Incorrectly identified '__dunder__' as hidden."
        )
        self.assertFalse(ishidden("text"), "Incorrectly identified 'text' as hidden.")

    # Skipping asdict test implementation for brevity.

    def test_aslist(self):
        """Test with strings that can be converted to lists, including edge cases."""
        self.assertEqual(
            aslist("1,2,3"), ["1", "2", "3"], "Failed to split string into list."
        )
        self.assertEqual(
            aslist("[1,2,3]"), [1, 2, 3], "Failed to interpret JSON list format."
        )
        self.assertEqual(aslist(""), [], "Failed to handle empty string correctly.")
        self.assertEqual(
            aslist("text"),
            ["text"],
            "Failed to handle single element string correctly.",
        )


class TestAlexLibCoreExtended(TestCase):
    """Extended test cases for the alexlib.core utility functions."""

    def test_chktext(self):
        """Test with texts that meet and do not meet the prefix, value, and suffix conditions."""
        self.assertTrue(
            chktext("hello world", prefix="hello"),
            "Failed to recognize correct prefix.",
        )
        self.assertTrue(
            chktext("hello world", value="world"), "Failed to recognize correct value."
        )
        self.assertTrue(
            chktext("hello world", suffix="world"),
            "Failed to recognize correct suffix.",
        )
        self.assertFalse(
            chktext("hello world", prefix="world"),
            "Incorrectly identified incorrect prefix.",
        )
        self.assertFalse(
            chktext("hello world", suffix="hello"),
            "Incorrectly identified incorrect suffix.",
        )

    def test_chktype(self):
        """Test with objects of correct and incorrect types. Also, test path existence if the object is a Path."""
        self.assertEqual(
            chktype("text", str), "text", "Failed to recognize correct type."
        )
        with self.assertRaises(TypeError):
            chktype(123, str)
        temp_file = Path("temp_file_for_testing.txt")
        temp_file.touch()  # Create the file for testing
        try:
            self.assertEqual(
                chktype(temp_file, Path, mustexist=True),
                temp_file,
                "Failed to recognize path existence.",
            )
        finally:
            temp_file.unlink()  # Clean up by removing the file

    def test_envcast(self):
        """Test with environment variables of various types."""
        with patch.dict(
            "os.environ",
            {"TEST_STRING": "example", "TEST_LIST": "1,2,3", "TEST_BOOL": "true"},
        ):
            self.assertEqual(
                envcast("example", str), "example", "Failed to cast string."
            )
            self.assertEqual(
                envcast("1,2,3", list), ["1", "2", "3"], "Failed to cast list."
            )
            self.assertTrue(envcast("true", bool), "Failed to cast bool.")

    def test_chkenv(self):
        """Test with existing and nonexisting environment variables."""
        with patch.dict("os.environ", {"EXISTING_VAR": "yes"}):
            self.assertEqual(
                chkenv("EXISTING_VAR"),
                "yes",
                "Failed to fetch existing environment variable.",
            )
            with self.assertRaises(ValueError):
                chkenv("NON_EXISTING_VAR", need=True)

    def test_concat_lists(self):
        """Test with various lists of lists."""
        self.assertEqual(
            concat_lists([[1, 2], [3, 4]]),
            [1, 2, 3, 4],
            "Failed to correctly concatenate lists.",
        )


class TestReadJson(TestCase):
    def test_read_json(self):
        """Test with valid and invalid JSON files."""
        valid_json_content = '{"key": "value"}'
        invalid_json_content = '{"key": "value"'

        # Create a mock Path object for valid JSON content
        with patch("pathlib.Path") as MockPath:
            mock_path_instance = MockPath.return_value
            mock_path_instance.read_text.return_value = valid_json_content
            self.assertEqual(
                read_json(mock_path_instance),
                {"key": "value"},
                "Failed to read valid JSON.",
            )

        # Create a mock Path object for invalid JSON content
        with patch("pathlib.Path") as MockPath:
            mock_path_instance = MockPath.return_value
            mock_path_instance.read_text.return_value = invalid_json_content
            with self.assertRaises(JSONDecodeError):
                read_json(mock_path_instance)

    # Further tests for show_dict, to_clipboard, copy_file_to_clipboard, etc., would similarly mock or simulate the necessary conditions for each function's execution and assert the expected outcomes or behaviors.

    # Note: Some functions like to_clipboard, copy_file_to_clipboard, and ping might involve system-specific behavior or external dependencies, which could require more complex mocking or conditional testing strategies to adequately simulate their operational context.


# This marks the end of the extended test case implementations.

if __name__ == "__main__":
    main()
