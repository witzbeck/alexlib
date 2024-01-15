"""
This module provides two classes, RandGen and FileFaker, for generating random data and simulating file operations respectively.

RandGen:
    A utility class for generating random data of various types, such as integers, strings, letters, printable characters,
    and more. It includes functions for generating random integers, strings of random integers, random letters,
    random printable characters, infinite generators for the above types, and utility functions for creating random names,
    file extensions, text content, directory names, and datetime objects.

FileFaker:
    A class designed to simulate file and directory operations in a specified target directory. It allows for the creation
    of a specified number of files and directories with random names and content. The class includes methods for creating
    file paths, writing files with optional text content, creating directories, and setting up and tearing down file structures
    for testing or simulation purposes.

Additionally, the module includes a helper function `pick_yn` to randomly select a 'Y' or 'N' character, with an optional
bias towards one of the choices.

Dependencies:
    - dataclasses: For creating data classes.
    - datetime: For working with date and time.
    - itertools: For efficient looping.
    - pathlib: For filesystem path operations.
    - string: For string constants.
    - random: For generating random numbers and choosing random elements.
    - alexlib.files: For file operation utilities (external library).

Typical usage example:
    file_faker = FileFaker(target_dir=Path('/tmp'))
    file_faker.setup_dirs()
    file_faker.setup_files(file_faker.dirs)
"""
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from itertools import chain
from pathlib import Path
from random import choice
from random import choices
from random import randint
from string import ascii_letters
from string import printable

from alexlib.files import Directory
from alexlib.files import File

letlist = list(ascii_letters)
printlist = list(printable)
vowels = list("aeiou")
consonants = [x for x in letlist if x not in vowels]


@dataclass
class RandGen:
    """generates random values"""

    @staticmethod
    def randint(min_int: int = 0, max_int: int = 10) -> int:
        """returns a random integer between min_int and max_int"""
        return randint(min_int, max_int)

    @staticmethod
    def _randintstr(**kwargs) -> str:
        """returns a random integer between min_int and max_int as a string"""
        return str(RandGen.randint(**kwargs))

    @staticmethod
    def randintstr(n: int = None, **kwargs) -> str:
        """returns a random integer between min_int and max_int as a string"""

        def g() -> str:
            return RandGen._randintstr(**kwargs)

        func = choices if n else choice
        arg = (g, n) if n else g
        return func(arg)

    @staticmethod
    def randlet(
        n: int = None,
        vowels_: bool = False,
    ) -> str:
        """returns a random letter from the alphabet"""
        lst = vowels if vowels_ else letlist
        func = choices if n else choice
        arg = (lst, n) if n else lst
        return func(arg)

    @staticmethod
    def randprint(n: int = None) -> str:
        """returns a random printable character"""
        func = choices if n else choice
        arg = (printlist, n) if n else printlist
        return func(arg)

    @staticmethod
    def infgen(
        int_: bool = False,
        intstr_: bool = False,
        let_: bool = False,
        printable_: bool = False,
    ) -> int | str:
        """generates an infinite stream of random integers or letters"""
        if not (int_ or intstr_ or let_ or printable_):
            raise ValueError("need choice")
        funcs = []
        if int_:
            funcs.append(RandGen.randint)
        if intstr_:
            funcs.append(RandGen.randintstr)
        if let_:
            funcs.append(RandGen.randlet)
        if printable_:
            funcs.append(RandGen.randprint)
        n = len(funcs)
        if n == 0:
            raise ValueError("need a func")
        if n == 1:
            func = funcs[0]
            while True:
                yield func()
        else:
            while True:
                yield choice(funcs)()

    @staticmethod
    def limgen(lim: int, concat: bool = True, **kwargs) -> list[str] | str:
        """generates a limited stream of random integers or letters"""
        infg = RandGen.infgen(**kwargs)
        gen = [next(infg) for _ in range(lim)]
        return "".join(gen) if concat else gen

    @staticmethod
    def mk_test_name(
        min_: int = 5, max_: int = 12, let_: bool = True, intstr_: bool = True
    ) -> str:
        """generates a random test name"""
        name_len = randint(min_, max_)
        name = RandGen.limgen(name_len, intstr_=intstr_, let_=let_)
        return "__test" + name

    @staticmethod
    def mk_test_ext(_min: int = 2, _max: int = 5) -> str:
        """generates a random test extension"""
        ext_len = randint(_min, _max)
        ext = RandGen.limgen(ext_len, _let=True)
        return ext.lower()

    @staticmethod
    def mk_text(lim: str = 100) -> str:
        """generates a random text string"""
        return RandGen.limgen(lim, printable=True)

    @staticmethod
    def mk_dirname() -> str:
        """generates a random directory name"""
        return RandGen.mk_test_name(let_=True, intstr_=False)

    @staticmethod
    def mk_filename() -> str:
        """generates a random file name"""
        name = RandGen.mk_test_name()
        ext = RandGen.mk_test_ext()
        return f"{name}.{ext}"

    @staticmethod
    def mk_timedelta(min_days: int = 10, max_days: int = 10_000) -> timedelta:
        """generates a random timedelta"""
        days = randint(min_days, max_days)
        return timedelta(days=days)

    @staticmethod
    def mk_datetime(
        min_year: int = 1990,
        max_year: int = 2030,
    ) -> datetime:
        """generates a random datetime"""
        year = randint(min_year, max_year)
        month = randint(1, 12)
        dt = datetime(year, month, 1)
        td = RandGen.mk_timedelta()
        return dt + td


@dataclass
class FileFaker:
    """creates a fake directory with files"""

    target_dir: Path
    nfiles: int = field(default=3)
    ndirs: int = field(default=1)
    topdir: Directory = field(default=None)
    dirs: list[Directory] = field(
        default=None,
        repr=False,
    )
    files: list[File] = field(
        default=None,
        repr=False,
    )

    @staticmethod
    def mk_filepath(dirpath: Path) -> Path:
        """generates a random filepath"""
        name = RandGen.mk_filename()
        return dirpath / name

    @staticmethod
    def write_file(
        dirpath: Path, inc_text: bool = True, overwrite: bool = True
    ) -> File:
        """writes a file to dirpath"""
        path = FileFaker.mk_filepath(dirpath)
        exists = path.exists()
        if exists and not overwrite:
            raise FileExistsError
        path.touch()
        if inc_text:
            text = RandGen.mk_text()
            path.write_text(text)
        return File(path=path)

    @staticmethod
    def write_files(
        dirpath: Path,
        nfiles: int,
        **kwargs,
    ) -> list[File]:
        """writes nfiles to dirpath"""
        dp = dirpath
        rng = range(nfiles)
        func = FileFaker.write_file
        return [func(dp, **kwargs) for _ in rng]

    @staticmethod
    def mk_dirpath(target_dir: Path) -> Path:
        """generates a random directory path"""
        name = RandGen.mk_dirname()
        return target_dir / name

    @staticmethod
    def write_dir(target_dir: Path) -> Directory:
        """writes a directory to target_dir"""
        path = FileFaker.mk_dirpath(target_dir)
        path.mkdir()
        return Directory(path=path)

    def setup_dirs(self) -> list[Directory]:
        """writes ndirs to target_dir"""
        td = self.target_dir
        _range = range(self.ndirs)
        return [FileFaker.write_dir(td) for _ in _range]

    def setup_files(self, dirs: list[Directory]) -> list[File]:
        """writes nfiles to each dir in dirs"""
        func = FileFaker.write_files
        flist = [func(dir.path, self.nfiles) for dir in dirs]
        return list(chain.from_iterable(flist))

    def __post_init__(self) -> None:
        """creates a fake directory with files"""
        self.dirs = self.setup_dirs()
        self.files = self.setup_files(self.dirs)

    def teardown(self) -> None:
        """deletes the fake directory"""
        for d in self.dirs:
            d.teardown()


def pick_yn(y_bias: float = None) -> str:
    """returns a random Y or N"""
    if y_bias is None:
        ret = choice(["Y", "N"])
    else:
        ys = int(y_bias * 100)
        ns = int(100 - ys)
        y_choices = ["Y" for _ in range(ys)]
        n_choices = ["N" for _ in range(ns)]
        ret = choice(y_choices + n_choices)
    return ret
