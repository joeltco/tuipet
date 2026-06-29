# tuipet corpus — the reference database

A consolidated **research/reference** corpus of everything about the five mono-16×16
devices (dm, dm20, dmx, pen, pen20): fan games, data sheets, documentation, sprites.

**This is NOT the shipped game data.** It's the layer we MINE to build the clean canon
data (see `../AUTHENTIC_REBUILD.md` §0a). Provenance is tracked on every record; on
conflict, **canon wins** (humulos / wikimon / official manuals) over **fan** (DVPet etc.).
Nothing here is bundled into the PyPI wheel.

## Provenance tiers
- **canon** — humulos per-version guides, wikimon, official Bandai manuals. Authoritative.
- **fan** — DVPet (decompiled), community sprite sheets, fan emulators. Cross-check only;
  great for structure/completeness, never the final word on stats or roster membership.
- **doc** — mechanics writeups (lostintranslationmon, withthewill). Context, not data.

## Layout
```
corpus/
  README.md              # this file
  sources.json           # registry of every source (url/path, tier, device, status)
  canon/
    humulos/<dev>/        # roster.txt (done), evolutions.json, manual.md, raw page dumps
    wikimon/              # per-device + per-digimon page dumps
    manuals/              # device manuals (text/markdown)
  docs/                   # mechanics writeups -> markdown
  sprites/<dev>/          # authentic 16x16 rips, source-tagged
  db/
    digimon.json          # MERGED unified DB (built from the above) -- the "one database"
```
Large FAN assets are **referenced in place**, not copied: DVPet model CSVs live at
`../raw_model/*.csv` and `../_extract/.../Model/*.csv`; 347 sprite PNGs at
`../raw_resources/*.png`. `sources.json` points to them with tier=fan.

## Unified DB schema (`db/digimon.json`) — target
One record per canonical Digimon:
```json
{
  "id": "agumon",
  "name_en": "Agumon", "name_jp": "Agumon", "aliases": ["Agumon"],
  "stage": "Child", "attribute": "Vaccine",
  "devices": {                       // per device/version presence + evo conditions
    "dm20": { "versions": [1],
      "evolves_to": [ { "to": "greymon",
        "conditions": {"care_mistakes":"0-2","training":"16+","weight":"...","overfeed":"0-2",
                       "battles":null,"win_ratio":null,"time":"..."},
        "source": "humulos:dm20/1" } ] }
  },
  "sprite": "sprites/dm20/agumon.png",
  "sources": ["humulos:dm20", "wikimon:Agumon", "dvpet:digimon.csv#row"]
}
```
Build it by reconciling canon (humulos/wikimon) as truth, using DVPet only to fill
structure/sprites, applying the JP↔EN romanization map (see sources.json `romanization`).

## Status — ALL FIVE DEVICES BUILT from authoritative humulos data (2026-06-29)
Pipeline (`db/rebuild_all.sh`): fetch device pages → `db/parse_humulos.py` (inline `result`
for pen20 / detail cards for the rest → `canon/humulos/<dev>/records.json`) → `db/build_device.py`
(structured conditions + correct per-device real-time stage timers + wayland sprites) → `db/<dev>.json`.

| dev | mons | w/ evolutions | sprite gaps | attr gaps |
|-----|------|---------------|-------------|-----------|
| dm    | 81  | 63  | 2  | 0  |
| dm20  | 154 | 114 | 20 | 0  |
| dmx   | 177 | 113 | 9  | 53 (V3 XE/XF chart-only — no attribute in source) |
| pen   | 115 | 88  | 1  | 0  |
| pen20 | 264 | 207 | 32 | 0  |

Each record: id/name/stage/level/attribute/devices.<dev>{versions,stage_time,evolves_to[{to,raw,parsed}]}/sprite/sleep/power.
Exact conditions (verbatim `raw` + structured `parsed`), real-time stage timers, sleep schedule, power.
- Sprite gaps = mons absent from wayland's set (jogress-finals/Royal Knights/Demon Lords/colosseum) → DVPet fallback.
- dmx attr gaps = the V3 XE/XF mons (chart had no attribute data) → backfill from wikimon/DVPet.
- Remaining: backfill dmx V3 attributes + the missing sprites; then the CODE rebuild.


⚠ `pen`/`pen20` humulos roster fetches were CONTAMINATED (modern non-Pendulum mons) — must
re-pull per-version and cross-check wikimon before trusting. dm/dm20/dmx looked clean.
