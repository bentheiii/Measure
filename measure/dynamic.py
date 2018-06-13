from typing import Union

from numbers import Real

from .measure import BasicMeasure, Measurement, DerivedMeasure
import operator as op
from ._util import combine_maps


class DynamicMeasure(BasicMeasure):
    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = 1) -> 'Measurement':
        """
        Create a measurement
        :param unit: the unit of the measurement
        :param amount: the amount of the measured unit
        :return: a new measurement of the appropriate amount
        """
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount

        return self.__measurement__(amount, unit)

    def __measurement__(self, amount, unit):
        return DynamicMeasurement(amount, unit, self)

    def __derived_type__(self):
        return DynamicDerivedMeasure


class DynamicDerivedMeasure(DerivedMeasure):
    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = 1) -> 'Measurement':
        """
        Create a measurement
        :param unit: the unit of the measurement
        :param amount: the amount of the measured unit
        :return: a new measurement of the appropriate amount
        """
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount

        return self.__measurement__(amount, unit)

    def __measurement__(self, amount, unit):
        return DynamicMeasurement(amount, unit, self)


# todo handle aggregate measures
# todo handle comparisons
class DynamicMeasurement(Measurement):
    __slots__ = 'unit'

    @staticmethod
    def combine_units(op, *measurements: Measurement, default=0, default_for_native=1):
        units = ((({x.unit: 1} if isinstance(x.unit, str) else x.unit) if isinstance(x, DynamicMeasurement) else {
            x.measure.native_unit(): default_for_native}) for x
                 in measurements)
        ret = combine_maps(op, *units, default=default)
        if len(ret) == 1 and next(iter(ret.values())) == 1:
            ret = next(iter(ret.keys()))
        return ret

    def __new__(cls, amount, unit, measure):
        return super().__new__(cls, amount, measure)

    def __init__(self, amount, unit, measure):
        super().__init__(amount, measure)
        self.unit = unit

    def arb(self):
        return self.amount * self.measure[self.unit]

    def __call__(self, item):
        # todo test this
        # todo doc this
        return self.measure(item) * self[item]

    def __getitem__(self, item):
        arb = self.arb()
        return arb / self.measure[item]

    def __mul__(self, other: Union['Measurement', Real]):
        if isinstance(other, Real):
            return type(self)(self.amount * other, self.unit, self.measure)
        if isinstance(other, Measurement):
            measure = self.measure * other.measure
            amount = self.amount * other.amount
            unit = self.combine_units(op.add, self, other)
            return type(self)(amount, unit, measure)
        return NotImplemented

    def __truediv__(self, other: Union['Measurement', Real]):
        if isinstance(other, Real):
            return type(self)(self.amount / other, self.measure)
        if isinstance(other, Measurement):
            measure = self.measure / other.measure
            amount = self.amount / other.amount
            unit = self.combine_units(op.sub, self, other)
            return type(self)(amount, unit, measure)
        return NotImplemented

    def __rtruediv__(self, other: Real):
        return type(self)(other / self.amount, self.unit, ~self.measure)

    def __pow__(self, power: int):
        return type(self)(self.amount ** power, self.unit, self.measure ** power)

    def __add__(self, other: 'Measurement'):
        other = self._coalesce(other)
        if not other or other.unit != self.unit:
            return NotImplemented
        return type(self)(self.amount + other.amount, self.unit, self.measure)

    def __sub__(self, other: 'Measurement'):
        other = self._coalesce(other)
        if not other or other.unit != self.unit:
            return NotImplemented
        return type(self)(self.amount - other.amount, self.unit, self.measure)

    def __round__(self, measurement: Union[str, 'Measurement']):
        measurement = self._coalesce(measurement)
        if not measurement or measurement.unit != self.unit:
            return NotImplemented
        amount = measurement.amount
        amount = amount * round(self.amount / amount)
        return type(self)(amount, self.measure)

    def __format__(self, format_spec):
        match = Measurement.format_pattern.fullmatch(format_spec)
        if not match:
            raise ValueError('could not parse format string ' + format_spec)
        decimal_format, convert, display = match.group('inner_format', 'convert', 'display')
        if not convert:
            convert = self.unit
        if not display:
            display = convert
        if not decimal_format:
            decimal_format = ''
        amount = self[convert]
        return f'{amount:{decimal_format}} {display}'
