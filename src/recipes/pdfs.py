"""PDF utilities for Cookbook"""

from collections.abc import Generator
from dataclasses import dataclass, field
from re import match

from reportlab.lib.fonts import _tt2ps_map
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen.canvas import Canvas


@dataclass
class Font:
    """A font"""

    name: str = field(default="times")
    size: int = field(default=12)

    @staticmethod
    def _get_ps_name(name: str, bold: bool, italic: bool) -> str:
        """Returns the PostScript name for the font"""
        return _tt2ps_map[(name, bold, italic)]

    def __iter__(self) -> Generator[str, int, None]:
        """Returns the font as a tuple"""
        yield self.ps_name
        yield self.size

    @property
    def ps_name(self) -> str:
        """Returns the PostScript name for the font"""
        return Font._get_ps_name(self.name, False, False)

    @property
    def bold(self) -> str:
        """Returns the PostScript name for the bold font"""
        return Font._get_ps_name(self.name, True, False)

    @property
    def italic(self) -> str:
        """Returns the PostScript name for the italic font"""
        return Font._get_ps_name(self.name, False, True)

    @property
    def bold_italic(self) -> str:
        """Returns the PostScript name for the bold italic font"""
        return Font._get_ps_name(self.name, True, True)


@dataclass
class RecipeOutput:
    """A recipe output"""

    text: str = field(repr=False)
    name: str = field()
    font: Font = field(default_factory=Font, repr=False)
    pagesize: tuple[int, int] = field(default=letter, repr=False)
    base_margin: int = field(default=72, repr=False)
    line_height: int = field(default=14, repr=False)
    canvas: Canvas = field(init=False, repr=False)

    @property
    def lines(self) -> list[str]:
        """Returns the lines of the recipe"""
        return [x for x in self.text.split("\n") if x]

    @property
    def filename(self) -> str:
        """Returns the filename"""
        return f"{self.name}.pdf" if not self.name.endswith(".pdf") else self.name

    def __post_init__(self) -> None:
        """Initializes the canvas"""
        self.canvas = Canvas(self.filename, pagesize=self.pagesize)

    @property
    def page_height(self) -> int:
        """Returns the page height"""
        return self.pagesize[1]

    def draw_line(
        self,
        line: str,
        current_height: int,
        margin: int = 0,
    ) -> int:
        """Draws a line on the canvas"""
        istitle = line.startswith("###")
        islistitem = line.startswith("- ")
        isnumbereditem = match(r"^\d+\.", line)

        line_step = self.line_height * 2 if istitle else self.line_height
        margin += 10 if islistitem or isnumbereditem else 0
        size = self.font.size + 2 if istitle else self.font.size
        drawfunc = self.canvas.drawString

        if ":**" in line:
            idx = line.index(":**") + 3
            sublines = line[idx:].split(". ")
            line = line[:idx].strip("*").strip(":")
            margin += 10
            for subline in sublines:
                towrite = subline if subline.endswith(".") else subline + "."
                self.canvas.setFont(*self.font.astuple)
                self.canvas.drawString(margin, current_height, towrite)
                current_height -= line_step

        if istitle:
            line = line.strip("# ")
            self.canvas.setFont(self.font.bold, size)
        elif isnumbereditem:
            self.canvas.setFont(self.font.bold, size)
        elif islistitem:
            self.canvas.setFont(self.font.bold_italic, size)
        else:
            self.canvas.setFont(*tuple(self.font))
        line = line.strip("*")
        drawfunc(margin, current_height, line)
        current_height -= line_step
        return current_height

    def draw(self) -> None:
        """Draws the recipe on the canvas"""
        current_height = self.page_height - self.base_margin
        for line in self.lines:
            margin = self.base_margin
            if current_height < self.base_margin:
                self.canvas.showPage()
                current_height = self.page_height - self.base_margin
            current_height = self.draw_line(line, current_height, margin=margin)
        self.canvas.save()


def export_recipe_to_pdf(
    recipe_text: str,
    filename: str,
) -> None:
    """Exports a recipe to a PDF file"""
    recipe = RecipeOutput(recipe_text, filename)
    recipe.draw()
