"""Merge website submissions into the contributor database.

Each website upload produces one archive, NNNNNN.zip.age: a zip holding one
anonymized SQLite database (rides.sqlite, same schema as anonymize.py),
encrypted with age to the project's public key. This tool decrypts the
archives with the private key, checks them, and copies their contributors,
rides, samples and weather into the main database:

  - rides are renumbered; contributor codes are kept (a new random code is
    drawn in the rare case of a clash);
  - a ride already in the main database (same content_hash, i.e. the same
    anonymized data) is skipped, so a ride uploaded twice is counted once;
  - every merged archive is recorded by its SHA-256 in the merged_archives
    table, so merging the same archive again does nothing;
  - each archive is merged in one transaction: all of it or nothing.

Archives are treated as untrusted input: only a zip with exactly one member
named rides.sqlite and a sane size is accepted, it is unpacked into a
temporary directory readable only by you, and the database is opened read-only.

Usage:
  .venv/bin/python -I tools/merge_submissions.py --identity ~/age/ep-upload.key incoming/*.zip.age
  .venv/bin/python -I tools/merge_submissions.py incoming/*.zip            # already decrypted
  .venv/bin/python -I tools/merge_submissions.py --dry-run --identity KEY incoming/*.zip.age

The main database is given with --db or the EP_DB environment variable. Decrypting .age files needs the `age` command.
"""
import argparse
import hashlib
import os
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anonymize as an  # noqa: E402

MAX_DB_BYTES = 512 * 2**20          # one submission of up to 10 rides is a few MB
MERGED_TABLE = """
CREATE TABLE IF NOT EXISTS merged_archives (
    sha256 TEXT PRIMARY KEY,
    name TEXT,
    rides_added INTEGER,
    rides_skipped INTEGER,
    merged_utc TEXT NOT NULL
);
"""
RIDE_COLUMNS = ("ride_type", "bike_kg", "tyre_type", "tyre_class", "tyre_tread", "tyre_width_mm", "position",
                "pm_type", "pm_sides",
                "group_ride", "context", "apparel", "extra_kg", "speed_sensor", "device_model",
                "start_alt_100m", "duration_s", "distance_m", "samples", "weather_points", "content_hash",
                "imported_utc")
SAMPLE_COLUMNS = ("t_s", "speed", "dist_m", "alt_rel_m", "cadence", "power", "temp_c", "heading_deg", "unpaved")
WEATHER_COLUMNS = ("t_s", "wind_ms", "wind_from_deg", "temp_c", "rh_pct")


class MergeError(RuntimeError):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def decrypt(path, identity, tmp, age_binary):
    out = os.path.join(tmp, "submission.zip")
    proc = subprocess.run([age_binary, "--decrypt", "--identity", identity, "--output", out, path],
                          capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise MergeError(f"decryption failed: {proc.stderr.strip() or 'age returned an error'}")
    return out


def extract_db(zip_path, tmp):
    try:
        with zipfile.ZipFile(zip_path) as z:
            infos = z.infolist()
            if len(infos) != 1 or infos[0].filename != "rides.sqlite" or infos[0].is_dir():
                raise MergeError("unexpected archive contents (expected only rides.sqlite)")
            if infos[0].file_size > MAX_DB_BYTES:
                raise MergeError("database in the archive is too large")
            target = os.path.join(tmp, "rides.sqlite")
            with z.open(infos[0]) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
                if dst.tell() > MAX_DB_BYTES:
                    raise MergeError("database in the archive is too large")
    except zipfile.BadZipFile:
        raise MergeError("not a valid zip file") from None
    return target


def open_submission(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise MergeError("submission database is corrupt")
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not {"contributors", "rides", "samples", "weather"} <= tables:
            raise MergeError("submission database is missing tables")
    except sqlite3.DatabaseError as exc:
        con.close()
        raise MergeError(f"not a valid database: {exc}") from None
    return con


def columns(con, table):
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def merge_db(main, sub):
    """Copies one submission database into main (inside the caller's transaction).
    Returns (rides_added, rides_skipped)."""
    have = columns(sub, "rides")
    ride_cols = [c for c in RIDE_COLUMNS if c in have]   # older submissions may lack new columns
    added = skipped = 0
    code_map = {}
    for code, rider_kg, height_cm, created in sub.execute(
            "SELECT code, rider_kg, height_cm, created_utc FROM contributors"):
        new = code
        while main.execute("SELECT 1 FROM contributors WHERE code = ?", (new,)).fetchone():
            new = secrets.token_hex(4).upper()
        code_map[code] = new
    used = set()
    for row in sub.execute(f"SELECT id, contributor, {', '.join(ride_cols)} FROM rides ORDER BY id"):
        old_id, contributor, values = row[0], row[1], dict(zip(ride_cols, row[2:]))
        if contributor not in code_map:
            raise MergeError(f"ride {old_id} refers to an unknown contributor")
        if values.get("content_hash") and main.execute(
                "SELECT 1 FROM rides WHERE content_hash = ?", (values["content_hash"],)).fetchone():
            skipped += 1
            continue
        code = code_map[contributor]
        if code not in used:
            c = sub.execute("SELECT rider_kg, height_cm, created_utc FROM contributors WHERE code = ?",
                            (contributor,)).fetchone()
            main.execute("INSERT INTO contributors (code, rider_kg, height_cm, created_utc) VALUES (?, ?, ?, ?)",
                         (code, *c))
            used.add(code)
        cur = main.execute(f"INSERT INTO rides (contributor, {', '.join(ride_cols)}) "
                           f"VALUES (?{', ?' * len(ride_cols)})", (code, *values.values()))
        new_id = cur.lastrowid
        main.executemany(f"INSERT INTO samples (ride_id, {', '.join(SAMPLE_COLUMNS)}) "
                         f"VALUES (?{', ?' * len(SAMPLE_COLUMNS)})",
                         ((new_id, *r) for r in sub.execute(
                             f"SELECT {', '.join(SAMPLE_COLUMNS)} FROM samples WHERE ride_id = ? ORDER BY t_s",
                             (old_id,))))
        main.executemany(f"INSERT INTO weather (ride_id, {', '.join(WEATHER_COLUMNS)}) "
                         f"VALUES (?{', ?' * len(WEATHER_COLUMNS)})",
                         ((new_id, *r) for r in sub.execute(
                             f"SELECT {', '.join(WEATHER_COLUMNS)} FROM weather WHERE ride_id = ? ORDER BY t_s",
                             (old_id,))))
        added += 1
    return added, skipped


def merge_archive(main, path, identity, age_binary, dry_run=False):
    digest = sha256_file(path)
    if main.execute("SELECT 1 FROM merged_archives WHERE sha256 = ?", (digest,)).fetchone():
        return "already merged", 0, 0
    tmp = tempfile.mkdtemp(prefix="merge_")
    os.chmod(tmp, 0o700)
    try:
        if path.endswith(".age"):
            if not identity:
                raise MergeError("encrypted archive: --identity (age private key file) is required")
            zip_path = decrypt(path, identity, tmp, age_binary)
        else:
            zip_path = path
        sub = open_submission(extract_db(zip_path, tmp))
        try:
            main.execute("SAVEPOINT archive")
            try:
                added, skipped = merge_db(main, sub)
                main.execute("INSERT INTO merged_archives VALUES (?, ?, ?, ?, ?)",
                             (digest, os.path.basename(path), added, skipped,
                              datetime.now(timezone.utc).strftime("%Y-%m-%d")))
            except Exception:
                main.execute("ROLLBACK TO archive")
                main.execute("RELEASE archive")
                raise
            if dry_run:
                main.execute("ROLLBACK TO archive")
            main.execute("RELEASE archive")
            main.commit()
        finally:
            sub.close()
        return ("would merge" if dry_run else "merged"), added, skipped
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archives", nargs="+", help=".zip.age (encrypted) or .zip (decrypted) website archives")
    ap.add_argument("--db", default=an.DEFAULT_DB, required=an.DEFAULT_DB is None, help=an.DB_HELP)
    ap.add_argument("--identity", help="age private key file (for .zip.age archives)")
    ap.add_argument("--age", default=shutil.which("age") or "age", help="age command")
    ap.add_argument("--dry-run", action="store_true", help="check and count, change nothing")
    a = ap.parse_args()
    con = an.db_connect(a.db)
    con.executescript(MERGED_TABLE)
    con.isolation_level = None          # explicit savepoints per archive
    totals = [0, 0]
    failed = 0
    for path in sorted(a.archives):
        name = os.path.basename(path)
        try:
            status, added, skipped = merge_archive(con, path, a.identity, a.age, a.dry_run)
        except MergeError as exc:
            print(f"{name}: REJECTED: {exc}")
            failed += 1
            continue
        totals[0] += added
        totals[1] += skipped
        print(f"{name}: {status}" + (f", {added} rides added, {skipped} duplicates skipped"
                                      if status != "already merged" else ""))
    print(f"total: {totals[0]} rides added, {totals[1]} duplicates skipped, {failed} archives rejected"
          + (" (dry run, nothing changed)" if a.dry_run else ""))
    con.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
