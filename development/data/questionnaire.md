# Contributor questions (website form)

Contributors answer these questions on the website when they upload rides.
The form (`website/app/server.py`, `CHOICES`, and `templates/upload.html`) uses
exactly these questions and answer options. `tools/anonymize.py` checks the
answers against the same options (short codes in brackets). Change all of them
together.

## Once per upload: the rider

| Question | Answer |
|---|---|
| Your weight (kg) | number, 30–200 |
| Your height (cm) | number, 120–220 (optional) |

## Once per upload: the bike

Each upload is for one bike; rides on another bike are a separate upload.

| Question | Answer options |
|---|---|
| Bike weight (kg) | number, 3–40 |
| Tyre type | Road tyres (`road`) · Gravel tyres (`gravel`) · Mountain bike tyres (`mtb`) |
| Tyre width | 18 mm … 60 mm, in steps of 1 mm |
| Tyre class | Fast (race / performance) (`fast`) · All-round (`all-round`) · Durable (puncture protection / comfort) (`durable`) |
| Tread *(gravel tyres)* | Slick (`slick`) · File tread / low knobs (`file`) · Knobby (`knobby`) |
| Tread *(mountain bike tyres)* | Semi-slick (`semi-slick`) · Low knobs (cross-country) (`low`) · Aggressive knobs (trail / enduro) (`aggressive`) |
| Riding position | Road bars (hoods and drops) (`road`) · Time trial / aero bars (`tt`) · Upright (flat bar) (`upright`) |
| Power meter | Pedals (`pedal`) · Crank arm (`crank`) · Spider / chainring (`spider`) · Rear hub (`hub`) · Other (`other`) |
| Power meter measures | Single-sided (one leg) (`single`) · Dual-sided (both legs) (`dual`) |

Every tyre has a class; gravel and mountain-bike tyres also a tread, and the
form shows only the tread question that fits the tyre type. Browsers that cannot
hide questions show both tread questions, and only the relevant one is required
and stored.
Mountain-bike rides are collected for future research; the add-on does not
model them yet.

## For each ride

| Question | Answer options |
|---|---|
| FIT file | the original `.fit` file of a ride recorded with a power meter |
| Did you ride alone? | Solo the whole time (`solo`) · In a group the whole time (`group`) · Partly in a group (`partly`) · Not sure (`unsure`) |
| Clothing | Cycling kit (tight fit) (`kit`) · Casual clothes / bags (`casual`) |
| Extra weight | 0.5 kg · 1 kg · 1.5 kg · 2 kg · 2.5 kg · 3 kg (bottles, tools, bags, spare clothing carried on the ride) |
