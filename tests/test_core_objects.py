""""""

from pathlib import Path
from random import choice
from tempfile import TemporaryFile
from unittest import TestCase, main
from unittest.mock import mock_open, patch
from hashlib import sha256
from socket import socket, AF_INET, SOCK_STREAM

from alexlib.core import (
    copy_file_to_clipboard,
    get_attrs,
    get_objects_by_attr,
    invert_dict,
    mk_dictvals_distinct,
    show_dict,
    show_environ,
    to_clipboard,
)


class TestClass:
    """Test class for `get_attrs` function."""

    def __init__(
        self,
        public_attr: str = "public",
        hidden_attr: str = "hidden",
        dunder_attr: str = "dunder",
    ) -> None:
        self.public_attr = public_attr
        self._hidden_attr = hidden_attr
        self.__dunder_attr__ = dunder_attr

    def public_method(self):
        return self.public_attr

    def _hidden_method(self):
        return self._hidden_attr

    def __dunder_method__(self):
        return self.__dunder_attr__


class TestGetAttrs(TestCase):
    """Test the `get_attrs` function."""

    def setUp(self):
        self.test_obj = TestClass()

    def test_get_all_attrs(self):
        d = get_attrs(
            self.test_obj,
            include_hidden=True,
            include_dunder=True,
            include_methods=True,
        )
        self.assertIn("public_attr", d.keys())
        self.assertIn("_hidden_attr", d.keys())
        self.assertIn("__dunder_attr__", d.keys())
        self.assertIn("public_method", d.keys())
        self.assertIn("_hidden_method", d.keys())
        self.assertIn("__dunder_method__", d.keys())

    def test_get_public_attrs(self):
        self.assertDictEqual(
            get_attrs(self.test_obj),
            {
                "public_attr": "public",
            },
        )

    def test_get_public_methods(self):
        d = get_attrs(self.test_obj, include_methods=True)
        self.assertIn("public_method", d)
        self.assertNotIn("_hidden_method", d)

    def test_get_hidden_attrs(self):
        self.assertDictEqual(
            get_attrs(self.test_obj, include_hidden=True),
            {
                "public_attr": "public",
                "_hidden_attr": "hidden",
            },
        )

    def test_get_hidden_methods(self):
        d = get_attrs(self.test_obj, include_methods=True, include_hidden=True)
        self.assertIn("_hidden_method", d)
        self.assertIn("public_method", d)
        self.assertNotIn("__dunder_method__", d)

    def test_get_dunder_attrs(self):
        d = get_attrs(self.test_obj, include_dunder=True)
        self.assertIn("__dunder_attr__", d)
        self.assertIn("public_attr", d)

    def test_get_dunder_methods(self):
        d = get_attrs(self.test_obj, include_methods=True, include_dunder=True)
        self.assertIn("__dunder_method__", d)
        self.assertIn("public_method", d)


class TestShowDict(TestCase):
    @patch("builtins.print")
    def test_show_dict_with_dict(self, mock_print):
        show_dict({"a": 1, "b": 2})
        mock_print.assert_called()

    @patch("builtins.print")
    def test_show_dict_with_list_of_dicts(self, mock_print):
        show_dict([{"a": 1}, {"b": 2}])
        self.assertEqual(mock_print.call_count, 4)

    @patch("builtins.print")
    def test_show_dict_with_show_environ(self, mock_print):
        show_environ()
        mock_print.assert_called()


class TestToClipboard(TestCase):
    @patch("subprocess.Popen")
    def test_to_clipboard_success(self, mock_popen):
        mock_process = mock_popen.return_value
        mock_process.wait.return_value = 0
        result = to_clipboard("Test string")
        self.assertTrue(result)

    @patch("subprocess.Popen")
    def test_to_clipboard_failure(self, mock_popen):
        mock_process = mock_popen.return_value
        mock_process.wait.return_value = 1
        self.assertTrue(to_clipboard("Test string"))


class TestCopyFileToClipboard(TestCase):
    """Test the `copy_file_to_clipboard` function."""

    @patch("alexlib.core.to_clipboard", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_copy_existing_file(self, mock_file, mock_to_clipboard):
        """Test with existing file."""
        parent = Path(__file__).parent
        randfile = choice([x for x in parent.iterdir() if x.is_file()])
        result = copy_file_to_clipboard(randfile)
        self.assertTrue(result)

    @patch("alexlib.core.to_clipboard", return_value=False)
    def test_copy_non_existing_file(self, mock_to_clipboard) -> None:
        """Test with non-existing file."""
        with self.assertRaises(FileNotFoundError):
            copy_file_to_clipboard(Path("/non/existing/path"))


class TestGetObjectsByAttr(TestCase):
    """Test the `get_objects_by_attr` function."""

    def test_with_specific_attribute(self) -> None:
        """Test with specific attribute."""

        class TestObj:
            def __init__(self, name):
                self.name = name

        objects = [TestObj("test1"), TestObj("test2")]
        result = get_objects_by_attr(objects, "name", "test1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "test1")

    def test_with_non_existing_attribute(self):
        objects = [{"name": "test1"}, {"name": "test2"}]
        with self.assertRaises(AttributeError):
            get_objects_by_attr(objects, "non_exist", "value")


class TestMkDictvalsDistinct(TestCase):
    """Test the `mk_dictvals_distinct` function."""

    def test_with_list_values_including_duplicates(self) -> None:
        """Test with list values including duplicates."""
        test_dict = {"a": [1, 2, 2, 3], "b": ["x", "y", "y"]}
        expected = {"a": [1, 2, 3], "b": ["x", "y"]}
        result = mk_dictvals_distinct(test_dict)
        self.assertIn("a", result)
        self.assertIn("b", result)
        result["a"].sort()
        result["b"].sort()
        self.assertListEqual(result["a"], expected["a"])
        self.assertListEqual(result["b"], expected["b"])


class TestInvertDict(TestCase):
    """Test the `invert_dict` function."""

    def test_with_dict(self) -> None:
        """Test with a dictionary."""
        test_dict = {"a": 1, "b": 2}
        expected = {1: "a", 2: "b"}
        result = invert_dict(test_dict)
        self.assertEqual(result, expected)

    def test_with_list_of_tuples(self) -> None:
        """Test with a list of tuples."""
        test_list = [("a", 1), ("b", 2)]
        expected = {1: "a", 2: "b"}
        result = invert_dict(dict(test_list))
        self.assertEqual(result, expected)


class TestSha256(TestCase):
    """Test the `sha256` function."""

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


class TestSocket(TestCase):
    """Test the `socket` function."""

    def test_socket(self) -> None:
        """Test with a socket."""
        with socket(AF_INET, SOCK_STREAM) as s:
            self.assertIsInstance(s, socket)

    def test_socket_with_invalid_family(self) -> None:
        """Test with an invalid family."""
        with self.assertRaises(OSError):
            socket(999, SOCK_STREAM)


if __name__ == "__main__":
    main()
