"""Recipe objects"""
from dataclasses import dataclass, field
from functools import cached_property
from json import loads
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


@dataclass
class RecipeBase:
    """A recipe core object"""

    name: str = field()
    notes: str | None = field(default=None)
    tags: list[str] = field(default_factory=list, repr=False)

    def __str__(self) -> None:
        return f"{self.name} {self.notes} {self.tags}"

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeBase":
        """Creates a Recipe from a dict"""
        return cls(**data)

    @classmethod
    def from_json(cls, path: Path) -> "RecipeBase":
        """Creates a Recipe from a JSON object"""
        if not path.exists():
            raise FileNotFoundError
        d = loads(path.read_text())
        return cls.from_dict(d)


@dataclass
class Equipment(RecipeBase):
    """Equipment"""

    name: str = field()
    quantity: int | float | str | None = field(default=None)
    size: str | None = field(default=None)

    def __post_init__(self) -> None:
        pass


@dataclass
class Ingredient(RecipeBase):
    """An ingredient"""

    quantity: int | float | str | None = field(default=None)
    unit: str | None = field(default=None)
    type_: str | None = field(default=None)
    prep: str | None = field(default=None)

    def __str__(self) -> None:
        return " ".join(
            [
                x
                for x in [
                    str(self.quantity),
                    self.unit,
                    self.type_,
                    self.prep,
                ]
                if x is not None
            ]
        )


@dataclass
class Recipe(RecipeBase):
    """A recipe"""

    equipment: list[Ingredient] = field(default_factory=list)
    ingredients: list[Ingredient] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    cook_time: int | None = field(default=None)
    prep_time: int | None = field(default=None)
    total_time: int | None = field(default=None)
    servings: int | None = field(default=None)
    source: str | None = field(default=None)
    calories: int | None = field(default=None)

    def __post_init__(self) -> None:
        self.set_ingredients(self.ingredients)
        self.set_equipment(self.equipment)

    @staticmethod
    def split_time(time: str) -> tuple[int, str]:
        """Splits a time string into int and unit"""
        if not time:
            return (None, None)
        number, unit = time.split(" ")
        return (int(number), unit)

    @staticmethod
    def get_equipment(lst: list[dict]) -> list[Equipment]:
        """Parses the raw dict into an ingredient object list"""
        return [Equipment.from_dict(x) for x in lst]

    def set_equipment(self, lst: list[dict]) -> None:
        """Sets the ingredients from a list of dicts"""
        self.equipment = Recipe.get_equipment(lst)

    @staticmethod
    def get_ingredients(lst: list[dict]) -> list[Ingredient]:
        """Parses the raw dict into an ingredient object list"""
        return [Ingredient.from_dict(x) for x in lst]

    def set_ingredients(self, lst: list[dict]) -> None:
        """Sets the ingredients from a list of dicts"""
        self.ingredients = Recipe.get_ingredients(lst)

    @cached_property
    def styles(self) -> dict[str, ParagraphStyle]:
        """Returns the styles"""
        return getSampleStyleSheet()

    @property
    def title_style(self) -> ParagraphStyle:
        """Returns the title style"""
        return self.styles["Title"]

    @property
    def normal_style(self) -> ParagraphStyle:
        """Returns the normal style"""
        return self.styles["Normal"]

    @property
    def title_paragraph(self) -> Paragraph:
        """Returns the title paragraph"""
        return Paragraph(self.name, self.title_style)

    @staticmethod
    def get_paragraph_list(
        lst: list[str],
        style: ParagraphStyle,
    ) -> list[Paragraph]:
        """Returns a list of paragraphs"""
        return [Paragraph(str(x), style) for x in lst]

    @property
    def equipment_paragraph(self) -> list[Paragraph]:
        """Returns the equipment paragraphs"""
        return Recipe.get_paragraph_list(self.equipment, self.normal_style)

    @property
    def steps_paragraph(self) -> list[Paragraph]:
        """Returns the steps paragraphs"""
        return Recipe.get_paragraph_list(self.steps, self.normal_style)

    @property
    def ingredient_paragraph(self) -> list[Paragraph]:
        """Returns the ingredient paragraphs"""
        return Recipe.get_paragraph_list(self.ingredients, self.normal_style)

    def to_pdf(self, path: Path) -> None:
        """Saves the recipe as a PDF"""
        doc = SimpleDocTemplate(path.name)
        elements = []
        elements.append(self.title_paragraph)
        elements.append(Spacer(1, 12))
        elements += self.equipment_paragraph
        elements.append(Spacer(1, 12))
        elements += self.ingredient_paragraph
        elements.append(Spacer(1, 12))
        elements += self.steps_paragraph
        doc.build(elements)


cc_cookies = Recipe.from_json(Path("chocolate_chip_cookies.json"))
print(cc_cookies.name, cc_cookies)
cc_cookies.to_pdf(Path("chocolate_chip_cookies.pdf"))
