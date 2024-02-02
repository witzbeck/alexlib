"""A response is a text file with a title and a body of text."""
from abc import abstractmethod
from itertools import chain
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

    @abstractmethod
    def process_content(self) -> None:
        """Process the content of a response."""
        pass

    @abstractmethod
    def index_content(self) -> None:
        """Index the content of a response."""
        pass

    @cached_property
    def lines(self) -> list[str]:
        """Get the lines of a response."""
        return [x.strip() for x in self.content.split("\n") if x]

    @property
    def raw_line_index(self) -> dict[str, int]:
        """Get the line index of a response."""
        return {line: i for i, line in enumerate(self.lines)}

    @property
    def line_indices(self) -> list[int]:
        """Get the line indexes of a response."""
        return list(self.raw_line_index.values())

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
        return f"{title.lower().replace(' ', '_')}.md"

    @property
    def title(self) -> str:
        """Get the title of a response."""
        return LargeLanguageModelResponse.get_title_from_path(self.path)

    @cached_property
    def _title_parts(self) -> list[str]:
        """Get the title parts of a response."""
        return self.title.split(" ")

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


@dataclass
class MarkdownResponse(LargeLanguageModelResponse):
    """A markdown response is a text file with a title and a body of text."""

    step_indices: list[int] = field(init=False, repr=False)
    heading_indices: list[int] = field(init=False, repr=False)
    has_steps: bool = field(init=False, repr=False)
    has_headings: bool = field(init=False, repr=False)
    first_content_line_index: int = field(init=False, repr=False)
    last_content_line_index: int = field(init=False, repr=False)
    preface: str = field(init=False, repr=False)
    epilogue: str = field(init=False, repr=False)
    formatted_heading_index: dict[str:int] = field(init=False, repr=False)
    formatted_step_index: dict[str:int] = field(init=False, repr=False)
    heading_step_map: dict[str, int] = field(init=False, repr=False)

    @cached_property
    def all_formatted_steps(self) -> list[str]:
        """Get all formatted steps of a response."""
        return list(self.formatted_step_index.keys())

    @cached_property
    def all_formatted_map_steps(self) -> list[str]:
        """Get all formatted steps of a response."""
        return list(chain.from_iterable(self.heading_step_map.values()))

    @property
    def headingless_steps(self) -> list[str]:
        """Get the headingless steps of a response."""
        return [
            step
            for step in self.all_formatted_steps
            if step not in self.all_formatted_map_steps
        ]

    @staticmethod
    def rm_markdown_chars(text: str) -> str:
        """Remove markdown characters from a string."""
        return text.replace("*", "").replace("#", "").replace("-", "").strip()

    @property
    def step_line_index(self) -> dict[str:int]:
        """Get the step line index of a response."""
        return {
            k: v
            for k, v in self.raw_line_index.items()
            if k[0].isnumeric() or k[0] in "-*"
        }

    @property
    def heading_line_index(self) -> dict[str:int]:
        """Get the heading line index of a response."""
        return {k: v for k, v in self.raw_line_index.items() if k.startswith("#")}

    @property
    def numbered_heading_index(self) -> dict[str:int]:
        """Get the numbered heading index of a response."""
        return {
            k: v
            for k, v in self.heading_line_index.items()
            if max(y.isnumeric() for y in k)
        }

    def index_content(self) -> None:
        """index the content of a response."""
        self.step_indices = list(self.step_line_index.values())
        self.heading_indices = list(self.heading_line_index.values())
        self.has_steps = bool(self.step_indices)
        self.has_headings = bool(self.heading_indices)
        content_indices = self.step_indices + self.heading_indices
        self.first_content_line_index = min(content_indices)
        self.last_content_line_index = max(content_indices)

    def process_content(self) -> None:
        """Process the content of a response."""
        if self.first_content_line_index:
            self.preface = "\n".join(self.lines[: self.first_content_line_index])
        if self.last_content_line_index:
            self.epilogue = "\n".join(self.lines[self.last_content_line_index + 1 :])
        self.formatted_heading_index = {
            self.rm_markdown_chars(k): v for k, v in self.heading_line_index.items()
        }
        self.formatted_step_index = {
            self.rm_markdown_chars(k): v for k, v in self.step_line_index.items()
        }
        self.heading_step_map = {
            heading: [
                step for step, k in self.formatted_step_index.items() if i < k < j
            ]
            for i, j, heading in zip(
                self.heading_indices,
                self.heading_indices[1:] + [self.last_content_line_index],
                self.formatted_heading_index.keys(),
            )
        }
        self.heading_step_map = {k: v for k, v in self.heading_step_map.items() if v}
        self.heading_step_map.update({"Miscellaneous": self.headingless_steps})

    def __post_init__(self) -> None:
        """Post init."""
        self.index_content()
        self.process_content()

    @property
    def content_lines(self) -> list[str]:
        """Get the content lines of a response."""
        return self.lines[
            self.first_content_line_index : self.last_content_line_index + 1
        ]

    @property
    def has_numbered_headings(self) -> bool:
        """Check if a response has numbered headings."""
        return bool(self.numbered_heading_index)

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
class TestCaseResponse(MarkdownResponse):
    """A test cases response is a text file with a title and a body of text."""


@dataclass
class PythonResponse(LargeLanguageModelResponse):
    """A python response is a text file with a title and a body of text."""

    def process_content(self) -> None:
        """Process the content of a response."""
        pass
