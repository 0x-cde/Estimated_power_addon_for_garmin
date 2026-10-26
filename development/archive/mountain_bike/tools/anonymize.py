"""Anonymize contributed ride files (FIT or CSV) into a local SQLite database.

Only the data the power model needs is kept, and it is transformed so the ride
cannot easily be linked to a person, a place or a time:

  kept       elapsed seconds, speed, distance, relative altitude, cadence, power,
             temperature (whole degrees), paved/unpaved flag, direction of travel,
             weather along the ride (wind, temperature, humidity)
  changed    time        -> seconds from the start of the kept part (no date or clock time)
             altitude    -> relative to the start; start altitude rounded to 100 m
             distance    -> from the start of the kept part
             direction   -> rotated by a random angle and randomly mirrored per ride;
                            weather wind directions get the same transform, so head-
                            and tailwinds stay correct (the transform is not stored)
             start / end -> the first and last TRIM metres (default 2 km) are removed
  removed    GPS positions, dates/times, heart rate, device and sensor serial numbers,
             names, user profile, laps, events, developer fields, everything else

Weather: before positions are discarded, the ride is sampled every 15 minutes
(position rounded to 0.1 degrees, ~11 km, and the hour) and historical weather
is requested from Open-Meteo (https://open-meteo.com, CC BY 4.0). Only the
weather values, at ride-relative times, are stored. Open-Meteo's free API is for
non-commercial use, and its server logs (kept 90 days) may contain the rounded
coordinates. Disable with --no-weather.

Contributors are identified only by a random code; a new one is created for
every import unless --contributor is given. Rider weight/height are stored
rounded. Raw files can be deleted after a successful import (--delete-original).

Usage:
  # rides of one contributor with the same answers (the website calls this per ride;
  # the questions are listed in data/questionnaire.md)
  .venv/bin/python -I tools/anonymize.py import RIDE1.fit RIDE2.fit RIDE3.csv \\
        --rider-kg 72 --height-cm 178 --bike-kg 8.4 --tyre-type road --tyre-width 28 \\
        --tyre-class fast --position road --pm-type crank --pm-sides dual \\
        --context solo --apparel kit --extra-kg 1.5 [--delete-original]
  # gravel tyres take --tyre-tread slick|file|knobby instead of --tyre-class
  .venv/bin/python -I tools/anonymize.py list
  .venv/bin/python -I tools/anonymize.py export RIDE_ID OUT.csv
  .venv/bin/python -I tools/anonymize.py delete-contributor CODE

Notes: deleting a file does not guarantee it cannot be recovered from an SSD.
The database is personal data under the GDPR as long as a contributor can be
re-identified (e.g. through their code); keep it private.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import secrets
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# Contributor data is personal data and is never stored in the repository. The
# database path comes from --db or the EP_DB environment variable; there is no default.
DEFAULT_DB = os.environ.get("EP_DB") or None
DB_HELP = "contributor database (required unless EP_DB is set)"
TRIM_M = 2000.0
HEADING_MIN_STEP_M = 3.0
WEATHER_STEP_S = 900          # one weather point per 15 minutes of ride time
WEATHER_GRID_DEG = 0.1        # positions sent to the weather service are rounded to this
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
UNPAVED = 34                  # FIT split_type

RIDE_TYPES = ["road", "gravel", "mountain", "commuting", "indoor"]
SUBSPORT_TO_RIDE = {"road": "road", "gravel_cycling": "gravel", "mountain": "mountain",
                    "commuting": "commuting", "indoor_cycling": "indoor", "generic": "road", None: "road"}

# Accepted answers (lower-case) -> stored value
TYRE_TYPES = {"road": "road", "gravel": "gravel", "mtb": "mtb", "mountain": "mtb", "mountain bike": "mtb",
              "road tyres": "road", "gravel tyres": "gravel", "mountain bike tyres": "mtb"}
TYRE_CLASSES = {"fast": "fast", "race": "fast", "performance": "fast", "all-round": "all-round",
                "allround": "all-round", "all round": "all-round", "durable": "durable",
                "puncture protection": "durable", "comfort": "durable",
                "fast (race / performance)": "fast", "durable (puncture protection / comfort)": "durable"}
POSITIONS = {"road": "road", "hoods": "road", "drops": "road", "tt": "tt", "time trial": "tt",
             "aero": "tt", "upright": "upright", "flat bar": "upright",
             "road bars (hoods and drops)": "road", "time trial / aero bars": "tt", "upright (flat bar)": "upright"}
PM_TYPES = {"pedal": "pedal", "pedals": "pedal", "crank": "crank", "crank arm": "crank", "spider": "spider",
            "spider / chainring": "spider", "hub": "hub", "rear hub": "hub", "trainer": "trainer", "other": "other"}
PM_SIDES = {"single": "single", "single-sided": "single", "left": "single", "one side": "single",
            "dual": "dual", "dual-sided": "dual", "double": "dual", "both": "dual", "both sides": "dual",
            "single-sided (one leg)": "single", "dual-sided (both legs)": "dual"}
# "Did you ride alone?"
CONTEXTS = {"solo": "solo", "alone": "solo", "solo the whole time": "solo",
            "group": "group", "in a group the whole time": "group",
            "partly": "partly", "partly in a group": "partly",
            "unsure": "unsure", "not sure": "unsure"}
# Clothing
APPAREL = {"kit": "kit", "cycling kit": "kit", "cycling kit (tight fit)": "kit",
           "casual": "casual", "casual clothes": "casual", "casual clothes / bags": "casual"}
# Extra weight carried (bottles, bags, tools, clothing beyond the kit): the only allowed values
EXTRA_KG_CHOICES = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
# Tread, asked instead of the tyre class for gravel tyres only
TREADS = {"slick": "slick", "file": "file", "file tread": "file", "file tread / low knobs": "file",
          "low knobs": "file", "semi-slick": "file", "knobby": "knobby"}
TYRE_WIDTH_RANGE = (18, 60)          # mm, whole millimetres

SCHEMA = """
CREATE TABLE IF NOT EXISTS contributors (
    code TEXT PRIMARY KEY,
    rider_kg INTEGER,
    height_cm INTEGER,
    created_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor TEXT NOT NULL REFERENCES contributors(code) ON DELETE CASCADE,
    ride_type TEXT,
    bike_kg REAL,
    tyre_type TEXT,
    tyre_class TEXT,             -- road and MTB tyres only
    tyre_tread TEXT,             -- gravel tyres only: slick / file / knobby
    tyre_width_mm INTEGER,       -- 18-60
    position TEXT,
    pm_type TEXT,
    pm_sides TEXT,
    group_ride INTEGER,          -- 1 if context is group or partly (kept for older tools)
    context TEXT,                -- solo / group / partly / unsure ("Did you ride alone?")
    apparel TEXT,                -- kit / casual
    extra_kg REAL,               -- extra weight carried, 0.5-3 kg
    speed_sensor INTEGER,
    device_model TEXT,
    start_alt_100m INTEGER,
    duration_s INTEGER,
    distance_m REAL,
    samples INTEGER,
    weather_points INTEGER,
    content_hash TEXT UNIQUE,
    imported_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS samples (
    ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    t_s INTEGER NOT NULL,
    speed REAL,
    dist_m REAL,
    alt_rel_m REAL,
    cadence INTEGER,
    power INTEGER,
    temp_c INTEGER,
    heading_deg REAL,
    unpaved INTEGER,
    PRIMARY KEY (ride_id, t_s)
);
CREATE TABLE IF NOT EXISTS weather (
    ride_id INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    t_s INTEGER NOT NULL,
    wind_ms REAL,
    wind_from_deg REAL,
    temp_c REAL,
    rh_pct REAL,
    PRIMARY KEY (ride_id, t_s)
);
"""


NEW_RIDE_COLUMNS = (("context", "TEXT"), ("apparel", "TEXT"), ("extra_kg", "REAL"),
                    ("tyre_tread", "TEXT"), ("tyre_width_mm", "INTEGER"))


def migrate(con):
    """Adds columns introduced after a database was created."""
    have = {row[1] for row in con.execute("PRAGMA table_info(rides)")}
    for name, kind in NEW_RIDE_COLUMNS:
        if name not in have:
            con.execute(f"ALTER TABLE rides ADD COLUMN {name} {kind}")
    con.commit()


def db_connect(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    migrate(con)
    return con


def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360.0


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- readers
# Each reader returns (rows, meta). rows: dicts with t (seconds from the first
# record), speed, dist, alt, cad, power, temp, lat, lon, heading, unpaved (any
# may be None). meta["t0"] is the absolute UTC start time (used only for the
# weather lookup, never stored). Heart rate and all other fields are not read.


def read_fit(path):
    import fitdecode  # only needed for FIT input

    rows, unpaved = [], []
    meta = {"sub_sport": None, "device_model": None, "speed_sensor": False, "t0": None}
    t0 = None
    with fitdecode.FitReader(path) as fit:
        for fr in fit:
            if not isinstance(fr, fitdecode.FitDataMessage):
                continue
            g = lambda k: fr.get_value(k, fallback=None)  # noqa: E731
            if fr.name == "record":
                ts = g("timestamp")
                if ts is None:
                    continue
                if t0 is None:
                    t0 = ts
                lat, lon = g("position_lat"), g("position_long")
                rows.append({
                    "t": (ts - t0).total_seconds(),
                    "speed": g("enhanced_speed") if g("enhanced_speed") is not None else g("speed"),
                    "dist": g("distance"),
                    "alt": g("enhanced_altitude") if g("enhanced_altitude") is not None else g("altitude"),
                    "cad": g("cadence"), "power": g("power"), "temp": g("temperature"),
                    "lat": lat * 180.0 / 2 ** 31 if lat is not None else None,
                    "lon": lon * 180.0 / 2 ** 31 if lon is not None else None,
                    "heading": None, "unpaved": 0,
                })
            elif fr.name == "split" and g("split_type") == UNPAVED:
                unpaved.append((g("start_time"), g("end_time")))
            elif fr.name == "session":
                meta["sub_sport"] = g("sub_sport")
            elif fr.name == "file_id":
                meta["device_model"] = str(g("garmin_product") or g("product") or "") or None
            elif fr.name == "device_info":
                # Only a yes/no flag is kept; serial numbers are never read.
                if str(g("antplus_device_type") or "") in ("bike_speed", "bike_speed_cadence") \
                        or str(g("garmin_product") or "") in ("gen3_bsm", "bsm"):
                    meta["speed_sensor"] = True
    if t0 is not None:
        meta["t0"] = t0 if t0.tzinfo else t0.replace(tzinfo=timezone.utc)
        spans = [((a - t0).total_seconds(), (b - t0).total_seconds()) for a, b in unpaved if a and b and b > a]
        for r in rows:
            r["unpaved"] = 1 if any(a <= r["t"] < b for a, b in spans) else 0
    return rows, meta


CSV_COLUMNS = {
    "t": ("t", "time", "secs", "seconds", "elapsed", "elapsed_s", "timestamp"),
    "speed": ("speed", "speed_ms", "enhanced_speed"),
    "speed_kmh": ("kph", "speed_kmh", "kmh"),
    "dist": ("distance", "dist", "distance_m"),
    "dist_km": ("km", "distance_km"),
    "alt": ("altitude", "alt", "elevation", "enhanced_altitude", "alt_m"),
    "cad": ("cadence", "cad", "rpm"),
    "power": ("power", "watts", "pwr"),
    "temp": ("temperature", "temp", "temp_c"),
    "lat": ("lat", "latitude", "position_lat"),
    "lon": ("lon", "lng", "longitude", "position_long"),
    "heading": ("heading", "bearing", "course"),
    "unpaved": ("unpaved",),
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        pick = {k: next((cols[n] for n in names if n in cols), None) for k, names in CSV_COLUMNS.items()}
        raw = list(reader)
    rows, t_first, t0 = [], None, None
    for i, r in enumerate(raw):
        get = lambda k: _num(r[pick[k]]) if pick[k] else None  # noqa: E731
        t = get("t")
        if t is None and pick["t"]:
            try:  # ISO timestamps
                ts = datetime.fromisoformat(r[pick["t"]].strip().replace("Z", "+00:00"))
                ts = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
                t0 = t0 or ts
                t = ts.timestamp()
            except ValueError:
                t = None
        if t is None:
            t = float(i)
        if t_first is None:
            t_first = t
        speed = get("speed")
        if speed is None and get("speed_kmh") is not None:
            speed = get("speed_kmh") / 3.6
        dist = get("dist")
        if dist is None and get("dist_km") is not None:
            dist = get("dist_km") * 1000.0
        up = get("unpaved")
        rows.append({"t": t - t_first, "speed": speed, "dist": dist, "alt": get("alt"), "cad": get("cad"),
                     "power": get("power"), "temp": get("temp"), "lat": get("lat"), "lon": get("lon"),
                     "heading": get("heading"), "unpaved": int(up) if up is not None else None})
    return rows, {"sub_sport": None, "device_model": None, "speed_sensor": None, "t0": t0}


# ---------------------------------------------------------------- weather


def weather_points(rows, t0):
    """(t_s from first record, lat, lon, UTC hour) every WEATHER_STEP_S, positions rounded."""
    if t0 is None:
        return []
    pts, next_t = [], 0.0
    for r in rows:
        if r["t"] >= next_t and r.get("lat") is not None and r.get("lon") is not None:
            lat = round(round(r["lat"] / WEATHER_GRID_DEG) * WEATHER_GRID_DEG, 2)
            lon = round(round(r["lon"] / WEATHER_GRID_DEG) * WEATHER_GRID_DEG, 2)
            when = t0 + timedelta(seconds=r["t"])
            pts.append((r["t"], lat, lon, when.replace(minute=0, second=0, microsecond=0) +
                        (timedelta(hours=1) if when.minute >= 30 else timedelta())))
            next_t = r["t"] + WEATHER_STEP_S
    return pts


def fetch_weather(pts):
    """Hourly weather for each point from Open-Meteo. Returns list of dicts (or None per point)."""
    if not pts:
        return []
    locs = sorted({(p[1], p[2]) for p in pts})
    days = sorted({p[3].date() for p in pts})
    query = urllib.parse.urlencode({
        "latitude": ",".join(f"{a:.2f}" for a, _ in locs),
        "longitude": ",".join(f"{b:.2f}" for _, b in locs),
        "start_date": days[0].isoformat(), "end_date": days[-1].isoformat(),
        "hourly": "wind_speed_10m,wind_direction_10m,temperature_2m,relative_humidity_2m",
        "wind_speed_unit": "ms", "timezone": "GMT",
    })
    with urllib.request.urlopen(f"{WEATHER_URL}?{query}", timeout=30) as resp:
        data = json.load(resp)
    if isinstance(data, dict):
        data = [data]
    by_loc = dict(zip(locs, data))
    out = []
    for _, lat, lon, hour in pts:
        h = by_loc[(lat, lon)]["hourly"]
        key = hour.strftime("%Y-%m-%dT%H:00")
        if key not in h["time"]:
            out.append(None)
            continue
        i = h["time"].index(key)
        out.append({"wind_ms": h["wind_speed_10m"][i], "wind_from_deg": h["wind_direction_10m"][i],
                    "temp_c": h["temperature_2m"][i], "rh_pct": h["relative_humidity_2m"][i]})
    return out


# ---------------------------------------------------------------- anonymize


def anonymize(rows, trim_m=TRIM_M, rng=None):
    """Returns (samples, start_alt_100m, transform). transform = (t_start, rot, mirror)
    is needed to align weather with the samples and is never stored."""
    rng = rng or secrets.SystemRandom()
    rows = [r for r in rows if r["dist"] is not None]
    if not rows:
        raise ValueError("no distance data")

    # Direction of travel from GPS (before positions are discarded).
    last = None
    for r in rows:
        if r.get("lat") is not None and r.get("lon") is not None:
            if last is None:
                last = (r["lat"], r["lon"])
            else:
                dy = (r["lat"] - last[0]) * 111320.0
                dx = (r["lon"] - last[1]) * 111320.0 * math.cos(math.radians(r["lat"]))
                if dx * dx + dy * dy >= HEADING_MIN_STEP_M ** 2:
                    r["heading"] = bearing(last[0], last[1], r["lat"], r["lon"])
                    last = (r["lat"], r["lon"])
    h = None
    for r in rows:
        if r.get("heading") is not None:
            h = r["heading"]
        r["heading"] = h

    total = rows[-1]["dist"] - rows[0]["dist"]
    if total <= 2 * trim_m + 1000:
        raise ValueError(f"ride too short after trimming ({total / 1000:.1f} km)")
    d0 = rows[0]["dist"]
    kept = [r for r in rows if trim_m <= r["dist"] - d0 <= total - trim_m]

    rot = rng.uniform(0.0, 360.0)
    mirror = rng.random() < 0.5
    t_start, dist_start = kept[0]["t"], kept[0]["dist"]
    alt_start = next((r["alt"] for r in kept if r["alt"] is not None), None)
    out = {}
    for r in kept:
        t_s = int(round(r["t"] - t_start))
        if t_s in out:
            continue
        out[t_s] = {
            "t_s": t_s,
            "speed": round(r["speed"], 3) if r["speed"] is not None else None,
            "dist_m": round(r["dist"] - dist_start, 1),
            "alt_rel_m": round(r["alt"] - alt_start, 1) if (r["alt"] is not None and alt_start is not None) else None,
            "cadence": int(r["cad"]) if r["cad"] is not None else None,
            "power": int(r["power"]) if r["power"] is not None else None,
            "temp_c": int(round(r["temp"])) if r["temp"] is not None else None,
            "heading_deg": round(transform_dir(r["heading"], rot, mirror), 1) if r["heading"] is not None else None,
            "unpaved": r.get("unpaved"),
        }
    samples = [out[k] for k in sorted(out)]
    start_alt_100m = int(round(alt_start / 100.0)) * 100 if alt_start is not None else None
    return samples, start_alt_100m, (t_start, rot, mirror)


def transform_dir(deg, rot, mirror):
    return ((-deg if mirror else deg) + rot) % 360.0


def content_hash(samples):
    h = hashlib.sha256()
    for s in samples[:600]:
        h.update(f"{s['t_s']},{s['speed']},{s['power']},{s['alt_rel_m']}".encode())
    return h.hexdigest()


# ---------------------------------------------------------------- import


def norm(value, table, what):
    key = str(value).strip().lower()
    if key not in table:
        raise ValueError(f"unknown {what} '{value}' (expected one of: {', '.join(sorted(set(table.values())))})")
    return table[key]


def new_contributor(con, rider_kg, height_cm):
    code = secrets.token_hex(4).upper()
    con.execute("INSERT INTO contributors VALUES (?, ?, ?, ?)",
                (code, round(rider_kg) if rider_kg else None, round(height_cm) if height_cm else None,
                 datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    return code


def import_ride(con, path, contributor, setup, trim_m, use_weather, ride_type=None, require_power=True):
    """Imports one file. Returns ride id. Raises on problems (nothing is written then)."""
    rows, meta = read_fit(path) if path.lower().endswith(".fit") else read_csv(path)
    if require_power and not any(r["power"] for r in rows):
        raise ValueError("no power data (a power meter is required)")
    pts = weather_points(rows, meta["t0"]) if use_weather else []
    samples, start_alt, (t_start, rot, mirror) = anonymize(rows, trim_m)
    weather = []
    if pts:
        try:
            values = fetch_weather(pts)
            for (t, *_), w in zip(pts, values):
                if w and None not in w.values():
                    weather.append({"t_s": int(round(t - t_start)), "wind_ms": round(w["wind_ms"], 1),
                                    "wind_from_deg": round(transform_dir(w["wind_from_deg"], rot, mirror), 0),
                                    "temp_c": round(w["temp_c"], 1), "rh_pct": round(w["rh_pct"], 0)})
        except Exception as exc:  # weather is optional
            print(f"  weather unavailable: {exc}")
    del rows, pts  # positions and absolute times are not kept beyond this point

    cur = con.execute(
        "INSERT INTO rides (contributor, ride_type, bike_kg, tyre_type, tyre_class, tyre_tread, tyre_width_mm, "
        "position, pm_type, pm_sides, group_ride, context, apparel, extra_kg, speed_sensor, device_model, "
        "start_alt_100m, duration_s, distance_m, samples, weather_points, content_hash, imported_utc) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (contributor, ride_type or SUBSPORT_TO_RIDE.get(meta["sub_sport"], "road"), setup["bike_kg"],
         setup["tyre_type"], setup["tyre_class"], setup["tyre_tread"], setup["tyre_width_mm"],
         setup["position"], setup["pm_type"], setup["pm_sides"],
         int(setup["context"] in ("group", "partly")), setup["context"], setup["apparel"], setup["extra_kg"],
         None if meta["speed_sensor"] is None else int(meta["speed_sensor"]),
         meta["device_model"], start_alt, samples[-1]["t_s"], samples[-1]["dist_m"], len(samples), len(weather),
         content_hash(samples), datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    ride_id = cur.lastrowid
    con.executemany("INSERT INTO samples VALUES (:ride_id, :t_s, :speed, :dist_m, :alt_rel_m, :cadence, :power, "
                    ":temp_c, :heading_deg, :unpaved)", [dict(s, ride_id=ride_id) for s in samples])
    con.executemany("INSERT OR IGNORE INTO weather VALUES (:ride_id, :t_s, :wind_ms, :wind_from_deg, :temp_c, "
                    ":rh_pct)", [dict(w, ride_id=ride_id) for w in weather])
    return ride_id, samples, weather


def import_contributor(con, rides, rider_kg, height_cm, trim_m, use_weather, delete_original,
                       contributor=None, ride_type=None, require_power=True):
    """Creates a contributor (unless given) and imports their rides, a list of
    (path, setup) with the answers for each ride. Returns the code or None."""
    code = contributor or new_contributor(con, rider_kg, height_cm)
    imported = 0
    for path, setup in rides:
        name = os.path.basename(path)
        try:
            ride_id, samples, weather = import_ride(con, path, code, setup, trim_m, use_weather, ride_type,
                                                    require_power)
        except sqlite3.IntegrityError:
            print(f"  SKIPPED {name}: already imported")
            continue
        except Exception as exc:
            print(f"  SKIPPED {name}: {exc}")
            continue
        con.commit()
        imported += 1
        print(f"  imported {name} as ride {ride_id}: {samples[-1]['dist_m'] / 1000:.1f} km, "
              f"{len(samples)} samples, {len(weather)} weather points")
        if delete_original:
            os.remove(path)
            print(f"    deleted original {name}")
    if imported == 0 and contributor is None:
        con.execute("DELETE FROM contributors WHERE code = ?", (code,))
        con.commit()
        print("  no rides imported; contributor not created")
        return None
    con.commit()
    return code


def extra_kg_from(value):
    text = str(value).strip().lower().replace("kg", "").replace(",", ".").strip()
    try:
        kg = float(text)
    except ValueError:
        raise ValueError(f"unknown extra weight '{value}'") from None
    if kg not in EXTRA_KG_CHOICES:
        raise ValueError(f"extra weight must be one of {', '.join(f'{c:g} kg' for c in EXTRA_KG_CHOICES)}")
    return kg


def tyre_width_from(value):
    w = _num(value)
    lo, hi = TYRE_WIDTH_RANGE
    if w is None or w != int(w) or not lo <= w <= hi:
        raise ValueError(f"tyre width must be a whole number of millimetres from {lo} to {hi}")
    return int(w)


def setup_from(values):
    """The answers for one ride, checked and normalized. Raises ValueError.
    Gravel tyres are described by their tread, road and MTB tyres by their class."""
    bike = _num(values["bike_kg"])
    if not bike or not 3 <= bike <= 40:
        raise ValueError("bike weight missing or outside 3-40 kg")
    tyre_type = norm(values["tyre_type"], TYRE_TYPES, "tyre type")
    if tyre_type == "gravel":
        tyre_class, tyre_tread = None, norm(values.get("tyre_tread") or "", TREADS, "tread")
    else:
        tyre_class, tyre_tread = norm(values.get("tyre_class") or "", TYRE_CLASSES, "tyre class"), None
    return {"bike_kg": bike,
            "tyre_type": tyre_type,
            "tyre_class": tyre_class,
            "tyre_tread": tyre_tread,
            "tyre_width_mm": tyre_width_from(values["tyre_width"]),
            "position": norm(values["position"], POSITIONS, "position"),
            "pm_type": norm(values["pm_type"], PM_TYPES, "power meter type"),
            "pm_sides": norm(values["pm_sides"], PM_SIDES, "power meter sides"),
            "context": norm(values["context"], CONTEXTS, "ride context"),
            "apparel": norm(values["apparel"], APPAREL, "clothing"),
            "extra_kg": extra_kg_from(values["extra_kg"])}


# ---------------------------------------------------------------- commands


def cmd_import(con, a):
    try:
        setup = setup_from(vars(a))
    except ValueError as exc:
        sys.exit(str(exc))
    code = import_contributor(con, [(f, setup) for f in a.files], a.rider_kg, a.height_cm, a.trim_m,
                              not a.no_weather, a.delete_original, a.contributor, a.ride_type,
                              not a.allow_no_power)
    if code:
        print(f"contributor code: {code}")


def cmd_list(con, a):
    print("id | contributor | ride type | tyres | position | clothing | bike kg | extra kg | rider kg | "
          "duration s | km | weather pts | pm | context")
    for row in con.execute("SELECT r.id, r.contributor, r.ride_type, r.tyre_type || ' ' || "
                           "COALESCE(r.tyre_width_mm, '?') || ' mm ' || COALESCE(r.tyre_class, r.tyre_tread, '?'), "
                           "r.position, r.apparel, r.bike_kg, r.extra_kg, c.rider_kg, r.duration_s, "
                           "round(r.distance_m / 1000, 1), r.weather_points, r.pm_type || '/' || r.pm_sides, "
                           "r.context "
                           "FROM rides r JOIN contributors c ON c.code = r.contributor ORDER BY r.id"):
        print(" | ".join(str(x) for x in row))


def cmd_export(con, a):
    cur = con.execute("SELECT t_s, speed, dist_m, alt_rel_m, cadence, power, temp_c, heading_deg, unpaved "
                      "FROM samples WHERE ride_id = ? ORDER BY t_s", (a.ride_id,))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([d[0] for d in cur.description])
        w.writerows(cur)
    wx = con.execute("SELECT t_s, wind_ms, wind_from_deg, temp_c, rh_pct FROM weather WHERE ride_id = ? "
                     "ORDER BY t_s", (a.ride_id,)).fetchall()
    if wx:
        base, ext = os.path.splitext(a.out)
        with open(f"{base}_weather{ext}", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_s", "wind_ms", "wind_from_deg", "temp_c", "rh_pct"])
            w.writerows(wx)
    print(f"wrote {a.out}" + (f" and {base}_weather{ext}" if wx else ""))


def cmd_delete_contributor(con, a):
    n = con.execute("SELECT COUNT(*) FROM rides WHERE contributor = ?", (a.code,)).fetchone()[0]
    con.execute("DELETE FROM contributors WHERE code = ?", (a.code,))
    con.commit()
    con.execute("VACUUM")
    print(f"deleted contributor {a.code} and {n} rides")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DEFAULT_DB, required=DEFAULT_DB is None, help=DB_HELP)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--trim-m", type=float, default=TRIM_M, help="metres removed at start and end (default 2000)")
        p.add_argument("--no-weather", action="store_true", help="do not look up weather")
        p.add_argument("--delete-original", action="store_true")
        p.add_argument("--allow-no-power", action="store_true", help="testing only: import rides without power")

    p = sub.add_parser("import", help="import rides with the same answers (creates a new contributor)")
    p.add_argument("files", nargs="+")
    p.add_argument("--rider-kg", type=float, required=True)
    p.add_argument("--height-cm", type=float)
    p.add_argument("--bike-kg", type=float, required=True)
    p.add_argument("--tyre-type", required=True)
    p.add_argument("--tyre-width", required=True, help="mm, 18-60")
    p.add_argument("--tyre-class", help="road and MTB tyres: fast, all-round or durable")
    p.add_argument("--tyre-tread", help="gravel tyres: slick, file or knobby")
    p.add_argument("--position", required=True)
    p.add_argument("--pm-type", required=True)
    p.add_argument("--pm-sides", required=True)
    p.add_argument("--context", required=True, help="solo, group, partly or unsure")
    p.add_argument("--apparel", required=True, help="kit or casual")
    p.add_argument("--extra-kg", required=True, help="0.5, 1, 1.5, 2, 2.5 or 3")
    p.add_argument("--ride-type", choices=RIDE_TYPES, help="default: from the FIT file, else road")
    p.add_argument("--contributor", help="add to an existing contributor instead of creating one")
    common(p)
    sub.add_parser("list")
    p = sub.add_parser("export")
    p.add_argument("ride_id", type=int)
    p.add_argument("out")
    p = sub.add_parser("delete-contributor")
    p.add_argument("code")
    a = ap.parse_args()
    con = db_connect(a.db)
    {"import": cmd_import, "list": cmd_list, "export": cmd_export,
     "delete-contributor": cmd_delete_contributor}[a.cmd](con, a)


if __name__ == "__main__":
    main()
