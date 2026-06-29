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
- [ ] Per-version humulos evolution tables + manuals (the big pull).
- [ ] wikimon per-device + per-digimon data.
- [ ] Authentic 16×16 sprite rips per device.
- [ ] Mechanics docs.
- [ ] Build `db/digimon.json`.

⚠ `pen`/`pen20` humulos roster fetches were CONTAMINATED (modern non-Pendulum mons) — must
re-pull per-version and cross-check wikimon before trusting. dm/dm20/dmx looked clean.
