"""Test cases for the SystemObject class."""

from pathlib import Path

from pytest import fixture

from alexlib.files.objects import SystemObject


@fixture(scope="class")
def sysobj(file_path: Path):
    return SystemObject.from_path(file_path)


def test_systemobject_instantiation(sysobj: SystemObject):
    """Test instantiation with different names and paths."""
    assert sysobj.name
    assert sysobj.path.exists()


def test_systemobject_properties(sysobj: SystemObject):
    """Test property methods like `isfile`, `isdir`, `haspath`, `user`, etc."""
    assert sysobj.isfile
    assert not sysobj.isdir
    assert sysobj.haspath


def test_systemobject_path_manipulation(sysobj: SystemObject):
    """Test path manipulation methods like `get_path`, `set_path`, `get_name`, `set_name`."""
    # Changing the name
    new_name = "new_file.txt"
    sysobj.set_name(new_name)
    assert sysobj.name == new_name
