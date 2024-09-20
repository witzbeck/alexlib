"""Tests for the clipboard funcs in the core module."""

from pathlib import Path
from subprocess import Popen

from pytest import mark, raises, skip

from alexlib.core import (
    copy_file_to_clipboard,
    to_clipboard,
    islinux,
    iswindows,
    ismacos,
    get_clipboard_cmd
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
    if not islinux():
        assert  copy_file_to_clipboard(copy_path)
    else:
        try:
            assert  copy_file_to_clipboard(copy_path)
        except OSError:
            skip("pbcopy/pbpaste not available on this system")

def test_to_clipboard_success(copy_text):
    if not islinux():
        assert to_clipboard(copy_text) == Popen(["pbpaste"], stdout=-1).communicate()[0].decode()
    else:
        try:
            assert to_clipboard(copy_text) == Popen(["pbpaste"], stdout=-1).communicate()[0].decode()
        except OSError:
            skip("pbcopy/pbpaste not available on this system")


def test_copy_path_not_a_file():
    try:
        with raises(FileNotFoundError):
            copy_file_to_clipboard(Path("/fake/path"))
    except OSError:
        skip("pbcopy/pbpaste not available on this system")
