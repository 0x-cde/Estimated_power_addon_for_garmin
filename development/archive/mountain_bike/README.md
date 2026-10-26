# Mountain-bike support (parked 2026-10-26)

Mountain biking is out of scope until enough data exists: there is little
research on mountain-bike tyres on the road (tread vs casing could not be
separated in the literature). This folder is a snapshot of the add-on, tools,
tests and docs as they were with mountain-bike support, so it can be restored.
Nothing here is built or run.

What the mountain-bike support consisted of:

| Item | Value | Where (in the snapshot) |
|---|---|---|
| Edge ride type "Mountain" (`SUB_SPORT_MOUNTAIN`) | supported; preset value 2 | `add-on/source/EstimatedPowerField.mc` (`RIDE_MOUNTAIN`, `currentRideType`) |
| Built-in defaults for Mountain | MTB tyres, upright position, 57 mm, cycling kit | `DEFAULT_*_BY_RIDE` index 2 |
| Tyre type "Mountain bike tyres" | preset value 2 | `settings.xml`, `strings.xml` (`TyreMtb`) |
| Drum watts, all-round MTB tyre | 30 W (drum Crr 0.0090; + 0.0033 real road = 0.0123) | `PowerModel.mc` / `power_model.py` `TYRE_WATTS[2]` |
| Tyre class factors | fast 0.80, all-round 1.00, durable 1.35 (shared with road tyres) | `TYRE_CLASS_FACTORS` |
| Unpaved addition, MTB tyres | +0.0040 | `UNPAVED_ADD[2]` |
| Width drag | the general width rule (57 mm default → +0.029 m²) | `tyreCdaExtra` |

Open research question before re-enabling: on pavement, does knob height or
casing/compound quality dominate? Evidence (see `development/research/`):
smooth vs knobby 21 ± 15 % (Bertucci 2013, abstract), knobby +31 % vs slick in
urban riders (Tengattini 2018, confounded with width/pressure), casing/tube
effects of 9–54 % on road tyres (Sellier 2025, Baldissera 2021). The website
keeps collecting mountain-bike tyre tread and class so club data can answer it.
