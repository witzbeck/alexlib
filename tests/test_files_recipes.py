from pathlib import Path

from pytest import FixtureRequest, fixture

from alexlib.constants import RECIPES_PATH
from recipes import Recipe, RecipeBase
from recipes.pdfs import Font


@fixture(
    scope="module",
    params=("chocolate_chip_cookies.json", "pizza_crust.json", "white_bread.json"),
)
def recipe_json_path(request: FixtureRequest):
    return RECIPES_PATH / request.param


@fixture(scope="module")
def recipe(recipe_json_path: Path):
    return Recipe.from_json(recipe_json_path)


@fixture(scope="module")
def recipe_and_pdf_path(recipe: Recipe, temp_dir: Path):
    return recipe, temp_dir / f"{recipe.name}.pdf"


@fixture(scope="module")
def recipe_base(recipe: Recipe):
    return RecipeBase(name=recipe.name)


def test_recipe_path_is_file(recipe_json_path: Path):
    assert recipe_json_path.exists()
    assert recipe_json_path.is_file()


def test_recipe_is_recipe(recipe: Recipe):
    assert isinstance(recipe, Recipe)


def test_recipe_base_is_recipe_base(recipe_base: RecipeBase):
    assert isinstance(recipe_base, RecipeBase)


def test_recipe_base_string_method(recipe_base: RecipeBase):
    assert str(recipe_base)


def test_recipe_base_name(recipe_base: RecipeBase):
    assert recipe_base.name
    assert isinstance(recipe_base.name, str)


def test_recipe_name(recipe: Recipe):
    assert recipe.name
    assert isinstance(recipe.name, str)


def test_recipe_and_pdf_path(recipe_and_pdf_path: tuple[Recipe, Path]):
    recipe, pdf_path = recipe_and_pdf_path
    assert recipe.name in pdf_path.stem
    assert pdf_path.suffix == ".pdf"
    recipe.to_pdf(pdf_path)
    assert pdf_path.exists()


@fixture(scope="module")
def font():
    return Font()


def test_font_is_font(font: Font):
    assert isinstance(font, Font)


def test_font_has_name(font: Font):
    assert font.name


def test_font_has_size(font: Font):
    assert font.size


def test_font_as_tuple(font: Font):
    assert isinstance(tuple(font), tuple)


def test_font_ps_name(font: Font):
    assert font.ps_name


def test_font_bold(font: Font):
    assert font.bold


def test_font_italic(font: Font):
    assert font.italic


def test_font_bold_itelic(font: Font):
    assert font.bold_italic
