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

## Status
- [x] Session rosters persisted: `canon/humulos/<dev>/roster.txt` (dm/dm20/dmx/pen/pen20).
- [x] Fan repos pulled (`fan/`, gitignored): wayland-vpets (sprites+timers), digilib, RG_Digimon, DigimonVPet.
- [x] **DM20 evolution conditions** → `canon/humulos/dm20/evo_ver1-5.md`, `evo_special.md`, `evo_extra.md`.
- [x] **DM20 unified DB built** → `db/dm20.json` (154 mons; 134 playable + 20 colosseum-only; via `db/build_dm20.py`).
- [x] **dmx complete** → `db/dmx.json` (175 mons, 119 w/ evolutions). V3 XE/XF edges parsed deterministically from the chart HTML (`db/parse_dmx3_chart.py`); pure-V3 attributes null (chart has none — backfill later).
- [~] pen20: 5 classic versions + MAJOR 20th bonus lines (`db/pen20.json`, 239 mons, 123 w/ evolutions). 57 extended-Adventure/misc still pending (WebFetch too noisy — needs chart-parse/manual).
- [~] pen: DERIVED from pen20 classic data + pen timers (`db/pen.json`, 143). Clean /pen/ pull would refine.
- [ ] dm evolution conditions + DB.
- [ ] Extract wayland sprites → usable atlas (downsample /4 + split frames).
- [ ] wikimon / mechanics docs (as needed).
- [ ] Merge per-device DBs → one `db/digimon.json` if desired.

⚠ `pen`/`pen20` humulos roster fetches were CONTAMINATED (modern non-Pendulum mons) — must
re-pull per-version and cross-check wikimon before trusting. dm/dm20/dmx looked clean.
