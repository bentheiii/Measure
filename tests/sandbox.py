# let's find out Loki's momentum when he hit the ground in Thor: Ragnarok
# first, let's get some units ready

#  a measure is a "dimension" in measurements
from measure import BasicMeasure
# BasicMeasures are the building blocks of more complex measures as we will see later

Distance = BasicMeasure('distance')

Distance['meter'] = 1  # let's define units in our measure
Distance['km'] = 1000  # bigger numbers -> bigger units
Distance['cm'] = 0.01
Distance['inch'] = 0.0254
Distance['m'] = 'meter'  # we can also alias existing units to ake them more easily accessible
Distance['foot'] = (12, 'inch')

# of course we can just do something like this
Duration = BasicMeasure('time', second= 1, s= 'second', minute= 60, hour= (60, 'minute'))

# the most common measures are already made to be imported
from measure.commons import Mass

# let's start with gravity
Acceleration = Distance / (Duration * Duration)
# we just combined multiple measures to create an entirely new measure: acceleration
# note that this arithmetic is symmetrical
assert Acceleration * Duration**2 is Distance
assert (Distance / Duration)/Duration is Acceleration is Distance/Duration**2
# and now: gravity
g = Acceleration(9.8, 'm/s**2')
# by calling a measure, we have created a measurement. A measurement is an amount of a specific measure
# there are a lot of ways to create a measurement, all the follwing are equivelant
assert Distance(8848, 'meter') == Distance('8848 meter') == 8.848 * Distance('km')
# with basic measures, we can create a 1-unit measurement simply by getting the unit as an attribute
assert Distance(8848, 'meter') == 8848 * Distance.m
# we can divide and multiply measurements, as though we were multiplying both their amounts and measures
assert g == (98 * Distance.m/Duration.s)/(10 * Duration.s)

# alright, let's speed this up, Loki was falling for 30 minutes
fall_time = 30*Duration.minute
# also some loki stats
loki_height = 6 * Distance.foot + 4 * Distance.inch
loki_mass = Mass(525, 'lb')
# and some human stats
human_projected_area = 0.7 * Distance.m ** 2
human_height = 167 * Distance.cm
# we can use these stats to approximate Loki's projected area
loki_projected_area = human_projected_area * (loki_height/human_height)**2

# some environmental stats
air_density = 1.23 * Mass.kg/Distance.m**3

# let's calculate loki's terminal velocity
# using formula from here: https://en.wikipedia.org/wiki/Speed_skydiving
terminal_velocity = (2*loki_mass*g / (air_density*loki_projected_area)) ** 0.5
assert terminal_velocity.measure is Distance / Duration
time_to_reach_tv = terminal_velocity / g

if time_to_reach_tv <= fall_time:
    # loki reached terminal velocity
    impact_speed = terminal_velocity
else:
    impact_speed = g * fall_time

impact_momentum = impact_speed * loki_mass

print(f'loki hit the ground with {impact_momentum:,.0f:kg*m/s} momentum')  # 15,169 kg*m/s