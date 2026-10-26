import Toybox.Lang;
import Toybox.Math;

//! Pure physics for the cycling power estimate. No device state lives here so
//! the same equations can be mirrored and tested in tools/power_model.py.
//!
//! Crank power = (rolling + gravity + aero + kinetic + wheel bearings) / drivetrain efficiency
//! Model structure follows Martin et al. 1998, "Validation of a mathematical
//! model for road cycling power", J Appl Biomech 14:276-291.
module PowerModel {

    const G = 9.80665;              // m/s^2
    const R_DRY_AIR = 287.058;      // J/(kg K)
    const R_WATER_VAPOUR = 461.495; // J/(kg K)

    // Drivetrain losses: a fixed part (seals, lubricant, chain) plus a share of
    // the power (Rohloff 2003; Kyle & Berto 2001). Crank = (wheel + LOSS_W) / EFF.
    // Matches Martin et al.'s constant 0.976 at about 170 W and is ~1 W higher
    // at recreational power.
    const DRIVETRAIN_LOSS_W = 2.0;
    const DRIVETRAIN_EFFICIENCY = 0.985;

    // Rotational inertia of two road wheels expressed as equivalent
    // translational mass (I / r^2). Approximate; matters only when accelerating.
    const WHEEL_INERTIA_MASS_KG = 1.4;

    // Extra drag area of the rotating wheels (spokes), not included in a
    // wind-tunnel CdA. Martin et al. 1998 use 0.0044 m^2; deep or disc wheels
    // and other studies suggest it can be larger.
    const WHEEL_DRAG_AREA = 0.0044;

    // Extra drag area of tyres wider than a road tyre (the Bassett frontal area
    // was derived on narrow-tyred bikes). About 0.010 m^2 per 10 mm of extra
    // width in wind-tunnel tests (Swiss Side, Cyclingnews); peer-reviewed data
    // show the same direction (Crane & Morton 2018, via Malizia & Blocken 2020).
    // Width comes from the preset (18-60 mm); up to 28 mm adds nothing.
    const TYRE_WIDTH_MIN_MM = 18;
    const TYRE_WIDTH_MAX_MM = 60;
    const TYRE_WIDTH_BASE_MM = 28.0;
    const TYRE_CDA_PER_MM = 0.0010;

    // Bassett et al. 1999 frontal area is for an aero (TT) position. Kyle's
    // static wind-tunnel data gives Cd ~= 0.707 for that position (CdA ~0.23).
    // Other positions are scaled with ratios of published CdA values
    // (drops ~0.30, hoods ~0.33, tops/upright ~0.40 m^2). Aero bars use 1.15:
    // pedalling and field-measured TT CdA is 0.25-0.29 m^2, above static
    // tunnel values (Garcia-Lopez 2008; Spoelstra 2019; Valenzuela 2020).
    const CD_TT = 0.707;
    const FACTOR_UPRIGHT = 1.75;
    const FACTOR_HOODS = 1.45;
    const FACTOR_DROPS = 1.30;
    const FACTOR_AERO = 1.15;

    // Preset "apparel": cycling kit, casual clothes. Casual clothing (and the
    // bags that go with it) raised the measured CdA of 557 urban riders by 17 %
    // (Tengattini & Bigazzi 2018: 0.570 vs 0.486 m^2).
    const APPAREL_FACTORS = [1.00, 1.17];

    // Riding-position modes (preset "position"). CdA is blended by the share of
    // time in each position; power is linear in CdA, so this matches the average.
    const POSITION_ROAD = 0;     // 70 % hoods, 30 % drops
    const POSITION_TT = 1;       // 95 % aero bars, 5 % base bar (braking)
    const POSITION_UPRIGHT = 2;  // flat bar / city

    // Rolling resistance, specified as the watts one tyre needs on a drum test
    // with 42.5 kg load at 28.8 km/h (the bicyclerollingresistance.com protocol),
    // for an all-round tyre on road. Index = preset "tyreType": road, gravel, MTB
    // (the gravel entry is not used: gravel tyres take GRAVEL_TREAD_WATTS).
    // Placeholder values until averaged test data is available.
    const TYRE_WATTS = [15.0, 20.0, 30.0];
    // Preset "tyreClass" for road and MTB tyres: fast (20 % better), all-round,
    // durable (35 % worse).
    const TYRE_CLASS_FACTORS = [0.80, 1.00, 1.35];
    // Gravel tyres use the tread instead of the class (preset "tyreTread"):
    // slick, file tread / low knobs, knobby. Drum watts for one tyre. File tread
    // keeps the former fast-gravel value; knobby is about +0.002 Crr over a slick
    // (Tengattini & Bigazzi 2018: knobby vs slick +0.0022; Bertucci et al. 2013:
    // smooth 21 % below knobby); a file tread sits between (estimate).
    const GRAVEL_TREAD_WATTS = [13.3, 16.0, 20.0];
    const TYRE_GRAVEL = 1;
    // Real roads vs the drum / good asphalt, added to the drum Crr. Field
    // measurements on ordinary asphalt and chip seal (UCPRC-RR-2016-02,
    // Caltrans) were +0.0026 to +0.0058 above good dense asphalt, median
    // +0.0035, including wheel-bearing friction; the bearings are modelled
    // separately here (~0.0002 at 25 km/h), hence 0.0033.
    const REAL_ROAD_ADD = 0.0033;
    // Added on unpaved surfaces, on top of the paved value. Gravel measured
    // +0.0025 (fine) to +0.0061 (coarse) above asphalt (Meyer et al. 2016);
    // gravel tyres get the middle of that range (+0.0043, x1.35 in ratio terms),
    // soft surfaces about +0.004 (Steyn & Warnich 2014; Tengattini & Bigazzi
    // 2018). Slick road tyres sink in and slip on loose surfaces, so they get
    // more. Index = tyre type: road, gravel, MTB. To be refined with club data.
    const UNPAVED_ADD = [0.0070, 0.0043, 0.0040];
    // Tyre temperature: Crr rises in the cold, as b / (T + 46.8) with T in C
    // (Rothhamel 2023, one tyre on a pendulum rig). The paper's own linear fit
    // gives about half that slope, so half strength is used. Reference 20 C.
    const CRR_TEMP_REF_C = 20.0;
    const CRR_TEMP_OFFSET_C = 46.8;
    const CRR_TEMP_STRENGTH = 0.5;
    const CRR_TEMP_MIN_C = -20.0;   // outside the clamp the fit is not trusted
    const CRR_TEMP_MAX_C = 40.0;
    const DRUM_LOAD_KG = 42.5;
    const DRUM_SPEED_MS = 8.0;

    // Fraction of the 10 m reported wind speed felt at rider height (~1.2 m),
    // from the logarithmic wind profile ln(1.2/z0)/ln(10/z0) with z0 = 0.1 m
    // (mixed terrain). Sheltered (z0 = 0.25 m) would give 0.43, open
    // (z0 = 0.03 m) 0.64.
    const WIND_EXPOSURE = 0.54;

    //! Projected frontal area (m^2) in the aero position, including the bike.
    //! Bassett DR et al., Med Sci Sports Exerc 1999;31:1665-1676.
    function frontalAreaTT(heightM as Float, riderMassKg as Float) as Float {
        return (0.0293 * Math.pow(heightM, 0.725) * Math.pow(riderMassKg, 0.425) + 0.0604).toFloat();
    }

    //! Crr multiplier for the air temperature (C), 1.0 at CRR_TEMP_REF_C.
    function crrTemperatureFactor(tempC as Float) as Float {
        var t = tempC < CRR_TEMP_MIN_C ? CRR_TEMP_MIN_C : (tempC > CRR_TEMP_MAX_C ? CRR_TEMP_MAX_C : tempC);
        var full = (CRR_TEMP_REF_C + CRR_TEMP_OFFSET_C) / (t + CRR_TEMP_OFFSET_C);
        return (1.0 + CRR_TEMP_STRENGTH * (full - 1.0)).toFloat();
    }

    //! Position factor for a riding-position mode (POSITION_*).
    function positionFactor(mode as Number) as Float {
        if (mode == POSITION_TT) {
            return 0.95 * FACTOR_AERO + 0.05 * FACTOR_HOODS;
        } else if (mode == POSITION_UPRIGHT) {
            return FACTOR_UPRIGHT;
        }
        return 0.70 * FACTOR_HOODS + 0.30 * FACTOR_DROPS;
    }

    //! Crr from drum-test watts for one tyre: P = Crr * m * g * v.
    function crrFromDrumWatts(watts as Float) as Float {
        return watts / (DRUM_LOAD_KG * G * DRUM_SPEED_MS);
    }

    //! Paved real-road Crr at the reference temperature for a tyre type
    //! (0 road, 1 gravel, 2 MTB). Road and MTB tyres use the class (0 fast,
    //! 1 all-round, 2 durable); gravel tyres use the tread (0 slick, 1 file
    //! tread, 2 knobby).
    function tyreCrr(tyreType as Number, tyreClass as Number, tyreTread as Number) as Float {
        var watts;
        if (tyreType == TYRE_GRAVEL) {
            watts = GRAVEL_TREAD_WATTS[tyreTread] as Float;
        } else {
            watts = (TYRE_WATTS[tyreType] as Float) * (TYRE_CLASS_FACTORS[tyreClass] as Float);
        }
        return crrFromDrumWatts(watts) + REAL_ROAD_ADD;
    }

    //! Extra drag area (m^2) of a tyre of the given width (mm).
    function tyreCdaExtra(widthMm as Number) as Float {
        var w = widthMm < TYRE_WIDTH_MIN_MM ? TYRE_WIDTH_MIN_MM : (widthMm > TYRE_WIDTH_MAX_MM ? TYRE_WIDTH_MAX_MM : widthMm);
        var extra = (w - TYRE_WIDTH_BASE_MM) * TYRE_CDA_PER_MM;
        return (extra > 0.0 ? extra : 0.0).toFloat();
    }

    function cdaFromAnthropometrics(heightM as Float, riderMassKg as Float, positionFactor as Float) as Float {
        return CD_TT * frontalAreaTT(heightM, riderMassKg) * positionFactor;
    }

    //! Moist air density (kg/m^3) from station pressure, temperature and
    //! relative humidity. Saturation vapour pressure uses the Tetens equation.
    function airDensity(pressurePa as Float, tempC as Float, relHumidityPct as Float) as Float {
        var tK = tempC + 273.15;
        var saturationPa = 610.78 * Math.pow(10.0, 7.5 * tempC / (tempC + 237.3));
        var vapourPa = saturationPa * relHumidityPct / 100.0;
        var dryPa = pressurePa - vapourPa;
        return (dryPa / (R_DRY_AIR * tK) + vapourPa / (R_WATER_VAPOUR * tK)).toFloat();
    }

    //! ISA pressure (Pa) for an altitude, used when the barometer gives no reading.
    function pressureFromAltitude(altitudeM as Float) as Float {
        return (101325.0 * Math.pow(1.0 - 2.25577e-5 * altitudeM, 5.25588)).toFloat();
    }

    //! Component of the wind blowing against the rider (m/s, positive = headwind).
    //! windFromDeg uses the meteorological convention (direction the wind comes
    //! from); travelDeg is the direction of travel. Both are clockwise from north.
    function headwindComponent(windSpeed as Float, windFromDeg as Float, travelDeg as Float) as Float {
        return (windSpeed * Math.cos(Math.toRadians(windFromDeg - travelDeg))).toFloat();
    }

    //! Power the rider must deliver at the cranks (W). Can be negative when
    //! decelerating or descending; the caller decides how to clamp.
    //! kineticW is the rate of change of kinetic energy (W), already including
    //! wheel inertia.
    function crankPower(speed as Float, airSpeed as Float, grade as Float, kineticW as Float,
                        massKg as Float, crr as Float, cda as Float, rho as Float) as Float {
        var theta = Math.atan(grade);
        var rolling = crr * massKg * G * Math.cos(theta) * speed;
        var gravity = massKg * G * Math.sin(theta) * speed;
        var absAir = airSpeed < 0 ? -airSpeed : airSpeed;
        var aero = 0.5 * rho * (cda + WHEEL_DRAG_AREA) * airSpeed * absAir * speed;
        var bearings = speed * (91.0 + 8.7 * speed) * 0.001;
        return ((rolling + gravity + aero + kineticW + bearings + DRIVETRAIN_LOSS_W) / DRIVETRAIN_EFFICIENCY).toFloat();
    }
}
