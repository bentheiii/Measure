from typing import Mapping, Any, Callable
import re
import itertools as it
from collections import Counter


class FalseWrapper:
    def __init__(self, v):
        self.v = v

    def __bool__(self):
        return False

    def __call__(self):
        return self.v


_float_args_pattern = re.compile(r'^(?P<float>[-+]?[0-9,]*(\.[0-9]*)?([eE][-+]?[0-9]+)?)\s+(?P<meas>.*)')


def split_amount_args(arg, default_amount=1):
    match = _float_args_pattern.fullmatch(arg)
    if match and match.group('float'):
        return float(match.group('float').replace(',', '')), match.group('meas')
    return default_amount, arg


def minimal_class(types, default=None):
    '''
    >>> assert minimal_class([bool]) is bool
    >>> assert minimal_class([bool, int]) is bool
    >>> assert minimal_class([object,bool,int]) is bool
    >>> assert minimal_class([int, float]) is None
    '''
    types = set(types)
    if len(types) == 1:
        return types.pop()
    for c in types:
        if all(c == t or issubclass(c, t) for t in types):
            return c
    return default


def combine_maps(func: Callable[..., int], *maps: Mapping[Any, int], default=0) -> Counter:
    keys = it.chain(*(m.keys() for m in maps))
    ret = Counter()
    for k in keys:
        if k in ret:
            continue
        args = (m.get(k, default) for m in maps)
        v = func(*args)
        if v != default:
            ret[k] = v
    return ret


if __name__ == '__main__':
    import doctest

    doctest.testmod()
