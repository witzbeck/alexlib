

def invert_dict(_dict: dict):
    rng = range(len(_dict))
    vals = list(_dict.values())
    return {vals[i]: _dict[vals[i]] for i in rng}
