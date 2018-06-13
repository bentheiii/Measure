from typing import Dict, Mapping, Tuple, Union, List, Any, Callable, FrozenSet
from abc import abstractmethod, ABC

from numbers import Real
from collections import Counter
import re
import itertools as it

from ._util import FalseWrapper, split_amount_args


# todo custom amount type

class Unit(ABC):
    """
    Abstract class for all types that can serve as units.
    """
    __slots__ = ()

    @abstractmethod
    def __rmul__(self, other: Real):
        """
        convert from unit to arbitrary
        :param other: the value in this unit
        :return: the value in arbitrary unit
        """
        pass

    @abstractmethod
    def __rtruediv__(self, other):
        """
        convert from arbitrary to unit
        :param other: the value in arbitrary unit
        :return: the value in this unit
        """
        pass

    @classmethod
    def __subclasshook__(cls, c):
        """
        all types that implement Unit's abstract methods are unit
        """
        if cls is Unit:
            return all(getattr(c, m, None) is not None for m in ("__rmul__", "__rtruediv__",)) or NotImplemented
        return NotImplemented

    @classmethod
    def register(cls, *args):
        # this is just to the type checker doesn't break
        return type(cls).register(cls, *args)


Unit.register(Real)


def _combine_maps(func: Callable[..., int], *maps: Mapping[Any, int], default=0) -> Counter:
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


class Measure(ABC):
    """
    An abstract base class for measures
    """
    __slots__ = ()

    @abstractmethod
    def __getitem__(self, item: str) -> Unit:
        """
        Get the coefficient of a unit
        :param item: the unit to get the coefficient of.
        :return: the coefficient of the unit
        """
        pass

    @abstractmethod
    def __contains__(self, item) -> bool:
        """
        whether the unit exists in the measure
        :param item: the unit to check for
        :return: whether or not the measure contains the unit
        """
        pass

    @abstractmethod
    def __primitives__(self) -> Counter:
        """
        :return: A counter to represent the factorization of the measure. Each key in the counter must be a Basic Measure (or like)
        the returned value not be mutated
        """
        pass

    @abstractmethod
    def native_unit(self) -> str:
        """
        A default unit to use for the measure when one is absent
        :return:
        """
        pass

    @abstractmethod
    def root(self, r) -> 'Measure':
        """
        perform a root operation on the measure
        :param r: the inverse power to apply to the measure
        :return: a new measure, if raised to r, must return self.
        """
        pass

    def __mul__(self, other: 'Measure'):
        """
        Multiply the measure by another measure
        :param other: another measure
        :return: a compound measure combining the primitives for both measures
        """
        primitives = _combine_maps(lambda x, y: x + y, self.__primitives__(), other.__primitives__())
        return DerivedMeasure(primitives)

    def __truediv__(self, other: 'Measure'):
        """
        Divide the measure by another measure
        :param other: another measure
        :return: a compound measure combining the primitives for both measures
        """
        primitives = _combine_maps(lambda x, y: x - y, self.__primitives__(), other.__primitives__())
        return DerivedMeasure(primitives)

    def __pow__(self, power: Union[int, Real]):
        """
        raise the measure to an integer power or a root
        :param power: the power to raise the measure by
        :return: a compound measure with self raised to a power
        """
        if power not in [0, 1, -1] and (1 / power) % 1 == 0:
            return self.root(int(1 / power))
        primitives = _combine_maps(lambda x: x * power, self.__primitives__())
        return DerivedMeasure(primitives)

    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = 1) -> 'Measurement':
        """
        Create a measurement
        :param unit: the unit of the measurement
        :param amount: the amount of the measured unit
        :return: a new measurement of the appropriate amount
        """
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount

        if unit is not None:
            amount *= self[unit]
        return self.__measurement__(amount)

    def __getattr__(self, item):
        """
        A convenience function to retrieve a 1-unit measurement
        :param item: the name of the unit to get a measurement of
        :return: a 1-amount measurement of the unit
        """
        return self(item, 1)

    def __invert__(self):
        """
        :return: an inverse measure of this measure
        """
        return ScalarMeasure() / self

    def __rtruediv__(self, other: int):
        """
        Convinience function to invert a measure by dividing 1 by it
        :param other: the number 1
        :exception NotImplementedError: if other is anything but the value 1
        :return: ~self
        """
        if other != 1:
            raise NotImplementedError()
        return ~self

    def __measurement__(self, amount):
        """
        create a measurement of an amount in arbitrary units
        :param amount: the amount in arbitrary units
        :return: a measurement of the specified amount
        """
        return Measurement(amount, self)

    def aggregate(self) -> 'AggregateMeasure':
        """
        :return:
        """
        return self.__aggregate__()

    def __aggregate__(self):
        """
        prepare and get the aggregate measure for this measure
        :return: the aggregate measure for this measure
        """
        return BasicAggregateMeasure(self)


class ScalarMeasure(Measure, int):
    """
    A measure representing scalar values, is treated as the integer 1. Is memoized as a singleton.
    """
    __slots__ = ()

    singleton = None

    def __new__(cls):
        if not cls.singleton:
            cls.singleton = int.__new__(cls, 1)
        return cls.singleton

    def __getitem__(self, item):
        """
        A singleton has no keys
        """
        raise KeyError(item)

    def __contains__(self, item):
        """
        A singleton has no keys
        :return: False
        """
        return False

    def __primitives__(self):
        """
        :return: an empty counter
        """
        return Counter()

    def native_unit(self):
        """
        :return: None
        """
        return None

    def __repr__(self):
        return f'{type(self).__name__}()'

    def root(self, r):
        """
        Scalar is its own root for all int roots
        :return: self
        """
        return self


class MutableMeasure(Measure):
    """
    A subclass of measure allowing for assigning new units
    """

    @abstractmethod
    def __setitem__(self, key, value):
        """
        set a new unit with a coefficient
        :param key: the name of the unit
        :param value: the new coefficient, or the name of a unit to create an alias,
        or a tuple of both a coefficient and a unit to create a facored alias.
        """
        pass

    def update(self, *mappings: Mapping, **kwargs):
        """
        Update a Measure, much like a mapping
        :param mappings: mappings to assign each element of as units.
        :param kwargs: additional units to assign
        :return: self, for piping
        """
        for m in it.chain(mappings, (kwargs,)):
            for k, v in m.items():
                self[k] = v
        return self

    def optimize_aliases(self):
        """
        optimize unit call, reducing all aliases to their alias's value
        :return: self, for piping
        """
        for k, v in self._dict.items():
            if not isinstance(v, Real):
                self._dict[k] = self[k]
        return self


class BasicMeasure(MutableMeasure):
    """
    Basic, atomic measures. Building blocks for other measures.
    """
    __slots__ = ('_name', '_dict')

    def __init__(self, name: str, **units: Union[Real, str, Tuple[Real, str]]):
        """
        constructor
        :param name: the name of the measure
        :param units: units for the measure to set at initialization
        """
        self._name = name
        self._dict = units

    def __setitem__(self, key: str, value: Union[Real, str, Tuple[Real, str]]):
        self._dict[key] = value

    def __getitem__(self, item):
        if isinstance(item, Measurement):
            if item.measure != self:
                raise ValueError(f'cannot accept measurement of unit {item}')
            return item.amount
        a, item = split_amount_args(item, default_amount=None)
        if a is not None:
            return a * self[item]
        ret = self._dict[item]
        if isinstance(ret, str):
            return self[ret]

        try:
            amount, unit = ret
        except (ValueError, TypeError):
            pass
        else:
            return amount * self[unit]

        return ret

    def __contains__(self, item):
        return item in self._dict

    def __primitives__(self):
        return Counter({self: 1})

    def __str__(self):
        return self._name

    def native_unit(self):
        return next(iter(self._dict))

    def root(self, r):
        if r == 1:
            return self
        raise ValueError('cannot get root of primitive unit')


class DerivedMeasure(MutableMeasure):
    """
    A compounding of multiple basic units
    """
    __slots__ = ('_parts', '_aliases', '_name')

    composite_measurement_pattern = re.compile(
        r'(?P<pos>(([a-zA-Z]+((\^|(\*\*)|())[1-9][0-9]*)?)(\s*\*?\s*[a-zA-Z]+((^|(\*\*)|())[1-9][0-9]*)?)*)|1)'
        r'(\s*\/\s*(?P<neg>([a-zA-Z]+((\^|(\*\*)|())[1-9][0-9]*)?)(\s*\*?\s*[a-zA-Z]+((^|(\*\*)|())[1-9][0-9]*)?)*))?'
    )
    measurement_pattern = re.compile(r'((?P<name>[a-zA-Z]+)((\^|(\*\*)|())(?P<num>[1-9][0-9]*))?)')
    cache: Dict[FrozenSet[Tuple[BasicMeasure, int]], 'DerivedMeasure'] = {}

    @staticmethod
    def _fix_counter(c: Mapping[BasicMeasure, int]) -> FrozenSet[Tuple[BasicMeasure, int]]:
        return frozenset(c.items())

    def __new__(cls, parts: Counter):
        parts_key = cls._fix_counter(parts)
        if not parts_key:
            return ScalarMeasure()
        if len(parts_key) == 1 and next(iter(parts_key))[1] == 1:
            return next(iter(parts_key))[0]

        try:
            return cls.cache[parts_key]
        except KeyError:
            pass

        ret = super().__new__(cls)
        cls.cache[parts_key] = ret
        return ret

    def __init__(self, parts: Counter):
        """
        constructor
        :param parts: the counter of primitive units. must not contain any zero-valued items
        """
        self._parts = parts
        self._aliases: Dict[str, Tuple[Real, str]] = {}
        self._name = None

    def __primitives__(self):
        return self._parts

    def __contains__(self, item) -> Union[FalseWrapper, List[Tuple[BasicMeasure, int, str]]]:
        """
        if called directly, __contains__ returns an assignemt dictionary, mapping each part of the measure to a
        valid unit, or a FalseWrapper, wrapping an exception if matching failed.
        """
        if item in self._aliases:
            f, a = self._aliases[item]
            return a in self
        match = self.composite_measurement_pattern.fullmatch(item)
        if not match:
            return FalseWrapper(ValueError(f'could not parse string {item!r}'))
        pos, neg = match.group('pos'), match.group('neg')
        assigned = []
        left = dict(self._parts)
        try:
            self._assign_measurements(pos, 1, assigned, left)
            self._assign_measurements(neg, -1, assigned, left)
        except KeyError as e:
            return FalseWrapper(e)

        for p, n in left.items():
            if n > 0:
                return FalseWrapper(KeyError(f'unit {p} unassigned'))

        return assigned

    @classmethod
    def _assign_measurements(cls, part: str, factor: int, assigned: List[Tuple[BasicMeasure, int, str]],
                             left: Dict[BasicMeasure, int]):
        if part is None or part == '1':
            return
        matches = cls.measurement_pattern.finditer(part)
        for m in matches:
            num = m.group('num')
            num = int(num) if num else 1
            num *= factor
            name = m.group('name')
            for p in (k for (k, n) in left.items() if n >= num):
                if name in p:
                    assigned.append((p, num, name))
                    left[p] -= num
                    assert left[p] >= 0
                    break
            else:
                raise KeyError(name)

    def __getitem__(self, item):
        if isinstance(item, Measurement):
            if item.measure != self:
                raise ValueError(f'cannot accept measurement of unit {item}')
            return item.amount
        a, i = split_amount_args(item, default_amount=None)
        if a is not None:
            return a * self[i]

        if item in self._aliases:
            a = self._aliases[item]
            if isinstance(a, str):
                f = 1
            else:
                f, a = a
            return f * self[a]
        assigned = self.__contains__(item)

        if not assigned:
            raise assigned()
        factor = 1
        for k, n, m in assigned:
            factor *= (k[m] ** n)

        return factor

    def __setitem__(self, key, value):
        if key == slice(None):
            self._name = value
            return
        self._aliases[key] = value

    def __str__(self):
        if self._name is not None:
            return self._name
        pos = []
        neg = []
        for m, n in self._parts.items():
            if n > 0:
                amount = '' if n == 1 else f'**{n}'
                pos.append(f'{m}{amount}')
            else:
                amount = '' if n == -1 else f'**{-n}'
                neg.append(f'{m}{amount}')
        if not pos:
            pos = ['1']
        return ' * '.join(pos) + '/' + ' * '.join(neg)

    def native_unit(self, compact=False):
        pos = []
        neg = []
        for m, n in self._parts.items():
            if n > 0:
                amount = '' if n == 1 else f'**{n}'
                pos.append(f'{m.native_unit()}{amount}')
            else:
                amount = '' if n == -1 else f'**{-n}'
                neg.append(f'{m.native_unit()}{amount}')
        if not pos:
            pos = ['1']
        separator = '*' if compact else ' * '
        pos = separator.join(pos)
        if not neg:
            return pos
        div = '/' if compact else ' / '
        neg = separator.join(neg)
        return ''.join((pos, div, neg))

    def root(self, r: int):
        if not all(n % r == 0 for n in self._parts.values()):
            raise ValueError(f'cannot get the {r} root of {self}')
        primitives = _combine_maps(lambda x: x / r, self.__primitives__())
        return DerivedMeasure(primitives)


class Measurement:
    """
    A specific measurement of a Measure
    """
    __slots__ = ('amount', 'measure')

    format_pattern = re.compile(
        r'((?P<inner_format>(.?[<>=^])?[-+ ]?#?0?[0-9]*[,_]?(\.[0-9]*)?[eEfFgGn%]?):)?'
        r'(?P<convert>[^|]*)(\|(?P<display>.*))?')

    def _coalesce(self, v, check_measure=True):
        if isinstance(v, Measurement):
            if check_measure and v.measure != self.measure:
                return None
            return v
        if isinstance(v, str) or v == 0:
            return self.measure(v)
        return None

    def __new__(cls, amount, measure):
        if measure is ScalarMeasure():
            return amount
        return super().__new__(cls)

    def __init__(self, amount: Real, measure: Measure):
        """
        constructor
        :param amount: the amount, in arbitrary units
        :param measure: the measure of this measurement
        """
        self.amount = amount
        self.measure = measure

    def __mul__(self, other: Union['Measurement', Real]):
        """
        multiply by either a number, changing the amount,
        or by another measure, changing both the amount and the measure.
        :param other: the number or measure to multiply by.
        :return: a new measure.
        """
        if isinstance(other, Real):
            return type(self)(self.amount * other, self.measure)
        if isinstance(other, Measurement):
            measure = self.measure * other.measure
            amount = self.amount * other.amount
            return type(self)(amount, measure)
        return NotImplemented

    def __truediv__(self, other: Union['Measurement', Real]):
        """
        divide by either a number, changing the amount,
        or by another measure, changing both the amount and the measure.
        :param other: the number or measure to divide by.
        :return: a new measure.
        """
        if isinstance(other, Real):
            return type(self)(self.amount / other, self.measure)
        if isinstance(other, Measurement):
            measure = self.measure / other.measure
            amount = self.amount / other.amount
            return type(self)(amount, measure)
        return NotImplemented

    def __rmul__(self, other: Real):
        return self * other

    def __rtruediv__(self, other: Real):
        """
        invert the measure
        :param other: a number
        :return: other / self
        """
        return type(self)(other / self.amount, ~self.measure)

    def __invert__(self):
        """
        invert the measure
        """
        return 1 / self

    def __pow__(self, power: int):
        """
        raise the measurement to a power, changing both the amount and the measure
        :param power: the power to raise the measurement
        :return: a new measurement
        """
        return type(self)(self.amount ** power, self.measure ** power)

    def __add__(self, other: 'Measurement'):
        """
        Add two measurements of the same measure together
        :param other: another measurement of the same measure
        :return: a new measurement of the same measure
        """
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return type(self)(self.amount + other.amount, self.measure)

    def __sub__(self, other: 'Measurement'):
        """
        Subtract two measurements of the same measure by each other
        :param other: another measurement of the same measure
        :return: a new measurement of the same measure
        """
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return type(self)(self.amount - other.amount, self.measure)

    def __rsub__(self, other):
        return -(self - other)

    def __radd__(self, other):
        return self + other

    def __eq__(self, other: Union['Measurement', int]):
        other = self._coalesce(other, check_measure=False)
        if not other:
            return NotImplemented
        return self.measure == other.measure and self.amount == other.amount

    def __round__(self, measurement: Union[str, 'Measurement']):
        """
        Round a measurement to the nearest unit of the measure
        :param measurement: the measurement or unit to round to
        :return: a new measurement of the same measure
        """
        measurement = self._coalesce(measurement)
        if not measurement:
            return NotImplemented
        amount = measurement.amount
        amount = amount * round(self.amount / amount)
        return type(self)(amount, self.measure)

    def __hash__(self):
        return hash((self.measure, self.amount))

    def __lt__(self, other: Union['Measurement', int]):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return self.amount.__lt__(other.amount)

    def __le__(self, other: Union['Measurement', int]):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return self.amount.__le__(other.amount)

    def __gt__(self, other: Union['Measurement', int]):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return self.amount.__gt__(other.amount)

    def __ge__(self, other: Union['Measurement', int]):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        return self.amount.__ge__(other.amount)

    def __getitem__(self, item):
        """
        Get the measurement's amount in a specific unit
        :param item: the unit to measure in
        :return: the amount of the measurement, as a number
        """
        return self.amount / self.measure[item]

    def __repr__(self):
        return format(self, '')

    def __format__(self, format_spec):
        """
        format the measurement
        the format_spec follows the pattern
        [<decimal format>:][<unit>][|<display unit>]
        decimal format: the format_spec arguments for formatting the amount. defaults to ''
        unit: the unit to measure the measurement in. defaults to native_unit.
        display unit: the unit to display after the amount. defaults to unit.
        """
        match = self.format_pattern.fullmatch(format_spec)
        if not match:
            raise ValueError('could not parse format string ' + format_spec)
        decimal_format, convert, display = match.group('inner_format', 'convert', 'display')
        if not convert:
            convert = self.measure.native_unit()
        if not display:
            display = convert
        if not decimal_format:
            decimal_format = ''
        amount = self[convert]
        return f'{amount:{decimal_format}} {display}'

    def __neg__(self):
        return type(self)(-self.amount, self.measure)

    def __abs__(self):
        return type(self)(abs(self.amount), self.measure)

    def root(self, r: int):
        """
        raise the measurement to a root, changing both the amount and the measure
        :param r: the power to lower the measurement
        :return: a new measurement
        """
        return type(self)(self.amount ** (1 / r), self.measure.root(r))


class AggregateMeasure(ABC):
    """
    An abstract base class for aggregate measures
    """
    __slots__ = ()

    def __getitem__(self, item: str) -> Unit:
        """
        Get the coefficient of a unit
        :param item: the unit to get the coefficient of.
        :return: the coefficient of the unit
        """
        return self.derivative()[item]

    def __contains__(self, item) -> bool:
        """
        whether the unit exists in the measure
        :param item: the unit to check for
        :return: whether or not the measure contains the unit
        """
        return item in self.derivative()

    def native_unit(self) -> str:
        """
        A default unit to use for the measure when one is absent
        :return:
        """
        return self.derivative().native_unit()

    @abstractmethod
    def derivative(self) -> Measure:
        """
        :return: the derivative measure (the delta measure) of this aggregate measure
        """
        pass

    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = None) -> 'AggregateMeasurement':
        """
        Create a measurement
        :param unit: the unit of the measurement
        :param amount: the amount of the measured unit
        :return: a new measurement of the appropriate amount
        """
        if amount is None:
            f, r = split_amount_args(unit, default_amount=None)
            if f is not None:
                unit, amount = r, f
            else:
                raise ValueError('amount must be specified')
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount
        converter = self[unit]
        amount *= converter
        return self.__measurement__(amount)

    def __measurement__(self, amount):
        """
        create a measurement of an amount in arbitrary units
        :param amount: the amount in arbitrary units
        :return: a measurement of the specified amount
        """
        return AggregateMeasurement(amount, self)


class AggregateMeasurement:
    """
        An absolute measurement of a linear measure
        """
    __slots__ = ('measure', 'amount')

    def __init__(self, amount: Real, owner: AggregateMeasure):
        """
        constructor
        :param amount: the amount, in arbitrary units
        :param owner: the LinearMeasure
        """
        self.amount = amount
        self.measure = owner

    def _coalesce_to_delta(self, v, check_measure=True):
        if isinstance(v, Measurement):
            if check_measure and v.measure != self.measure.derivative():
                return None
            return v
        if isinstance(v, str) or (isinstance(v, Real) and v == 0):
            return self.measure.derivative()(v)
        return None

    def _coalesce_to_absolute(self, v, check_measure=True):
        if isinstance(v, AggregateMeasurement):
            if check_measure and v.measure != self.measure:
                return None
            return v
        if isinstance(v, str) or v == 0:
            return self.measure(v)
        return None

    def __add__(self, other: Measurement):
        other = self._coalesce_to_delta(other)
        if not other:
            return NotImplemented
        arb = self.amount + other.amount
        return type(self)(arb, self.measure)

    def __radd__(self, other: Measurement):
        return self + other

    def __sub__(self, other_orig: Union[Measurement, 'AggregateMeasurement']):
        other = self._coalesce_to_delta(other_orig)
        if other:
            arb = self.amount - other.amount
            return type(self)(arb, self.measure)

        other = self._coalesce_to_absolute(other_orig)
        if other:
            arb = self.amount - other.amount
            return self.measure.derivative()(None, arb)
        return NotImplemented

    def __eq__(self, other):
        other = self._coalesce_to_absolute(other)
        return other and other.owner == self.measure and other.amount == self.amount

    def __hash__(self):
        return hash((self.measure, self.amount))

    def __round__(self, measurement):
        measurement = self._coalesce_to_delta(measurement)
        if not measurement:
            raise TypeError("can't handle precision of type")
        amount = measurement.amount
        amount = amount * round(self.amount / amount)
        return type(self)(amount, self.measure)

    def __lt__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        return self.amount.__lt__(other.amount)

    def __le__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        return self.amount.__le__(other.amount)

    def __gt__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        return self.amount.__gt__(other.amount)

    def __ge__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        return self.amount.__ge__(other.amount)

    def __getitem__(self, item):
        return self.amount / self.measure[item]

    def __repr__(self):
        return format(self, '')

    def __format__(self, format_spec):
        match = Measurement.format_pattern.fullmatch(format_spec)
        if not match:
            raise ValueError('could not parse format string ' + format_spec)
        decimal_format, convert, display = match.group('inner_format', 'convert', 'display')
        if not convert:
            convert = self.measure.native_unit()
        if not display:
            display = convert
        if not decimal_format:
            decimal_format = ''
        amount = self[convert]
        return f'{amount:{decimal_format}} {display}'


class BasicAggregateMeasure(AggregateMeasure):
    def __init__(self, derivative: Measure):
        self._derivative = derivative

    def derivative(self):
        return self._derivative
