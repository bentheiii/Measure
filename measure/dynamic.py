from typing import Union

from numbers import Real

from .measure import BasicMeasure, Measurement, DerivedMeasure, AggregateMeasurement, BasicAggregateMeasure
import operator as op
from ._util import combine_maps, split_amount_args


class DynamicMeasure(BasicMeasure):
    __slots__ = ()

    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = 1) -> 'DynamicMeasurement':
        """
        Create a measurement
        :param unit: the unit of the measurement
        :param amount: the amount of the measured unit
        :return: a new measurement of the appropriate amount
        """
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount

        if isinstance(unit, str):
            f, u = split_amount_args(unit, None)
            if f is not None:
                amount *= f
                unit = u

        return self.__measurement__(amount, unit)

    def __measurement__(self, amount, unit):
        return DynamicMeasurement(amount, unit, self)

    def __derived_type__(self):
        return DynamicDerivedMeasure

    def __aggregate__(self):
        return DynamicAggregateMeasure(self)

    def aggregate(self)->'DynamicAggregateMeasure':
        pass

    del aggregate


class DynamicDerivedMeasure(DerivedMeasure):
    __slots__ = ()

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

    def __aggregate__(self):
        return DynamicAggregateMeasure(self)


class DynamicMeasurement(Measurement):
    __slots__ = 'unit'

    def _coalesce(self, v, check_measure=True):
        if v == 0:
            return type(self)(v, self.unit, self.measure)
        return super()._coalesce(v, check_measure=check_measure)

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

    def __call__(self, item)->'DynamicMeasurement':
        """
        convert the measurement to a measurement of the same measure but different unit
        :param item:  the new unit of the measurement
        :return: a new measurement of this unit, of equal value to self
        """
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

    def __lt__(self, other):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__lt__(other.amount)
        return self(other.unit).__lt__(other)

    def __le__(self, other):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__le__(other.amount)
        return self(other.unit).__le__(other)

    def __gt__(self, other):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__gt__(other.amount)
        return self(other.unit).__gt__(other)

    def __ge__(self, other):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__ge__(other.amount)
        return self(other.unit).__ge__(other)

    def __eq__(self, other):
        other = self._coalesce(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__eq__(other.amount)
        return self(other.unit).__eq__(other)


class DynamicAggregateMeasure(BasicAggregateMeasure):
    __slots__ = ()

    def __call__(self, unit: Union[str, Real], amount: Union[str, Real] = None) -> 'DynamicAggregateMeasurement':
        if isinstance(unit, Real) and isinstance(amount, str):
            amount, unit = unit, amount
        if amount is None:
            f, r = split_amount_args(unit, default_amount=None)
            if f is not None:
                unit, amount = r, f
            else:
                raise ValueError('amount must be specified')
        return self.__measurement__(amount, unit)

    def __measurement__(self, amount, unit):
        return DynamicAggregateMeasurement(amount, unit, self)


class DynamicAggregateMeasurement(AggregateMeasurement):
    __slots__ = 'unit'

    def _coalesce_to_absolute(self, v, check_measure=True):
        if v == 0:
            return type(self)(v, self.unit, self.measure)
        return super()._coalesce_to_absolute(v, check_measure=check_measure)

    def _coalesce_to_delta(self, v, check_measure=True):
        if v == 0:
            return self.measure.derivative(v, self.unit)
        return super()._coalesce_to_delta(v, check_measure=check_measure)

    def __init__(self, amount, unit, measure):
        super().__init__(amount, measure)
        self.unit = unit

    def arb(self):
        return self.amount * self.measure[self.unit]

    def __call__(self, item):
        """
        convert the aggregate measurement to an aggregate measurement of the same measure but different unit
        :param item:  the new unit of the aggregate measurement
        :return: a new aggregate measurement of this unit, of equal value to self
        """
        return self.measure(item, self[item])

    def __getitem__(self, item):
        arb = self.arb()
        return arb / self.measure[item]

    def __add__(self, other: Measurement):
        other = self._coalesce_to_delta(other)
        if not other or self.unit != other.unit:
            return NotImplemented
        arb = self.amount + other.amount
        return type(self)(arb, self.unit, self.measure)

    def __sub__(self, other_orig: Union[Measurement, 'AggregateMeasurement']):
        other = self._coalesce_to_delta(other_orig)
        if other and other.unit != self.unit:
            arb = self.amount - other.amount
            return type(self)(arb, self.unit, self.measure)

        other = self._coalesce_to_absolute(other_orig)
        if other and other.unit != self.unit:
            arb = self.amount - other.amount
            return self.measure.derivative()(self.unit, arb)
        return NotImplemented

    def __round__(self, measurement):
        measurement = self._coalesce_to_delta(measurement)
        if not measurement:
            raise TypeError("can't handle precision of type")
        amount = measurement.amount
        amount = amount * round(self.amount / amount)
        return type(self)(amount, self.unit, self.measure)

    def __lt__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__lt__(other.amount)
        return self(other.unit).__lt__(other)

    def __le__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__le__(other.amount)
        return self(other.unit).__le__(other)

    def __gt__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__gt__(other.amount)
        return self(other.unit).__gt__(other)

    def __ge__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__ge__(other.amount)
        return self(other.unit).__ge__(other)

    def __eq__(self, other):
        other = self._coalesce_to_absolute(other)
        if not other:
            return NotImplemented
        if other.unit == self.unit:
            return self.amount.__eq__(other.amount)
        return self(other.unit).__eq__(other)

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
