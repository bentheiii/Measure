from typing import Dict, Tuple, Union

from numbers import Real
from collections import namedtuple, Counter
from math import isclose

from .measure import Measure, Measurement, AggregateMeasure, Unit
from ._util import split_amount_args


class Ladder(namedtuple('LadderBase', 'scale offset')):
    """
    A ladder is a linear unit that is not necessarily based on 0.
    """
    __slots__ = ()

    def from_arb(self, v: Real) -> Real:
        """
        :param v: measurement in arbitrary units
        :return: measure in this ladder's units
        """
        return (v / self.scale) - self.offset

    def to_arb(self, v: Real) -> Real:
        """
        :param v: measurement in this ladder's units
        :return: measure in arbitrary units
        """
        return (v + self.offset) * self.scale

    __rtruediv__ = from_arb
    __rmul__ = to_arb

    @classmethod
    def from_points(cls, this_ladder_points: Tuple[Real, Real], other_ladder_points: Tuple[Real, Real],
                    other_ladder: 'Ladder' = None):
        """
        construct a ladder from two fixed points
        :param this_ladder_points: two points on the newly constructed ladder
        :param other_ladder_points: two points on an already created ladder
        :param other_ladder: the ladder to which the other_ladder_points are made.
        None if they are in the arbitrary ladder.
        :return: a new ladder that adheres to the fixed points.
        """
        if other_ladder is not None:
            return cls.from_points(this_ladder_points, tuple(other_ladder.to_arb(v) for v in other_ladder_points),
                                   other_ladder=None)
        s = (other_ladder_points[0] - other_ladder_points[1]) / (this_ladder_points[0] - this_ladder_points[1])
        o = other_ladder_points[0] * s - this_ladder_points[0]
        ret = Ladder(scale=s, offset=o)
        assert isclose(ret.from_arb(other_ladder_points[1]), this_ladder_points[1])
        return ret

    @classmethod
    def arbitrary(cls):
        """
        :return: an arbitrary scale
        """
        return cls(scale=1, offset=0)


Unit.register(Ladder)


class LinearMeasure:
    """
    A measure with two different forms: an interval form (.delta, 0-based) and an absolute form (.absolute, not 0-based)
    """
    __slots__ = 'name', 'delta', 'absolute', 'ladders'

    def __init__(self, name):
        """
        constructor
        :param name: the name of the measure
        """
        self.name = name
        self.delta = LinearMeasureDelta(self)
        self.absolute = self.delta.aggregate()
        self.ladders: Dict['str', Union[Ladder, str]] = {}

    def add_ladder(self, name, this_ladder_points: Tuple[Real, Real], other_ladder_points: Tuple[Real, Real],
                   other_ladder: Union[Ladder, str] = None):
        """
        Add a ladder to the measure
        :param name: the Name of the new ladder
        :param this_ladder_points: points on the new ladder
        :param other_ladder_points: points on the other ladder
        :param other_ladder: name or identity of the other ladder. None for arbitrary
        :return: the newly created ladder, for piping
        """
        if isinstance(other_ladder, str):
            other_ladder = self[other_ladder]
        ladder = Ladder.from_points(this_ladder_points, other_ladder_points, other_ladder)
        self[name] = ladder
        return ladder

    def __setitem__(self, key, value):
        """
        add a new ladder or alias
        :param key: name of the new ladder
        :param value: a ladder or name of existing ladder
        """
        self.ladders[key] = value

    def __getitem__(self, item):
        """
        get a ladder
        :param item: name of a ladder
        :return: the measure's named ladder
        """
        ret = self.ladders[item]
        if isinstance(ret, str):
            return self[ret]
        return ret

    def optimize_aliases(self):
        """
        optimize unit call, reducing all aliases to their alias's value
        :return: self, for piping
        """
        for k, v in self.ladders.items():
            if not isinstance(v, Ladder):
                self.ladders[k] = self[k]


class LinearMeasureDelta(Measure):
    """
    A measure that is the delta of a linear measure
    """
    __slots__ = 'owner'

    def __init__(self, owner: LinearMeasure):
        super().__init__()
        self.owner = owner

    def __getitem__(self, item):
        if isinstance(item, Measurement):
            if item.measure != self:
                raise ValueError(f'cannot accept measurement of unit {item}')
            return item.amount
        if isinstance(item, str):
            a, item = split_amount_args(item, default_amount=None)
            if a is not None:
                return a * self[item]
        return self.owner[item].scale

    def __contains__(self, item):
        return item in self.owner.ladders

    def __primitives__(self):
        return Counter({self: 1})

    def native_unit(self) -> str:
        return next(iter(self.owner.ladders.keys()))

    def root(self, r):
        if r == 1:
            return self
        raise ValueError('cannot get root of primitive unit')

    def __str__(self):
        return f'{self.owner.name}_delta'

    def __aggregate__(self):
        return AggregateLinearMeasure(self.owner)


class AggregateLinearMeasure(AggregateMeasure):
    """
    An absolute value of a linear measure
    """
    __slots__ = 'owner'

    def __init__(self, owner: LinearMeasure):
        super().__init__()
        self.owner = owner

    def __getitem__(self, item):
        return self.owner[item]

    def derivative(self):
        return self.owner.delta
