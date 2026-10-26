#!/bin/sh
# Screenshot the add-on in several Edge page layouts using the headless simulator.
# Coordinates match the simulator window at its default position on the virtual
# screen started by `ciq.sh headless`.
#
#   layout_shots.sh DEVICE OUTDIR [LAYOUT ...]
#   LAYOUT is a Data Fields > Layout menu entry: 1 2 3A 3B 4A 4B 5A 5B 6A 6B 7A 7B 8 9 10
#
# Runs on the host (uses docker). Builds nothing: compile first with `ciq.sh compile DEVICE`.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
CIQ="$HERE/ciq.sh"
DEVICE=${1:?device}
OUT=${2:?output dir}
shift 2
LAYOUTS=${*:-"1 2 3A 3B 6A"}
mkdir -p "$OUT"

xdo() { "$CIQ" hl-xdo "$@"; }
dialog_id() {  # window id of a visible simulator window with the given geometry
    for id in $(xdo search --onlyvisible --class "[Ss]imulator" 2>/dev/null); do
        if xdo getwindowgeometry "$id" | grep -q "Geometry: $1"; then echo "$id"; return; fi
    done
}

"$CIQ" headless >/dev/null
sleep 8
"$CIQ" run "$DEVICE" >/dev/null 2>&1 &
sleep 15

# Activity Select: Cycling / Gravel Cycling (the simulator defaults to Running)
xdo mousemove 186 76 click 1; sleep 1.5; xdo key Down Down Down Down Return; sleep 4
id=$(dialog_id 243x278); xdo windowmove "$id" 600 60; sleep 1
xdo mousemove 721 118 click 1; sleep 2
xdo mousemove 721 300 click --repeat 150 --delay 15 4; sleep 1
xdo mousemove 680 358 click 1; sleep 1.5
xdo mousemove 717 186 click 1; sleep 2
xdo mousemove 675 247 click 1; sleep 1
xdo mousemove 768 300 click 1; sleep 1

# Reload the add-on so it reads the new profile
"$CIQ" run "$DEVICE" >/dev/null 2>&1 &
sleep 15

# Activity Data: simulated data, timer started
xdo mousemove 186 76 click 1; sleep 1.5; xdo key Down Down Return; sleep 4
id=$(dialog_id 489x393); xdo windowmove "$id" 600 60; sleep 1
xdo mousemove 631 395 click 1; sleep 2
xdo mousemove 659 243 click 1; sleep 12
xdo windowmove "$id" 2000 2000; sleep 1

y_of() {
    case "$1" in
        1) echo 101;; 2) echo 126;; 3A) echo 151;; 3B) echo 176;; 4A) echo 201;; 4B) echo 226;;
        5A) echo 251;; 5B) echo 276;; 6A) echo 301;; 6B) echo 326;; 7A) echo 351;; 7B) echo 376;;
        8) echo 401;; 9) echo 426;; 10) echo 451;;
    esac
}
for l in $LAYOUTS; do
    xdo mousemove 273 76 click 1; sleep 1; xdo mousemove 300 110; sleep 1.5
    xdo mousemove 486 "$(y_of "$l")" click 1; sleep 4
    "$CIQ" hl-shot "$OUT/${DEVICE}_$l.png"
    echo "$OUT/${DEVICE}_$l.png"
done
"$CIQ" headless-stop
