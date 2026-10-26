"""Reference implementation of source/PowerModel.mc and source/GradeEstimator.mc.

Mirrors the Monkey C code so the physics can be tested and tuned on a desktop
(e.g. against FIT files from a ride with a real power meter). Keep the two in
sync when either changes.
"""
import math

G = 9.80665
R_DRY_AIR = 287.058
R_WATER_VAPOUR = 461.495
DRIVETRAIN_LOSS_W = 2.0     # fixed loss (Rohloff 2003); crank = (wheel + loss) / efficiency
DRIVETRAIN_EFFICIENCY = 0.985
WHEEL_INERTIA_MASS_KG = 1.4
WHEEL_DRAG_AREA = 0.0044     # spoke/rotation drag area, Martin et al. 1998
TYRE_WIDTH_MIN_MM, TYRE_WIDTH_MAX_MM = 18, 60  # preset tyre width range
TYRE_WIDTH_BASE_MM = 28.0                      # up to this width no extra drag
TYRE_CDA_PER_MM = 0.0010                       # ~0.010 m^2 per 10 mm of extra width
CD_TT = 0.707
POSITION_FACTORS = [1.75, 1.45, 1.30, 1.15]   # tops/upright, hoods, drops, aero (pedalling, field TT CdA)
FACTOR_UPRIGHT, FACTOR_HOODS, FACTOR_DROPS, FACTOR_AERO = POSITION_FACTORS
POSITION_ROAD, POSITION_TT, POSITION_UPRIGHT = 0, 1, 2   # preset "position"
APPAREL_FACTORS = [1.00, 1.17]           # cycling kit, casual clothes (Tengattini & Bigazzi 2018)
TYRE_WATTS = [15.0, 20.0, 30.0]          # road, gravel, MTB tyres; all-round, on road (drum test)
TYRE_CLASS_FACTORS = [0.80, 1.00, 1.35]  # fast, all-round, durable (road and MTB tyres)
GRAVEL_TREAD_WATTS = [13.3, 16.0, 20.0]  # gravel tyres: slick, file tread / low knobs, knobby
TYRE_GRAVEL = 1
REAL_ROAD_ADD = 0.0033                   # UCPRC-RR-2016-02 median +0.0035 minus bearings (modelled separately)
UNPAVED_ADD = [0.0070, 0.0043, 0.0040]   # added on unpaved (Meyer 2016; Steyn 2014; Tengattini 2018)
CRR_TEMP_REF_C = 20.0                    # Rothhamel 2023: Crr ~ b / (T + 46.8), used at half strength
CRR_TEMP_OFFSET_C = 46.8
CRR_TEMP_STRENGTH = 0.5
CRR_TEMP_MIN_C, CRR_TEMP_MAX_C = -20.0, 40.0
DRUM_LOAD_KG = 42.5
DRUM_SPEED_MS = 8.0
WIND_EXPOSURE = [0.0, 0.43, 0.54, 0.64]       # off, sheltered, mixed, open


def frontal_area_tt(height_m, rider_mass_kg):
    return 0.0293 * height_m ** 0.725 * rider_mass_kg ** 0.425 + 0.0604


def crr_temperature_factor(temp_c):
    t = min(CRR_TEMP_MAX_C, max(CRR_TEMP_MIN_C, temp_c))
    full = (CRR_TEMP_REF_C + CRR_TEMP_OFFSET_C) / (t + CRR_TEMP_OFFSET_C)
    return 1.0 + CRR_TEMP_STRENGTH * (full - 1.0)


def position_factor(mode):
    if mode == POSITION_TT:
        return 0.95 * FACTOR_AERO + 0.05 * FACTOR_HOODS
    if mode == POSITION_UPRIGHT:
        return FACTOR_UPRIGHT
    return 0.70 * FACTOR_HOODS + 0.30 * FACTOR_DROPS


def crr_from_drum_watts(watts):
    return watts / (DRUM_LOAD_KG * G * DRUM_SPEED_MS)


def tyre_crr(tyre_type, tyre_class=1, tyre_tread=1):
    """Paved real-road Crr at 20 C. Road/MTB tyres use the class, gravel tyres the tread."""
    if tyre_type == TYRE_GRAVEL:
        watts = GRAVEL_TREAD_WATTS[tyre_tread]
    else:
        watts = TYRE_WATTS[tyre_type] * TYRE_CLASS_FACTORS[tyre_class]
    return crr_from_drum_watts(watts) + REAL_ROAD_ADD


def tyre_crr_unpaved(tyre_type, tyre_class=1, tyre_tread=1):
    return tyre_crr(tyre_type, tyre_class, tyre_tread) + UNPAVED_ADD[tyre_type]


def tyre_cda_extra(width_mm):
    w = min(TYRE_WIDTH_MAX_MM, max(TYRE_WIDTH_MIN_MM, width_mm))
    return max(0.0, (w - TYRE_WIDTH_BASE_MM) * TYRE_CDA_PER_MM)


def cda_from_anthropometrics(height_m, rider_mass_kg, position_factor):
    return CD_TT * frontal_area_tt(height_m, rider_mass_kg) * position_factor


def air_density(pressure_pa, temp_c, rh_pct):
    t_k = temp_c + 273.15
    saturation = 610.78 * 10.0 ** (7.5 * temp_c / (temp_c + 237.3))
    vapour = saturation * rh_pct / 100.0
    return (pressure_pa - vapour) / (R_DRY_AIR * t_k) + vapour / (R_WATER_VAPOUR * t_k)


def pressure_from_altitude(altitude_m):
    return 101325.0 * (1.0 - 2.25577e-5 * altitude_m) ** 5.25588


def headwind_component(wind_speed, wind_from_deg, travel_deg):
    return wind_speed * math.cos(math.radians(wind_from_deg - travel_deg))


def crank_power(speed, air_speed, grade, kinetic_w, mass_kg, crr, cda, rho):
    theta = math.atan(grade)
    rolling = crr * mass_kg * G * math.cos(theta) * speed
    gravity = mass_kg * G * math.sin(theta) * speed
    aero = 0.5 * rho * (cda + WHEEL_DRAG_AREA) * air_speed * abs(air_speed) * speed
    bearings = speed * (91.0 + 8.7 * speed) * 0.001
    return (rolling + gravity + aero + kinetic_w + bearings + DRIVETRAIN_LOSS_W) / DRIVETRAIN_EFFICIENCY


class GradeEstimator:
    SIZE = 30
    MIN_SPAN_M = 25.0
    MIN_SAMPLES = 4
    MIN_STEP_M = 0.5
    MAX_GRADE = 0.30

    def __init__(self):
        self.samples = []  # (distance, altitude), newest last
        self.grade = 0.0

    def add_sample(self, distance_m, altitude_m):
        if self.samples:
            last = self.samples[-1][0]
            if distance_m < last - 1.0:
                self.samples, self.grade = [], 0.0
            elif distance_m - last < self.MIN_STEP_M:
                return
        self.samples.append((distance_m, altitude_m))
        self.samples = self.samples[-self.SIZE:]
        self._fit()

    def _fit(self):
        newest = self.samples[-1][0]
        window = None
        for n in range(1, len(self.samples) + 1):
            if newest - self.samples[-n][0] >= self.MIN_SPAN_M and n >= self.MIN_SAMPLES:
                window = self.samples[-n:]
                break
        if window is None:
            return
        mean_d = sum(d for d, _ in window) / len(window)
        mean_h = sum(h for _, h in window) / len(window)
        sxx = sum((d - mean_d) ** 2 for d, _ in window)
        if sxx <= 0.0:
            return
        sxy = sum((d - mean_d) * (h - mean_h) for d, h in window)
        self.grade = max(-self.MAX_GRADE, min(self.MAX_GRADE, sxy / sxx))
