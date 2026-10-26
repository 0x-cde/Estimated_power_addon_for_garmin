# Estimated Power

**A free, open-source power estimate for Garmin Edge bike computers, for riders
who do not own a power meter.**

Estimated Power is a Connect IQ data field for the Garmin Edge 540, 550, 840,
850, 1040 and 1050. Every second it estimates the power the rider puts into the
pedals from data the Edge already has:
- speed, barometric altitude and air pressure;
- the weather: wind, temperature and humidity;
- the rider's and bike's details.

It shows a 3-second average and records the estimate in the ride's FIT file, so
it also appears in Garmin Connect after the ride.

Source code: <https://github.com/0x-cde/Estimated_power_addon_for_garmin>

> **Status: in development.** Earlier builds compiled for all six Edge models
> and ran in the Connect IQ simulator; the latest model changes still need to be
> compiled and run there. The Python reference model is covered
> by tests. It has not yet been tested on a device or checked against rides
> recorded with a power meter. Collecting those rides is the next step (see
> [Testing the assumptions](#testing-the-assumptions)).

## Contents

- [Goals](#goals)
- [How the estimate works](#how-the-estimate-works)
- [The current formula](#the-current-formula)
- [Assumptions and their reasoning](#assumptions-and-their-reasoning)
- [The scientific process](#the-scientific-process)
- [Testing the assumptions](#testing-the-assumptions)
- [What is deliberately not modelled](#what-is-deliberately-not-modelled)
- [Expected accuracy](#expected-accuracy)
- [Repository layout](#repository-layout)
- [Building and testing](#building-and-testing)
- [About the project](#about-the-project)

## Goals

Training with power is the most reliable way to follow a structured plan, but a
power meter is a large expense. Estimated Power is for:

- riders who cannot afford a power meter;
- riders who are new to structured training and not ready to buy one;
- riders who are curious about their power numbers.

The aims, in order:

1. **Consistency.** The same effort on the same kind of road should give the same
   number from ride to ride, so riders can follow their progress.
2. **Physical honesty.** Every number in the model comes from published research
   or measurement, or is clearly marked as an estimate. Its source and reasoning
   are documented, including where studies disagree. Nothing is tuned to copy another platform's numbers.
3. **No burden while riding.** Riders describe each bike once in the phone
   settings. Nothing needs changing during a ride.
4. **Quality before reach.** Estimate quality is never traded for support of more
   devices.

A first practical check is that the estimate lands in the same range as the
estimates riders already know from Strava and Zwift. Those are estimates too, so
the real test is rides recorded with power meters.

An estimate cannot match a power meter second by second, and it cannot detect
drafting or braking. Short-term values are noisy; lap and ride averages are much
more reliable.

## How the estimate works

To hold a speed, a rider must supply the power lost to:

- **gravity** on climbs (gained back on descents);
- **rolling resistance** of the tyres on the road surface;
- **aerodynamic drag**, which depends on speed, wind and the rider's size and
  position;
- **acceleration**, when speeding up;
- **friction** in the wheel bearings and the drivetrain.

Each of these follows from physics once a few properties of the rider, bike and
conditions are known. The model is the road-cycling model of
[Martin et al. 1998](https://doi.org/10.1123/jab.14.3.276), which was validated
against power meters (R² = 0.97, standard error 2.7 W under controlled
conditions). In that study the inputs were measured. The
work in this project is choosing the best-supported values for those inputs
when nothing is measured, and testing them.

## The current formula

Every second the add-on calculates the power at the cranks:

```
P = ( Crr · m · g · cos θ · v                       rolling resistance
    + m · g · sin θ · v                             gravity
    + ½ · ρ · (CdA + 0.0044) · v_air · |v_air| · v  air drag + wheel rotation drag
    + ½ · m_eff · (v² − v_prev²) / Δt               acceleration
    + v · (91 + 8.7 · v) · 10⁻³                     wheel bearings
    + 2 W                                           fixed drivetrain loss
    ) / 0.985                                       drivetrain efficiency
```

| Symbol | Meaning | Source on the device |
|---|---|---|
| `v` | ground speed (m/s) | speed sensor if paired, otherwise GPS |
| `v_air` | air speed along the direction of travel: `v` + headwind | wind from Garmin's weather (below) |
| `θ` | road angle, `atan(gradient)` | barometric altitude, least-squares slope over the last ≥ 25 m |
| `m` | rider + bike + extra weight (kg) | Garmin profile; bike and extra weight from the bike preset |
| `m_eff` | `m` + 1.4 kg for the spinning wheels | [Martin et al. 1998](https://doi.org/10.1123/jab.14.3.276) |
| `g` | 9.80665 m/s² | |
| `ρ` | air density | barometer pressure, weather temperature and humidity (Tetens equation) |
| `CdA` | drag area of rider and bike (m²) | below |
| `Crr` | rolling resistance coefficient | below |

**Drag area**

```
CdA = 0.707 × A × position factor × clothing factor + width drag
A   = 0.0293 · H^0.725 · M^0.425 + 0.0604        frontal area in m² (H height in m, M body mass in kg)
width drag = 0.0010 m² per mm of tyre width above 28 mm
```

| Riding position | Factor | Clothing | Factor |
|---|---|---|---|
| Road: 70 % hoods, 30 % drops | 1.405 | Cycling kit | 1.00 |
| Time trial: 95 % aero bars, 5 % base bar | 1.165 | Casual clothes or bags | 1.17 |
| Upright (flat bar) | 1.75 | | |

**Rolling resistance**

```
Crr = ( drum watts × class factor / (42.5 kg · g · 8 m/s) + 0.0033 ) × temperature factor
      + unpaved addition                      (only while the Edge reports an unpaved surface)

temperature factor = 1 + 0.5 · ( (20 + 46.8) / (T + 46.8) − 1 )      T = air temperature, −20…40 °C
```

| Tyre | Drum watts (all-round class) | Class factor | Unpaved addition |
|---|---|---|---|
| Road | 15 W | Fast 0.80 · All-round 1.00 · Durable 1.35 | + 0.0070 |
| Gravel: slick / file tread / knobby | 16.7 / 20 / 25 W | same | + 0.0043 |

For an all-round road tyre at 20 °C this gives Crr 0.0078 on paved roads.

**Wind**

```
headwind = weather wind speed × 0.54 × cos(wind direction − direction of travel)
```

The 0.54 reduces the weather service's 10 m wind to the rider's height.

**Rules applied each second**
- Below 1 m/s, or while a cadence sensor reads 0 rpm (coasting), power is 0.
- Negative values (braking, descending) are shown and recorded as 0.
- The shown and recorded value is the mean of the last 3 seconds.

Every term and source is explained in
[Estimated_Power/docs/METHODOLOGY.md](Estimated_Power/docs/METHODOLOGY.md).

## Assumptions and their reasoning

Every parameter, with its basis and how certain it is:
- **Measured:** taken from validated measurements.
- **Literature:** chosen from published studies, which may disagree.
- **Estimate:** a reasoned value with weak or no direct evidence, to be checked
  against data.

| Parameter | Value | Reasoning | Certainty |
|---|---|---|---|
| Model structure | [Martin et al. 1998](https://doi.org/10.1123/jab.14.3.276) | Validated against power meters and includes every significant loss. Strava's formula ([as quoted from its support article](https://www.roadbikereview.com/threads/whats-up-with-strava-watts.367269/)) and community reverse-engineering of Zwift ([Hilton](https://greghilton.co.uk/php/zwift-bike-selector.html)) use the same structure without the bearing, wheel-drag and drivetrain terms (about 4 % of the estimate). Those terms are real losses, so they are kept. | Measured |
| Wheel drag, wheel inertia, bearings | 0.0044 m², 1.4 kg, `v(91 + 8.7v)·10⁻³` W | Measured by [Martin et al. 1998](https://doi.org/10.1123/jab.14.3.276). Each is small. | Measured |
| Drivetrain | 2 W + 1.5 % | Measured drivetrain losses have a fixed part (seals, lubricant, chain) plus a share of the power ([Kyle & Berto 2001](https://www.ihpva.org/HParchive/PDF/hp52-2001.pdf); [Rohloff & Greb 2003](https://hupi.org/HParchive/PDF/hp55/hp55p11-15.pdf)). This equals Martin's constant 97.6 % at about 220 W and adds about 1.3 W at 75 W. | Literature |
| Frontal area | [Bassett et al. 1999](https://doi.org/10.1097/00005768-199911000-00025), from height and weight | A published estimator from body size, so no input beyond the Garmin profile is needed. Body size explains only part of drag: frontal area explained 54 % of the variation in drag area in [Peterman et al. 2015](https://doi.org/10.7717/peerj.1144). This is the main per-rider uncertainty. | Literature |
| Drag coefficient | 0.707 | The average of Kyle's wind-tunnel data, quoted with the Bassett equation by [Coggan](http://www.trainingandracingwithapowermeter.com/2011/04/estimation-of-cda-from-anthropometric.html). Together they give a static time-trial drag area of about 0.23 m². | Literature |
| Position factors | road 1.405, TT 1.165, upright 1.75 | Ratios of typical published drag areas by position (drops about 0.30, hoods 0.33, upright 0.40 m²). The aero-bar factor is 1.15, not 1.00: drag measured while pedalling and on the road (0.25–0.29 m²) is higher than static wind-tunnel values ([García-López et al. 2008](https://doi.org/10.1080/02640410701501697): +31 % pedalling; field values in [Malizia & Blocken 2021](https://doi.org/10.1016/j.jweia.2021.104673)). Riders change position, so each option is a time-weighted mix; power is linear in drag area, so the mix gives the correct average. | Literature |
| Clothing | casual × 1.17 | 557 urban riders measured by coast-down: 0.570 m² in casual clothes against 0.486 m² in cycling kit ([Tengattini & Bigazzi 2018](https://doi.org/10.1080/02640414.2018.1458587)). | Literature |
| Tyre width drag | + 0.0010 m² per mm above 28 mm | Industry wind-tunnel tests show about 0.010 m² per 10 mm ([Swiss Side gravel report](https://www.swissside.com/en-us/blogs/aero-tech-tips/gravel-report)). Peer-reviewed data agree on the direction: wheel drag grows with the tyre-to-rim width ratio (Crane & Morton 2018, as reviewed by [Malizia & Blocken 2020](https://doi.org/10.1016/j.jweia.2020.104134)). Width does not change rolling resistance in the model, because studies disagree on that at realistic pressures. | Estimate |
| Tyre drum watts | road 15 W; gravel 16.7 / 20 / 25 W | Uses the format of the public [Bicycle Rolling Resistance drum test](https://www.bicyclerollingresistance.com/the-test): one tyre, 42.5 kg, 28.8 km/h. These are placeholders for typical tyres until averaged test data is available. The knobby–slick gap of about 0.002 follows field data ([Tengattini & Bigazzi 2018](https://doi.org/10.1080/02640414.2018.1458587); [Bertucci et al. 2013](https://doi.org/10.1080/02640414.2013.792945)). No study compared a file tread with a slick, so the file tread sits in between as an estimate. | Estimate |
| Tyre class | 0.80 / 1.00 / 1.35 | Casing and compound make large differences between tyres that look alike. The class lets riders describe this without knowing test data. | Estimate |
| Real roads | + 0.0033 | Drum tests run on smooth steel. A field study by the University of California Pavement Research Center for Caltrans ([Li et al. 2017](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0016607-ca17-2693-finalreport.pdf)) measured ordinary asphalt and chip seal at + 0.0026 to + 0.0058 above good asphalt, median + 0.0035. That includes about 0.0002 of bearing friction, which the model counts separately. The study measured a difference, so the value is added rather than used as a ratio. The device cannot know the road quality, so one typical value is used. | Measured (one study) |
| Unpaved surfaces | road tyres + 0.0070, gravel tyres + 0.0043 | Gravel measured + 0.0025 (fine) to + 0.0061 (coarse) above asphalt ([Meyer et al. 2016](https://doi.org/10.1016/j.proeng.2016.06.232)), and gravel and grass about + 0.004 above bitumen ([Steyn & Warnich 2014](https://repository.up.ac.za/handle/2263/42518)), so gravel tyres get the middle. Slick, high-pressure road tyres sink in and slip on loose surfaces (Nilges 2004, as cited by [Rothhämel 2023](https://doi.org/10.1504/ijvsmt.2023.132317)), so they get more. The surface comes from the Edge's map-based paved/unpaved splits. | Estimate within the measured range |
| Tyre temperature | half of Rothhämel's curve | Rolling resistance rises in the cold. [Rothhämel 2023](https://doi.org/10.1504/ijvsmt.2023.132317) measured one tyre from −30 to +25 °C. His two fits differ by about 2×, so half strength is used: × 1.14 at 5 °C, × 0.93 at 30 °C. A data field cannot read the Edge's temperature sensor. The weather temperature is used instead, else the last stored weather (under 6 h old), else 15 °C; indoors 20 °C. | Literature (one tyre) |
| Air density | moist-air formula | Standard physics (the Tetens equation for water vapour) from the barometer and the weather, with the same fallbacks as temperature (humidity 50 %). | Standard physics |
| Wind exposure | 0.54 | The logarithmic wind profile from 10 m down to 1.2 m over mixed terrain (roughness 0.1 m). Sheltered terrain would give 0.43 and open country 0.64. No published value exists for cyclists, and riders cannot judge it reliably, so it is fixed. | Estimate |
| Wind direction | meteorological convention | Garmin documents the bearing only as "North = 0, East = 90". The model assumes it is the direction the wind comes from; this needs confirming on a device. | Assumption |
| Gradient | least squares of barometric altitude over ≥ 25 m | Connect IQ exposes no gradient and no map elevation. Windows of 5–60 m were tested on recorded rides; 25 m had the smallest error. | Tested |
| Extra weight | 1 / 1.5 / 2 kg, 1.5 kg by default | Bottles, tools and clothing; the rider chooses. | Rider input |

## The scientific process

Every part of the model goes through the same steps:

1. **Establish the constraints.** Find out what a Connect IQ data field can
   actually read on the supported Edges. It gets no gradient, no map data and no
   device temperature, so these are derived or replaced.
2. **Review the literature.** About 100 sources on rolling resistance,
   aerodynamic drag, road surfaces and cycling dynamics, preferring peer-reviewed
   studies over articles. Each source is marked by how fully it was read (full
   text, partly, abstract only); numbers seen only in an abstract count as weaker
   evidence. The bibliography is at the end of
   [Estimated_Power/README.md](Estimated_Power/README.md#research-bibliography),
   and notes and extracted findings are in [development/research/](development/research/).
3. **Choose the best-supported value.** Document the reasoning and record where
   studies disagree. Weak evidence is labelled as an estimate (table above).
4. **Mirror the model in Python.** [development/tools/power_model.py](development/tools/power_model.py)
   reproduces the device code, and tests keep the two in step. The replay tool
   runs recorded rides through the device's exact per-second pipeline, including
   the live gradient estimate and the smoothing, so every change can be checked
   without a device.
5. **Test against data and correct.** Values that the data contradicts are
   changed, with the evidence recorded in the methodology.
6. **Keep the scope honest.** Where the evidence is too thin, a feature is left
   out rather than guessed. Mountain biking is out of scope for this reason: on
   paved roads the research cannot separate the effect of knob height from tyre
   construction. The earlier work is kept in
   [development/archive/mountain_bike/](development/archive/mountain_bike/).

Analyses so far (methodology, section 4):

- **Virtual rides.** Trainer-based virtual rides tested whether the model
  reproduces a known physics engine. With a fitted drag area it reproduced one
  ride's average power within 1 %. These rides are not ground truth: their power is itself
  calculated from a basic trainer's resistance curve.
- **Model variants.** Published and reverse-engineered model variants were
  compared on one outdoor ride. None explained a third-party platform's
  higher estimate; the differences came from parameter values, mainly rolling
  resistance, not from the equation.
- **Segment comparison.** Twenty segments of that ride were compared with the
  third-party estimate. Adding the real-road rolling resistance moved the mean
  ratio from 0.82 to 0.93; with the tyre-width drag it is 0.94, RMS difference
  11.6 %.
- **Coasting.** Coasting stretches from five rides were analysed. They suggested
  higher total resistance than the model had before the real-road addition, but
  were too few to separate drag from rolling resistance.
- **Sensitivity.** The sensitivity analysis (below) showed that gradient and wind
  dominate short-term error.

## Testing the assumptions

The values marked as estimates will be checked against rides recorded **with a
power meter**, contributed by volunteer club riders through a website. That data
is the project's ground truth. Zwift rides are not used for this, because
virtual power on a basic trainer is itself an estimate.

**What contributors provide.** One upload describes one bike:
- rider weight and height;
- bike weight;
- tyre type, width, class and, for gravel and mountain-bike tyres, the tread;
- riding position;
- power meter type and whether it measures one or both legs.

For each ride they also say whether they rode alone, what they wore and how much
extra weight they carried. The full question list is in
[development/data/questionnaire.md](development/data/questionnaire.md).
Mountain-bike rides are collected too, for future research.

**Privacy.** Each ride is anonymized when it is uploaded, and the original file
is deleted ([development/tools/anonymize.py](development/tools/anonymize.py)):

- the first and last 2 km are removed;
- GPS positions, dates and clock times, heart rate, device serial numbers and
  profile data are discarded; only the month of the upload is kept;
- the direction of travel is kept only after a random rotation and mirroring, so
  the route is hard to reconstruct. The weather wind gets the same change, so
  head- and tailwinds stay correct;
- altitude is kept only relative to the start;
- historical weather is looked up beforehand from a position rounded to about
  11 km;
- each upload is stored encrypted to a key that is not on the server.

**How each assumption is tested**

| Assumption | Test |
|---|---|
| Rolling resistance: drum values, class, tread, real-road addition | [fit_rides.py](development/tools/fit_rides.py) fits rolling resistance, drag area and wind for each ride against the measured power, with standard errors. The fitted rolling resistance is compared by tyre type, class, tread and width with the model's values. |
| Drag area: body size, position, clothing, tyre width | The fitted drag areas are compared with the model's prediction from each rider's height, weight, position, clothing and tyre width. A consistent difference by position or clothing corrects that factor. |
| Unpaved additions | Rides with and without unpaved sections, compared by tyre type. |
| Tyre temperature | Rides in different seasons: the fitted rolling resistance should follow the temperature factor. |
| Wind exposure | The exposure factor is fitted against the weather stored with each ride (`fit_rides.py fit --wind weather`). |
| The whole live estimate | [replay.py](development/tools/replay.py) runs each ride through the device's exact pipeline and compares the estimate with the measured power, for all rides and for solo rides only. |

Before it is trusted with real data, the fitting tool's self-test checks that it
recovers known values on a real ride's geometry.

**Guarding against misleading data**

- **Drafting:** rides in a group, partly in a group or "not sure" are flagged by
  the rider and kept out of the fits. Unflagged group riding shows up as measured
  power far below the model on fast flat roads but close to it on climbs, where
  drafting matters little.
- **Single rides:** a rider's rides on one bike should give similar drag areas,
  so an outlier ride stands out.
- **Single contributors:** fits use statistics that resist outliers, and are
  repeated leaving out one contributor at a time.
- **Power meters:** the meter type and whether it measures one or both legs are
  recorded. Some pedal and crank-arm meters read low under vibration, and
  single-sided meters depend on the left/right balance
  ([Bouillod et al. 2022](https://doi.org/10.3390/s22010386)), so their rides on
  rough surfaces are treated with caution.
- **Uploads:** only club members with an access code can upload.

**Known bias.** Riders with power meters are likely more experienced than the
riders this add-on is for, with better-optimised setups. Values calibrated on
their rides could make the estimate read slightly low for less optimised setups.
The bike presets keep the main setup choices explicit, so only the unmeasured
part of that difference remains.

## What is deliberately not modelled

- **Drafting:** it cannot be detected, so the estimate reads high in a group.
- **Braking:** it cannot be detected; negative values are shown as 0.
- **Crosswind drag:** only the head- or tailwind component is used.
- **Tyre pressure:** the tyre values assume a sensibly inflated tyre, so no
  pressure setting is needed.
- **Inner tube type** (tube, tubeless, latex): not asked and not modelled.
- **Mountain biking, cyclocross and e-bikes:** not supported for now.
  Cyclocross power changes too quickly to estimate from speed and gradient, and
  an e-bike motor's share is unknown.

## Expected accuracy

For an 85.5 kg rider and bike on the hoods (drag area 0.348 m²), all-round road
tyres, at 15 °C:

| Situation | Estimate | Gradient off by 1 % | Headwind off by 2 m/s | Drag area off by 10 % | Crr off by 0.001 | Mass off by 2 kg |
|---|---|---|---|---|---|---|
| Flat, 25 km/h | 124 W | ±59 W | ±48 W | ±7 W | ±6 W | ±1 W |
| Flat, 35 km/h | 272 W | ±83 W | ±91 W | ±20 W | ±8 W | ±2 W |
| 7 % climb, 12 km/h | 232 W | ±28 W | ±13 W | ±1 W | ±3 W | ±5 W |

Gradient and wind dominate the short-term error. Gradient errors largely cancel
over a ride that starts and ends at a similar altitude, so lap and ride averages
are much more reliable than the 3-second value. Steady climbs are the most
accurate case.

## Repository layout

```
Estimated_Power/          the Connect IQ data field (Monkey C)
  README.md               how the add-on works, its settings, the research bibliography
  docs/METHODOLOGY.md     every parameter, its sources, the analyses and decisions
development/
  tools/                  Python reference model, ride replay, anonymizer, merge and fitting tools
  tests/                  unit and pipeline tests
  research/               literature notes, full-text findings, bibliography scripts
  data/questionnaire.md   the questions contributors answer
  devenv/                 container for Garmin's SDK Manager and simulator
  archive/mountain_bike/  parked mountain-bike support
```

Deliberately not in the repository:
- the signing key and build output;
- ride recordings and contributor data, which are personal data. The anonymized
  club database is planned to be published here once collection and analysis
  are further along;
- the research papers themselves, for copyright reasons;
- the Connect IQ SDK, which Garmin's developer agreement does not allow to be
  redistributed.

The development tools keep these in a separate private folder outside the
repository (see [development/README.md](development/README.md)).
[.gitignore](.gitignore) blocks them as a second line of defence.

## Building and testing

```sh
git clone https://github.com/0x-cde/Estimated_power_addon_for_garmin.git
cd Estimated_power_addon_for_garmin
```

**The add-on.** Building needs the Garmin Connect IQ SDK, which you download
with Garmin's SDK Manager, and your own developer key. The helper script
[development/devenv/ciq.sh](development/devenv/ciq.sh) runs the SDK Manager and
simulator in a container and compiles on the host:

```sh
development/devenv/ciq.sh compile edge840
development/devenv/ciq.sh simulator &
development/devenv/ciq.sh run edge840
```

**The reference model and tools.**

```sh
cd development
python3 -m venv .venv && .venv/bin/pip install fitdecode numpy scipy
.venv/bin/python -I -m unittest discover -s tests
```

## About the project

Estimated Power is a personal, non-commercial project. The author has a
bachelor's degree in Physics but never worked as a physicist, and works as a
cybersecurity analyst.

**Use of AI.** The author does not have the experience of a professional
developer and uses an AI coding assistant (Claude Code) to help write the code
and to read and summarise the literature. The add-on itself contains no AI and
collects no data: it runs on the bike computer and writes the estimate only to
the rider's own activity file. All research used is cited in full.

**Trademarks.** Garmin, Edge and Connect IQ are trademarks of Garmin Ltd. or
its subsidiaries. This is an independent project, not affiliated with or
endorsed by Garmin.

**License.** [MIT](LICENSE). The license covers this project's own code and
texts. The research notes summarise and cite published papers. Those papers
remain under their authors' and publishers' copyright and are not included here.
