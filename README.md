# tuipet

A terminal virtual pet — Digimon V-Pet style — rendered with halfblock Unicode
sprites and animated in the terminal. Built on data mined from the free
[DVPet](https://theundersigned.itch.io/dvpet) fan game.

## What's inside

- **1511 creatures**, 11 animation frames each, extracted from the game's sprite
  atlases as 1-bit bitmaps (`src/tuipet/data/sprites.json.gz`, ~330 KB).
- Real **evolution graph** and **food** tables parsed from the game CSVs.
- A `rich`/`textual` UI: an LCD screen with an animated pet, stat bars, and care
  actions (feed, train, play, clean, heal, sleep), plus time-based evolution.

## Install

**One command** (Termux on Android, or any Linux):

```sh
curl -fsSL https://raw.githubusercontent.com/joeltco/tuipet/main/install.sh | bash
tuipet
```

That installs Python + tuipet with every sprite, sound, and CSV bundled — nothing
else to download. On **Termux** it also pulls `termux-api`; to actually hear the
LCD beeps you additionally need the **Termux:API** app from F-Droid/Play (the
package alone isn't enough). Over SSH, sound stays silent on purpose.

Prefer pip directly:

```sh
pip install git+https://github.com/joeltco/tuipet
```

## Run from source

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e .
tuipet           # or: PYTHONPATH=src python -m tuipet.app
```

Start from an **egg** — one of 11 real DVPet egg designs (from armorEggs.png) — it wobbles, cracks, and hatches into a random Fresh baby.

Keys: **f** feed · **t** train (minigame) · **p** play · **c** clean · **h** heal ·
**s** sleep · **n** new egg · **q** quit.

**Training** is a timing minigame: strike **SPACE** when the marker hits the green
target zone. Three reps raise effort and the pet's attribute power (Vaccine/Data/Virus).

## Asset pipeline

Raw game files live under `_extract/` (gitignored). Re-extract with:

```sh
python tools/extract_sprites.py     # rebuilds data/sprites.json.gz
python tools/preview.py Agumon      # preview a creature as halfblocks
python tools/allframes.py Agumon    # see all 11 frames
```

The atlases are 672×672, an 11×11 grid: each **column** is one creature, each of
the 11 **rows** is an animation frame. Creatures are authored at 3× scale on a
cyan LCD background; the extractor box-downsamples 3× (recovering native ~20px
sprites and dropping the dev-build column labels) and thresholds to 1-bit.

## Sprite frame convention

Each creature's 11-frame strip uses a fixed pose order, reverse-engineered from
the game's own `View/SpriteAnim.class` (cfr-decompiled). Animations in
`src/tuipet/data.py::ROLES` mirror the game's `cheer`/`jeer`/`eat`/`idleSleep`/etc.

| idx | pose                          | used by                          |
|-----|-------------------------------|----------------------------------|
| 0   | idle / walk A                 | idle bob (0,1), walk             |
| 1   | idle / walk B                 | idle bob, play, tantrum          |
| 2   | sleep / rest A                | `idleSleep` (2,3), wake stretch  |
| 3   | sleep / rest B                | `idleSleep`                      |
| 4   | angry / refuse / attack       | jeer, refuse head-shake, battle  |
| 5   | happy / cheer-up              | cheer (good), play               |
| 6   | sad / unhappy                 | jeer (bad), tantrum, attack      |
| 7   | eat-closed (chew) / cheer-down| eat (8↔7), heal, cheer           |
| 8   | eat-open (mouth) / neutral    | eat, heal, default expression    |
| 9   | tired / sick / disliked / old | fatigue idle, geriatric, dislike |
| 10  | exhausted (very tired)        | deep-fatigue idle                |

`refuse` is drawn as a left/right mirror flip on alternating frames (head-shake).

## Evolution (care-quality based)

Evolution is a faithful port of DVPet's `Model/Evolution.checkEvolReq` + selection.
Each form's row in `digimon.csv` defines gates (comparison `Key` + `Value`):
care **mistakes**, **overfeed**, **sleep disturbances**, **sickness**, **injuries**,
**weight** class (Over/Healthy/Under, ±50% of base), **mood**, **attribute power**
(Vaccine/Data/Virus), **battles/wins**, plus a probability roll.

When a stage's minimum time elapses, the engine gathers the current form's
evolution targets, keeps those whose every gate passes, then picks the one with
the highest **fulfilledReq** score (priority + per-gate rates), breaking ties by
the smallest **deviation** (closest stat match) — exactly as the game does.

Per-stage counters (mistakes, overfeed, disturbances, sickness, injuries) **reset
on evolution**; **attribute power, battles and wins carry over** for life — matching
DVPet's `resetEvolVar`.

Verified against the game data and online guides:

| Care during Koromon (In-Training) | Evolves to |
|-----------------------------------|------------|
| good care + Vaccine training      | Agumon     |
| good care + Data training         | Gabumon    |
| good care + Virus training        | Goburimon  |
| neglect (many care mistakes)      | Chuumon    |

Note: most Champion+ forms in DVPet's data are **battle-gated** (e.g. Greymon needs
10+ battles), so without the battle system a well-raised pet reaches the classic
"default" Champions (Numemon / Bakemon / Sukamon) — authentic V-Pet behaviour.
Battles are the next system to unlock the full tree.

## Battles

Press **b** to battle a stage-appropriate enemy (from `enemies.csv`, 462 foes).
Combat uses the canonical Digimon **attribute triangle — Vaccine > Virus > Data >
Vaccine**. Each round you pick an attack type (**1** Vaccine / **2** Data / **3**
Virus); effective power is your trained power in that attribute, boosted when it
beats the foe's shown type and dampened when it loses to it. Higher effective
power lands a hit; first to 0 HP loses. **ESC** flees.

Both **training** and **strategy** matter — vs a typical foe a well-trained pet
that counters the enemy's type wins ~85%, naive play far less. Wins grant bits and
mood; **battles/wins are tracked and feed evolution**: most Champion+ forms
(Greymon, etc.) require battle experience plus multi-attribute training, so battling
unlocks the rest of the evolution tree that care alone cannot reach.

## Sprite extraction

All DVPet sprite sheets are RGBA with transparent backgrounds. The extractor masks on "opaque AND not the cyan LCD colour", recovering every creature (~1525), the eggs, and the food/item icons (from the food/item sheets' alpha channel). A few genuinely-unfinished cells are detected and shown as a generic blob.

## Adventure

Press **a** to travel the Digital World — 5 maps, 26 zones parsed from
`zones.csv` + `enemies.csv` (faithful to DVPet's `WorldMap`). Your pet walks a
zone's progress bar; **wild encounters** launch battles, a **town** midway
restores adventure life, and a **zone boss** gates the way to the next zone.
Clear every zone in a map to unlock the next region. Bosses are the canonical
villains (Devimon, Etemon, the Dark Masters…). Travel tires the pet (energy +
weight, like exercise), wins grant bits, and every fight counts toward the
battle/win requirements that drive evolution. Progress persists on the pet.

Keys in adventure: **SPACE** go/stop · **ESC** leave.

## Shop

Press **o** to open the shop and spend the bits you earn from battles and
adventures. Inventory comes from `shopConsumable.csv` (21 foods/items resolved
from `foods.csv` + `items.csv`), each with its real DVPet effects: food (hunger,
weight, mood), medicine that **cures** sickness, items that **heal** injuries,
discipline books (obedience), and **attribute chips** that add Vaccine/Data/Virus
power. Browse with **↑↓**, **ENTER** to buy, **TAB** to switch to your **bag** and
use what you own, **ESC** to leave. Items you buy persist in the pet's inventory.

## Saving

Your pet persists automatically — there's nothing to do. tuipet writes to
`~/.local/share/tuipet/save.json` every 10 seconds and on quit, and loads it on
startup, so your Digimon (stats, evolution, bits, inventory, adventure progress)
survives between runs. While the game is closed the pet ages gently: reopening
applies a bounded "while you were away" decay to hunger/energy/mood (capped at
12h, and never evolves or dies offline), with a "Welcome back!" greeting. Press
**n** to abandon the current pet and start a fresh egg (this overwrites the save).

## Jogress (DNA fusion)

Press **j** at Champion or above to fuse your pet with a partner and DNA-evolve
into a special Ultimate. The partner's attribute decides the result via DVPet's
`attributeJogress` matrix (e.g. a Data pet + Virus partner → Virus fusion), and
the fusion targets come from the pet's evolution graph (`SpecialEvolution=Jogress`,
112 of them). Jogress bypasses the normal care requirements — the partner supplies
the "DNA" — so it's a deliberate fusion you trigger. Pick a partner with **↑↓**,
**ENTER** to fuse, **ESC** to cancel. Normal (non-special) evolution is unchanged;
jogress/fusion forms no longer appear in ordinary evolution.

## Tournaments

Press **u** at Champion or above to enter a **single-elimination cup** — three
matches (Quarterfinal → Semifinal → Final, the final a boss-tier opponent),
faithful to DVPet's 8-entrant bracket. Each match reuses the battle engine, so
cup fights count toward your battle/win record too. Win all three to be crowned
**Champion**: a trophy (tracked and shown in your stats) plus bits scaled by stage
(Rookie 60 → Mega 400). Lose a match and you're eliminated. **SPACE** to fight,
**ESC** to leave.

## Setup (game data not included)

tuipet's code is here, but the **game data is not distributed** — the sprites and
CSVs are derived from [DVPet](https://theundersigned.itch.io/dvpet) (a Digimon fan
game, © Bandai for the franchise) and belong to their creators. To play, regenerate
them from your own free copy of DVPet:

```sh
# 1. download DVPet from itch.io and locate DVPet.jar inside the extracted zip
# 2. regenerate assets:
tools/setup_assets.sh /path/to/DVPet.jar
# 3. install + run:
python -m venv .venv && . .venv/bin/activate
pip install -e .
tuipet
```

`setup_assets.sh` unpacks the jar, copies the needed CSVs, and runs the sprite
extractor (`tools/extract_sprites.py`) to build `src/tuipet/data/sprites.json.gz`.
