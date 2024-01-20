"""PDF utilities for Cookbook"""

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

    def __iter__(self) -> tuple[str, int]:
        """Returns the font as a tuple"""
        yield self.ps_name
        yield self.size

    @property
    def astuple(self) -> tuple[str, int]:
        """Returns the font as a tuple"""
        return tuple(self)

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
            self.canvas.setFont(*self.font.astuple)
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


RECIPE = """
### Classic Homemade White Bread

#### Ingredients

- 3 cups all-purpose flour, plus extra for dusting
- 1 packet (2¼ tsp) active dry yeast
- 1 cup warm water (around 110°F or 45°C)
- 2 tablespoons sugar
- 1 tablespoon salt
- 2 tablespoons unsalted butter, softened
- Optional: 1 egg (for egg wash)

#### Instructions

1. **Activate the Yeast:** In a large bowl, dissolve the sugar in warm water. Sprinkle yeast over the top and let it sit for about 10 minutes, until it becomes frothy.

2. **Make the Dough:** Add salt, butter, and flour to the yeast mixture. Mix until a shaggy dough forms. Knead the dough on a floured surface for about 8-10 minutes, until it's smooth and elastic.

3. **First Rise:** Place the dough in a lightly oiled bowl, turning it once to coat all sides with oil. Cover with a damp cloth and let it rise in a warm place for about 1 hour, or until it doubles in size.

4. **Shape the Bread:** Punch down the dough and turn it out onto a lightly floured surface. Shape it into a loaf and place it in a greased 9x5 inch loaf pan.

5. **Second Rise:** Cover the loaf and let it rise for about 30 minutes, or until it puffs up just above the rim of the pan.

6. **Preheat Oven:** Preheat your oven to 375°F (190°C).

7. **Optional Egg Wash:** If desired, lightly beat an egg with a tablespoon of water and brush it over the top of the loaf. This gives the bread a beautiful golden crust.

8. **Bake:** Bake for about 30 minutes, or until the bread is golden brown and sounds hollow when tapped on the bottom.

9. **Cool:** Remove the bread from the oven and let it cool in the pan for a few minutes. Then, transfer it to a wire rack to cool completely.

10. **Slice and Serve:** Slice the bread and serve it warm, or store it in an airtight container for up to 3 days. Enjoy!

#### Notes

- **Yeast:** If you're using instant yeast, you can skip the first step and add the yeast directly to the flour. You may also need to reduce the rise times by 10-15 minutes.
- **Flour:** You can use bread flour instead of all-purpose flour for a chewier loaf.
- **Butter:** You can use olive oil instead of butter for a dairy-free loaf.
- **Egg Wash:** This is optional, but it gives the bread a beautiful golden crust.
- **Storage:** Store the bread in an airtight container at room temperature for up to 3 days. You can also freeze it for up to 3 months.
- **Serving Suggestions:** This bread is delicious on its own, but it's also great with a pat of butter, a drizzle of honey, or a sprinkle of cinnamon sugar.

"""

if __name__ == "__main__":
    export_recipe_to_pdf(RECIPE, "homemade_bread_recipe.pdf")
