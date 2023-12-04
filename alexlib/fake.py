from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import chain
from pathlib import Path
from string import printable, ascii_letters
from random import randint, choice

from alexlib.file import File, Directory

letlist = list(ascii_letters)
printlist = list(printable)


@dataclass
class RandGen:
    @staticmethod
    def randint(
        min_int: int = 0,
        max_int: int = 10
    ) -> int:
        return randint(min_int, max_int)

    @staticmethod
    def randintstr(**kwargs):
        return str(RandGen.randint(**kwargs))

    @staticmethod
    def randlet():
        return choice(letlist)

    @staticmethod
    def randprint():
        return choice(printlist)

    @staticmethod
    def infgen(
        _int: bool = False,
        _intstr: bool = False,
        _let: bool = False,
        printable: bool = False,
    ) -> int | str:
        if not (_int or _intstr or _let or printable):
            raise ValueError("need choice")
        else:
            funcs = []
        if _int:
            funcs.append(RandGen.randint)
        if _intstr:
            funcs.append(RandGen.randintstr)
        if _let:
            funcs.append(RandGen.randlet)
        if printable:
            funcs.append(RandGen.randprint)
        n = len(funcs)
        if n == 0:
            raise ValueError("need a func")
        elif n == 1:
            func = funcs[0]
            while True:
                yield func()
        else:
            while True:
                yield choice(funcs)()

    @staticmethod
    def limgen(
        lim: int,
        concat: bool = True,
        **kwargs
    ):
        infg = RandGen.infgen(**kwargs)
        gen = [next(infg) for _ in range(lim)]
        if concat:
            return "".join(gen)
        else:
            return gen

    @staticmethod
    def mk_test_name(
        _min: int = 5,
        _max: int = 12,
        _let: bool = True,
        _intstr: bool = True
    ):
        name_len = randint(_min, _max)
        name = RandGen.limgen(name_len, _intstr=_intstr, _let=_let)
        return "__test" + name

    @staticmethod
    def mk_test_ext(_min: int = 2, _max: int = 5):
        ext_len = randint(_min, _max)
        ext = RandGen.limgen(ext_len, _let=True)
        return ext.lower()

    @staticmethod
    def mk_text(lim: str = 100):
        return RandGen.limgen(lim, printable=True)

    @staticmethod
    def mk_dirname() -> str:
        return RandGen.mk_test_name(_let=True, _intstr=False)

    @staticmethod
    def mk_filename() -> str:
        name = RandGen.mk_test_name()
        ext = RandGen.mk_test_ext()
        return f"{name}.{ext}"

    @staticmethod
    def mk_timedelta(
        min_days: int = 10,
        max_days: int = 10_000
    ):
        days = randint(min_days, max_days)
        return timedelta(days=days)

    @staticmethod
    def mk_datetime(
        min_year: int = 1990,
        max_year: int = 2030,
    ):
        year = randint(min_year, max_year)
        month = randint(1, 12)
        dt = datetime(year, month, 1)
        td = RandGen.mk_timedelta()
        return dt + td


@dataclass
class FileFaker:
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
    def mk_filepath(dirpath: Path):
        name = RandGen.mk_filename()
        return dirpath / name

    @staticmethod
    def write_file(dirpath: Path,
                   inc_text: bool = True,
                   overwrite: bool = True
                   ) -> File:
        path = FileFaker.mk_filepath(dirpath)
        exists = path.exists()
        if (exists and not overwrite):
            raise FileExistsError
        else:
            path.touch()
        if inc_text:
            text = RandGen.mk_text()
            path.write_text(text)
        return File(path=path)

    @staticmethod
    def write_files(dirpath: Path,
                    nfiles: int,
                    **kwargs,
                    ):
        dp = dirpath
        rng = range(nfiles)
        func = FileFaker.write_file
        return [func(dp, **kwargs) for _ in rng]

    @staticmethod
    def mk_dirpath(target_dir: Path
                   ) -> Path:
        name = RandGen.mk_dirname()
        return target_dir / name

    @staticmethod
    def write_dir(target_dir: Path):
        path = FileFaker.mk_dirpath(target_dir)
        path.mkdir()
        return Directory(path=path)

    def setup_dirs(self):
        td = self.target_dir
        _range = range(self.ndirs)
        return [FileFaker.write_dir(td) for _ in _range]

    def setup_files(self, dirs: list[Directory]):
        func = FileFaker.write_files
        flist = [func(dir.path, self.nfiles) for dir in dirs]
        return list(chain.from_iterable(flist))

    def __post_init__(self):
        self.dirs = self.setup_dirs()
        self.files = self.setup_files(self.dirs)

    def teardown(self):
        for dir in self.dirs:
            dir.teardown()


def pick_yn(y_bias: float = None) -> str:
    if y_bias is None:
        return choice(["Y", "N"])
    else:
        ys = int(y_bias * 100)
        ns = int(100 - ys)
        y_choices = ["Y" for _ in range(ys)]
        n_choices = ["N" for _ in range(ns)]
        return choice(y_choices + n_choices)
