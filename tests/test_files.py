from datetime import datetime, timedelta
from pathlib import Path
from random import choice

from matplotlib.figure import Figure
from pytest import FixtureRequest, fixture, mark, raises, skip

from alexlib.files import (
    CreatedTimestamp,
    Directory,
    File,
    JsonFile,
    ModifiedTimestamp,
    SettingsFile,
    SystemObject,
    TomlFile,
    __sysobj_names__,
)
from alexlib.files.sizes import (
    NBYTES_LABEL_MAP,
    FileSize,
)
from alexlib.files.times import SystemTimestamp
from alexlib.files.types import (
    SUFFIX_FILETYPE_MAP,
    CommentSyntax,
    FileType,
)
from alexlib.files.utils import (
    eval_parents,
    figsave,
    get_parent,
    path_search,
    read_json,
    read_toml,
)


@fixture(scope="module")
def this_file_path() -> Path:
    return Path(__file__)


@fixture(scope="module")
def this_dir_path(this_file_path: Path) -> Path:
    return this_file_path.parent


def test_find_this_file(this_file_path: Path, this_dir_path: Path):
    assert this_file_path.exists()
    assert this_dir_path.exists()
    file = File.find(this_file_path.name, start_path=this_dir_path)
    assert file.path == this_file_path
    assert isinstance(file, File)


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
    obj = SystemObject(path=Path("/test/path"))
    assert isinstance(obj, SystemObject)
    assert isinstance(obj.path, Path)


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
    assert isinstance(settings_file, SettingsFile)


def test_settings_envdict_init(settings_file: SettingsFile):
    assert isinstance(settings_file.envdict, dict)


def test_settings_envdict_has_values(settings_file: SettingsFile):
    assert len(settings_file.envdict) > 0


@mark.slow
def test_save_png_format(figure: Figure, figure_path: Path):
    """Test saving a figure in PNG format."""
    _ = figure
    assert figsave(figure_path.stem, figure_path.parent, "png")
    assert figure_path.exists()


@mark.slow
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
    assert sysobj.path.exists()


def test_systemobject_properties(sysobj: SystemObject):
    """Test property methods like `isfile`, `isdir`, `haspath`, `user`, etc."""
    assert sysobj.isfile
    assert not sysobj.isdir


def test_sysobj_get_parent(sysobj: SystemObject):
    """Test the get_parent method of the SystemObject class."""
    rand_parent_name = choice([x.name for x in sysobj.path.parents if len(x.name) > 1])
    parent = get_parent(sysobj.path, rand_parent_name)
    assert isinstance(parent, Path)


def test_sysobj_get_parent_failure(sysobj: SystemObject):
    """Test the get_parent method of the SystemObject class."""
    with raises(ValueError):
        get_parent(sysobj.path, "nonexistent")


def test_sysobj_modified_timestamp_type(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp, ModifiedTimestamp)


def test_sysobj_modified_timestamp_ts(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp.timestamp, float)


def test_sysobj_modified_datetime(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp.datetime, datetime)


def test_sysobj_modified_strfdatetime(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp.strfdatetime, str)


def test_sysobj_modified_strfdate(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp.strfdate, str)


def test_sysobj_modified_delta(sysobj: SystemObject):
    assert isinstance(sysobj.modified_timestamp.delta, timedelta)


def test_sysobj_created_timestamp_type(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp, CreatedTimestamp)


def test_sysobj_created_timestamp_ts(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp.timestamp, float)


def test_sysobj_created_datetime(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp.datetime, datetime)


def test_sysobj_created_strfdatetime(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp.strfdatetime, str)


def test_sysobj_created_strfdate(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp.strfdate, str)


def test_sysobj_created_delta(sysobj: SystemObject):
    assert isinstance(sysobj.created_timestamp.delta, timedelta)


def test_sysobj_is_new_enough(sysobj: SystemObject):
    assert sysobj.created_timestamp.is_new_enough(timedelta(days=1))


def test_sysobj_is_new_enough_not_timedelta(sysobj: SystemObject):
    with raises(TypeError):
        sysobj.modified_timestamp.is_new_enough(1e5)


def test_sysobj_from_path(dir_obj: Directory):
    """Test the from_path method of the SystemObject class."""
    sysobj = SystemObject.from_path(dir_obj.path)
    assert isinstance(sysobj, SystemObject)


def test_sysobj_from_parent(settings_file: SettingsFile):
    """Test the from_parent method of the SystemObject class."""
    sysobj = SystemObject.from_parent(
        settings_file.path.name, settings_file.path.parent, notexistok=True
    )
    assert isinstance(sysobj, SystemObject)


def test_sysobj_clsname(sysobj: SystemObject):
    assert sysobj.__class__.__name__ in __sysobj_names__


def test_dir_obj_filelist_islist(subdir_with_files: Directory):
    """Test the filelist property of the Directory class."""
    assert isinstance(subdir_with_files.filelist, list)


def test_dir_obj_filelist_are_file_objs(subdir_with_files: Directory):
    assert all(isinstance(f, File) for f in subdir_with_files.filelist)


def test_dir_obj_dirlist_islist(dir_obj: Directory):
    """Test the dirlist property of the Directory class."""
    assert isinstance(dir_obj.dirlist, list)


def test_dir_obj_dirlist_are_dir_objs(dir_obj: Directory):
    assert all(isinstance(d, Directory) for d in dir_obj.dirlist)


def test_dir_obj_contents_islist(dir_obj: Directory):
    """Test the dirlist property of the Directory class."""
    assert isinstance(dir_obj.dirlist, list)


def test_dir_obj_contents_are_paths(dir_obj: Directory):
    assert all(isinstance(d, Path) for d in dir_obj.contents)


def test_dir_obj_objlist_islist(subdir_with_files: Directory):
    """Test the contents property of the Directory class."""
    assert isinstance(subdir_with_files.contents, list)


def test_dir_obj_objlist_are_sysobjs(subdir_with_files: Directory):
    assert all(issubclass(d.__class__, SystemObject) for d in subdir_with_files.objlist)


def test_dir_obj_get_latest_file(subdir_latest_file: File):
    """Test the get_latest_file method of the Directory class."""
    assert isinstance(subdir_latest_file, File)


def test_dir_obj_created_timestamp_repr(dir_obj_created_ts: CreatedTimestamp):
    assert isinstance(repr(dir_obj_created_ts), str)


def test_dir_obj_created_timestamp_str(dir_obj_created_ts: CreatedTimestamp):
    assert isinstance(str(dir_obj_created_ts), str)


def test_dir_obj_modified_timestamp_repr(dir_obj_modified_ts: ModifiedTimestamp):
    assert isinstance(repr(dir_obj_modified_ts), str)


def test_dir_obj_modified_timestamp_str(dir_obj_modified_ts: ModifiedTimestamp):
    assert isinstance(str(dir_obj_modified_ts), str)


def test_system_timestamp_not_implemented_from_stat_result():
    with raises(NotImplementedError):
        SystemTimestamp.from_stat_result(None)


def test_system_timestamp_from_path(dir_path: Path):
    with raises(NotImplementedError):
        sys_ts = SystemTimestamp.from_path(dir_path)
        assert isinstance(sys_ts, SystemTimestamp)


def test_system_obj_from_string_path():
    obj = SystemObject.from_path(".")
    assert isinstance(obj, SystemObject)


def test_system_obj_from_parent():
    obj = SystemObject.from_parent(".gitignore", Path(".").resolve(), notexistok=False)
    assert isinstance(obj, SystemObject)


def test_system_obj_from_parent_notreal_but_fine():
    obj = SystemObject.from_parent("notrealfile", Path("."), notexistok=True)
    assert isinstance(obj, SystemObject)


def test_system_obj_from_parent_not_exist():
    with raises(FileNotFoundError):
        SystemObject.from_parent("notrealfile", Path("."), notexistok=False)


def test_file_obj_repr(text_file_obj: File):
    assert isinstance(repr(text_file_obj), str)


def test_file_obj_str(text_file_obj: File):
    assert isinstance(str(text_file_obj), str)


def test_file_clipboard(text_file_obj: File):
    assert isinstance(text_file_obj.clip(), str)


@mark.parametrize("label, scale", NBYTES_LABEL_MAP.items())
def test_map_has_expected_values(label, scale):
    assert isinstance(label, str)
    assert isinstance(scale, int)
    assert label[-1] == "B" or label == "bytes"
    assert scale >= 0


def test_file_size_init(file_obj: File):
    assert isinstance(file_obj.size, FileSize)
    assert isinstance(file_obj.size.nbytes, int)
    assert isinstance(file_obj.size.min_scale_level, int)
    assert isinstance(file_obj.size.roundto, int)


def test_file_size_repr(file_obj: File):
    assert isinstance(repr(file_obj.size), str)


def test_file_size_str(file_obj: File):
    assert isinstance(str(file_obj.size), str)


def test_file_size_lt(file_obj: File):
    assert file_obj.size < FileSize(1e6)


def test_file_size_gt(file_obj: File):
    assert file_obj.size > FileSize(1e1)


def test_file_size_from_path(file_obj: File):
    assert isinstance(FileSize.from_path(file_obj.path), FileSize)


def test_file_size_from_system_object(file_obj: File):
    assert isinstance(FileSize.from_system_object(file_obj), FileSize)


def test_file_size_from_system_object_not_pathlike(file_obj: File):
    with raises(TypeError):
        FileSize.from_system_object("notpathlike")


@fixture(
    scope="module",
    params=SUFFIX_FILETYPE_MAP.values(),
)
def filetype(request: FixtureRequest) -> FileType:
    return request.param


def test_filetype_init(filetype: FileType):
    assert isinstance(filetype, FileType)


def test_filetype_repr(filetype: FileType):
    assert isinstance(repr(filetype), str)


def test_filetype_str(filetype: FileType):
    assert isinstance(str(filetype), str)


def test_filetype_name_str(filetype: FileType):
    assert isinstance(filetype.name, str)


def test_filetype_suffix_str(filetype: FileType):
    assert isinstance(filetype.suffix, str)


def test_filetype_suffix_in_map(filetype: FileType):
    assert isinstance(SUFFIX_FILETYPE_MAP[filetype.suffix], FileType)


def test_filetype_from_suffix(filetype: FileType):
    assert FileType.from_suffix(filetype.suffix, SUFFIX_FILETYPE_MAP) == filetype


def test_line_comment_chars(filetype: FileType):
    assert isinstance(filetype.comment_syntax, CommentSyntax)
    if filetype.comment_syntax.line_comment is None:
        skip("No line comment chars for this filetype")
    assert filetype.comment_syntax.line_comment is not None
    assert isinstance(filetype.comment_syntax.line_comment, (str, list))


def test_multiline_comment_chars(filetype: FileType):
    assert isinstance(filetype.comment_syntax, CommentSyntax)
    if filetype.comment_syntax.multiline_comment is None:
        skip("No multiline comment chars for this filetype")
    assert isinstance(filetype.comment_syntax.multiline_comment, tuple)
    assert all(isinstance(c, str) for c in filetype.comment_syntax.multiline_comment)
    assert len(filetype.comment_syntax.multiline_comment) == 2


@fixture(scope="module")
def file_obj_type(file_obj: File):
    return FileType.from_suffix(file_obj.path.suffix, SUFFIX_FILETYPE_MAP)


def test_file_obj_has_created_timestamp(file_obj: File):
    assert isinstance(file_obj.created_timestamp, CreatedTimestamp)


def test_file_obj_has_modified_timestamp(file_obj: File):
    assert isinstance(file_obj.modified_timestamp, ModifiedTimestamp)


def test_file_obj_created_timestamp_datetime(file_obj: File):
    assert isinstance(file_obj.created_timestamp.datetime, datetime)


def test_file_obj_created_timestamp_strfdatetime(file_obj: File):
    assert isinstance(file_obj.created_timestamp.strfdatetime, str)


def test_file_obj_created_timestamp_strfdate(file_obj: File):
    assert isinstance(file_obj.created_timestamp.strfdate, str)


def test_file_obj_created_timestamp_delta(file_obj: File):
    assert isinstance(file_obj.created_timestamp.delta, timedelta)


def test_file_obj_created_timestamp_is_new_enough(file_obj: File):
    assert file_obj.created_timestamp.is_new_enough(timedelta(days=1))


def test_file_obj_modified_timestamp_datetime(file_obj: File):
    assert isinstance(file_obj.modified_timestamp.datetime, datetime)


def test_file_obj_modified_timestamp_strfdatetime(file_obj: File):
    assert isinstance(file_obj.modified_timestamp.strfdatetime, str)


def test_file_obj_modified_timestamp_strfdate(file_obj: File):
    assert isinstance(file_obj.modified_timestamp.strfdate, str)


def test_file_obj_modified_timestamp_delta(file_obj: File):
    assert isinstance(file_obj.modified_timestamp.delta, timedelta)


def test_file_obj_modified_timestamp_is_new_enough(file_obj: File):
    assert file_obj.modified_timestamp.is_new_enough(timedelta(days=1))
