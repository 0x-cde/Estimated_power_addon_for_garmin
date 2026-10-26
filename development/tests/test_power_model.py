"""Sanity tests for the reference model. Run: python3 -m unittest discover -s tests"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import power_model as pm  # noqa: E402


def steady(speed, grade=0.0, headwind=0.0, mass=85.5, crr=0.005, cda=0.35, rho=1.225):
    return pm.crank_power(speed, speed + headwind, grade, 0.0, mass, crr, cda, rho)


class AirDensity(unittest.TestCase):
    def test_isa_sea_level_dry(self):
        self.assertAlmostEqual(pm.air_density(101325.0, 15.0, 0.0), 1.225, places=3)

    def test_humid_air_is_lighter(self):
        self.assertLess(pm.air_density(101325.0, 25.0, 90.0), pm.air_density(101325.0, 25.0, 0.0))

    def test_isa_pressure_at_1000m(self):
        self.assertAlmostEqual(pm.pressure_from_altitude(1000.0), 89875.0, delta=50.0)


class Aerodynamics(unittest.TestCase):
    def test_bassett_worked_example(self):
        # 1.75 m / 69 kg -> 0.3262 m^2 (worked example published with the formula)
        self.assertAlmostEqual(pm.frontal_area_tt(1.75, 69.0), 0.3262, places=3)

    def test_position_ordering(self):
        cdas = [pm.cda_from_anthropometrics(1.78, 75.0, f) for f in pm.POSITION_FACTORS]
        self.assertEqual(cdas, sorted(cdas, reverse=True))

    def test_hoods_cda_in_typical_range(self):
        cda = pm.cda_from_anthropometrics(1.78, 75.0, pm.POSITION_FACTORS[1])
        self.assertTrue(0.30 <= cda <= 0.40, cda)

    def test_wind_direction(self):
        # Riding north (0 deg) with wind from the north is a pure headwind.
        self.assertAlmostEqual(pm.headwind_component(5.0, 0.0, 0.0), 5.0)
        self.assertAlmostEqual(pm.headwind_component(5.0, 180.0, 0.0), -5.0)
        self.assertAlmostEqual(pm.headwind_component(5.0, 90.0, 0.0), 0.0, places=9)


class Presets(unittest.TestCase):
    def test_tyre_crr_from_drum_watts(self):
        # 15 W at 42.5 kg and 8 m/s -> Crr ~0.0045 on the drum, + 0.0033 on real roads
        self.assertAlmostEqual(pm.crr_from_drum_watts(15.0), 15.0 / (42.5 * pm.G * 8.0))
        self.assertAlmostEqual(pm.tyre_crr(0, 1), 0.0045 + 0.0033, places=4)

    def test_tyre_order_paved_and_unpaved(self):
        # all-round road tyre vs a file-tread gravel tyre
        paved = [pm.tyre_crr(0, 1), pm.tyre_crr(1, tyre_tread=1)]
        unpaved = [pm.tyre_crr_unpaved(0, 1), pm.tyre_crr_unpaved(1, tyre_tread=1)]
        self.assertLess(paved[0], paved[1])             # road < gravel on pavement
        self.assertLess(unpaved[1], unpaved[0])         # gravel tyres beat road tyres off-road
        for p, u in zip(paved, unpaved):
            self.assertGreater(u, p)
        self.assertEqual(len(pm.TYRE_WATTS), 2)         # mountain-bike tyres are out of scope

    def test_gravel_uses_tread_and_class(self):
        slick, file_, knobby = (pm.tyre_crr(1, 1, t) for t in range(3))
        self.assertLess(slick, file_)
        self.assertLess(file_, knobby)
        self.assertLess(pm.tyre_crr(1, 0, 1), pm.tyre_crr(1, 1, 1))          # class applies to gravel too
        self.assertLess(pm.tyre_crr(1, 1, 1), pm.tyre_crr(1, 2, 1))
        # fast class reproduces the earlier tread-only values; all-round file tread = old all-round gravel
        for t, watts in enumerate((13.3, 16.0, 20.0)):
            self.assertAlmostEqual(pm.tyre_crr(1, 0, t), pm.crr_from_drum_watts(watts) + pm.REAL_ROAD_ADD, places=4)
        self.assertAlmostEqual(pm.tyre_crr(1, 1, 1), pm.crr_from_drum_watts(20.0) + pm.REAL_ROAD_ADD)
        self.assertAlmostEqual(pm.UNPAVED_ADD[1], 0.0043)

    def test_width_drag(self):
        self.assertEqual(pm.tyre_cda_extra(18), 0.0)
        self.assertEqual(pm.tyre_cda_extra(28), 0.0)
        self.assertAlmostEqual(pm.tyre_cda_extra(45), 0.017)
        self.assertAlmostEqual(pm.tyre_cda_extra(60), 0.032)
        self.assertEqual(pm.tyre_cda_extra(80), pm.tyre_cda_extra(60))   # clamped to the preset range
        widths = [pm.tyre_cda_extra(w) for w in range(18, 61)]
        self.assertEqual(widths, sorted(widths))

    def test_tyre_class_scales_the_drum_part_only(self):
        drum = pm.crr_from_drum_watts(pm.TYRE_WATTS[0])
        self.assertAlmostEqual(pm.tyre_crr(0, 0), 0.80 * drum + pm.REAL_ROAD_ADD)
        self.assertAlmostEqual(pm.tyre_crr(0, 2), 1.35 * drum + pm.REAL_ROAD_ADD)

    def test_position_blends(self):
        self.assertAlmostEqual(pm.position_factor(pm.POSITION_ROAD), 0.7 * 1.45 + 0.3 * 1.30)
        self.assertAlmostEqual(pm.position_factor(pm.POSITION_TT), 0.95 * 1.15 + 0.05 * 1.45)
        self.assertLess(pm.position_factor(pm.POSITION_TT), pm.position_factor(pm.POSITION_ROAD))
        self.assertLess(pm.position_factor(pm.POSITION_ROAD), pm.position_factor(pm.POSITION_UPRIGHT))

    def test_tt_cda_matches_field_values(self):
        # Pedalling / field TT CdA is 0.25-0.29 m^2 for typical riders.
        cda = pm.cda_from_anthropometrics(1.78, 72.0, pm.position_factor(pm.POSITION_TT))
        self.assertTrue(0.25 <= cda <= 0.30, cda)

    def test_apparel(self):
        self.assertEqual(pm.APPAREL_FACTORS[0], 1.0)
        self.assertAlmostEqual(pm.APPAREL_FACTORS[1], 1.17)


class Temperature(unittest.TestCase):
    def test_reference_is_neutral(self):
        self.assertAlmostEqual(pm.crr_temperature_factor(20.0), 1.0)

    def test_cold_raises_warm_lowers(self):
        self.assertAlmostEqual(pm.crr_temperature_factor(5.0), 1 + 0.5 * (66.8 / 51.8 - 1))
        self.assertGreater(pm.crr_temperature_factor(0.0), pm.crr_temperature_factor(10.0))
        self.assertLess(pm.crr_temperature_factor(30.0), 1.0)

    def test_clamped(self):
        self.assertEqual(pm.crr_temperature_factor(-60.0), pm.crr_temperature_factor(-20.0))
        self.assertEqual(pm.crr_temperature_factor(60.0), pm.crr_temperature_factor(40.0))


class Drivetrain(unittest.TestCase):
    def test_matches_constant_efficiency_near_170w(self):
        wheel = 170.0
        self.assertAlmostEqual((wheel + pm.DRIVETRAIN_LOSS_W) / pm.DRIVETRAIN_EFFICIENCY, wheel / 0.976, delta=1.0)

    def test_relatively_larger_loss_at_low_power(self):
        lo = (60.0 + pm.DRIVETRAIN_LOSS_W) / pm.DRIVETRAIN_EFFICIENCY / 60.0
        hi = (300.0 + pm.DRIVETRAIN_LOSS_W) / pm.DRIVETRAIN_EFFICIENCY / 300.0
        self.assertGreater(lo, hi)


class CrankPower(unittest.TestCase):
    def test_flat_40kmh_hoods_is_plausible(self):
        # 75 kg rider + 10.5 kg bike/kit on hoods at 40 km/h: expect roughly 300-380 W.
        cda = pm.cda_from_anthropometrics(1.78, 75.0, pm.POSITION_FACTORS[1])
        p = steady(40 / 3.6, cda=cda)
        self.assertTrue(300 <= p <= 380, p)

    def test_climb_dominated_by_gravity(self):
        # 8 % at 12 km/h: gravity alone is ~m*g*v*sin(theta) ~= 222 W.
        p = steady(12 / 3.6, grade=0.08)
        self.assertTrue(230 <= p <= 270, p)

    def test_monotonic_in_speed_grade_wind(self):
        self.assertLess(steady(8.0), steady(9.0))
        self.assertLess(steady(8.0, grade=0.0), steady(8.0, grade=0.02))
        self.assertLess(steady(8.0, headwind=-3.0), steady(8.0), )
        self.assertLess(steady(8.0), steady(8.0, headwind=3.0))

    def test_steep_descent_is_negative(self):
        self.assertLess(steady(12.0, grade=-0.08), 0.0)

    def test_strong_tailwind_reverses_aero_term(self):
        # Air speed negative -> aero force pushes the rider.
        self.assertLess(steady(5.0, headwind=-8.0), steady(5.0, headwind=-5.0))


class Grade(unittest.TestCase):
    def test_recovers_constant_grade_from_noisy_baro(self):
        rng = random.Random(1)
        est = pm.GradeEstimator()
        d = 0.0
        for _ in range(120):
            d += 4.0  # 14.4 km/h
            est.add_sample(d, 100.0 + 0.06 * d + rng.gauss(0.0, 0.15))
        self.assertAlmostEqual(est.grade, 0.06, delta=0.01)

    def test_holds_grade_while_stopped(self):
        est = pm.GradeEstimator()
        for i in range(20):
            est.add_sample(i * 5.0, i * 5.0 * 0.04)
        before = est.grade
        for _ in range(30):
            est.add_sample(95.0, 3.0)  # no distance progress, altitude drifts
        self.assertEqual(est.grade, before)

    def test_reset_when_distance_goes_back(self):
        est = pm.GradeEstimator()
        for i in range(20):
            est.add_sample(i * 5.0, i * 5.0 * 0.04)
        est.add_sample(0.0, 0.0)
        self.assertEqual(est.grade, 0.0)
        self.assertEqual(len(est.samples), 1)


if __name__ == "__main__":
    unittest.main()
