"""Check that anonymized rides give the same power estimates as the originals.

For each FIT file:
  pass 1  model on the original file
  pass 2  copy the file, run the anonymizer CLI on the copy (temporary database),
          load the anonymized samples and run the model again
Then compare per second over the part the anonymizer keeps (after a warm-up),
whole-ride averages and recorded power (if any).

Usage:
  .venv/bin/python -I tools/anon_check.py FILE.fit [...] --rider-kg 75 --height-m 1.75 \\
      --bike-kg 9 --extra-kg 1.5 --tyre-type 1 --tyre-width 42 --tyre-tread 1 --position 0 [--no-weather]
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anonymize as an  # noqa: E402
import replay  # noqa: E402

WARMUP_S = 60
TYRE_NAMES = ["road", "gravel"]
CLASS_NAMES = ["fast", "all-round", "durable"]
TREAD_NAMES = ["slick", "file", "knobby"]
POS_NAMES = ["road", "tt", "upright"]


def anon_rows(db, ride_id):
    con = sqlite3.connect(db)
    start_alt = con.execute("SELECT start_alt_100m FROM rides WHERE id = ?", (ride_id,)).fetchone()[0] or 0
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    rows = []
    for t, sp, d, alt, cad, pw, tc, hd, up in con.execute(
            "SELECT t_s, speed, dist_m, alt_rel_m, cadence, power, temp_c, heading_deg, unpaved "
            "FROM samples WHERE ride_id = ? ORDER BY t_s", (ride_id,)):
        rows.append({"t": base + timedelta(seconds=t), "t_s": t, "speed": sp, "dist": d,
                     "alt": (start_alt + alt) if alt is not None else None, "cad": cad, "power": pw,
                     "temp": tc, "hr": None, "lat": None, "lon": None, "unpaved": up})
    weather = con.execute("SELECT COUNT(*) FROM weather WHERE ride_id = ?", (ride_id,)).fetchone()[0]
    con.close()
    # unpaved windows from the per-second flags
    spans, start = [], None
    for r in rows:
        if r["unpaved"] and start is None:
            start = r["t"]
        elif not r["unpaved"] and start is not None:
            spans.append((start, r["t"]))
            start = None
    if start is not None:
        spans.append((start, rows[-1]["t"] + timedelta(seconds=1)))
    return rows, spans, weather


def mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rider-kg", type=float, required=True)
    ap.add_argument("--height-m", type=float, required=True)
    ap.add_argument("--bike-kg", type=float, required=True)
    ap.add_argument("--extra-kg", type=float, required=True, choices=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
    ap.add_argument("--tyre-type", type=int, default=0)
    ap.add_argument("--tyre-class", type=int, default=1, help="0 fast, 1 all-round, 2 durable")
    ap.add_argument("--tyre-tread", type=int, default=1, help="gravel tyres: 0 slick, 1 file tread, 2 knobby")
    ap.add_argument("--tyre-width", type=int, required=True, help="mm, 18-60")
    ap.add_argument("--position", type=int, default=0)
    ap.add_argument("--no-weather", action="store_true")
    a = ap.parse_args()
    model = dict(position_mode=a.position, tyre_type=a.tyre_type, tyre_class=a.tyre_class,
                 tyre_tread=a.tyre_tread, tyre_width=a.tyre_width)
    tyre_args = ["--tyre-class", CLASS_NAMES[a.tyre_class]] + (
        ["--tyre-tread", TREAD_NAMES[a.tyre_tread]] if a.tyre_type == 1 else [])

    tmp = tempfile.mkdtemp(prefix="anon_check_")
    db = os.path.join(tmp, "check.sqlite")
    try:
        for path in a.files:
            name = os.path.basename(path)
            print(f"\n=== {name}")
            # ---- pass 1: original
            raw = replay.load_records(path)
            raw_splits = replay.load_surface_splits(path)
            raw_est = replay.estimate(raw, a.rider_kg, a.height_m, a.bike_kg, a.extra_kg, **model,
                                      unpaved_splits=raw_splits)
            t0 = raw[0]["t"]
            raw_by_s = {int(round((r["t"] - t0).total_seconds())): (e, r) for r, e in zip(raw, raw_est)}
            has_power = any(r["power"] for r in raw)
            vals = [e for e in raw_est if e is not None]
            print(f"  pass 1 (original):   avg {mean(vals):6.1f} W over {len(vals)} s"
                  + (f", recorded power avg {mean([r['power'] for r in raw]):6.1f} W" if has_power else ""))

            # ---- pass 2: anonymized (via the CLI, on a copy)
            copy = os.path.join(tmp, name)
            shutil.copy(path, copy)
            cmd = [sys.executable, "-I", os.path.join(HERE, "anonymize.py"), "--db", db, "import", copy,
                   "--rider-kg", str(a.rider_kg), "--height-cm", str(a.height_m * 100), "--bike-kg", str(a.bike_kg),
                   "--tyre-type", TYRE_NAMES[a.tyre_type], "--tyre-width", str(a.tyre_width), *tyre_args,
                   "--position", POS_NAMES[a.position], "--pm-type", "other", "--pm-sides", "single",
                   "--context", "solo", "--apparel", "kit", "--extra-kg", f"{a.extra_kg:g}",
                   "--allow-no-power", "--delete-original"] + (["--no-weather"] if a.no_weather else [])
            out = subprocess.run(cmd, capture_output=True, text=True).stdout
            print("  anonymizer: " + " | ".join(l.strip() for l in out.splitlines() if l.strip()))
            con = sqlite3.connect(db)
            ride = con.execute("SELECT MAX(id) FROM rides").fetchone()[0]
            con.close()
            if ride is None or "SKIPPED" in out or " as ride " not in out:
                print("  pass 2 skipped: not imported")
                continue
            arows, aspans, nweather = anon_rows(db, ride)
            a_est = replay.estimate(arows, a.rider_kg, a.height_m, a.bike_kg, a.extra_kg, **model,
                                    unpaved_splits=aspans)
            avals = [e for e in a_est if e is not None]

            # alignment: the anonymized ride starts where the original passed TRIM_M
            d0 = next(r["dist"] for r in raw if r["dist"] is not None)
            first = next(r for r in raw if r["dist"] is not None and r["dist"] - d0 >= an.TRIM_M)
            off = int(round((first["t"] - t0).total_seconds()))
            diffs, raw_part, anon_part, pw_same = [], [], [], 0
            for r, e in zip(arows, a_est):
                if r["t_s"] < WARMUP_S or e is None or (r["t_s"] + off) not in raw_by_s:
                    continue
                re_, rr = raw_by_s[r["t_s"] + off]
                if re_ is None:
                    continue
                diffs.append(e - re_)
                raw_part.append(re_)
                anon_part.append(e)
                pw_same += (rr["power"] == r["power"])
            exact = sum(1 for d in diffs if d == 0)
            print(f"  pass 2 (anonymized): avg {mean(avals):6.1f} W over {len(avals)} s, {nweather} weather points")
            print(f"  kept part after {WARMUP_S} s warm-up: original {mean(raw_part):6.1f} W, anonymized "
                  f"{mean(anon_part):6.1f} W | per second: {exact}/{len(diffs)} identical, "
                  f"max |diff| {max((abs(d) for d in diffs), default=0)} W, mean diff {mean(diffs):+.2f} W")
            if has_power:
                print(f"  recorded power identical in {pw_same}/{len(diffs)} aligned seconds")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
