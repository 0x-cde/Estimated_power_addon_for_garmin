import Toybox.Activity;
import Toybox.Application;
import Toybox.FitContributor;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;
import Toybox.Time;
import Toybox.UserProfile;
import Toybox.WatchUi;
import Toybox.Weather;

const FIELD_ID_POWER = 0;
const FIELD_ID_LAP_AVG = 1;
const FIELD_ID_SESSION_AVG = 2;

// FIT profile: record message (20), field 7 = power. Garmin Connect shows the
// field as a Connect IQ chart regardless; some third-party sites (e.g. Strava)
// treat it as power when the file has no real power meter data.
const FIT_NATIVE_POWER = 7;

const DEFAULT_RIDER_KG = 75.0;
const DEFAULT_BIKE_KG = 9.0;     // only if a preset has no bike weight
const DEFAULT_EXTRA_TENTHS = 15; // extra weight in 0.1 kg (setting values 10 / 15 / 20)
const SMOOTHING_SEC = 3;         // averaging window; fixed until decided from test results
const INDOOR_TEMP_C = 20.0;      // indoors the outdoor weather temperature does not apply

// Ride types (preset "rideType"), matched to the Edge profile's sub-sport.
const RIDE_UNSUPPORTED = -1;
const RIDE_ROAD = 0;
const RIDE_GRAVEL = 1;
// 2 was Mountain: out of scope for now (see development/archive/mountain_bike);
// the number stays reserved so existing presets keep their meaning.
const RIDE_COMMUTING = 3;
const RIDE_INDOOR = 4;
// Built-in values per ride type when the rider has no preset for it
// (index = ride type; index 2 is unused).
const DEFAULT_TYRE_BY_RIDE = [0, 1, 0, 0, 0];
const DEFAULT_POSITION_BY_RIDE = [0, 0, 0, 2, 0];
const DEFAULT_APPAREL_BY_RIDE = [0, 0, 0, 1, 0];  // commuting: casual clothes
// Tyre width (mm) when no preset exists; matches the widths the former per-type
// drag values assumed (road 25-28, gravel 40-45 mm).
const DEFAULT_TYRE_WIDTH_BY_RIDE = [28, 42, 28, 28, 28];
const DEFAULT_TYRE_TREAD = 1;      // gravel tyres: file tread / low knobs
const DEFAULT_HEIGHT_M = 1.75;
const DEFAULT_TEMP_C = 15.0;
const DEFAULT_RH_PCT = 50.0;
const MIN_MOVING_SPEED = 1.0;     // m/s, below this power is reported as 0
const WEATHER_REFRESH_MS = 60000; // the device itself only refreshes every 15-30 min

// Data fields cannot read the Edge's own temperature sensor (Sensor.getInfo()
// crashes data fields; SensorHistory is not available on the supported Edges).
// Without weather, the last weather temperature/humidity is used: kept for the
// rest of the ride, and saved so a ride starting without weather can use it if
// it is recent enough.
const STORED_WEATHER_MAX_AGE_SEC = 6 * 3600;
const STORED_WEATHER_SAVE_EVERY_SEC = 600;
const KEY_LAST_TEMP_C = "lastTempC";
const KEY_LAST_RH_PCT = "lastRhPct";
const KEY_LAST_WEATHER_SEC = "lastWeatherSec";

// Garmin documents windBearing only as "North = 0, East = 90". This code
// assumes the meteorological convention (direction the wind comes FROM).
// If on-device testing shows it is the direction the wind blows TO, set 180.
const WIND_BEARING_OFFSET_DEG = 0.0;

// Display layouts, chosen from the slot's share of the screen.
const LAYOUT_SINGLE = 0;   // 3 s value only
const LAYOUT_STACKED = 1;  // tall slot: lap average underneath
const LAYOUT_SIDE = 2;     // full-width slot: lap average beside
const STACK_MIN_HEIGHT = 0.30;  // fraction of screen height
const SIDE_MIN_WIDTH = 0.85;    // fraction of screen width (a full-width slot)
const SIDE_MIN_HEIGHT = 0.12;   // fraction of screen height
const SIDE_MIN_ASPECT = 1.6;    // width / height for the side-by-side layout
const LAP_MAX_RATIO = 0.6;      // lap value at most this fraction of the 3 s value's height

class EstimatedPowerField extends WatchUi.DataField {

    private var _grade as GradeEstimator;
    private var _powerField as FitContributor.Field;
    private var _lapField as FitContributor.Field;
    private var _sessionField as FitContributor.Field;
    private var _hasWeather as Boolean;

    // Derived from settings and the user profile
    private var _massKg as Float = 0.0;
    private var _effMassKg as Float = 0.0;
    private var _cda as Float = 0.0;
    private var _crrPaved as Float = 0.0;
    private var _crrUnpavedAdd as Float = 0.0;
    private var _crrTyre as Float = 0.0;  // paved Crr adjusted for the current temperature
    private var _unpaved as Boolean = false;  // from the Edge's surface-type splits
    private var _supported as Boolean = true; // false for cyclocross, e-bikes, other sports
    private var _indoor as Boolean = false;   // indoor cycling: no gradient, wind or surface
    private var _windExposure as Float = 0.0;

    // Rolling average of per-second power
    private var _window as Array<Float> = [] as Array<Float>;
    private var _windowIdx as Number = 0;
    private var _windowCount as Number = 0;

    private var _prevSpeed as Float or Null;
    private var _prevTimeMs as Number or Null;
    private var _cadenceSeen as Boolean = false;

    private var _lapSum as Float = 0.0;
    private var _lapCount as Number = 0;
    private var _sessionSum as Float = 0.0;
    private var _sessionCount as Number = 0;

    // Cached weather (refreshed once a minute)
    private var _lastWeatherMs as Number or Null;
    private var _windSpeed as Float = 0.0;
    private var _windFromDeg as Float = 0.0;
    private var _tempC as Float = DEFAULT_TEMP_C;
    private var _rhPct as Float = DEFAULT_RH_PCT;
    private var _lastSavedSec as Number or Null;

    // Display
    private var _powerText as String = "--";
    private var _lapText as String = "--";
    private const NUMBER_FONTS = [Graphics.FONT_NUMBER_THAI_HOT, Graphics.FONT_NUMBER_HOT,
        Graphics.FONT_NUMBER_MEDIUM, Graphics.FONT_NUMBER_MILD, Graphics.FONT_LARGE,
        Graphics.FONT_MEDIUM, Graphics.FONT_SMALL, Graphics.FONT_TINY, Graphics.FONT_XTINY] as Array<Graphics.FontType>;

    function initialize() {
        DataField.initialize();
        _grade = new GradeEstimator();
        _hasWeather = (Toybox has :Weather);
        loadStoredWeather();
        loadSettings();

        // nativeNum is fixed for the whole activity, so it is only read here.
        if (getBool("writeNativePower", true)) {
            _powerField = createField("est_power", FIELD_ID_POWER, FitContributor.DATA_TYPE_UINT16,
                {:mesgType => FitContributor.MESG_TYPE_RECORD, :units => "W", :nativeNum => FIT_NATIVE_POWER});
        } else {
            _powerField = createField("est_power", FIELD_ID_POWER, FitContributor.DATA_TYPE_UINT16,
                {:mesgType => FitContributor.MESG_TYPE_RECORD, :units => "W"});
        }
        _lapField = createField("lap_avg_est_power", FIELD_ID_LAP_AVG, FitContributor.DATA_TYPE_UINT16,
            {:mesgType => FitContributor.MESG_TYPE_LAP, :units => "W"});
        _sessionField = createField("avg_est_power", FIELD_ID_SESSION_AVG, FitContributor.DATA_TYPE_UINT16,
            {:mesgType => FitContributor.MESG_TYPE_SESSION, :units => "W"});
    }

    //! Reads rider/bike/environment settings. Called at start-up and whenever
    //! the user changes settings in Connect IQ / Garmin Connect.
    function loadSettings() as Void {
        var profile = UserProfile.getProfile();

        var riderKg = getFloat("riderWeightKg", 0.0);
        if (riderKg <= 0.0 && profile.weight != null) {
            riderKg = (profile.weight as Number) / 1000.0;
        }
        if (riderKg <= 0.0) {
            riderKg = DEFAULT_RIDER_KG;
        }

        var heightM = getFloat("riderHeightCm", 0.0) / 100.0;
        if (heightM <= 0.0 && profile.height != null) {
            heightM = (profile.height as Number) / 100.0;
        }
        if (heightM <= 0.0) {
            heightM = DEFAULT_HEIGHT_M;
        }

        // Bike setup comes from the preset for the ride type of the current
        // Edge profile; without one, built-in values for that ride type.
        var rideType = currentRideType();
        _supported = rideType != RIDE_UNSUPPORTED;
        _indoor = rideType == RIDE_INDOOR;
        var typeIdx = _supported ? rideType : RIDE_ROAD;
        var preset = selectPreset(rideType);
        var tyreType = pickIndex(presetNumber(preset, "tyreType", DEFAULT_TYRE_BY_RIDE[typeIdx] as Number),
            PowerModel.TYRE_WATTS.size());
        var tyreClass = pickIndex(presetNumber(preset, "tyreClass", 1), PowerModel.TYRE_CLASS_FACTORS.size());
        var tyreTread = pickIndex(presetNumber(preset, "tyreTread", DEFAULT_TYRE_TREAD),
            PowerModel.GRAVEL_TREAD_WATTS.size());
        var tyreWidth = presetNumber(preset, "tyreWidth", DEFAULT_TYRE_WIDTH_BY_RIDE[typeIdx] as Number);
        var position = presetNumber(preset, "position", DEFAULT_POSITION_BY_RIDE[typeIdx] as Number);
        var apparel = pickIndex(presetNumber(preset, "apparel", DEFAULT_APPAREL_BY_RIDE[typeIdx] as Number),
            PowerModel.APPAREL_FACTORS.size());

        // Bike weight is entered by the rider (required in the settings).
        var bikeKg = presetFloat(preset, "bikeKg", 0.0);
        if (bikeKg <= 0.0) {
            bikeKg = DEFAULT_BIKE_KG;
        }
        var extraKg = presetNumber(preset, "extraWeight", DEFAULT_EXTRA_TENTHS) / 10.0;
        _massKg = riderKg + bikeKg + extraKg;
        _effMassKg = _massKg + PowerModel.WHEEL_INERTIA_MASS_KG;

        _cda = PowerModel.cdaFromAnthropometrics(heightM, riderKg, PowerModel.positionFactor(position))
            * (PowerModel.APPAREL_FACTORS[apparel] as Float)
            + PowerModel.tyreCdaExtra(tyreWidth);
        // Reference-temperature values; the temperature factor applies to the
        // tyre part each second, the unpaved surface addition is not scaled.
        _crrPaved = PowerModel.tyreCrr(tyreType, tyreClass, tyreTread);
        _crrUnpavedAdd = PowerModel.UNPAVED_ADD[tyreType] as Float;
        updateTyreCrr();

        _windExposure = PowerModel.WIND_EXPOSURE;
        _lastWeatherMs = null;

        if (_window.size() != SMOOTHING_SEC) {
            _window = new Array<Float>[SMOOTHING_SEC];
            for (var i = 0; i < SMOOTHING_SEC; i++) {
                _window[i] = 0.0;
            }
            _windowIdx = 0;
            _windowCount = 0;
        }
    }

    function compute(info as Activity.Info) as Void {
        if (!_supported) {
            _powerText = "--";
            _lapText = "--";
            return;
        }
        var now = System.getTimer();
        var speed = info.currentSpeed;
        if (speed == null) {
            _prevSpeed = null;
            _prevTimeMs = null;
            _powerText = "--";
            return;
        }
        var v = speed.toFloat();

        var dt = 0.0;
        if (_prevTimeMs != null) {
            dt = (now - (_prevTimeMs as Number)) / 1000.0;
        }

        var altitude = info.altitude;
        var distance = info.elapsedDistance;
        if (!_indoor && altitude != null && distance != null) {
            _grade.addSample(distance.toFloat(), altitude.toFloat());
        }

        if (!_indoor) {
            updateWeather(now);
        }
        var tempC = _indoor ? INDOOR_TEMP_C : _tempC;

        var pressure = info.ambientPressure;
        var rho;
        if (pressure != null) {
            rho = PowerModel.airDensity(pressure.toFloat(), tempC, _rhPct);
        } else {
            var alt = (altitude != null) ? altitude.toFloat() : 0.0;
            rho = PowerModel.airDensity(PowerModel.pressureFromAltitude(alt), tempC, _rhPct);
        }

        // Track is GPS course over ground; fall back to compass heading.
        var travel = info.track;
        if (travel == null) {
            travel = info.currentHeading;
        }
        var headwind = 0.0;
        if (!_indoor && _windSpeed > 0.0 && travel != null) {
            headwind = PowerModel.headwindComponent(_windSpeed * _windExposure, _windFromDeg,
                Math.toDegrees(travel.toFloat()).toFloat());
        }

        // Rate of change of kinetic energy. Ignore if samples are irregular.
        var kineticW = 0.0;
        if (_prevSpeed != null && dt >= 0.5 && dt <= 3.0) {
            var pv = _prevSpeed as Float;
            kineticW = 0.5 * _effMassKg * (v * v - pv * pv) / dt;
        }
        _prevSpeed = v;
        _prevTimeMs = now;

        // A cadence of 0 means coasting only if a cadence sensor has reported
        // pedalling at some point; some devices may report 0 without a sensor.
        // A missing reading (sensor dropout) is not treated as coasting.
        var cadence = info.currentCadence;
        if (cadence != null && cadence > 0) {
            _cadenceSeen = true;
        }
        var coasting = _cadenceSeen && cadence != null && cadence == 0;

        var crr = _crrTyre;
        if (_unpaved && !_indoor) {
            crr += _crrUnpavedAdd;
        }

        // With a cadence sensor, coasting is already reported as 0 and negative
        // model values while pedalling are mostly gradient/speed noise, so they
        // are averaged before clamping; clamping each second would bias the
        // average upwards. Without one, descents give genuinely negative values
        // and each second is clamped.
        var p = 0.0;
        if (v >= MIN_MOVING_SPEED && !coasting) {
            p = PowerModel.crankPower(v, v + headwind, _indoor ? 0.0 : _grade.getGrade(), kineticW,
                _massKg, crr, _cda, rho);
            if (p < 0.0 && !_cadenceSeen) {
                p = 0.0;
            }
        }

        var avg = pushAndAverage(p);
        var watts = (avg > 0.0) ? Math.round(avg).toNumber() : 0;
        _powerField.setData(watts);

        if (info.timerState == Activity.TIMER_STATE_ON) {
            _lapSum += watts;
            _lapCount++;
            _sessionSum += watts;
            _sessionCount++;
            _lapField.setData(Math.round(_lapSum / _lapCount).toNumber());
            _sessionField.setData(Math.round(_sessionSum / _sessionCount).toNumber());
        }

        _powerText = watts.toString();
        _lapText = (_lapCount > 0) ? Math.round(_lapSum / _lapCount).toNumber().toString() : "--";
    }

    function onTimerLap() as Void {
        _lapSum = 0.0;
        _lapCount = 0;
        _lapText = "--";
    }

    function onTimerReset() as Void {
        _lapSum = 0.0;
        _lapCount = 0;
        _lapText = "--";
        _sessionSum = 0.0;
        _sessionCount = 0;
        _cadenceSeen = false;
        _unpaved = false;
        _grade.reset();
    }

    //! Surface type from the Edge's map-based paved/unpaved splits (API 5.2.2).
    //! Splits alternate through the ride; the Edge's map data decides the surface.
    function onTimerSplitStart(info as Activity.SplitInfo) as Void {
        var type = info.splitType;
        if (type == Activity.SplitInfo.SPLIT_TYPE_SURFACE_TYPE_UNPAVED) {
            _unpaved = true;
        } else if (type == Activity.SplitInfo.SPLIT_TYPE_SURFACE_TYPE_PAVED) {
            _unpaved = false;
        }
    }

    function onTimerSplitEnd(info as Activity.SplitInfo) as Void {
        if (info.splitType == Activity.SplitInfo.SPLIT_TYPE_SURFACE_TYPE_UNPAVED) {
            _unpaved = false;
        }
    }

    //! Ride type of the current Edge profile (RIDE_*), from its sport and
    //! sub-sport. Cyclocross, e-bikes and other activity types are not supported.
    private function currentRideType() as Number {
        if (!(Activity has :getProfileInfo)) {
            return RIDE_ROAD;
        }
        var info = Activity.getProfileInfo();
        if (info.sport != Activity.SPORT_CYCLING) {
            return RIDE_UNSUPPORTED;
        }
        var sub = info.subSport;
        if (sub == null || sub == Activity.SUB_SPORT_GENERIC || sub == Activity.SUB_SPORT_ROAD) {
            return RIDE_ROAD;
        } else if (sub == Activity.SUB_SPORT_GRAVEL_CYCLING) {
            return RIDE_GRAVEL;
        } else if (sub == Activity.SUB_SPORT_COMMUTING) {
            return RIDE_COMMUTING;
        } else if (sub == Activity.SUB_SPORT_INDOOR_CYCLING) {
            return RIDE_INDOOR;
        }
        return RIDE_UNSUPPORTED;
    }

    //! First preset whose ride type matches, or null if there is none.
    private function selectPreset(rideType as Number) as Dictionary or Null {
        var presets = Application.Properties.getValue("presets");
        if (!(presets instanceof Array)) {
            return null;
        }
        var list = presets as Array;
        for (var i = 0; i < list.size(); i++) {
            var entry = list[i];
            if (entry instanceof Dictionary && presetNumber(entry as Dictionary, "rideType", -1) == rideType) {
                return entry as Dictionary;
            }
        }
        return null;
    }

    private function presetFloat(preset as Dictionary or Null, key as String, fallback as Float) as Float {
        if (preset == null) {
            return fallback;
        }
        var value = (preset as Dictionary).get(key);
        if (value instanceof Number || value instanceof Float) {
            return (value as Numeric).toFloat();
        }
        if (value instanceof String) {
            var parsed = (value as String).toFloat();
            return parsed != null ? parsed : fallback;
        }
        return fallback;
    }

    private function presetNumber(preset as Dictionary or Null, key as String, fallback as Number) as Number {
        if (preset == null) {
            return fallback;
        }
        var value = (preset as Dictionary).get(key);
        if (value instanceof Number || value instanceof Float) {
            return (value as Numeric).toNumber();
        }
        if (value instanceof String) {
            var parsed = (value as String).toNumber();
            return parsed != null ? parsed : fallback;
        }
        return fallback;
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        var bg = getBackgroundColor();
        var fg = (bg == Graphics.COLOR_BLACK) ? Graphics.COLOR_WHITE : Graphics.COLOR_BLACK;
        dc.setColor(fg, bg);
        dc.clear();

        var w = dc.getWidth();
        var h = dc.getHeight();
        var settings = System.getDeviceSettings();
        // Full-width, wide slot: lap beside. Tall slot: lap underneath. Otherwise 3 s only.
        var layout = LAYOUT_SINGLE;
        if (w >= settings.screenWidth * SIDE_MIN_WIDTH && w >= h * SIDE_MIN_ASPECT
                && h >= settings.screenHeight * SIDE_MIN_HEIGHT) {
            layout = LAYOUT_SIDE;
        } else if (h >= settings.screenHeight * STACK_MIN_HEIGHT) {
            layout = LAYOUT_STACKED;
        }

        // The lap value is always clearly smaller than the 3 s value: a smaller
        // font, at most LAP_MAX_RATIO of its height.
        if (layout == LAYOUT_STACKED) {
            var split = (h * 0.66).toNumber();
            var main = drawValueWithUnit(dc, w / 2, split / 2, w * 0.9, split * 0.9, _powerText, "W");
            var lapH = minOf((h - split) * 0.8, Graphics.getFontAscent(NUMBER_FONTS[main]) * LAP_MAX_RATIO);
            drawLapLine(dc, w / 2, split + (h - split) / 2, w * 0.9, lapH, main + 1);
        } else if (layout == LAYOUT_SIDE) {
            var split = (w * 0.62).toNumber();
            var main = drawValueWithUnit(dc, split / 2, h / 2, split * 0.92, h * 0.9, _powerText, "W");
            dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
            dc.drawLine(split, h / 6, split, h - h / 6);
            dc.setColor(fg, Graphics.COLOR_TRANSPARENT);
            var labelH = Graphics.getFontHeight(Graphics.FONT_XTINY);
            var lapH = minOf(h * 0.9 - labelH, Graphics.getFontAscent(NUMBER_FONTS[main]) * LAP_MAX_RATIO);
            drawLapBlock(dc, split + (w - split) / 2, h / 2, (w - split) * 0.9, lapH + labelH, main + 1);
        } else {
            drawValueWithUnit(dc, w / 2, h / 2, w * 0.9, h * 0.9, _powerText, "W");
        }
    }

    private function minOf(a as Numeric, b as Numeric) as Numeric {
        return (a < b) ? a : b;
    }

    //! Index of the largest font in NUMBER_FONTS, from minIndex down, whose
    //! rendering of text fits the box.
    private function fitFontIndex(dc as Graphics.Dc, text as String, maxW as Numeric, maxH as Numeric,
                                  minIndex as Number) as Number {
        for (var i = minIndex; i < NUMBER_FONTS.size(); i++) {
            var font = NUMBER_FONTS[i];
            var dims = dc.getTextDimensions(text, font);
            if (dims[0] <= maxW && Graphics.getFontAscent(font) <= maxH) {
                return i;
            }
        }
        return NUMBER_FONTS.size() - 1;
    }

    //! Large value with a small unit to its right, centred on (cx, cy).
    //! Returns the index of the font used.
    private function drawValueWithUnit(dc as Graphics.Dc, cx as Numeric, cy as Numeric, maxW as Numeric,
                                       maxH as Numeric, value as String, unit as String) as Number {
        var unitFont = (maxH > 60) ? Graphics.FONT_SMALL : Graphics.FONT_XTINY;
        var unitW = dc.getTextDimensions(unit, unitFont)[0];
        var gap = 3;
        var index = fitFontIndex(dc, value, maxW - unitW - gap, maxH, 0);
        var font = NUMBER_FONTS[index];
        var valueW = dc.getTextDimensions(value, font)[0];
        var x0 = cx - (valueW + gap + unitW) / 2;
        dc.drawText(x0, cy, font, value, Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        dc.drawText(x0 + valueW + gap, cy + Graphics.getFontAscent(font) / 4, unitFont, unit,
            Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        return index;
    }

    //! "Lap 152" on one line, centred on (cx, cy).
    private function drawLapLine(dc as Graphics.Dc, cx as Numeric, cy as Numeric, maxW as Numeric, maxH as Numeric,
                                 minFont as Number) as Void {
        var label = "Lap";
        var labelFont = Graphics.FONT_SMALL;
        var labelW = dc.getTextDimensions(label, labelFont)[0];
        var gap = 8;
        var font = NUMBER_FONTS[fitFontIndex(dc, _lapText, maxW - labelW - gap, maxH, minFont)];
        var valueW = dc.getTextDimensions(_lapText, font)[0];
        var x0 = cx - (labelW + gap + valueW) / 2;
        dc.drawText(x0, cy, labelFont, label, Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
        dc.drawText(x0 + labelW + gap, cy, font, _lapText, Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    //! "Lap" above its value, centred on (cx, cy).
    private function drawLapBlock(dc as Graphics.Dc, cx as Numeric, cy as Numeric, maxW as Numeric, maxH as Numeric,
                                  minFont as Number) as Void {
        var labelFont = Graphics.FONT_XTINY;
        var labelH = Graphics.getFontHeight(labelFont);
        var font = NUMBER_FONTS[fitFontIndex(dc, _lapText, maxW, maxH - labelH, minFont)];
        var valueH = Graphics.getFontAscent(font);
        var top = cy - (labelH + valueH) / 2;
        dc.drawText(cx, top + labelH / 2, labelFont, "Lap", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        dc.drawText(cx, top + labelH + valueH / 2, font, _lapText, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    private function pushAndAverage(p as Float) as Float {
        _window[_windowIdx] = p;
        _windowIdx = (_windowIdx + 1) % _window.size();
        if (_windowCount < _window.size()) {
            _windowCount++;
        }
        var sum = 0.0;
        for (var i = 0; i < _windowCount; i++) {
            sum += _window[i];
        }
        return sum / _windowCount;
    }

    //! Wind, temperature and humidity from Garmin's phone-synced weather.
    //! Current conditions are preferred; the nearest hourly forecast fills gaps
    //! (current conditions sometimes have no wind data).
    private function updateWeather(nowMs as Number) as Void {
        if (!_hasWeather) {
            return;
        }
        if (_lastWeatherMs != null && nowMs - (_lastWeatherMs as Number) < WEATHER_REFRESH_MS) {
            return;
        }
        _lastWeatherMs = nowMs;

        var windSpeed = null;
        var windBearing = null;
        var temp = null;
        var rh = null;

        var current = Weather.getCurrentConditions();
        if (current != null) {
            windSpeed = current.windSpeed;
            windBearing = current.windBearing;
            temp = current.temperature;
            rh = current.relativeHumidity;
        }

        if (windSpeed == null || windBearing == null || temp == null) {
            var hourly = Weather.getHourlyForecast();
            if (hourly != null && hourly.size() > 0) {
                var nearest = hourly[0];
                var nowSec = Time.now().value();
                var best = null;
                for (var i = 0; i < hourly.size(); i++) {
                    var t = hourly[i].forecastTime;
                    if (t != null) {
                        var diff = t.value() - nowSec;
                        if (diff < 0) {
                            diff = -diff;
                        }
                        if (best == null || diff < best) {
                            best = diff;
                            nearest = hourly[i];
                        }
                    }
                }
                if (windSpeed == null || windBearing == null) {
                    windSpeed = nearest.windSpeed;
                    windBearing = nearest.windBearing;
                }
                if (temp == null) {
                    temp = nearest.temperature;
                }
                if (rh == null) {
                    rh = nearest.relativeHumidity;
                }
            }
        }

        if (windSpeed != null && windBearing != null) {
            _windSpeed = windSpeed.toFloat();
            _windFromDeg = windBearing.toFloat() + WIND_BEARING_OFFSET_DEG;
        } else {
            _windSpeed = 0.0;
        }
        // Without weather values, keep whatever is already in use (earlier
        // weather this ride, stored weather, or the defaults).
        if (temp != null && temp.toFloat() != _tempC) {
            _tempC = temp.toFloat();
            updateTyreCrr();
        }
        if (rh != null) {
            _rhPct = rh.toFloat();
        }
        if (temp != null) {
            saveWeather();
        }
    }

    //! Tyre Crr for the current temperature. Data fields cannot read the Edge's
    //! temperature sensor, so this is the weather temperature, else the stored
    //! one, else the default; indoors a fixed 20 C. Only recalculated when the
    //! temperature or the settings change.
    private function updateTyreCrr() as Void {
        _crrTyre = _crrPaved * PowerModel.crrTemperatureFactor(_indoor ? INDOOR_TEMP_C : _tempC);
    }

    //! Uses the last saved weather temperature/humidity if it is recent enough.
    private function loadStoredWeather() as Void {
        var savedSec = Application.Storage.getValue(KEY_LAST_WEATHER_SEC);
        var temp = Application.Storage.getValue(KEY_LAST_TEMP_C);
        var rh = Application.Storage.getValue(KEY_LAST_RH_PCT);
        if (!(savedSec instanceof Number) || !(temp instanceof Float)) {
            return;
        }
        if (Time.now().value() - (savedSec as Number) > STORED_WEATHER_MAX_AGE_SEC) {
            return;
        }
        _tempC = temp as Float;
        if (rh instanceof Float) {
            _rhPct = rh as Float;
        }
    }

    private function saveWeather() as Void {
        var nowSec = Time.now().value();
        if (_lastSavedSec != null && nowSec - (_lastSavedSec as Number) < STORED_WEATHER_SAVE_EVERY_SEC) {
            return;
        }
        _lastSavedSec = nowSec;
        Application.Storage.setValue(KEY_LAST_TEMP_C, _tempC);
        Application.Storage.setValue(KEY_LAST_RH_PCT, _rhPct);
        Application.Storage.setValue(KEY_LAST_WEATHER_SEC, nowSec);
    }

    private function getFloat(key as String, fallback as Float) as Float {
        var value = Application.Properties.getValue(key);
        return (value instanceof Number || value instanceof Float) ? (value as Numeric).toFloat() : fallback;
    }

    private function getBool(key as String, fallback as Boolean) as Boolean {
        var value = Application.Properties.getValue(key);
        return (value instanceof Boolean) ? value as Boolean : fallback;
    }

    private function pickIndex(index as Number, size as Number) as Number {
        return (index >= 0 && index < size) ? index : 0;
    }
}
