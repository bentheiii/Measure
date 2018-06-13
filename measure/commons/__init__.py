from math import pi

from ..measure import BasicMeasure
from ..linear import LinearMeasure, Ladder

Distance = BasicMeasure('distance', meter=1, kilometer=1000, centimeter=0.01, millimeter=0.0001)
Distance.update({
    'm': 'meter',
    'km': 'kilometer',
    'cm': 'centimeter',
    'mm': 'millimeter',
    'inch': (2.54, 'centimeter'),
    'foot': (12, 'inch'),
    'yard': (3, 'foot'),
    'mile': (1760, 'yard')
})
Distance.optimize_aliases()

Duration = BasicMeasure('duration', second=1, minute=60, hour='60 minute', millisecond=0.001, day='24 hour')
Duration.update({
    's': 'second',
    'ms': 'millisecond'
})
Duration.optimize_aliases()

Mass = BasicMeasure('mass', kilogram=1, ton=1000, pound=0.4536, gram=0.001)
Mass.update({
    'kg': 'kilogram',
    'lb': 'pound',
    'g': 'gram'
})
Mass.optimize_aliases()

Angle = BasicMeasure('angle', turn=1, degree=1 / 360, radian=1 / pi, gradian=1 / 400)
Angle.update({
    'quarter': 1 / 4
})
Angle.optimize_aliases()

Temperature = LinearMeasure('temperature')
Temperature['K'] = Temperature['kelvin'] = Ladder.arbitrary()
Temperature['C'] = Temperature['celsius'] = Ladder.from_points((-273.15, 0), (0, 273.15))
Temperature['F'] = Temperature['fahrenheit'] = Ladder.from_points((-459.67, -40), (0, 233.15))
Temperature.optimize_aliases()

__all__ = 'Distance', 'Duration', 'Mass', 'Angle', 'Temperature'
