from pathlib import Path

from pytest import FixtureRequest, fixture

from alexlib.constants import RECIPES_PATH
from alexlib.files.recipe import Recipe, RecipeBase


@fixture(scope="module")
def cookie_path():
    return RECIPES_PATH / "chocolate_chip_cookies.json"


@fixture(scope="module")
def cookie_recipe(cookie_path: Path):
    return Recipe.from_json(cookie_path)


@fixture(scope="module")
def cookie_base(cookie_recipe: Recipe):
    return RecipeBase(name=cookie_recipe.name)


@fixture(scope="module", params=("Chocolate", "Chip", "Cookie"))
def cookie_name(request: FixtureRequest):
    return request.param


def test_cookie_path_is_file(cookie_path: Path):
    assert cookie_path.exists()
    assert cookie_path.is_file()


def test_cookie_recipe_is_recipe(cookie_recipe: Recipe):
    assert isinstance(cookie_recipe, Recipe)


def test_cookie_base_is_recipe_base(cookie_base: RecipeBase):
    assert isinstance(cookie_base, RecipeBase)


def test_cookie_base_string_method(cookie_base: RecipeBase):
    assert str(cookie_base)


def test_cookie_base_name_parts(cookie_base: RecipeBase, cookie_name: str):
    assert cookie_name in cookie_base.name


def test_cookie_recipe_name_parts(cookie_recipe: Recipe, cookie_name: str):
    assert cookie_name in cookie_recipe.name
