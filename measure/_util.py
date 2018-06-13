import re


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
