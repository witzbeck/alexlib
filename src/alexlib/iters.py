"""
This module provides various utility functions for list manipulation and combination generation.
It includes functionalities to flatten a list of lists, generate index combinations for an ndarray shape,
produce combinations of elements from a list, iterate through list items in a specific order,
and manipulate elements based on certain conditions.

Each function is designed to offer flexibility and convenience for various list manipulation tasks,
ranging from simple list flattening to more complex operations like index mapping and pattern removal.
"""

from collections.abc import Generator
from itertools import combinations as comb
from itertools import product
from random import randint
from typing import Any


def idx_list(shape: tuple[int]) -> list[tuple[int, ...]]:
    """returns a list of all indices for the shape of an ndarray"""
    return list(product(range(x) for x in shape))


def get_comb_gen(list_: list, int_: int) -> Generator[tuple, None, None]:
    """returns a generator for all combinations of a list"""
    for pair in comb(list_, int_):
        yield pair


def get_pop_item(item: str, list_: list) -> str:
    """returns an item from a list and removes it from the list"""
    return list_.pop(list_.index(item))


def get_pop_rand_item(list_: list) -> Any:
    """returns a random item from a list and removes it from the list"""
    return list_.pop(randint(0, len(list_) - 1))


def rm_pattern(list_of_strs: list, pattern: str, end: bool = True) -> list:
    """removes all strings from a list that contain a pattern"""
    if end is True:
        p_len = -len(pattern)
        ret = [x for x in list_of_strs if x[p_len:] != pattern]
    else:
        p_len = len(pattern)
        ret = [x for x in list_of_strs if x[:p_len] != pattern]
    return ret
