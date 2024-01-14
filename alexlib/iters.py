"""
This module provides various utility functions for list manipulation and combination generation.
It includes functionalities to flatten a list of lists, generate index combinations for an ndarray shape,
produce combinations of elements from a list, iterate through list items in a specific order,
and manipulate elements based on certain conditions.

Functions:
    link(lists: list[list]) -> list:
        Flattens a list of lists into a single list.

    idx_list(shape: list[int]) -> list[tuple[int, ...]]:
        Generates all possible index tuples for a given ndarray shape.

    get_comb_gen(_list: list, _int: int) -> tuple:
        Yields all possible combinations of a given size from a list.

    list_gen(_list: list, rand: bool = False, inf: bool = False) -> Any:
        Generates items from a list. Can return items in random order or infinitely.

    get_pop_item(item: str, _list: list) -> str:
        Removes a specified item from a list and returns it.

    get_pop_rand_item(_list: list) -> Any:
        Removes and returns a random item from a list.

    rm_pattern(list_of_strs: list, pattern: str, end: bool = True) -> list:
        Removes strings from a list that contain a specified pattern.

    get_idx_val(idx_counter: int, in_val: Any, in_list: list[Any], out_list: list[Any]) -> Any:
        Returns the value from one list at the index corresponding to an element's position in another list.

Each function is designed to offer flexibility and convenience for various list manipulation tasks,
ranging from simple list flattening to more complex operations like index mapping and pattern removal.
"""
from itertools import chain
from itertools import combinations as comb
from itertools import product
from random import randint
from typing import Any


def link(lists: list[list]) -> list:
    """creates a single list from a list of lists"""
    return list(chain.from_iterable(lists))


def idx_list(shape: list[int]) -> list[tuple[int, ...]]:
    """returns a list of all indices for the shape of an ndarray"""
    return list(product(range(x) for x in shape))


def get_comb_gen(_list: list, _int: int) -> tuple:
    """returns a generator for all combinations of a list"""
    for pair in comb(_list, _int):
        yield pair


def list_gen(_list: list, rand: bool = False, inf: bool = False) -> Any:
    """returns a generator for a list of items
    - if rand is True, the items are returned in random order
    - if inf is True, the items can be returned infinitely
    """
    _list = list(_list)
    while True:
        _len = len(_list)
        if _len > 0:
            _idx = randint(0, _len) if rand else 0
            if inf:
                yield _list[_idx]
            else:
                yield _list.pop(_idx)
        else:
            break


def get_pop_item(item: str, _list: list) -> str:
    """returns an item from a list and removes it from the list"""
    return _list.pop(_list.index(item))


def get_pop_rand_item(_list: list) -> Any:
    """returns a random item from a list and removes it from the list"""
    return _list.pop(randint(0, len(_list)))


def rm_pattern(list_of_strs: list, pattern: str, end: bool = True) -> list:
    """removes all strings from a list that contain a pattern"""
    if end is True:
        p_len = -len(pattern)
        ret = [x for x in list_of_strs if x[p_len:] != pattern]
    else:
        p_len = len(pattern)
        ret = [x for x in list_of_strs if x[:p_len] != pattern]
    return ret


def get_idx_val(
    idx_counter: int,
    in_val: Any,
    in_list: list[Any],
    out_list: list[Any],
) -> Any:
    """returns the value of the out_list
    at the index of the in_val in the in_list"""
    idx = in_list.index(in_val, idx_counter)
    return out_list[idx]
