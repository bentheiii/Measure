from typing import Union

from numbers import Real

from .measure import BasicMeasure, Measurement


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


# todo handle derived measures
class DynamicMeasurement(Measurement):
    __slots__ = 'unit'

    def __new__(cls, amount, unit, measure):
        return super().__new__(cls, amount, measure)

    def __init__(self, amount, unit, measure):
        super().__init__(amount, measure)
        self.unit = unit

    def arb(self):
        return self.amount * self.measure[self.unit]

    def __getitem__(self, item):
        arb = self.arb()
        return arb / self.measure[item]