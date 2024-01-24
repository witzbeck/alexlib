"""A response is a text file with a title and a body of text."""
from pathlib import Path
from dataclasses import dataclass, field
from functools import cached_property

ml_path = Path(__file__).parent
proj_path = ml_path.parent
db_path = proj_path / "db"
DB_TEST_CASES = "db_test_cases.txt"
db_test_cases_path = db_path / DB_TEST_CASES
SDE_FILENAME = "how_to_build_a_symbolic_deductive_engine.txt"

symbolic_deductive_engine_path = ml_path / SDE_FILENAME


@dataclass(frozen=True)
class Response:
    """A response is a text file with a title and a body of text."""

    path: str = field(repr=False)

    @property
    def haspath(self) -> bool:
        """Check if a response has a path."""
        return self.path is not None

    @staticmethod
    def get_title_from_filename(filename: str) -> str:
        """Get the title of a response from its filename."""
        return filename.replace("_", " ").replace(".txt", "")

    @staticmethod
    def get_title_from_path(path: str) -> str:
        """Get the title of a response from its path."""
        return Response.get_title_from_filename(Path(path).name)

    @staticmethod
    def get_filename_from_title(title: str) -> str:
        """Get the filename of a response from its title."""
        return title.replace(" ", "_") + ".txt"

    @property
    def title(self) -> str:
        """Get the title of a response."""
        return Response.get_title_from_path(self.path)

    @property
    def text(self) -> str:
        """Get the text of a response."""
        return self.path.read_text()

    def __repr__(self) -> str:
        """Get the representation of a response."""
        return f"{self.title}\n{self.text}"

    @cached_property
    def _title_parts(self) -> list[str]:
        """Get the title parts of a response."""
        return self.title.split(" ")

    @cached_property
    def lines(self) -> list[str]:
        """Get the lines of a response."""
        return [x.strip() for x in self.text.split("\n") if x]

    @cached_property
    def line_indexes(self) -> list[int]:
        """Get the line indexes of a response."""
        return [self.lines.index(x) for x in self.lines]

    @cached_property
    def line_index(self) -> dict[str, int]:
        """Get the line index of a response."""
        return dict(zip(self.lines, self.line_indexes))

    @cached_property
    def headings(self) -> list[str]:
        """Get the headings of a response."""
        return [x for x in self.lines if x.startswith("#")]

    @cached_property
    def step_lines(self) -> list[str]:
        """Get the step lines of a response."""
        return [x for x in self.lines if x.startswith("-")]

    @cached_property
    def step_indexes(self) -> list[int]:
        """Get the step indexes of a response."""
        return [self.lines.index(x) for x in self.step_lines]

    @property
    def numbered_headings(self) -> list[str]:
        """Get the numbered headings of a response."""
        return [x.strip("*") for x in self.lines if max(y.isnumeric() for y in x)]

    @cached_property
    def heading_indexes(self) -> list[int]:
        """Get the heading indexes of a response."""
        return [self.lines.index(x) for x in self.headings]

    @cached_property
    def heading_step_index_map(self) -> dict[str, int]:
        """Get the heading step index map of a response."""
        heading_stagger = self.heading_indexes[1:] + [self.line_indexes[-1]]
        return {
            i: [k for k in self.step_indexes if i < k < j]
            for i, j in zip(self.heading_indexes, heading_stagger)
        }

    @cached_property
    def heading_step_map(self) -> dict[str, list[str]]:
        """Get the heading step map of a response."""
        return {
            self.lines[i]: [self.lines[k] for k in v]
            for i, v in self.heading_step_index_map.items()
        }

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
