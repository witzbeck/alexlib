from itertools import combinations as comb, chain
from pathlib import Path
from os import getenv

from dotenv import load_dotenv
from matplotlib.pyplot import savefig
from numpy import array
from numpy.random import randint

from pandas import DataFrame, Series

here = Path(__file__).parent.parent


def set_envs(envname: str):
    return load_dotenv(here / f".env.{envname}")


def keyslist(_dict: dict):
    return list(_dict.keys())


def valslist(_dict: dict):
    return list(_dict.values())


def istrue(w: str):
    return True if w == 'True' else False


def isnone(x: str):
    return True if (x == 'None' or x is None) else False


def set_envint(y: str):
    return None if isnone(y) else int(y)


def set_nrows():
    set_envint(getenv("NROWS"))


def set_rand_state():
    set_envint(getenv("RANDOM_STATE"))


def get_distinct_col_vals(df: DataFrame, col: str):
    return list(df.loc[:, col].unique())


def filter_df(df: DataFrame, col: str, val: str):
    return df[df.loc[:, col] == val]


def series_col(df: DataFrame, col: str):
    return Series(df.loc[:, col])


def idx_list(nrows: int, ncols: int):
    rrng = range(nrows)
    crng = range(ncols)
    return list(chain.from_iterable([[(i, j) for j in crng] for i in rrng]))


def pathsearch(pattern: str, start_path: Path = here):
    while True:
        try:
            return [x for x in start_path.rglob(pattern)][0]
        except IndexError:
            start_path = start_path.parent


def figsave(figname: str,
            figpath: Path = pathsearch("figures"),
            format: str = "png",
            **kwargs,  # use bb_inches=tight if cutoff
            ):
    fullpath = figpath / f"{figname}.{format}"
    savefig(fullpath, format=format, **kwargs)
    return fullpath.exists()


def get_comb_gen(_list: list, _int: int):
    for pair in comb(_list, _int):
        yield pair


def list_gen(_list: list,
             rand: bool = False,
             inf: bool = False
             ):
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


def unpack_clf_keys(params_dict: dict):
    keys = keyslist(params_dict)
    return [x.split("__")[-1] for x in keys]


def unpack_clf_params(params_dict: dict):
    new_keys = unpack_clf_keys(params_dict)
    vals = valslist(params_dict)
    _range = range(len(new_keys))
    return {new_keys[i]: vals[i] for i in _range}


def lengthen_params_log(params_log: dict):
    keys = keyslist(params_log)
    vals = valslist(params_log)
    rg = range(len(keys))
    log = []
    for i in rg:
        val = vals[i]
        if val is None:
            log.append([val])
        elif (valt := type(val)) in [str, float, int, bool]:
            log.append([val])
        elif valt in [list, tuple]:
            log.append(list(val))
        else:
            log.append(val.data.tolist())
    plen = max([len(x) for x in log])
    return {keys[i]: log[i] * plen if len(log[i]) == 1 else log[i] for i in rg}


def overwrite_std_params(clf_params: dict,
                         std_params: dict,
                         all: bool = True
                         ):
    sp = std_params
    np = unpack_clf_params(clf_params)
    keys = keyslist(std_params)
    new_keys = keyslist(np)
    out_params = {key: np[key] if key in new_keys else sp[key] for key in keys}
    if all:
        return lengthen_params_log(out_params)
    else:
        return out_params


def get_props(series: Series):
    dist_vals = list(series.unique())
    n_all_vals = len(series)
    freqs = [sum(series == x) for x in dist_vals]
    props = [sum(series == x) / n_all_vals for x in dist_vals]
    return DataFrame.from_dict(
        {
            "value": dist_vals,
            "frequency": freqs,
            "proportion": props
        })


def make_prop_dict(df: DataFrame):
    non_id_cols = [x for x in df.columns if x[-3:] != "_id"]
    all_series = [Series(df.loc[:, x]) for x in non_id_cols]
    return {col: get_props(col) for col in all_series}


def rm_pattern(list_of_strs: list, pattern: str, end: bool = True):
    if end is True:
        p_len = -len(pattern)
        return [x for x in list_of_strs if x[p_len:] != pattern]
    else:
        p_len = len(pattern)
        return [x for x in list_of_strs if x[:p_len] != pattern]


def wo_ids(x: str):
    return rm_pattern(x, "_id")


def get_pop_item(item: str, _list: list):
    return _list.pop(_list.index(item))


def get_pop_rand_item(_list: list):
    return _list.pop(randint(len(_list)))


def rm_df_col_pattern(pattern: str | tuple | list,
                      df: DataFrame,
                      end: bool = True
                      ) -> DataFrame:
    cols = df.columns
    if (type(pattern) == str and end):
        new_cols = rm_pattern(cols, pattern)
    elif (type(pattern) == str and not end):
        new_cols = rm_pattern(cols, pattern, end=False)
    elif type(pattern) == tuple:
        new_pattern = pattern[0]
        end = pattern[-1]
        new_cols = rm_pattern(cols, new_pattern, end=end)
    elif type(pattern) == list:
        for pat in pattern:
            df = rm_df_col_pattern(pat, df)
        return df
    else:
        raise ValueError("input not recognized")
    return df.loc[:, new_cols]


def percentiles(_list: list, tiles: int = 100):
    _list = list(_list)
    _list.sort(key=lambda x: int(x))
    _len = len(_list)
    out_dict = {}
    tile_ratio = (1 / tiles)
    idx_ratio = _len * tile_ratio

    out_dict['0'] = _list[0]
    for i in range(1, tiles):
        tile_idx = int(i * idx_ratio)
        out_dict[i] = _list[tile_idx]

    out_dict[tiles] = _list[-1]
    return out_dict


def combine_domains(x1: list, x2: list):
    x = list(set(list(x1) + list(x2)))
    domain = x * 2
    domain.sort()
    return array(domain)


def get_list_difs(_list):
    _range = range(len(_list))
    return [_list[i - 1] - _list[i] for i in _range if i > 0]


def get_list_mids(_list: list):
    _range = range(len(_list))
    return [(_list[i - 1] + _list[i]) / 2 for i in _range if i > 0]


def get_rect_area(heights: list,
                  widths: list,
                  absolute: bool = True
                  ):
    _range = range(len(heights))
    rect_areas = [heights[i] * widths[i] for i in _range]
    if absolute:
        return sum([abs(x) for x in rect_areas])
    return sum(rect_areas)


def get_idx_val(idx_counter, in_val, in_list, out_list):
    idx = in_list.index(in_val, idx_counter)
    return out_list[idx]
