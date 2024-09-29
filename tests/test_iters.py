from collections.abc import Generator
from random import randint

from pytest import fixture

from alexlib.iters import (
    get_comb_gen,
    get_pop_item,
    get_pop_rand_item,
    idx_list,
)


@fixture(scope="module")
def ndims() -> int:
    return randint(2, 5)


@fixture(scope="module")
def shape(ndims: int) -> list[int]:
    return [randint(2, 5) for _ in range(ndims)]


@fixture(scope="module")
def index_list(shape: list[int]) -> list[tuple[int, ...]]:
    return idx_list(shape)


@fixture(scope="module")
def comb_gen() -> Generator[tuple, None, None]:
    return get_comb_gen(list(range(10)), 3)


@fixture(scope="function")
def to_pop_list() -> list:
    return list(range(10))


@fixture(scope="function")
def pop_list_copy(to_pop_list: list):
    return to_pop_list.copy()


@fixture(scope="function")
def popped_item(to_pop_list: list):
    return get_pop_item(to_pop_list[randint(0, len(to_pop_list) - 1)], to_pop_list)


@fixture(scope="function")
def popped_rand_item(to_pop_list: list):
    return get_pop_rand_item(to_pop_list)


def test_idx_list(index_list: list[tuple[int, ...]], ndims: int):
    assert len(index_list) == ndims
    assert all(isinstance(x, (tuple, int)) for x in index_list)


def test_comb_gen(comb_gen: Generator[tuple, None, None]):
    assert len(list(comb_gen)) == 120


def test_get_pop_item(to_pop_list: list, pop_list_copy: list, popped_item: int):
    assert popped_item not in to_pop_list
    assert popped_item in pop_list_copy


def test_get_pop_rand_item(
    to_pop_list: list, pop_list_copy: list, popped_rand_item: int
):
    assert popped_rand_item not in to_pop_list
    assert popped_rand_item in pop_list_copy
