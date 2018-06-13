import unittest

from measure import *
from measure.commons import *


class PrimitiveUnitsTests(unittest.TestCase):
    def test_create(self):
        Population = BasicMeasure('population', person=1, couple=2, minyan=10, team=5, play=(2, 'team'))
        self.assertEqual(Population['team'] * 2, Population['minyan'])
        self.assertEqual(Population['minyan'], Population['play'])
        Population.optimize_aliases()
        self.assertEqual(Population['team'] * 2, Population['minyan'])
        self.assertEqual(Population['minyan'], Population['play'])


class GeneralTests(unittest.TestCase):
    def test_div(self):
        Speed = Distance / Time

        Acceleration = Speed / Time

        self.assertIs(Acceleration, Distance / Time ** 2)

        g = Acceleration('meter/second2', 9.8)

        self.assertAlmostEqual(Speed(0.98, 'meter/second') / Time(0.1, 'second'), g, delta='0.0001 m/s^2')

    def test_pow(self):
        sq_km = (Distance ** 2)('kilometer**2')
        km = Distance.km
        self.assertEqual(km ** 2, sq_km)

    def test_inv(self):
        Frequency = 1 / Time

        Frequency['hz'] = '1/second'
        self.assertAlmostEqual(Frequency['hz'] / Frequency['1/minute'], 60)

    def test_mul(self):
        Speed = Distance / Time

        Acceleration = Speed / Time

        Force = Mass * Acceleration

        Energy = Mass * Distance ** 2 / Time ** 2

        self.assertEqual(Energy, Force * Distance)

    def test_loki(self):
        loki_mass = Mass(525, 'lb')

        g = 9.8 * Distance.m / Time.s ** 2

        human_area = 1 * Distance.m ** 2
        human_height = 167 * Distance.cm
        loki_height = 6 * Distance.foot + 4 * Distance.inch

        loki_area = human_area * (loki_height / human_height) ** 2

        terminal_velocity = ((2 * loki_mass * g) / (
                (1.23 * Mass.kg / Distance.meter ** 3) * loki_area)) ** .5

        time_to_reach_tv = terminal_velocity / g
        if 30 * Time.minute > time_to_reach_tv:
            loki_momentum = loki_mass * terminal_velocity
        else:
            loki_momentum = 30 * Time.minute * g * loki_mass
        self.assertAlmostEqual(loki_momentum, '12690 kg*m/s', delta='1 kg*m/s')

    def test_ratio(self):
        speed_of_sound = 340 * Distance.m / Time.s
        speed_of_light = 299_792 * Distance.km / Time.s
        self.assertAlmostEqual(speed_of_light / speed_of_sound, 881_741, delta=1)

    def test_format(self):
        a = 1.27 * Distance.m / Time.s ** 2
        s = format(a, '.2f:m/s2')
        self.assertEqual(s, '1.27 m/s2')
        s = format(a, '10 m/s2|g')
        self.assertEqual(s, '0.127 g')
        s = format(a, '.2e:10 m/s2|g')
        self.assertEqual(s, '1.27e-01 g')

    def test_access_map(self):
        acc = Distance / Time ** 2
        self.assertEqual(acc[{'km': 1, 's': -2}], 1e3)


class LinearTests(unittest.TestCase):
    def test_simple(self):
        Temperature = LinearMeasure('temperature')
        Temperature['K'] = Temperature['kelvin'] = Ladder.arbitrary()
        Temperature['C'] = Temperature['celsius'] = Ladder.from_points((-273.15, 0), (0, 273.15))
        Temperature['F'] = Temperature['fahrenheit'] = Ladder.from_points((-459.67, -40), (0, 233.15))

        room_temp = Temperature.absolute('25 C')
        self.assertAlmostEqual(room_temp['kelvin'], 298.15)
        self.assertAlmostEqual(room_temp['fahrenheit'], 77)

        water_freezing = Temperature.absolute('0 C')
        self.assertGreater(room_temp, water_freezing)

        diff = room_temp - water_freezing

        self.assertAlmostEqual(diff['F'], 45)

        water_boiling = water_freezing + Temperature.delta('100 C')

        diff = water_boiling - room_temp
        self.assertEqual(diff, "75 C")
        self.assertEqual(diff, "135 F")


class AggregateTests(unittest.TestCase):
    def test_simple(self):
        Position = Distance.aggregate()
        tom = Position('8 m')
        jerry = Position('-6 m')
        jerry += 2 * Distance.foot
        self.assertLess(jerry, tom)


class DynamicTests(unittest.TestCase):
    def test_simple(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        pogs = Currency('3 pog')
        self.assertEqual(pogs['gold'], 6)
        self.assertEqual(pogs['toy'], 600)

        Currency['toy'] = 10
        Currency['pog'] = 0.5

        self.assertEqual(pogs['gold'], 1.5)
        self.assertEqual(pogs['toy'], 0.15)

    def test_derived(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        cost_of_fence = 3 * Currency.toy / Distance.m
        self.assertEqual((cost_of_fence * Distance.km)['gold'], 30)
        Currency['toy'] = 10
        self.assertEqual((cost_of_fence * Distance.km)['gold'], 30_000)

    def test_aggregate(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        CurAgg = Currency.aggregate()

        bunch_pogs = CurAgg('100 pog')
        self.assertEqual(bunch_pogs['gold'], 200)
        bunch_pogs += Currency.pog * 50
        Currency['pog'] = 0.5
        self.assertEqual(bunch_pogs['gold'], 75)

    def test_cmp(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        bunch_toys = Currency('100 toy')
        pog = Currency.pog

        self.assertLess(bunch_toys, pog)

        Currency['pog'] = 1

        self.assertEqual(bunch_toys, pog)

        self.assertGreater(pog, 0)

    def test_cmp_agg(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        CurAgg = Currency.aggregate()

        bunch_toys = CurAgg('100 toy')
        pog = CurAgg('1 pog')

        self.assertLess(bunch_toys, pog)

        Currency['pog'] = 1

        self.assertEqual(bunch_toys, pog)

        self.assertGreater(pog, 0)

    def test_add(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        bunch_toys = Currency('100 toy')
        bunch_toys += '50 toy'

        self.assertEqual(bunch_toys['gold'], 1.5)

        Currency['toy'] = 1.5

        self.assertEqual(bunch_toys['gold'], 225)

        with self.assertRaises(TypeError):
            bunch_toys += '5 gold'

    def test_conv(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2

        bunch_toys = Currency('100 toy')

        as_pog = bunch_toys('pog')
        self.assertEqual(as_pog.unit, 'pog')
        self.assertEqual(as_pog, bunch_toys)

    def test_conv_agg(self):
        Currency = DynamicMeasure('currency')
        Currency['gold'] = 1
        Currency['toy'] = 0.01
        Currency['pog'] = 2
        CurrAgg = Currency.aggregate()

        bunch_toys = CurrAgg('100 toy')

        as_pog = bunch_toys('pog')
        self.assertEqual(as_pog.unit, 'pog')
        self.assertEqual(as_pog, bunch_toys)

