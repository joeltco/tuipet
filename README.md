# tuipet

[![CI](https://github.com/joeltco/tuipet/actions/workflows/ci.yml/badge.svg)](https://github.com/joeltco/tuipet/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tuipet)](https://pypi.org/project/tuipet/)
[![Python](https://img.shields.io/pypi/pyversions/tuipet)](https://pypi.org/project/tuipet/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A terminal virtual pet — Digimon V-Pet style — rendered with halfblock Unicode
sprites and animated in the terminal, in **full colour**. Its rules and art are
ripped from multiple fan games and the V-pet community's sprite archives — see
[Credits & acknowledgments](#credits--acknowledgments), and press **z** in-game
for the artist credits.

![tuipet demo — hatch, feed, train, and adventure with your pet in the terminal](demo.gif)

**Status: live and actively developed** — see the
[changelog](CHANGELOG.md) for what each release brought.

## What's inside

- **991 creatures** in 16×16 palette-indexed colour, 11 animation poses each
  (`src/tuipet/data/mons.json.gz`), plus 57 pickable digitama.
- A **real-time V-pet**: one wall-clock minute is one sim tick. It gets
  hungry on the hour, sleeps on a clock, calls you when it needs something
  (ignore a call for 20 minutes and it counts a care mistake), and can die
  of neglect or old age — but never of good care.
- **Growth chart evolution**: time-in-stage gates with best/middle/worst
  branches decided by your care, training, and battles; crest-egg armor
  evolutions; exact-pair jogress fusion with a real partner online.
- **Battle as a timing game**: set your strike form on a sweeping bar
  (good condition widens the perfect zone), then watch the volley play out
  — the fight is decided by care, training, stage and the attribute
  triangle.
- **Adventures** across 5 world maps with bosses, towns and finds — plus a
  **scene gallery** of picked backdrops for the home screen.
- **Online play**: accounts with cloud saves, a live lobby with chat, a
  monthly ladder, PvP battles and two-player jogress fusion.
- A `rich`/`textual` UI: a fixed LCD arena with the animated pet, a live
  status card, and a one-line control strip — every screen lives in the box.

## Install

**Requires Python 3.10+.**

**One command:**

```sh
pip install tuipet && tuipet
```

Or with pipx / uv (isolated):

```sh
pipx install tuipet      # then: tuipet
uvx tuipet               # run without installing
```

Every sprite, sound, and CSV is bundled in the package — nothing else to download.

**On Termux (Android):** first `pkg install python`, then `pip install tuipet`. To
actually hear the LCD beeps you also need the **termux-api** package
(`pkg install termux-api`) *and* the **Termux:API** app from F-Droid/Play — the
package alone isn't enough: it installs a *bridge* that only works when the app
is there. Missing the app, tuipet detects that and falls back to the terminal
bell (Options → sound then reads *bell only*), so a silent install tells you
what's wrong instead of just being quiet. Over SSH, sound stays silent on purpose. The
`curl -fsSL https://raw.githubusercontent.com/joeltco/tuipet/main/install.sh | bash`
script does all of that in one shot.

**On iPhone / iPad — use [a-Shell](https://holzschu.github.io/a-Shell_iOS/)
(the supported iOS way):** a-Shell is a free, open-source terminal on the App
Store that ships Python 3.11 — everything tuipet needs.

```sh
pip install tuipet
python3 -m tuipet
```

Use `python3 -m tuipet` rather than the bare `tuipet` command: a-Shell installs
console scripts somewhere `PATH` doesn't always look, and the module launch
always works. Tap the **⌨ key row** above the keyboard for `Esc` and the arrow
keys. Turn your phone to landscape (or drop the font size in a-Shell's settings)
if the panels wrap.

Two iOS notes, both handled for you:

* **Saves.** iOS forbids writing to `~`, so tuipet keeps your pet in
  `~/Documents/tuipet/` there instead of the usual `~/.local/share/tuipet/`. That
  folder is visible in the Files app, so your pet is backup-able and AirDrop-able.
  Set `TUIPET_SAVE_DIR` to put it anywhere you like.
* **Sound.** iOS sandboxes audio players, so tuipet falls back to the terminal
  bell (Options → sound shows *bell only*). Everything else — the lobby, battles,
  jogress, adventures — works exactly as it does everywhere else.

**On iSH:** iSH's Alpine usually ships a Python older than 3.10, so
`pip install tuipet` fails with *"No matching distribution found"*. Prefer
**a-Shell** above — it's the smoother iOS experience.

## Run from source

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e .
tuipet           # or: PYTHONPATH=src python -m tuipet.app
```

Start from an **egg** — real dot-matrix egg designs; it wobbles, cracks, and hatches.

## Keys

| key | screen | key | screen |
|-----|--------|-----|--------|
| **f** | feed (meat / pill) | **l** | online lobby |
| **t** | train | **n** | new egg |
| **c** | clean | **e** | scenes |
| **h** | pill | **z** | credits |
| **a** | adventure | **g** | options |
| **o** | shop | **b** | bug report |
| **i** | bag | **?** | help |
| **s** | lights | **q** | quit |

Battles and jogress live where they belong: **PvE combat happens in
adventures; PvP battles and fusion happen in the lobby** — there is no
free-standing battle key.

## Care & evolution

Your mon lives in **real time**. Hunger and strength each lose a heart every
waking hour; an empty meter rings a call, and a call ignored for 20 minutes
is a **care mistake**. Filth and overweight risk sickness (the pill cures
it); mistakes, sickness and age feed a per-minute death roll — a
well-kept young pet literally cannot die, a neglected one can. Sleep runs
on a fixed clock per stage; leave the lights on at bedtime and that's a
mistake too. Waking refills energy to full.

**Evolution** is a growth chart: each stage opens its gate after a fixed
time (10 minutes as a hatchling, up to a full day at the top), and your
record picks the branch — few mistakes and heavy training take the BEST
road, neglect takes the worst. Evolving banks a slice of your training as a
permanent energy bonus. Crest eggs (bag items) trigger armor evolutions on
the right Child; the X path waits for species with an X variant.

**Training** (`t`) is the timing drill: stop the sweeping marker in the
zone. The zone's width is your pet's CONDITION — win rate, meters, and age
all widen it. A clean strike sheds weight; every attempt counts toward the
evolution gates, and the grade you land is the **strike form your next
battle fires with** (mega / normal / miss).

## Adventure

Press **a** to teleport into the world — 5 maps, 26 zones, towns, zone
bosses and roadside finds. Wild battles fight ON the road (the biome you
are crossing is the backdrop), boss wins pay a bits purse and open the
gate, and losses cost adventure life. Towns rest you and keep shops.

## Battle

Every fight is a **5-HP race**: both sides volley, hit chance comes from
care, training, stage rank and the attribute triangle, and damage comes
from the trained strike form. Before the bell you set your timing on the
bar — then the volley plays out as the full alternating-view show.

## Online

Press **l** for the lobby (accounts are free — pick a name and password).
Live **chat** with backlog, presence, private messages, a **monthly
ladder** (one rung per online win, resets monthly), a weekly **RAID BOSS**
(one shared boss for the whole server — 3 attempts a day, your damage joins
the pool, contributor ranks pay out when it falls), **PvP battles**
(seeded-symmetric: both clients run the identical engine on a shared
nonce — no host advantage, nothing to tamper with), and two-player
**jogress fusion** (exact species pairs). Online wins pay bits — half
again as much on weekends. Your save syncs to the cloud on the same
account and follows you across devices.

## Scenes

Press **e** to browse the scene gallery — the backdrop behind your mon is
a picked cosmetic. All scenes are currently free.

## Saving

Automatic — local save every 10 seconds and on quit, with backup generation
and offline catch-up decay (bounded; never evolves or dies while closed).
With an account, the same save syncs to the cloud in the background.

## Data

Every sprite, table and sound ships inside the wheel — the colour atlas
(`mons.json.gz`), the growth chart (`evo_branches.json.gz`), the hatch and
jogress tables, the item catalog and the rule constants
(`vpet_rules.json`). All of it is ripped from multiple fan games and
transcribed exactly; `tests/test_clone_sim.py` pins the numbers.

## Credits & acknowledgments

tuipet stands on the shoulders of the **Digimon V-Pet fan community** — a whole
ecosystem of hobbyists who reverse-engineered, documented, and preserved these
devices. Its game data and art are ripped from multiple fan games and the
community sprite archives around them.

- The **sprite artists** whose pixels fill this game are credited BY NAME
  in-game: press **z** for the CREDITS screen. Thank them.
- **[humulos.com/digimon](https://humulos.com/digimon)** — device evolution,
  egg, and roster documentation used during development.
- the wider V-Pet preservation scene whose archives made any of this possible.

Sincere thanks to every one of these creators and archivists — none of this
would exist without your work.

The **Digimon** franchise and all creature names, designs, and sprites are
© **Bandai**. tuipet is a **non-commercial fan project**, not affiliated with or
endorsed by Bandai or any project listed above.
