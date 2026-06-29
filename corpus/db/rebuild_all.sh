#!/usr/bin/env bash
# Reproducible: fetch humulos device pages -> extract records -> build per-device DBs.
# All data is authoritative humulos (inline `result` for pen20; detail cards for the rest).
set -e
UA="Mozilla/5.0"; B="https://humulos.com/digimon"; H="${TMPDIR:-/tmp}/humulos_html"; mkdir -p "$H"
cd "$(dirname "$0")/../.."   # repo root
for p in dm dm20 pen pen20 "dmx" "dmx/2" "dmx/3"; do
  f="$H/$(echo $p | tr / _).html"; curl -s "$B/$p/" -A "$UA" -o "$f"
done
P=corpus/db/parse_humulos.py
python3 $P corpus/canon/humulos/dm/records.json    "$H/dm.html"
python3 $P corpus/canon/humulos/dm20/records.json  "$H/dm20.html"
python3 $P corpus/canon/humulos/pen/records.json   "$H/pen.html"
python3 $P corpus/canon/humulos/pen20/records.json "$H/pen20.html"
python3 $P corpus/canon/humulos/dmx/records.json   "$H/dmx.html" "$H/dmx_2.html" "$H/dmx_3.html"
for dev in dm dm20 dmx pen pen20; do python3 corpus/db/build_device.py $dev; done
