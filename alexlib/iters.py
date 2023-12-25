from itertools import combinations as comb, chain, product
from typing import Any
from random import randint


def link(lists: list[list]):
    """creates a single list from a list of lists"""
    return list(chain.from_iterable(lists))


def keys(_dict: dict):
    """returns the keys of a dictionary as a list"""
    return list(_dict.keys())


def vals(_dict: dict):
    """returns the values of a dictionary as a list"""
    return list(_dict.values())


def idx_list(shape: list[int]):
    """returns a list of all indices for the shape of an ndarray"""
    return list(product(range(x) for x in shape))


def get_comb_gen(_list: list, _int: int):
    """returns a generator for all combinations of a list"""
    for pair in comb(_list, _int):
        yield pair


def list_gen(_list: list, rand: bool = False, inf: bool = False):
    """returns a generator for a list of items
    - if rand is True, the items are returned in random order
    - if inf is True, the items can be returned infinitely
    """
    _list = list(_list)
    while True:
        _len = len(_list)
        if _len > 0:
            _idx = randint(_len) if rand else 0
            if inf:
                yield _list[_idx]
            else:
                yield _list.pop(_idx)
        else:
            break


def get_pop_item(item: str, _list: list):
    """returns an item from a list and removes it from the list"""
    return _list.pop(_list.index(item))


def get_pop_rand_item(_list: list):
    """returns a random item from a list and removes it from the list"""
    return _list.pop(randint(len(_list)))


def rm_pattern(list_of_strs: list, pattern: str, end: bool = True):
    """removes all strings from a list that contain a pattern"""
    if end is True:
        p_len = -len(pattern)
        return [x for x in list_of_strs if x[p_len:] != pattern]
    else:
        p_len = len(pattern)
        return [x for x in list_of_strs if x[:p_len] != pattern]


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
