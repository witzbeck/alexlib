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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import partial
from itertools import chain
from pathlib import Path
from random import choice, randint
from string import ascii_letters, digits, printable, punctuation, whitespace
from alexlib.constants import ISTYPE_EXTS

from alexlib.files import Directory, File

DIGITS = list(digits)
LETTERS = list(ascii_letters)
PRINTABLES = list(printable)
VOWELS = list("aeiou")
CONSONANTS = [x for x in LETTERS if x.lower() not in VOWELS]
WHITESPACE = list(whitespace)
PUNCTUATION = list(punctuation)


def randintstr(min_int: int = 0, max_int: int = 10) -> str:
    """returns a random integer between min_int and max_int as a string"""
    return str(randint(min_int, max_int))


def randrange(min_int: int = 1, max_int: int = 20) -> int:
    """returns a range spanning min_int to max_int"""
    return range(randint(min_int, max_int))


randdigit = partial(choice, DIGITS)
randvowel = partial(choice, VOWELS)
randprint = partial(choice, PRINTABLES)
randlet = partial(choice, LETTERS)
randfileext = partial(choice, ISTYPE_EXTS)
randpunct = partial(choice, PUNCTUATION)
randwhitespace = partial(choice, WHITESPACE)


def infgen(
    digit: bool = False,
    vowel: bool = False,
    letter: bool = False,
    intstr: bool = False,
    printable_: bool = False,
    punct: bool = False,
) -> int | str:
    """generates an infinite stream of random integers or letters"""
    funcs = [
        x["func"]
        for x in [
            {"bool": digit, "func": randdigit},
            {"bool": vowel, "func": randvowel},
            {"bool": letter, "func": randlet},
            {"bool": intstr, "func": randintstr},
            {"bool": printable_, "func": randprint},
            {"bool": punct, "func": randpunct},
        ]
        if x["bool"]
    ]
    if (n := len(funcs)) == 0:
        raise ValueError("need choice(s)")
    if n == 1:
        func = funcs[0]
        while True:
            yield func()
    else:
        while True:
            yield choice(funcs)()


def limgen(lim: int, concat: bool = True, **kwargs) -> list[str] | str:
    """generates a limited stream of random integers or letters"""
    infg = infgen(**kwargs)
    gen = [next(infg) for _ in range(lim)]
    return "".join(gen) if concat else gen


def randfilename(
    min_: int = 5,
    max_: int = 12,
    let_: bool = True,
    intstr_: bool = True,
) -> str:
    """generates a random test name"""
    name_len = randint(min_, max_)
    name = limgen(name_len, intstr_=intstr_, let_=let_)
    return f"{name}.{randfileext()}"


def mk_test_filename(prefix: str = "__test") -> str:
    """generates a random test name"""
    return f"{prefix}{randfilename()}"


def randtext(lim: int = 100) -> str:
    """generates a random text string"""
    return limgen(lim, printable=True)


def randdirname() -> str:
    """generates a random directory name"""
    return mk_test_filename(let_=True, intstr_=False)


def randtimedelta(min_days: int = 10, max_days: int = 10_000) -> timedelta:
    """generates a random timedelta"""
    days = randint(min_days, max_days)
    return timedelta(days=days)


def randyear(min_year: int = 1990, max_year: int = 2030) -> int:
    """generates a random year"""
    return randint(min_year, max_year)


def randmonth() -> int:
    """generates a random month"""
    return randint(1, 12)


def randdatetime(
    min_year: int = 1990,
    max_year: int = 2030,
) -> datetime:
    """generates a random datetime"""
    dt = datetime(
        randyear(
            min_year=min_year,
            max_year=max_year,
        ),
        randmonth(),
        1,
    )
    return dt + randtimedelta()


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
        return dirpath / randfilename()

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
            path.write_text(randtext())
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
        return target_dir / randdirname()

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
