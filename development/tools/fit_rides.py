"""Fit rolling resistance (Crr), drag area (CdA) and wind to rides with measured power.

Reads anonymized rides from the database written by anonymize.py. For each ride
with power, the measured power is compared with the physical model:

  P = (Crr m g cos(th) v + m g sin(th) v + 1/2 rho (CdA + Fw) va |va| v
       + m_eff a v + bearings) / eta,          va = v + headwind

The fit compares mean power over BLOCK_S-second blocks of consecutive pedalling
seconds (cadence > 0, power >= MIN_POWER_W, speed > 2 m/s). Gravity and acceleration are
taken from energy over each block (m g dh and 1/2 m_eff d(v^2), divided by the
block time), so no gradient estimate is needed and barometer noise only adds
random, not systematic, error. Rolling and air terms are summed per second.

Wind modes:
  free     constant wind per ride: headwind = wx cos(h) + wy sin(h), fitted
           (direction in the ride's rotated frame, see anonymize.py)
  weather  headwind = k * (Open-Meteo 10 m wind projected on the heading), k fitted;
           k is the 10 m -> rider-height exposure factor (the add-on uses 0.54)
  none     no wind

Usage:
  .venv/bin/python -I tools/fit_rides.py fit [--db DB] [--wind free|weather|none] [--extra-kg 1.5]
  .venv/bin/python -I tools/fit_rides.py selftest --db DB --ride ID [--crr 0.008 --cda 0.34
        --wind-ms 4 --wind-from 70 --noise-w 20 --bias 0.02 --extra-kg 1.5]

The self-test replaces a ride's power (in a temporary copy of the database) with
the model's power for known Crr, CdA and wind, adds noise and power-meter bias,
computes it with a finer gradient than the fit uses, and checks that the fit
recovers the known values.
"""
import argparse
import math
import os
import shutil
import sqlite3
import sys
import tempfile

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anonymize as an  # noqa: E402

G = 9.80665
ETA = 0.976
WHEEL_DRAG_AREA = 0.0044
WHEEL_INERTIA_KG = 1.4
GRADE_HALF_M = 20.0
BLOCK_S = 20
MIN_POWER_W = 40
DEFAULT_EXTRA_KG = 1.5
DEFAULT_TEMP_C = 15.0
DEFAULT_RH = 50.0


# ---------------------------------------------------------------- data


def load_ride(con, ride_id, extra_kg):
    meta = con.execute(
        "SELECT r.id, r.contributor, r.ride_type, r.bike_kg, r.tyre_type, "
        "COALESCE(r.tyre_class, r.tyre_tread), r.position, r.pm_type, "
        "r.pm_sides, r.group_ride, r.start_alt_100m, c.rider_kg, c.height_cm, r.context, r.apparel, r.extra_kg, "
        "r.tyre_width_mm "
        "FROM rides r JOIN contributors c ON c.code = r.contributor WHERE r.id = ?", (ride_id,)).fetchone()
    keys = ["id", "contributor", "ride_type", "bike_kg", "tyre_type", "tyre_class", "position", "pm_type",
            "pm_sides", "group_ride", "start_alt", "rider_kg", "height_cm", "context", "apparel", "ride_extra_kg",
            "tyre_width_mm"]
    m = dict(zip(keys, meta))
    rows = con.execute("SELECT t_s, speed, dist_m, alt_rel_m, cadence, power, temp_c, heading_deg, unpaved "
                       "FROM samples WHERE ride_id = ? ORDER BY t_s", (ride_id,)).fetchall()
    arr = np.array([[np.nan if v is None else v for v in r] for r in rows], dtype=float)
    d = {k: arr[:, i] for i, k in enumerate(["t", "v", "dist", "alt", "cad", "power", "temp", "heading", "unpaved"])}
    wx = con.execute("SELECT t_s, wind_ms, wind_from_deg, temp_c, rh_pct FROM weather WHERE ride_id = ? "
                     "ORDER BY t_s", (ride_id,)).fetchall()
    d["weather"] = np.array(wx, dtype=float) if wx else None
    if not m["rider_kg"] or not m["bike_kg"]:
        raise ValueError(f"ride {ride_id}: rider or bike weight missing in the database")
    # The contributor's own answer; extra_kg (the --extra-kg option) only fills in for
    # rides imported before the question existed, or overrides when given explicitly.
    m["extra_kg"] = extra_kg if extra_kg is not None else (
        m["ride_extra_kg"] if m["ride_extra_kg"] is not None else DEFAULT_EXTRA_KG)
    m["mass"] = m["rider_kg"] + m["bike_kg"] + m["extra_kg"]
    return m, d


def centred_grade(dist, alt, half=GRADE_HALF_M):
    """Least-squares slope of altitude over distance within +/- half metres."""
    n = len(dist)
    g = np.full(n, np.nan)
    lo = hi = 0
    for i in range(n):
        while dist[lo] < dist[i] - half:
            lo += 1
        while hi + 1 < n and dist[hi + 1] <= dist[i] + half:
            hi += 1
        x, y = dist[lo:hi + 1], alt[lo:hi + 1]
        ok = ~np.isnan(x) & ~np.isnan(y)
        if ok.sum() >= 3 and np.ptp(x[ok]) > half:
            xm = x[ok] - x[ok].mean()
            g[i] = (xm * (y[ok] - y[ok].mean())).sum() / (xm * xm).sum()
    return np.clip(g, -0.3, 0.3)


def prepare(m, d, grade_half=GRADE_HALF_M):
    """Per-second inputs for the model plus the blocks used for fitting."""
    t, v = d["t"], d["v"]
    grade = centred_grade(d["dist"], d["alt"], grade_half)
    acc = np.full(len(t), np.nan)
    acc[1:-1] = (v[2:] - v[:-2]) / np.maximum(t[2:] - t[:-2], 1)
    alt_abs = (m["start_alt"] or 0) + np.nan_to_num(d["alt"])
    pressure = 101325.0 * (1 - 2.25577e-5 * alt_abs) ** 5.25588

    # Weather interpolated in time (wind as vector components to avoid angle wrap)
    temp = np.full(len(t), DEFAULT_TEMP_C)
    rh = np.full(len(t), DEFAULT_RH)
    hw_weather = np.zeros(len(t))
    has_weather = d["weather"] is not None and len(d["weather"]) > 0
    if has_weather:
        w = d["weather"]
        ws, wd = w[:, 1], np.radians(w[:, 2])
        u = np.interp(t, w[:, 0], ws * np.sin(wd))
        n_ = np.interp(t, w[:, 0], ws * np.cos(wd))
        temp = np.interp(t, w[:, 0], w[:, 3])
        rh = np.interp(t, w[:, 0], w[:, 4])
        h = np.radians(d["heading"])
        hw_weather = u * np.sin(h) + n_ * np.cos(h)   # wind FROM (u, n) projected on heading
    elif not np.all(np.isnan(d["temp"])):
        temp = np.where(np.isnan(d["temp"]), DEFAULT_TEMP_C, d["temp"])
    tk = temp + 273.15
    pv = rh / 100 * 610.78 * 10 ** (7.5 * temp / (temp + 237.3))
    rho = (pressure - pv) / (287.058 * tk) + pv / (461.495 * tk)

    # Only seconds where the rider is clearly pushing: near-zero power with the cranks
    # turning (soft-pedalling downhill, braking) cannot be explained by the model.
    ok = (d["cad"] > 0) & (d["power"] >= MIN_POWER_W) & (v > 2) & ~np.isnan(d["heading"]) & ~np.isnan(d["alt"])
    # blocks of BLOCK_S consecutive valid seconds
    blocks, run = [], []
    for i in range(len(t)):
        if ok[i] and (not run or t[i] - t[run[-1]] == 1):
            run.append(i)
        else:
            run = [i] if ok[i] else []
        if len(run) == BLOCK_S:
            blocks.append(np.array(run))
            run = []
    h = np.radians(d["heading"])
    # Energy terms per block (gravity and kinetic), in watts averaged over the block.
    alt = d["alt"]
    e_grav, e_kin = [], []
    for b in blocks:
        i0, i1 = b[0] - 1 if b[0] > 0 else b[0], b[-1]
        dt = max(t[i1] - t[i0], 1)
        e_grav.append((alt[i1] - alt[i0]) * G / dt)                       # x mass
        e_kin.append(0.5 * (v[i1] ** 2 - v[i0] ** 2) / dt)                  # x effective mass
    return {"v": v, "grade": grade, "acc": acc, "rho": rho, "cos_h": np.cos(h), "sin_h": np.sin(h),
            "hw_weather": hw_weather, "has_weather": has_weather, "power": d["power"], "blocks": blocks,
            "heading": d["heading"], "e_grav": np.array(e_grav), "e_kin": np.array(e_kin)}


def model_power(p, crr, cda, headwind, mass):
    v, th = p["v"], np.arctan(p["grade"])
    va = v + headwind
    pw = (crr * mass * G * np.cos(th) * v + mass * G * np.sin(th) * v
          + 0.5 * p["rho"] * (cda + WHEEL_DRAG_AREA) * va * np.abs(va) * v
          + (mass + WHEEL_INERTIA_KG) * p["acc"] * v + v * (91 + 8.7 * v) * 1e-3)
    return pw / ETA


# ---------------------------------------------------------------- fit


def fit_ride(m, p, wind_mode):
    idx = np.concatenate(p["blocks"]) if p["blocks"] else np.array([], dtype=int)
    if len(p["blocks"]) < 8:
        return None
    meas = np.array([p["power"][b].mean() for b in p["blocks"]])

    def headwind(x):
        if wind_mode == "free":
            return x[2] * p["cos_h"] + x[3] * p["sin_h"]
        if wind_mode == "weather":
            return x[2] * p["hw_weather"]
        return 0.0

    v = p["v"]
    mass = m["mass"]
    grav = mass * p["e_grav"]
    kin = (mass + WHEEL_INERTIA_KG) * p["e_kin"]

    def resid(x):
        va = v + headwind(x)
        per_s = x[0] * mass * G * v + 0.5 * p["rho"] * (x[1] + WHEEL_DRAG_AREA) * va * np.abs(va) * v \
            + v * (91 + 8.7 * v) * 1e-3
        pred = (np.array([per_s[b].mean() for b in p["blocks"]]) + grav + kin) / ETA
        return pred - meas

    x0 = {"free": [0.006, 0.33, 0.0, 0.0], "weather": [0.006, 0.33, 0.5], "none": [0.006, 0.33]}[wind_mode]
    lo = {"free": [0.001, 0.12, -15, -15], "weather": [0.001, 0.12, 0.0], "none": [0.001, 0.12]}[wind_mode]
    hi = {"free": [0.03, 0.9, 15, 15], "weather": [0.03, 0.9, 1.5], "none": [0.03, 0.9]}[wind_mode]
    r = least_squares(resid, x0, bounds=(lo, hi))
    n, k = len(meas), len(x0)
    s2 = (r.fun ** 2).sum() / max(n - k, 1)
    try:
        cov = np.linalg.inv(r.jac.T @ r.jac) * s2
        se = np.sqrt(np.diag(cov))
        corr = cov[0, 1] / (se[0] * se[1])
    except np.linalg.LinAlgError:
        se, corr = np.full(k, np.nan), np.nan
    # identifiability diagnostics
    hd = np.radians(p["heading"][idx])
    heading_spread = 1 - math.hypot(np.cos(hd).mean(), np.sin(hd).mean())   # 0 = one direction, 1 = all
    vb = np.array([p["v"][b].mean() for b in p["blocks"]]) * 3.6
    out = {"crr": r.x[0], "cda": r.x[1], "crr_se": se[0], "cda_se": se[1], "corr": corr,
           "rmse": math.sqrt((r.fun ** 2).mean()), "mean_power": meas.mean(), "blocks": n,
           "heading_spread": heading_spread, "v10": np.percentile(vb, 10), "v90": np.percentile(vb, 90)}
    if wind_mode == "free":
        out["wind_ms"] = math.hypot(r.x[2], r.x[3])
        out["wind_from"] = math.degrees(math.atan2(r.x[3], r.x[2])) % 360
        out["wind_se"] = math.hypot(se[2], se[3])
    elif wind_mode == "weather":
        out["k"], out["k_se"] = r.x[2], se[2]
    warn = []
    if heading_spread < 0.3 and wind_mode == "free":
        warn.append("little heading variety: wind and CdA hard to separate")
    if out["v90"] - out["v10"] < 8:
        warn.append("narrow speed range: Crr and CdA hard to separate")
    if out["crr_se"] > 0.2 * out["crr"] or out["cda_se"] > 0.15 * out["cda"]:
        warn.append(f"uncertain Crr/CdA (correlation {corr:+.2f})")
    if r.x[0] <= lo[0] * 1.05 or r.x[0] >= hi[0] * 0.95 or r.x[1] <= lo[1] * 1.05 or r.x[1] >= hi[1] * 0.95:
        warn.append("fit hit a limit: the model does not explain this ride (drafting? power meter?)")
    context = m["context"] or ("group" if m["group_ride"] else None)
    if context in ("group", "partly"):
        warn.append(f"{'group' if context == 'group' else 'partly group'} ride: drafting lowers apparent CdA")
    elif context == "unsure":
        warn.append("rider not sure whether it was a group ride: check for drafting")
    out["warnings"] = warn
    return out


def cmd_fit(a):
    con = sqlite3.connect(a.db)
    ids = [r[0] for r in con.execute("SELECT id FROM rides ORDER BY id")]
    results = []
    print(f"wind mode: {a.wind}; extra mass "
          f"{'per contributor answer' if a.extra_kg is None else f'{a.extra_kg} kg (override)'}; block {BLOCK_S} s")
    for rid in ids:
        try:
            m, d = load_ride(con, rid, a.extra_kg)
        except ValueError as exc:
            print(f"skipped {exc}")
            continue
        if np.nansum(d["power"]) == 0:
            continue
        p = prepare(m, d)
        if a.wind == "weather" and not p["has_weather"]:
            print(f"ride {rid}: no weather stored, skipped")
            continue
        f = fit_ride(m, p, a.wind)
        if f is None:
            print(f"ride {rid}: too few pedalling blocks, skipped")
            continue
        results.append((m, f))
        extra = ""
        if a.wind == "free":
            extra = f" wind {f['wind_ms']:.1f}±{f['wind_se']:.1f} m/s from {f['wind_from']:.0f}° (rotated frame)"
        elif a.wind == "weather":
            extra = f" exposure k {f['k']:.2f}±{f['k_se']:.2f}"
        print(f"ride {rid} ({m['contributor']}, {m['tyre_type']} {m['tyre_width_mm'] or '?'} mm/{m['tyre_class']}, "
              f"{m['position']}, "
              f"{m['mass']:.0f} kg): Crr {f['crr']:.4f}±{f['crr_se']:.4f}  CdA {f['cda']:.3f}±{f['cda_se']:.3f}"
              f"{extra}  rmse {f['rmse']:.0f} W of {f['mean_power']:.0f} W, {f['blocks']} blocks, "
              f"{f['v10']:.0f}-{f['v90']:.0f} km/h, heading spread {f['heading_spread']:.2f}")
        for w in f["warnings"]:
            print(f"   ! {w}")
    if len(results) > 1:
        print("\nby tyre type/class or tread (inverse-variance weighted Crr):")
        groups = {}
        for m, f in results:
            if any(w.startswith(("uncertain", "group ride", "partly group", "rider not sure", "fit hit"))
                   for w in f["warnings"]):
                continue
            groups.setdefault((m["tyre_type"], m["tyre_class"]), []).append(f)
        for (tt, tc), fs in sorted(groups.items()):
            w = np.array([1 / max(f["crr_se"], 1e-4) ** 2 for f in fs])
            crr = (np.array([f["crr"] for f in fs]) * w).sum() / w.sum()
            print(f"  {tt}/{tc}: Crr {crr:.4f} from {len(fs)} rides")


def cmd_selftest(a):
    tmp = tempfile.mkdtemp(prefix="fit_selftest_")
    try:
        db = os.path.join(tmp, "t.sqlite")
        shutil.copy(a.db, db)
        con = sqlite3.connect(db)
        m, d = load_ride(con, a.ride, a.extra_kg)
        # Truth computed with a finer gradient than the fit uses, plus noise and bias
        p_true = prepare(m, d, grade_half=8.0)
        wd = math.radians(a.wind_from)
        hw = a.wind_ms * (math.cos(wd) * p_true["cos_h"] + math.sin(wd) * p_true["sin_h"])
        pw = model_power(p_true, a.crr, a.cda, hw, m["mass"]) * (1 + a.bias)
        rng = np.random.default_rng(1)
        pw = pw + rng.normal(0, a.noise_w, len(pw))
        coasting = (d["cad"] <= 0) | np.isnan(d["cad"])
        pw = np.where(coasting | np.isnan(pw), 0, np.maximum(pw, 1))
        con.executemany("UPDATE samples SET power = ? WHERE ride_id = ? AND t_s = ?",
                        [(int(round(x)), a.ride, int(t)) for x, t in zip(pw, d["t"])])
        con.commit()
        m, d = load_ride(con, a.ride, a.extra_kg)
        f = fit_ride(m, prepare(m, d), "free")
        print(f"truth: Crr {a.crr:.4f}  CdA {a.cda:.3f}  wind {a.wind_ms:.1f} m/s from {a.wind_from:.0f}°  "
              f"(noise {a.noise_w} W, power-meter bias {a.bias:+.0%})")
        if f is None:
            print("fit: too few pedalling blocks")
            return
        print(f"fit:   Crr {f['crr']:.4f}±{f['crr_se']:.4f}  CdA {f['cda']:.3f}±{f['cda_se']:.3f}  "
              f"wind {f['wind_ms']:.1f}±{f['wind_se']:.1f} m/s from {f['wind_from']:.0f}°  "
              f"rmse {f['rmse']:.1f} W, heading spread {f['heading_spread']:.2f}, "
              f"{f['v10']:.0f}-{f['v90']:.0f} km/h")
        for w in f["warnings"]:
            print(f"   ! {w}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=an.DEFAULT_DB, required=an.DEFAULT_DB is None, help=an.DB_HELP)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fit")
    p.add_argument("--wind", choices=["free", "weather", "none"], default="free")
    p.add_argument("--extra-kg", type=float, default=None,
                   help="override the extra weight each contributor entered (default: their answer)")
    p = sub.add_parser("selftest")
    p.add_argument("--ride", type=int, required=True)
    p.add_argument("--crr", type=float, default=0.008)
    p.add_argument("--cda", type=float, default=0.34)
    p.add_argument("--wind-ms", type=float, default=4.0)
    p.add_argument("--wind-from", type=float, default=70.0)
    p.add_argument("--noise-w", type=float, default=20.0)
    p.add_argument("--bias", type=float, default=0.0)
    p.add_argument("--extra-kg", type=float, default=None,
                   help="override the extra weight each contributor entered (default: their answer)")
    a = ap.parse_args()
    {"fit": cmd_fit, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    main()
