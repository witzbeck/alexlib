"""Tests for the clipboard funcs in the core module."""

from pathlib import Path
from subprocess import Popen

from pytest import mark, raises

from alexlib.core import (
    copy_file_to_clipboard,
    to_clipboard,
)


@mark.parametrize(
    "value",
    (1, 0.0, None, False),
)
def test_to_clipboard_typeerror(value):
    with raises(TypeError):
        to_clipboard(value)


def test_copy_non_existing_file():
    with raises(FileNotFoundError):
        copy_file_to_clipboard(Path("/fake/path"))


def test_copy_existing_file(copy_path, copy_text):
    copy_file_to_clipboard(copy_path)
    assert copy_text == Popen(["pbpaste"], stdout=-1).communicate()[0].decode()


def test_to_clipboard_success(copy_text):
    assert (
        to_clipboard(copy_text)
        == Popen(["pbpaste"], stdout=-1).communicate()[0].decode()
    )


def test_copy_path_not_a_file():
    with raises(FileNotFoundError):
        copy_file_to_clipboard(Path("/fake/path"))
