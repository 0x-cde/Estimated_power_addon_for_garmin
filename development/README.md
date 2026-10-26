# Development workspace

Tools used to build, test and validate the add-on in `../Estimated_Power/`.
Nothing here ships with the add-on. Project repository:
<https://github.com/0x-cde/Estimated_power_addon_for_garmin>.

## Role in the project

The add-on's formula rests on published research, and several of its values are
estimates (see [Assumptions and their reasoning](../README.md#assumptions-and-their-reasoning)).
This workspace is where those values are checked and corrected:

1. **Reference model.** `tools/power_model.py` mirrors the device code line for
   line, and `tests/` keeps the two in step. Any change to the model is made and
   tested here first, then carried over to `PowerModel.mc`.
2. **Data collection.** Volunteer club riders upload rides recorded with a power
   meter, with their answers to `data/questionnaire.md`. Each ride is
   anonymized on upload (`tools/anonymize.py`). `tools/merge_submissions.py`
   brings the uploads into one contributor database.
3. **Fitting.** `tools/fit_rides.py` fits rolling resistance, drag area and wind
   exposure for each ride against the measured power. The fitted values are
   compared with the model's values, grouped by tyre type, class, tread and
   width, riding position, clothing and temperature.
4. **Replay.** `tools/replay.py` runs each ride through the add-on's exact
   per-second pipeline and compares the live estimate with the measured power.
   This tests the whole estimate, including gradient, wind and smoothing.
5. **Correction.** Where the data consistently contradicts a value, the value is
   changed and the evidence is recorded in
   [METHODOLOGY.md](../Estimated_Power/docs/METHODOLOGY.md).

Every tool takes rider and bike values only from what each contributor answered.
Rides with missing answers are skipped, not filled with guesses. Group rides
and rides where the rider was not sure are kept out of the fits.

```
devenv/Dockerfile          Ubuntu 22.04 image for Garmin's SDK Manager + simulator
devenv/ciq.sh              Helper: image, sdkmanager, simulator, compile, run, shell,
                           headless / hl-shot / hl-xdo / headless-stop (virtual screen)
devenv/layout_shots.sh     Screenshots of the field in several Edge page layouts (headless)
devenv/xwd2png.py          X11 screen dump to PNG
devenv/montage.py          Side-by-side montage of screenshot crops
tools/power_model.py       Python mirror of source/PowerModel.mc + GradeEstimator.mc
tools/replay.py            Replay database rides (or a FIT file) through the device pipeline vs measured power
tools/anonymize.py         Anonymize contributed FIT/CSV rides into the contributor database
tools/merge_submissions.py Merge the website's encrypted archives into the contributor database
tools/anon_check.py        Model on the original vs the anonymized copy of a ride
tools/fit_rides.py         Fit Crr, CdA and wind per ride against measured power (+ selftest)
tests/test_power_model.py  Unit tests for the Python mirror
tests/test_pipeline.py     Import and answer checks, migration, merge and replay on synthetic rides
research/                  Literature notes, full-text findings, bibliography scripts
data/questionnaire.md      The questions contributors answer on the website, with the allowed answers
```

## Private folder

Everything that must not be published lives **outside the repository**, in a
folder next to it: `../../EstimatedPower_private/` by default, or set
`EP_PRIVATE_DIR`. It holds:

```
keys/       Connect IQ developer signing key (store updates must be signed with the same key)
build/      compiler output
data/       rides.sqlite, the anonymized contributor database (personal data under the GDPR
            while a contributor code can be linked to a person)
testData/   ride files used for testing
research/papers/   papers obtained for reading only
```

`ciq.sh` and `anonymize.py` use these locations by default, so nothing private
is ever written inside the repository. The repository `.gitignore` also blocks
these file types as a second line of defence.

## Setup

On LMDE 7 / Debian 13, Garmin's SDK Manager and simulator don't start: they
need WebKitGTK 4.0 and libjpeg8, which Debian 13 no longer ships. Both run in an
Ubuntu 22.04 container shown on the host X11 display. The compiler (`monkeyc`)
is plain Java and runs on the host (JDK 17).

The Connect IQ SDK and device profiles are downloaded with Garmin's SDK Manager
into `~/.Garmin/ConnectIQ/`. Garmin's developer agreement does not allow them to
be redistributed, so they are never copied into this repository.

```sh
devenv/ciq.sh image              # once, or after changing the Dockerfile
devenv/ciq.sh sdkmanager         # sign in, download SDKs and device profiles
devenv/ciq.sh compile edge840    # -> private build folder
devenv/ciq.sh simulator &        # start the simulator
devenv/ciq.sh run edge840        # load the add-on into the simulator
python3 -m venv .venv && .venv/bin/pip install fitdecode numpy scipy
.venv/bin/python -I -m unittest discover -s tests
```

In the simulator, use *Simulation → FIT Data* to play back a recorded ride. If
the editor's shell is a Flatpak sandbox, run the Docker commands on the host,
e.g. `flatpak-spawn --host development/devenv/ciq.sh simulator`.

## Working from the database

Once club data arrives, all analysis works from the contributor database only.
FIT files are imported, anonymized and deleted. The tools take every rider and
bike value from the contributor's own answers stored with each ride: weight,
height, bike weight, tyres, position, clothing and extra weight. Rides with
missing values are skipped, not guessed.

```sh
.venv/bin/python -I tools/fit_rides.py fit --wind weather      # fit Crr, CdA, wind exposure per ride
.venv/bin/python -I tools/replay.py --all                      # the add-on's live estimate vs measured power
.venv/bin/python -I tools/replay.py --ride 12 --csv ride12.csv # one ride, per-second output
```

`replay.py --ride/--all` runs each ride through the same per-second pipeline as
the device. That pipeline includes the live gradient estimate, the 3 s
smoothing, the stored weather (wind, temperature, humidity) and the unpaved
flag. Results are reported for all rides and for solo rides separately.
FIT-file mode (`replay.py FILE.fit --rider-kg … --height-m … --bike-kg …`) is
only for checking single files before import.

## Database

`rides.sqlite` (SQLite) has four tables:

| Table | One row per | Contents |
|---|---|---|
| `contributors` | person | random `code`, `rider_kg`, `height_cm` (rounded), `created_utc` |
| `rides` | ride | the ride's answers (`bike_kg`, `tyre_type`, `tyre_width_mm`, `tyre_class` (all tyres), `tyre_tread` (gravel, mountain bike), `position`, `pm_type`, `pm_sides`, `context`, `apparel`, `extra_kg`); from the file: `ride_type`, `speed_sensor`, `device_model`, `start_alt_100m` (metres, rounded to 100); summary (`duration_s`, `distance_m`, `samples`, `weather_points`); `content_hash` (prevents importing a ride twice); `group_ride` (derived from `context`, kept for older tools) |
| `samples` | second of a ride | `t_s`, `speed`, `dist_m`, `alt_rel_m`, `cadence`, `power`, `temp_c`, `heading_deg` (rotated/mirrored), `unpaved` |
| `weather` | 15 minutes of a ride | `t_s`, `wind_ms`, `wind_from_deg` (rotated/mirrored like the headings), `temp_c`, `rh_pct` |

`context` is the answer to "Did you ride alone?": `solo`, `group`, `partly` or
`unsure`. Databases created before a column existed are upgraded automatically
when opened. `merged_archives` records which website archives have been merged.

## Contributed rides: anonymizer and database

`tools/anonymize.py` imports contributed FIT or CSV rides (a power meter is
required) into the contributor database, keeping only what the model needs:

- **kept:** elapsed seconds, speed, distance, relative altitude, cadence, power,
  temperature (whole °C), paved/unpaved flag (from FIT splits), direction of
  travel, and weather along the ride;
- **transformed:**
  - time counts from the start of the kept part (no date or clock time);
  - altitude is relative, with the start altitude rounded to 100 m;
  - distance counts from the start of the kept part;
  - direction is rotated by a random angle and randomly mirrored for each ride.
    Weather wind directions get the same change, so head- and tailwinds stay
    correct. The change itself is not stored;
  - the first and last 2 km are removed;
- **removed:** GPS positions, timestamps, serial numbers, names, user profile,
  heart rate, laps, events, developer fields and everything else;
- **contributors:** a random code, with rider weight and height rounded.

Before positions are discarded, the ride is sampled every 15 minutes (position
rounded to 0.1°, about 11 km, and the hour) and historical weather is requested
from Open-Meteo. Open-Meteo's free API is for non-commercial use only, and its
logs (kept 90 days) may contain the rounded coordinates. `--no-weather` turns
this off.

Contributions come through the website, which runs the anonymizer once per
uploaded ride with that ride's answers. To import a file by hand:

```sh
.venv/bin/python -I tools/anonymize.py import RIDE.fit --rider-kg 72 --height-cm 178 --bike-kg 8.4 \
    --tyre-type road --tyre-width 28 --tyre-class fast --position road --pm-type crank --pm-sides dual \
    --context solo --apparel kit --extra-kg 1.5 [--delete-original]
.venv/bin/python -I tools/anonymize.py list
```

Every tyre takes `--tyre-class`. Gravel tyres also take
`--tyre-tread slick|file|knobby`, and mountain-bike tyres (collected, not
modelled yet) `--tyre-tread semi-slick|low|aggressive`.
Answers are checked against the options in `data/questionnaire.md`, the same
list the website form uses; an invalid answer stops the import with a message.

## Merging website submissions

The website stores each upload as one encrypted archive, `NNNNNN.zip.age`,
containing that upload's anonymized database. To bring them into the main
database:

```sh
rsync -a server:/var/lib/ep-upload/outbox/ ./incoming/
.venv/bin/python -I tools/merge_submissions.py --identity PATH/TO/age-private.key incoming/*.zip.age
```

Each archive is decrypted into a private temporary folder, checked, and merged
in one transaction:
- the archive must contain only a valid `rides.sqlite`;
- rides already in the database (same `content_hash`) are skipped;
- an archive that was merged before is skipped.

`--dry-run` shows what would happen without changing anything.

Residual risk: the route shape can in principle still be reconstructed from
distance and direction and matched to a map by someone determined. The random
rotation, mirroring and trimming make this harder, not impossible.

## Fitting tool

`tools/fit_rides.py fit --wind free|weather|none` fits Crr, CdA and wind for
each ride with power in the database. Mean power is compared over 20 s blocks of
pedalling seconds (cadence > 0, power ≥ 40 W, speed > 2 m/s). Gravity and
acceleration come from the energy over each block, so no gradient estimate is
needed.

The wind modes are:
- `free`: a constant wind vector per ride;
- `weather`: Open-Meteo wind times a fitted exposure factor k (the add-on uses 0.54);
- `none`: no wind.

The tool reports standard errors. It warns about little heading variety, a
narrow speed range, uncertain or limit-hitting fits, and group rides.
`selftest --ride N` checks that known values are recovered on a real ride's
geometry.
