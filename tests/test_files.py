from datetime import datetime, timedelta
from pathlib import Path
from random import choice

from matplotlib.figure import Figure
from pytest import mark, raises

from alexlib.files import JsonFile, SettingsFile, TomlFile
from alexlib.files.objects import Directory, File, SystemObject
from alexlib.files.utils import eval_parents, figsave, path_search, read_json, read_toml


def test_instantiation(text_file_obj: File):
    """Test instantiation of the File class and its properties."""
    assert isinstance(text_file_obj, File)
    assert text_file_obj.path.exists()
    assert text_file_obj.path.is_file()


def test_is_type_methods(text_file_obj: File):
    """Test the file-specific property methods (isfile, isempty, etc.)."""
    assert text_file_obj.istype("txt")
    assert text_file_obj.size > 0


def test_file_write_lines(text_file_obj: File):
    """Test writing lines to a file."""
    lines_to_write = ["Line 1", "Line 2"]
    text_file_obj.write_lines(lines_to_write)
    assert text_file_obj.lines == lines_to_write


def test_file_append_lines(text_file_obj: File):
    """Test appending lines to a file."""
    lines_to_append = ["Line 3"]
    text_file_obj.append_lines(lines_to_append)
    assert text_file_obj.lines == ["Line 1", "Line 2"] + lines_to_append


def test_file_replace_text(text_file_obj: File):
    """Test replacing text in a file."""
    text_file_obj.replace_text("Line 2", "Line 4")
    assert "Line 4" in text_file_obj.lines


def test_dir_obj_init(dir_obj: Directory):
    """Test initialization of the Directory class."""
    assert isinstance(dir_obj, Directory)
    assert dir_obj.path.exists()


def test_dir_obj_utility_methods(dir_obj: Directory):
    """Test utility methods like get_type_filelist, tree, maxtreedepth."""
    assert isinstance(dir_obj.tree, dict)
    assert isinstance(dir_obj.maxtreedepth, int)


@mark.parametrize(
    "path, include, exclude, expected",
    [
        ("/path/to/file", {"path"}, {"exclude"}, True),
        ("/path/to/file", {"other"}, {"file"}, False),
    ],
)
def test_eval_parents_inclusion_exclusion(path, include, exclude, expected):
    """Test various combinations of include and exclude criteria"""
    path = Path(path)
    assert eval_parents(path, include, exclude) is expected


def test_system_object_initialization():
    # Test initialization and attribute setting
    obj = SystemObject(name="test", path=Path("/test/path"))
    assert obj.name


def test_json_file_init(json_file: JsonFile):
    """Test the initialization of the JsonFile class"""
    assert json_file.istype("json")
    assert json_file.path.exists()


def test_toml_file_init(toml_file: TomlFile):
    """Test the initialization of the TomlFile class"""
    assert toml_file.istype("toml")
    assert toml_file.path.exists()


def test_read_toml(toml_file: TomlFile):
    """Test reading a TOML file"""
    assert read_toml(toml_file.path) == {"key": "value"}


def test_read_json(json_file: JsonFile):
    """Test reading a JSON file"""
    assert read_json(json_file.path) == {"key": "value"}


def test_settings_init(settings_file: SettingsFile):
    assert settings_file.name == "settings.json"
    assert isinstance(settings_file, SettingsFile)


def test_settings_envdict_init(settings_file: SettingsFile):
    assert isinstance(settings_file.envdict, dict)
    assert len(settings_file.envdict) > 0


def test_save_png_format(figure: Figure, figure_path: Path):
    """Test saving a figure in PNG format."""
    _ = figure
    assert figsave(figure_path.stem, figure_path.parent, "png")
    assert figure_path.exists()


def test_save_with_bbox_inches(figure: Figure, figure_path: Path):
    """Test saving a figure with the bbox_inches parameter."""
    _ = figure
    assert figsave(figure_path.stem, figure_path.parent, "png", bbox_inches="tight")
    assert figure_path.exists()


@mark.parametrize(
    "path, include, exclude, expected",
    [
        (Path("/test/dir/subdir/file.txt"), {"subdir"}, set(), True),
        (Path("/test/dir/exclude/file.txt"), set(), {"exclude"}, False),
    ],
)
def test_eval_parents(path: Path, include: set, exclude: set, expected: bool):
    """Test the eval_parents function for evaluating file paths with different include and exclude criteria."""
    assert eval_parents(path, include, exclude) is expected


def test_search_with_pattern(dir_path: Path):
    """Test searching with a specific pattern."""
    testfile_name = "test_file.txt"
    (dir_path / testfile_name).touch()
    found_path = path_search(testfile_name, start_path=dir_path)
    assert found_path.name == testfile_name


def test_search_nonexistent_file(dir_path: Path):
    """Test searching for a non-existent file."""
    with raises(FileNotFoundError):
        path_search("nonexistent.txt", start_path=dir_path, max_ascends=0)


def test_systemobject_instantiation(sysobj: SystemObject):
    """Test instantiation with different names and paths."""
    assert sysobj.name
    assert sysobj.path.exists()


def test_systemobject_properties(sysobj: SystemObject):
    """Test property methods like `isfile`, `isdir`, `haspath`, `user`, etc."""
    assert sysobj.isfile
    assert not sysobj.isdir


def test_sysobj_get_parent(sysobj: SystemObject):
    """Test the get_parent method of the SystemObject class."""
    rand_parent_name = choice([x.name for x in sysobj.path.parents if len(x.name) > 1])
    parent = sysobj.get_parent(rand_parent_name)
    assert isinstance(parent, Path)


def test_sysobj_get_parent_failure(sysobj: SystemObject):
    """Test the get_parent method of the SystemObject class."""
    with raises(ValueError):
        sysobj.get_parent("nonexistent")


def test_sysobj_modified_timestamp(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp, float)


def test_sysobj_modified_datetime(sysobj: SystemObject):
    assert isinstance(sysobj.modified_datetime, datetime)


def test_sysobj_modified_strfdatetime(sysobj: SystemObject):
    assert isinstance(sysobj.modified_strfdatetime, str)


def test_sysobj_modified_strfdate(sysobj: SystemObject):
    assert isinstance(sysobj.modified_strfdate, str)


def test_sysobj_modified_delta(sysobj: SystemObject):
    assert isinstance(sysobj.modified_delta, timedelta)


def test_sysobj_created_timestamp(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp, float)


def test_sysobj_created_datetime(sysobj: SystemObject):
    assert isinstance(sysobj.created_datetime, datetime)


def test_sysobj_created_strfdatetime(sysobj: SystemObject):
    assert isinstance(sysobj.created_strfdatetime, str)


def test_sysobj_created_strfdate(sysobj: SystemObject):
    assert isinstance(sysobj.created_strfdate, str)


def test_sysobj_created_delta(sysobj: SystemObject):
    assert isinstance(sysobj.created_delta, timedelta)


def test_dir_obj_filelist(subdir_with_files: Directory):
    """Test the filelist property of the Directory class."""
    assert isinstance(subdir_with_files.filelist, list)
    assert all(isinstance(f, File) for f in subdir_with_files.filelist)


def test_dir_obj_dirlist(dir_obj: Directory):
    """Test the dirlist property of the Directory class."""
    assert isinstance(dir_obj.dirlist, list)
    assert all(isinstance(d, Directory) for d in dir_obj.dirlist)


def test_dir_obj_contents(dir_obj: Directory):
    """Test the dirlist property of the Directory class."""
    assert isinstance(dir_obj.dirlist, list)
    assert all(isinstance(d, Path) for d in dir_obj.contents)


def test_dir_obj_objlist(subdir_with_files: Directory):
    """Test the contents property of the Directory class."""
    assert isinstance(subdir_with_files.contents, list)
    assert all(issubclass(d.__class__, SystemObject) for d in subdir_with_files.objlist)


def test_dir_obj_get_latest_file(subdir_with_files: Directory):
    """Test the get_latest_file method of the Directory class."""
    latest_file = subdir_with_files.get_latest_file()
    assert isinstance(latest_file, File)
