"""A response is a text file with a title and a body of text."""
from abc import abstractmethod
from json import dumps
from pathlib import Path
from dataclasses import dataclass, field
from functools import cached_property

from alexlib.files import File

ML_PATH = Path(__file__).parent
PROJ_PATH = ML_PATH.parent
DB_PATH = PROJ_PATH / "db"
DB_TEST_CASES = "db_test_cases.txt"
DB_TEST_CASES_PATH = DB_PATH / DB_TEST_CASES


@dataclass
class LargeLanguageModelResponse:
    content: str = field(repr=False)
    path: Path = field(default=None, repr=False)

    @classmethod
    def from_file(cls, file: File) -> "LargeLanguageModelResponse":
        """Create a response from a file."""
        return cls(file.text, path=file.path)

    @classmethod
    def from_path(cls, path: Path) -> "LargeLanguageModelResponse":
        """Create a response from a path."""
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")
        return cls(path.read_text(), path=path)

    @cached_property
    def lines(self) -> list[str]:
        """Get the lines of a response."""
        return [x.strip() for x in self.content.split("\n") if x]

    @cached_property
    def line_indexes(self) -> list[int]:
        """Get the line indexes of a response."""
        return [self.lines.index(x) for x in self.lines]

    @cached_property
    def line_index(self) -> dict[str, int]:
        """Get the line index of a response."""
        return dict(zip(self.lines, self.line_indexes))

    @cached_property
    def step_lines(self) -> list[str]:
        """Get the step lines of a response."""
        return [x for x in self.lines if x.startswith("-")]

    @cached_property
    def step_indexes(self) -> list[int]:
        """Get the step indexes of a response."""
        return [self.lines.index(x) for x in self.step_lines]

    @abstractmethod
    def process_content(self) -> None:
        """Process the content of a response."""
        pass

    @staticmethod
    def get_title_from_filename(filename: str) -> str:
        """Get the title of a response from its filename."""
        return filename.split(".")[0].replace("_", " ").title()

    @staticmethod
    def get_title_from_path(path: str) -> str:
        """Get the title of a response from its path."""
        return LargeLanguageModelResponse.get_title_from_filename(Path(path).name)

    @staticmethod
    def get_filename_from_title(title: str) -> str:
        """Get the filename of a response from its title."""
        return title.replace(" ", "_") + ".txt"

    @property
    def title(self) -> str:
        """Get the title of a response."""
        return LargeLanguageModelResponse.get_title_from_path(self.path)

    @cached_property
    def _title_parts(self) -> list[str]:
        """Get the title parts of a response."""
        return self.title.split(" ")


@dataclass
class MarkdownResponse(LargeLanguageModelResponse):
    """A markdown response is a text file with a title and a body of text."""

    @cached_property
    def headings(self) -> list[str]:
        """Get the headings of a response."""
        return [x for x in self.lines if x.startswith("#")]

    @property
    def has_headings(self) -> bool:
        """Check if a response has headings."""
        return bool(self.headings)

    @property
    def first_content_line(self) -> int:
        """Get the first content line of a response."""
        return min(self.step_indexes, self.heading_indexes)

    @property
    def last_content_line(self) -> int:
        """Get the last content line of a response."""
        return max(self.step_indexes, self.heading_indexes)

    @property
    def preface(self) -> str:
        """Get the preface of a response."""
        return "\n".join(self.lines[: self.first_content_line])

    @property
    def epilogue(self) -> str:
        """Get the epilogue of a response."""
        return "\n".join(self.lines[self.last_content_line + 1 :])

    @property
    def content_lines(self) -> list[str]:
        """Get the content lines of a response."""
        return self.lines[self.first_content_line : self.last_content_line + 1]

    @cached_property
    def heading_indexes(self) -> list[int]:
        """Get the heading indexes of a response."""
        return [self.lines.index(x) for x in self.headings]

    @property
    def has_numbered_headings(self) -> bool:
        """Check if a response has numbered headings."""
        return bool(self.numbered_headings)

    @cached_property
    def heading_index(self) -> dict[str, int]:
        """Get the heading index of a response."""
        return dict(zip(self.headings, self.heading_indexes))

    @property
    def title_prefix(self) -> str:
        """Get the title prefix of a response."""
        return self._title_parts[0]

    @property
    def text_prefix(self) -> str:
        """Get the text prefix of a response."""
        return self.lines[0]

    @property
    def title_suffix(self) -> str:
        """Get the title suffix of a response."""
        return self._title_parts[-1]

    @property
    def text_suffix(self) -> str:
        """Get the text suffix of a response."""
        return self.lines[-1]

    @property
    def heading_step_index_map(self) -> dict[str, int]:
        """Get the heading step index map of a response."""
        heading_stagger = self.heading_indexes[1:] + [self.line_indexes[-1]]
        return {
            i: [k for k in self.step_indexes if i < k < j]
            for i, j in zip(self.heading_indexes, heading_stagger)
        }

    @property
    def heading_step_map(self) -> dict[str, list[str]]:
        """Get the heading step map of a response."""
        return {
            self.lines[i]: [self.lines[k] for k in v]
            for i, v in self.heading_step_index_map.items()
        }

    @property
    def numbered_headings(self) -> list[str]:
        """Get the numbered headings of a response."""
        return [x.strip("*") for x in self.lines if max(y.isnumeric() for y in x)]

    def process_content(self) -> None:
        """Process the content of a response."""
        pass


@dataclass
class TestCase:
    module_name: str
    description: str
    test_cases: list[str]

    def __str__(self) -> str:
        """Get the string of a test case."""
        return f"{self.module_name}: {self.description}\n{self.test_cases}"

    def __repr__(self) -> str:
        """Get the representation of a test case."""
        return str(self)

    def to_dict(self) -> dict[str, str]:
        """Get the dictionary of a test case."""
        return {
            "module_name": self.module_name,
            "description": self.description,
            "test_cases": self.test_cases,
        }

    def to_json(self) -> str:
        """Get the json of a test case."""
        return dumps(self.to_dict())


@dataclass
class TestCasesResponse(LargeLanguageModelResponse):
    """A test cases response is a text file with a title and a body of text."""

    def process_content(self) -> None:
        """Process the content of a response."""
        pass


@dataclass
class PythonResponse(LargeLanguageModelResponse):
    """A python response is a text file with a title and a body of text."""

    def process_content(self) -> None:
        """Process the content of a response."""
        pass
