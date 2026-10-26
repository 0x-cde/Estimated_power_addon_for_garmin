"""End-to-end tests of the data pipeline on synthetic rides (no personal data, no network):
anonymizer import and questionnaire batch import, schema migration, merging website
archives, and replaying rides from the database.

Run: .venv/bin/python -I -m unittest discover -s tests
"""
import csv
import math
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
sys.path.insert(0, TOOLS)

import anonymize as an  # noqa: E402
import merge_submissions as ms  # noqa: E402
import power_model as pm  # noqa: E402
import replay  # noqa: E402

RIDER = dict(rider_kg=75.0, height_cm=175.0, bike_kg=9.0, extra_kg=1.5)


def synthetic_ride(path, seconds=3600, phase=0.0, speed=8.0):
    """A ride whose power is the model's own estimate, so replay should match it."""
    mass = RIDER["rider_kg"] + RIDER["bike_kg"] + RIDER["extra_kg"]
    cda = pm.cda_from_anthropometrics(RIDER["height_cm"] / 100, RIDER["rider_kg"],
                                      pm.position_factor(pm.POSITION_ROAD))
    crr = pm.tyre_crr(0, 1) * pm.crr_temperature_factor(15.0)
    rho = pm.air_density(pm.pressure_from_altitude(100.0), 15.0, 50.0)
    dist, alt = 0.0, 100.0
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "speed", "distance", "altitude", "cadence", "power", "heading"])
        prev_v = speed
        for t in range(seconds):
            v = speed + 1.5 * math.sin(t / 97.0 + phase)
            grade = 0.02 * math.sin(t / 400.0 + phase)
            dist += v
            alt += grade * v
            kinetic = 0.5 * (mass + pm.WHEEL_INERTIA_MASS_KG) * (v * v - prev_v * prev_v)
            prev_v = v
            p = pm.crank_power(v, v, grade, kinetic, mass, crr, cda, rho)
            w.writerow([t, round(v, 3), round(dist, 2), round(alt, 2), 85, max(0, round(p)),
                        round((t * 0.1 + phase * 50) % 360, 1)])


def run(*args):
    return subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "anonymize.py"), *args],
                          capture_output=True, text=True)


ANSWERS = ["--tyre-type", "road", "--tyre-width", "28", "--tyre-class", "all-round", "--position", "road",
           "--pm-type", "crank",
           "--pm-sides", "dual", "--context", "solo", "--apparel", "kit", "--extra-kg", "1.5"]


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rides = []
        for i in range(3):
            p = os.path.join(self.tmp, f"ride{i}.csv")
            synthetic_ride(p, phase=i * 1.3, speed=7.5 + i)
            self.rides.append(p)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def import_one(self, db, path, *extra):
        r = run("--db", db, "import", path, "--rider-kg", "75", "--height-cm", "175", "--bike-kg", "9",
                *ANSWERS, "--no-weather", *extra)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_import_stores_all_answers(self):
        db = os.path.join(self.tmp, "main.sqlite")
        self.import_one(db, self.rides[0])
        with sqlite3.connect(db) as con:
            row = con.execute("SELECT bike_kg, tyre_type, tyre_width_mm, tyre_class, tyre_tread, position, context, "
                              "apparel, extra_kg, group_ride FROM rides").fetchone()
        self.assertEqual(row, (9.0, "road", 28, "all-round", None, "road", "solo", "kit", 1.5, 0))

    def test_rejects_non_finite_rider_values(self):
        db = os.path.join(self.tmp, "main.sqlite")
        for value in ("nan", "inf", "-inf", "20"):
            r = run("--db", db, "import", self.rides[0], f"--rider-kg={value}", "--bike-kg", "9", *ANSWERS,
                    "--no-weather")
            self.assertNotEqual(r.returncode, 0, value)
            self.assertIn("rider weight must be a number", r.stdout + r.stderr)
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--height-cm", "nan", "--bike-kg", "9",
                *ANSWERS, "--no-weather")
        self.assertIn("rider height must be a number", r.stdout + r.stderr)

    def test_dates_are_month_only(self):
        db = os.path.join(self.tmp, "main.sqlite")
        self.import_one(db, self.rides[0])
        with sqlite3.connect(db) as con:
            values = [v for (v,) in con.execute("SELECT imported_utc FROM rides UNION SELECT created_utc FROM contributors")]
        for v in values:
            self.assertRegex(v, r"^\d{4}-\d{2}$")

    def test_rejects_invalid_answers(self):
        db = os.path.join(self.tmp, "main.sqlite")
        bad = [a if a != "1.5" else "4" for a in ANSWERS]
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--bike-kg", "9", *bad, "--no-weather")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("extra weight must be one of", r.stdout + r.stderr)

    def test_gravel_tyres_store_tread_and_class(self):
        db = os.path.join(self.tmp, "main.sqlite")
        gravel = ["--tyre-type", "gravel", "--tyre-width", "45", "--tyre-tread", "file", "--tyre-class", "fast",
                  "--position", "road", "--pm-type", "crank", "--pm-sides", "dual", "--context", "partly",
                  "--apparel", "casual", "--extra-kg", "2"]
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--bike-kg", "9", *gravel, "--no-weather")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with sqlite3.connect(db) as con:
            row = con.execute("SELECT tyre_type, tyre_width_mm, tyre_class, tyre_tread, context, group_ride "
                              "FROM rides").fetchone()
        self.assertEqual(row, ("gravel", 45, "fast", "file", "partly", 1))

    def test_mountain_bike_tyres_store_class_and_tread(self):
        db = os.path.join(self.tmp, "main.sqlite")
        mtb = ["--tyre-type", "mtb", "--tyre-width", "57", "--tyre-class", "durable", "--tyre-tread", "aggressive",
               "--position", "upright", "--pm-type", "spider", "--pm-sides", "dual", "--context", "solo",
               "--apparel", "kit", "--extra-kg", "2.5"]
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--bike-kg", "13", *mtb, "--no-weather")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with sqlite3.connect(db) as con:
            row = con.execute("SELECT tyre_type, tyre_class, tyre_tread FROM rides").fetchone()
        self.assertEqual(row, ("mtb", "durable", "aggressive"))
        # the model does not cover mountain-bike tyres: replay skips the ride
        con = sqlite3.connect(db)
        self.addCleanup(con.close)
        with self.assertRaises(ValueError):
            replay.load_db_ride(con, 1)

    def test_rejects_missing_tread_and_bad_width(self):
        db = os.path.join(self.tmp, "main.sqlite")
        base = ["--position", "road", "--pm-type", "crank", "--pm-sides", "dual", "--context", "solo",
                "--apparel", "kit", "--extra-kg", "1"]
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--bike-kg", "9",
                "--tyre-type", "gravel", "--tyre-class", "fast", "--tyre-width", "45", *base, "--no-weather")
        self.assertIn("unknown gravel tread", r.stdout + r.stderr)
        r = run("--db", db, "import", self.rides[0], "--rider-kg", "75", "--bike-kg", "9",
                "--tyre-type", "road", "--tyre-class", "fast", "--tyre-width", "28.5", *base, "--no-weather")
        self.assertIn("whole number of millimetres", r.stdout + r.stderr)

    def test_migrates_old_database(self):
        db = os.path.join(self.tmp, "old.sqlite")
        con = sqlite3.connect(db)
        old = an.SCHEMA
        for line in ("    context TEXT,", "    apparel TEXT,", "    extra_kg REAL,", "    tyre_tread TEXT,",
                     "    tyre_width_mm INTEGER,"):
            old = "\n".join(l for l in old.splitlines() if not l.startswith(line))
        con.executescript(old)
        self.assertNotIn("context", {r[1] for r in con.execute("PRAGMA table_info(rides)")})
        con.close()
        con = an.db_connect(db)
        self.assertTrue({"context", "apparel", "extra_kg", "tyre_tread", "tyre_width_mm"}
                        <= {r[1] for r in con.execute("PRAGMA table_info(rides)")})
        con.close()

    def make_archive(self, name, rides):
        sub = os.path.join(self.tmp, name + ".sqlite")
        for p in rides:
            self.import_one(sub, p, "--contributor", self.code(sub)) if self.code(sub) else self.import_one(sub, p)
        z = os.path.join(self.tmp, name + ".zip")
        with zipfile.ZipFile(z, "w") as f:
            f.write(sub, "rides.sqlite")
        return z

    def code(self, db):
        if not os.path.exists(db):
            return None
        with sqlite3.connect(db) as con:
            row = con.execute("SELECT code FROM contributors LIMIT 1").fetchone()
        return row[0] if row else None

    def merge(self, db, *archives, expect_ok=True):
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "merge_submissions.py"), "--db", db,
                            *archives], capture_output=True, text=True)
        if expect_ok:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def test_merge_archives(self):
        main = os.path.join(self.tmp, "main.sqlite")
        a1 = self.make_archive("000001", self.rides[:2])
        a2 = self.make_archive("000002", self.rides[1:])          # ride1 again: a duplicate
        r = self.merge(main, a1, a2)
        self.assertIn("000001.zip: merged, 2 rides added, 0 duplicates skipped", r.stdout)
        self.assertIn("000002.zip: merged, 1 rides added, 1 duplicates skipped", r.stdout)
        with sqlite3.connect(main) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM rides").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM contributors").fetchone()[0], 2)
            n_samples = con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
            per_ride = con.execute("SELECT SUM(samples) FROM rides").fetchone()[0]
            self.assertEqual(n_samples, per_ride)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM merged_archives").fetchone()[0], 2)
        r = self.merge(main, a1)                                   # same archive again: nothing happens
        self.assertIn("already merged", r.stdout)

    def test_merge_rejects_bad_archives(self):
        main = os.path.join(self.tmp, "main.sqlite")
        bad = os.path.join(self.tmp, "bad.zip")
        with zipfile.ZipFile(bad, "w") as f:
            f.writestr("rides.sqlite", b"not a database")
            f.writestr("../evil.sh", b"rm -rf /")
        r = self.merge(main, bad, expect_ok=False)
        self.assertIn("REJECTED: unexpected archive contents", r.stdout)
        notdb = os.path.join(self.tmp, "notdb.zip")
        with zipfile.ZipFile(notdb, "w") as f:
            f.writestr("rides.sqlite", b"not a database at all, just text" * 100)
        r = self.merge(main, notdb, expect_ok=False)
        self.assertIn("REJECTED", r.stdout)
        enc = os.path.join(self.tmp, "x.zip.age")
        with open(enc, "wb") as f:
            f.write(b"age-encryption.org/v1")
        r = self.merge(main, enc, expect_ok=False)
        self.assertIn("--identity", r.stdout)

    def test_dry_run_changes_nothing(self):
        main = os.path.join(self.tmp, "main.sqlite")
        a1 = self.make_archive("000001", self.rides[:1])
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "merge_submissions.py"), "--db", main,
                            "--dry-run", a1], capture_output=True, text=True)
        self.assertIn("would merge, 1 rides added", r.stdout)
        with sqlite3.connect(main) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM rides").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM merged_archives").fetchone()[0], 0)

    def test_replay_from_database(self):
        db = os.path.join(self.tmp, "main.sqlite")
        self.import_one(db, self.rides[0])
        con = sqlite3.connect(db)
        self.addCleanup(con.close)
        rows, setup, weather = replay.load_db_ride(con, 1)
        self.assertEqual((setup["rider_kg"], setup["height_m"], setup["bike_kg"], setup["extra_kg"]),
                         (75.0, 1.75, 9.0, 1.5))
        self.assertEqual(setup.pop("context"), "solo")
        est = replay.estimate(rows, **setup)
        res = replay.compare(est, [r["power"] for r in rows])
        # Power was generated by the same model; the live gradient estimate and smoothing differ slightly.
        self.assertAlmostEqual(res["avg_est"] / res["avg_act"], 1.0, delta=0.05)
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "replay.py"), "--db", db, "--all"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ride 1 (solo", r.stdout)


if __name__ == "__main__":
    unittest.main()
