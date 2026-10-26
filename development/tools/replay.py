"""Replay a FIT file through the same per-second pipeline as
Estimated_Power/source/EstimatedPowerField.mc and compare with recorded power.

Usage:
  .venv/bin/python -I tools/replay.py --ride 12 [--ride 13 ...]      # rides from the contributor database
  .venv/bin/python -I tools/replay.py --all                          # every ride with power in the database
  .venv/bin/python -I tools/replay.py --rider-kg 72 --height-m 1.78 --bike-kg 8.4 FILE.fit ...   # a FIT file

Database mode is the normal way to work: it uses the answers the contributor
gave (rider and bike weight, height, tyres, position, clothing, extra weight),
the ride's anonymized samples and the weather stored with it. FIT mode exists
for checking single files before import.

Differences from the device, because a FIT file lacks some live inputs:
  - air pressure: ISA pressure from altitude (device: barometer ambientPressure)
  - temperature: fixed --temp (device: weather, else last weather value; the
    device's own temperature sensor is not readable from a data field)
  - wind: none unless --wind-speed/--wind-from given (device: Garmin weather)
"""
import argparse
import math
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import fitdecode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import power_model as pm  # noqa: E402

MIN_MOVING_SPEED = 1.0


UNPAVED, PAVED = 34, 42  # FIT split_type values (Activity.SplitInfo.SPLIT_TYPE_SURFACE_TYPE_*)


def load_surface_splits(path):
    """(start, end) datetimes of the unpaved splits the Edge recorded."""
    out = []
    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if isinstance(frame, fitdecode.FitDataMessage) and frame.name == "split":
                if frame.get_value("split_type", fallback=None) == UNPAVED:
                    out.append((frame.get_value("start_time", fallback=None),
                                frame.get_value("end_time", fallback=None)))
    return [(a, b) for a, b in out if a is not None and b is not None and b > a]


def load_records(path):
    rows = []
    with fitdecode.FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                continue
            g = lambda k: frame.get_value(k, fallback=None)  # noqa: E731
            speed = g("enhanced_speed")
            if speed is None:
                speed = g("speed")
            alt = g("enhanced_altitude")
            if alt is None:
                alt = g("altitude")
            lat, lon = g("position_lat"), g("position_long")
            rows.append({
                "t": g("timestamp"), "speed": speed, "dist": g("distance"), "alt": alt,
                "cad": g("cadence"), "power": g("power"), "temp": g("temperature"),
                "hr": g("heart_rate"),
                "lat": lat * 180.0 / 2 ** 31 if lat is not None else None,
                "lon": lon * 180.0 / 2 ** 31 if lon is not None else None,
            })
    return rows


TYRE_INDEX = {"road": 0, "gravel": 1}     # mountain-bike tyres are out of the model's scope for now
CLASS_INDEX = {"fast": 0, "all-round": 1, "durable": 2}
POSITION_INDEX = {"road": pm.POSITION_ROAD, "tt": pm.POSITION_TT, "upright": pm.POSITION_UPRIGHT}
APPAREL_INDEX = {"kit": 0, "casual": 1}
TREAD_INDEX = {"slick": 0, "file": 1, "knobby": 2}
DEFAULT_WIDTH = {0: 28, 1: 42}          # mm, only when a width is missing (as on the device)
DEFAULT_EXTRA_KG = 1.5           # only for rides imported before the extra-weight question existed
_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)   # anonymized rides have no date; any origin works


def default_db():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import anonymize
    return anonymize.DEFAULT_DB


def load_db_ride(con, ride_id):
    """One anonymized ride from the contributor database, in replay's row format.
    Returns (rows, setup, weather) where setup holds the contributor's answers."""
    meta = con.execute(
        "SELECT r.id, c.rider_kg, c.height_cm, r.bike_kg, r.tyre_type, r.tyre_class, r.position, r.apparel, "
        "r.extra_kg, r.start_alt_100m, r.context, r.tyre_width_mm, r.tyre_tread "
        "FROM rides r JOIN contributors c ON c.code = r.contributor "
        "WHERE r.id = ?", (ride_id,)).fetchone()
    if meta is None:
        raise ValueError(f"ride {ride_id} not found")
    keys = ("id", "rider_kg", "height_cm", "bike_kg", "tyre_type", "tyre_class", "position", "apparel",
            "extra_kg", "start_alt_100m", "context", "tyre_width_mm", "tyre_tread")
    m = dict(zip(keys, meta))
    if not m["rider_kg"] or not m["bike_kg"]:
        raise ValueError(f"ride {ride_id}: rider or bike weight missing")
    if not m["height_cm"]:
        raise ValueError(f"ride {ride_id}: rider height missing (needed for the drag area)")
    if m["tyre_type"] not in TYRE_INDEX:
        raise ValueError(f"ride {ride_id}: {m['tyre_type']} tyres are not covered by the model yet")
    base_alt = float(m["start_alt_100m"] or 0)   # metres, rounded to the nearest 100 m
    rows = [{"t": _EPOCH + timedelta(seconds=t), "speed": v, "dist": d,
             "alt": base_alt + a if a is not None else None, "cad": c, "power": p, "temp": tc,
             "hr": None, "lat": None, "lon": None, "heading": h, "unpaved": u}
            for t, v, d, a, c, p, tc, h, u in con.execute(
                "SELECT t_s, speed, dist_m, alt_rel_m, cadence, power, temp_c, heading_deg, unpaved "
                "FROM samples WHERE ride_id = ? ORDER BY t_s", (ride_id,))]
    weather = [dict(zip(("t_s", "wind_ms", "wind_from_deg", "temp_c", "rh_pct"), w)) for w in con.execute(
        "SELECT t_s, wind_ms, wind_from_deg, temp_c, rh_pct FROM weather WHERE ride_id = ? ORDER BY t_s",
        (ride_id,))]
    setup = dict(rider_kg=float(m["rider_kg"]), height_m=m["height_cm"] / 100.0, bike_kg=m["bike_kg"],
                 extra_kg=m["extra_kg"] if m["extra_kg"] is not None else DEFAULT_EXTRA_KG,
                 position_mode=POSITION_INDEX.get(m["position"], pm.POSITION_ROAD),
                 tyre_type=TYRE_INDEX.get(m["tyre_type"], 0), tyre_class=CLASS_INDEX.get(m["tyre_class"], 1),
                 apparel=APPAREL_INDEX.get(m["apparel"], 0), context=m["context"],
                 tyre_width=m["tyre_width_mm"], tyre_tread=TREAD_INDEX.get(m["tyre_tread"], 1))
    return rows, setup, weather


def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360.0


def estimate(rows, rider_kg, height_m, bike_kg, extra_kg, position_mode=0, tyre_type=0, tyre_class=1,
             cda=None, crr=None, smoothing=3, temp_c=15.0, rh=50.0, wind_speed=0.0, wind_from=0.0,
             wind_mode=2, unpaved_splits=(), apparel=0, weather=None, tyre_width=None, tyre_tread=1):
    """Returns a list of smoothed estimates (W, int) aligned with rows (None if no speed).
    unpaved_splits: (start, end) datetimes during which the unpaved Crr applies; rows may
    also carry their own "unpaved" flag and "heading" (database rides).
    weather: optional list of {t_s, wind_ms, wind_from_deg, temp_c, rh_pct}; like the
    device, the latest point so far sets wind, temperature and humidity (and so the
    tyre-temperature factor). Without it, the fixed temp_c / rh / wind_* are used.
    crr, if given, is used as-is (no temperature factor, no unpaved addition)."""
    mass = rider_kg + bike_kg + extra_kg
    eff_mass = mass + pm.WHEEL_INERTIA_MASS_KG
    if cda is None:
        cda = (pm.cda_from_anthropometrics(height_m, rider_kg, pm.position_factor(position_mode))
               * pm.APPAREL_FACTORS[apparel]
               + pm.tyre_cda_extra(tyre_width if tyre_width is not None else DEFAULT_WIDTH[tyre_type]))
    def crr_for(t_c):
        if crr is not None:
            return crr, crr
        paved = pm.tyre_crr(tyre_type, tyre_class, tyre_tread) * pm.crr_temperature_factor(t_c)
        return paved, paved + pm.UNPAVED_ADD[tyre_type]
    crr_paved, crr_unpaved = crr_for(temp_c)
    wx_idx = -1
    t_first = next((r["t"] for r in rows if r["t"] is not None), None)
    exposure = pm.WIND_EXPOSURE[wind_mode]

    grade = pm.GradeEstimator()
    window = []
    prev_speed = prev_t = None
    prev_pos = None
    travel = None
    cadence_seen = False
    out = []
    for r in rows:
        v = r["speed"]
        if v is None:
            prev_speed = prev_t = None
            out.append(None)
            continue
        dt = (r["t"] - prev_t).total_seconds() if prev_t is not None else 0.0
        if r["alt"] is not None and r["dist"] is not None:
            grade.add_sample(r["dist"], r["alt"])

        if weather:
            t_s = (r["t"] - t_first).total_seconds()
            while wx_idx + 1 < len(weather) and weather[wx_idx + 1]["t_s"] <= t_s:
                wx_idx += 1
            w = weather[max(wx_idx, 0)]
            if w["temp_c"] is not None and w["temp_c"] != temp_c:
                temp_c = w["temp_c"]
                crr_paved, crr_unpaved = crr_for(temp_c)
            rh = w["rh_pct"] if w["rh_pct"] is not None else rh
            wind_speed = w["wind_ms"] or 0.0
            wind_from = w["wind_from_deg"] or 0.0

        alt = r["alt"] if r["alt"] is not None else 0.0
        rho = pm.air_density(pm.pressure_from_altitude(alt), temp_c, rh)

        # Direction of travel: stored heading (database rides), else the GPS track:
        # bearing between successive positions at least 3 m apart.
        if r.get("heading") is not None:
            travel = r["heading"]
        elif r["lat"] is not None:
            if prev_pos is not None:
                dy = (r["lat"] - prev_pos[0]) * 111320.0
                dx = (r["lon"] - prev_pos[1]) * 111320.0 * math.cos(math.radians(r["lat"]))
                if dx * dx + dy * dy >= 9.0:
                    travel = bearing_deg(prev_pos[0], prev_pos[1], r["lat"], r["lon"])
                    prev_pos = (r["lat"], r["lon"])
            else:
                prev_pos = (r["lat"], r["lon"])
        headwind = 0.0
        if wind_speed > 0.0 and travel is not None:
            headwind = pm.headwind_component(wind_speed * exposure, wind_from, travel)

        kinetic = 0.0
        if prev_speed is not None and 0.5 <= dt <= 3.0:
            kinetic = 0.5 * eff_mass * (v * v - prev_speed * prev_speed) / dt
        prev_speed, prev_t = v, r["t"]

        cad = r["cad"]
        if cad is not None and cad > 0:
            cadence_seen = True
        coasting = cadence_seen and cad is not None and cad == 0

        unpaved = bool(r.get("unpaved")) or any(a <= r["t"] < b for a, b in unpaved_splits)
        p = 0.0
        if v >= MIN_MOVING_SPEED and not coasting:
            p = pm.crank_power(v, v + headwind, grade.grade, kinetic, mass,
                               crr_unpaved if unpaved else crr_paved, cda, rho)
            if not cadence_seen:  # with a cadence sensor, clamp after averaging (as on the device)
                p = max(0.0, p)
        window.append(p)
        window = window[-smoothing:]
        out.append(max(0, int(round(sum(window) / len(window)))))
    return out


def rolling(values, n):
    out, acc = [], []
    for v in values:
        acc.append(v)
        acc = acc[-n:]
        out.append(sum(acc) / len(acc))
    return out


def normalized_power(values):
    r30 = rolling(values, 30)
    return (sum(x ** 4 for x in r30) / len(r30)) ** 0.25 if r30 else 0.0


def compare(est, actual):
    pairs = [(e, a) for e, a in zip(est, actual) if e is not None and a is not None]
    if not pairs:
        return None
    e = [p[0] for p in pairs]
    a = [p[1] for p in pairs]
    a3 = rolling(a, 3)  # compare like with like: 3 s actual vs 3 s estimate
    n = len(e)
    me, ma = sum(e) / n, sum(a3) / n
    cov = sum((x - me) * (y - ma) for x, y in zip(e, a3))
    var_e = sum((x - me) ** 2 for x in e)
    var_a = sum((y - ma) ** 2 for y in a3)
    corr = cov / math.sqrt(var_e * var_a) if var_e and var_a else float("nan")
    res = {"n": n, "avg_est": sum(e) / n, "avg_act": sum(a) / n,
           "np_est": normalized_power(e), "np_act": normalized_power(a),
           "corr_3s": corr,
           "mae_3s": sum(abs(x - y) for x, y in zip(e, a3)) / n}
    for w in (30, 300):
        ew, aw = rolling(e, w)[w - 1::w], rolling(a, w)[w - 1::w]
        res[f"mae_{w}s"] = sum(abs(x - y) for x, y in zip(ew, aw)) / max(len(ew), 1)
    return res


def report(label, est, actual):
    print(f"== {label}")
    res = compare(est, actual)
    if res:
        print("  avg est {avg_est:6.1f} W | avg actual {avg_act:6.1f} W | "
              "NP est {np_est:6.1f} | NP actual {np_act:6.1f}".format(**res))
        print("  3 s: corr {corr_3s:.3f}, MAE {mae_3s:5.1f} W | "
              "30 s MAE {mae_30s:5.1f} W | 5 min MAE {mae_300s:5.1f} W".format(**res))
    else:
        vals = [e for e in est if e is not None]
        if vals:
            print(f"  no recorded power; avg est {sum(vals) / len(vals):6.1f} W, "
                  f"NP est {normalized_power(vals):6.1f} W, max 3 s {max(vals)} W")
    return res


def write_csv(path, rows, est):
    with open(path, "w") as f:
        f.write("t_s,speed,distance,altitude,cadence,power,est_power\n")
        t0 = rows[0]["t"]
        for r, e in zip(rows, est):
            f.write(f"{(r['t'] - t0).total_seconds():.0f},{r['speed']},{r['dist']},{r['alt']},{r['cad']},"
                    f"{r['power'] if r['power'] is not None else ''},{e if e is not None else ''}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="FIT files (FIT mode); omit to use the database")
    ap.add_argument("--db", default=None, help="contributor database (default: the private folder)")
    ap.add_argument("--ride", type=int, action="append", default=[], help="database ride id (repeatable)")
    ap.add_argument("--all", action="store_true", help="every database ride with power")
    ap.add_argument("--rider-kg", type=float, help="FIT mode: the rider's weight")
    ap.add_argument("--height-m", type=float, help="FIT mode: the rider's height")
    ap.add_argument("--bike-kg", type=float, help="FIT mode: the bike's weight")
    ap.add_argument("--extra-kg", type=float, default=None,
                    help="FIT mode: extra weight (default 1.5); database mode: override the contributor's answer")
    ap.add_argument("--position", type=int, default=0, help="FIT mode: 0 road (70/30 hoods/drops), 1 TT, 2 upright")
    ap.add_argument("--tyre-type", type=int, default=0, choices=[0, 1], help="FIT mode: 0 road, 1 gravel")
    ap.add_argument("--tyre-class", type=int, default=1, help="FIT mode: 0 fast, 1 all-round, 2 durable")
    ap.add_argument("--tyre-tread", type=int, default=1, help="FIT mode: gravel tyres: 0 slick, 1 file tread, 2 knobby")
    ap.add_argument("--tyre-width", type=int, help="FIT mode: tyre width in mm (18-60)")
    ap.add_argument("--apparel", type=int, default=0, help="FIT mode: 0 cycling kit, 1 casual clothes")
    ap.add_argument("--no-surface", action="store_true", help="ignore unpaved sections")
    ap.add_argument("--no-weather", action="store_true", help="database mode: ignore the stored weather")
    ap.add_argument("--cda", type=float, help="use this CdA instead of the model's")
    ap.add_argument("--crr", type=float, help="use this Crr instead of the model's")
    ap.add_argument("--smoothing", type=int, default=3)
    ap.add_argument("--temp", type=float, default=15.0, help="temperature when no weather is available")
    ap.add_argument("--wind-speed", type=float, default=0.0, help="FIT mode: m/s at 10 m")
    ap.add_argument("--wind-from", type=float, default=0.0, help="FIT mode: degrees, direction wind comes from")
    ap.add_argument("--wind-mode", type=int, default=2)
    ap.add_argument("--csv", help="write the per-second estimate to this CSV (one ride only)")
    args = ap.parse_args()

    if args.files and (args.ride or args.all):
        ap.error("give either FIT files or database rides, not both")
    if args.files:
        missing = [n for n in ("rider_kg", "height_m", "bike_kg") if getattr(args, n) is None]
        if missing:
            ap.error("FIT mode needs the rider's values: " + ", ".join("--" + n.replace("_", "-") for n in missing))
        for path in args.files:
            rows = load_records(path)
            splits = () if args.no_surface else load_surface_splits(path)
            est = estimate(rows, args.rider_kg, args.height_m, args.bike_kg,
                           1.5 if args.extra_kg is None else args.extra_kg,
                           args.position, args.tyre_type, args.tyre_class, args.cda, args.crr,
                           args.smoothing, args.temp, 50.0, args.wind_speed, args.wind_from,
                           args.wind_mode, splits, args.apparel, tyre_width=args.tyre_width,
                           tyre_tread=args.tyre_tread)
            report(os.path.basename(path), est, [r["power"] for r in rows])
            if args.csv:
                write_csv(args.csv, rows, est)
        return

    if not args.ride and not args.all:
        ap.error("give --ride N, --all, or FIT files")
    con = sqlite3.connect(f"file:{args.db or default_db()}?mode=ro", uri=True)
    ids = args.ride or [r[0] for r in con.execute(
        "SELECT DISTINCT ride_id FROM samples WHERE power IS NOT NULL ORDER BY ride_id")]
    results = []
    for rid in ids:
        try:
            rows, setup, weather = load_db_ride(con, rid)
        except ValueError as exc:
            print(f"== ride {rid}: skipped: {exc}")
            continue
        if args.no_surface:
            for r in rows:
                r["unpaved"] = 0
        context = setup.pop("context")
        if args.extra_kg is not None:
            setup["extra_kg"] = args.extra_kg
        est = estimate(rows, cda=args.cda, crr=args.crr, smoothing=args.smoothing, temp_c=args.temp,
                       wind_mode=args.wind_mode, weather=None if args.no_weather else weather, **setup)
        res = report(f"ride {rid} ({context or 'context unknown'}, {len(weather)} weather points)",
                     est, [r["power"] for r in rows])
        if res:
            results.append((rid, context, res))
        if args.csv and len(ids) == 1:
            write_csv(args.csv, rows, est)
    con.close()
    if len(results) > 1:
        solo = [r for _, c, r in results if c == "solo"]
        for label, sel in (("all rides", [r for _, _, r in results]), ("solo rides", solo)):
            if sel:
                ratio = sum(r["avg_est"] for r in sel) / sum(r["avg_act"] for r in sel)
                mae = sum(r["mae_30s"] for r in sel) / len(sel)
                print(f"{label}: {len(sel)} rides, estimate/actual {ratio:.3f}, mean 30 s MAE {mae:.1f} W")


if __name__ == "__main__":
    main()
