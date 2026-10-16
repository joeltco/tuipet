# tuipet

[![CI](https://github.com/joeltco/tuipet/actions/workflows/ci.yml/badge.svg)](https://github.com/joeltco/tuipet/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tuipet)](https://pypi.org/project/tuipet/)
[![Python](https://img.shields.io/pypi/pyversions/tuipet)](https://pypi.org/project/tuipet/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**▶ Play in your browser: [ff3mmo.com/tuipet](https://ff3mmo.com/tuipet/)** — no install, same online lobby as the terminal game.

A terminal virtual pet — Digimon V-Pet style — rendered with halfblock Unicode
sprites and animated in the terminal. It builds on the work of the Digimon V-Pet
fan community — see [Credits & acknowledgments](#credits--acknowledgments).

![tuipet 0.6 trailer — the Godzilla line: 28 new kaiju, the G-Cell meter, and real gameplay](https://raw.githubusercontent.com/joeltco/tuipet/main/demo.gif)

**Status: live and actively developed** — see the
[changelog](CHANGELOG.md) for what each release brought. tuipet is its own game: the core
V-Pet behaviour draws on documented device evolution charts and community
references, with tuipet's own care, combat, economy and progression rules.
Regular updates ship as the game grows.

## What's inside

- **NEW in 0.6 — the Godzilla line.** The full Digital Monster COLOR Godzilla
  70th Edition chart: 28 new kaiju, from Botamon G and Baby Godzilla up
  through SpaceGodzilla, Kiryu, Destoroyah and Godzilla 1994 to Burning
  Godzilla, plus the G-Erosion forms of MetalGreymon, SkullGreymon and
  WarGreymon, each firing its own shot in battle. Reach Mega with any
  Digimon to earn the Godzilla Egg; the device's **G-Cell meter** decides
  which kaiju your pet becomes, and a **G-Cell Fragment** left where a kaiju
  falls is the only road to Burning Godzilla.
- **1,576 creatures**, 11 animation frames each, extracted from the game's
  sprite atlases as 1-bit bitmaps (`src/tuipet/data/sprites.json.gz`).
- A **basic V-Pet** with care (hunger, effort, filth, sleep, lights), training
  drills, evolution (care-quality gates + DNA divergence + armor
  Digimentals + jogress), an **Adventure** mode (30 maps,
  bosses, towns), raid bosses, cups on a real-calendar schedule
  (seasons, weekends, holidays), a shop with the classic four-tab
  storefront, digitama earned by play (and bought outright in each town's
  own egg shop), an in-game AI care assistant, and the device's own screen
  transitions and animation timelines.
- **Online play** tuipet adds on top: free accounts whose save lives in the
  cloud — **one pet, on one device at a time**, the way a cartridge works —
  and a live lobby with chat, PvP battles, and two-player jogress fusion.
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
  jogress, raids — works exactly as it does everywhere else.

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

<!-- egg audit 2026-10-14: document the existing generation handoff. -->
The egg guide shows unlock goals; the carousel shows only eggs you can hatch.
Earned permanent eggs stay available, while lineage eggs last only while their
previous-generation condition holds. Towns also sell permanent egg shortcuts
for 10,000 bits, limited to one purchase per real day across towns.

Death or retirement starts the next generation. Bits, inventory, trophies,
qualifier records and banked DNA carry over; body stats, injuries, fight records
and applied DNA reset. Unused DigiMemory carries as one payload and one chip.
At death, etching spends the care bonus; declining carries the adjusted bonus.
Re-picking an unhatched egg keeps its generation and inheritance. An unhatched
Godzilla egg's fragment waits again if you choose another egg, until you pick
Godzilla Egg. The album remembers species; the Hall remembers the latest 30
departed or retired partners.

## Keys

The action bar reads in the in-game Help screen's order — care, then
explore, then grow, then manage:

| key | screen | key | screen |
|-----|--------|-----|--------|
| **f** | feed | **x** | DNA |
| **h** | heal an injury | **d** | DigiCore |
| **c** | clean | **e** | digitama guide |
| **o** | lights | **s** | shop |
| **v** | AI assistant | **b** | bag |
| **m** | battle | **n** | scenes |
| **a** | adventure | **g** | options |
| **r** | raid | **i** | bug report |
| **u** | tournament cup | **?** | help |
| **l** | online lobby | **q** | quit |
| **t** | train | **ENTER** | accept a found gift |
| **p** | discipline (praise·scold) | | |

<!-- final sweep 2026-10-14: the road and DigiCore distinguish these keys. -->
SPACE doubles ENTER on most screens; DigiCore uses it for gaze/page, and
the road distinguishes walking on from entering or digging. PageUp/PageDown
leap through supported long lists. ESC returns from a screen.

**m** is the battle key: a real recorded bout against a rival of your
pet's own stage, right at home — no purse, and each bout spends energy,
so the tank paces the fighting.  Beyond it, **PvE combat happens in
adventure, raids and cups; PvP battles and fusion happen in the lobby**.

## Care & evolution

Evolution uses the real V-Pet gating model: each form's
`digimon.csv` row gates on care **mistakes**, **overfeed**, **sleep
disturbances**, **weight** class, **battles/wins** and **generation**,
with the game's exact fulfilled-requirement scoring and deviation
tiebreak. Per-stage counters
reset on evolution; power and battle records carry for life. Good care with
focused training walks the classic lines; neglect finds Numemon.
<!-- battle audit 2026-10-14: describe the recorded progression channels. -->
Battle-gated Champions and above need local fights — home battles, adventure
and cups feed the battle record. Lobby duels and raid volleys bill the body
without feeding that record; defeated raid claims separately count Mega kills.

**Training** (`t`) is the timing drill: stop the sweep on the beat to land
the hit — every attempt grows effort and training, and saves its strike grade.
Local battle wins grow power in the defeated foe's attribute.
Battles resolve as the device's HP race.

**Armor evolution**: the shop's Eggs tab sells the 11 crest Digimentals in
their canonical discovery waves — Courage and Hope from day one, the crest
five after your first armor evolution, Light and Kindness at 25 wins,
Miracles behind the raid bosses, Destiny at generation 5. All 73 armor
forms are crest-exclusive, and the shop dossier names the form your pet
would become *right now*.

**DNA** (`x`) is the per-Field collectible layer: charge banked Field-DNA
into the pet, or generate more with a 10-second SPACE exercise. A unique
leading Field at its stage threshold **arms a divergence** when that form
has a road in the Field; ties disarm it. The next growth uses that road
instead of the egg chart. Divergence lists every road destination; the final
choice uses care scores and chance. Charges clear at every evolution;
banked DNA stays. Charging costs energy (double off-Field), adds Effort up
to three hearts, and costs obedience if energy goes negative. Charged-share
conditions are selection bonuses for off-chart forms, not unlock gates.
DigiCore shows evolution requirements and your collection. **Jogress** (two-player DNA fusion) happens in the
lobby with a real partner — the partner's attribute picks the fusion via the
game's `attributeJogress` matrix.

**DigiCore** (`d`) is tuipet's data book: the field-flavoured core counts down
toward the hatch/growth window, then counts age toward elderhood. Growth
still needs its gates and an awake, unblocked pet. SPACE on CORE shows a
silhouette of a potential next form; other pages use SPACE to advance.
EVOLVES lists every chart route: ENTER opens its requirements, including
incubation and lobby partners. TROPHIES keeps inherited wins and distinct
career cups; ENTER opens the album, or the hall of memory on LEGACY.

## Raids & cups

Press **r** for raids: boss fights against the world's heavies, with a
shared community pool that **sizes itself to the crowd** — a small crew can
fell its boss, and every kill grows the next one. Three volleys a day, each
billing energy and a little weight like any other fight. A felled boss
collapses on the arena before the next one takes the stage, and your share
waits on the board until you press **C** to claim it — your pet steps out to
celebrate while the prize line names every bit and item. Each felled boss
counts toward egg unlocks and the Miracles Digimental wave; even an escaped
boss pays out by your share of the damage.

Press **u** for the cup page, which runs on the **real calendar**: seasonal
cup pools, a featured cup picked by the date (the weekend headliner is one
**your pet's own bracket** can win), and holiday specials — including
Odaiba Memorial Day on August 1. A grand-final chain that crosses real
seasons tells you which season's qualifier you're missing.
Each cup is the 8-entrant single-elimination bracket (Quarterfinal →
Semifinal → Final) with real rolled entrants; the other pairs auto-resolve
between your rounds. Titles pay the canonical purse, count trophies, and
gate tournament egg unlocks. An alarm can call you when a cup you care
about opens.
<!-- battle audit 2026-10-14: fees and elimination fractions are existing rules. -->
Each entry spends a stake and its hourly slot (all unrun slots open on festival
days); the featured cup runs once per real day. A quarterfinal exit pays nothing,
a semifinal loss one third of the purse, and a final loss half. A title defense
pays 1.5× the purse, and weekend payouts also receive 1.5×.

## Online

Press **l** for the lobby (accounts are free — pick a name and password).
Live **chat** with backlog, presence, private messages (threads keep their
full scrollable history), **PvP battles** (host-authoritative, with the
full round-replay animation), and two-player **jogress fusion**. TAB opens
the **monthly ladder** — online wins race a fresh season each month, and
past-season podium finishers claim a bits award, confirmed by the server and
paid out in a full award ceremony under the arena lights.
**Password rooms** give you a private scope: everyone who types the same
phrase lands in the same room, chat and roster included.

Your save lives in the cloud on your account, and it behaves like a
**cartridge**: the pet is checked out to exactly one device at a time. Open
tuipet somewhere else and it asks before touching anything — *"Your pet is on
phone. Take it onto this device?"* — and only a yes moves it. The device
holding the pet is never prompted and plays exactly as before; no other
device can write over your save, however fresh its clock claims to be.
Offline play is untouched; the network is fail-soft everywhere.

## Scenes

Press **n** to change the backdrop — real ripped scenes, and each egg comes
wired to its own home scene, so the digitama you choose decides the view
your pet grows up with (until you repaint it).

## Shop, bag & economy

**s** opens the classic four-tab storefront — **[Food] Items Eggs Honors**
— stocked with the TUIPET catalog: real foods that get **eaten on the LCD**
through their own device art (fish, steak, a feast, one mushroom you should
NOT feed), care goods and growth tools, and **toys that actually play** —
the ball bounces, the skateboard rides, the TV glows — each nudging a real
meter (exercise sheds weight, couch time builds DP for fusion). Every item wears its
own device sprite, and the live dossier shows the effect, a word of
character, what you already hold, and (for a crest egg) the armor form it
would trigger right now. **b** is the bag: use with ENTER, sell back for
half with R. Birthdays hand out treats you can actually eat. The Honors
board sells cosmetic tamer titles for the truly rich.

**Digitama are earned by playing** — reaching stages, felling raid bosses,
winning cups, clearing adventure maps, celebrating festivals, growing your
album — exactly like the real devices; the carousel shows only what you can
hatch and teases the one you're closest to earning, and a newly earned
digitama announces itself by name when you get home (**e** opens the guide). **On the road, each
town's egg shop also sells a distinct band of eggs outright** — the real 8×8
egg sprites, a paid shortcut that drops straight onto your carousel, and no
two towns stock the same eggs.

## AI assistant & options

**v** hires the device's auto-care AI (per-stage retainer and per-care fees —
it minds the pet, at a price). **g** opens options: account switching, sound backend, updates,
key reference, theme, and the new-game/erase controls.

## Updating

tuipet **updates itself**. On launch it checks PyPI in the background, installs
any newer release, and tells you to restart to play it — the running process
keeps the version it started with, so the new one comes up next time.

Prefer to do it yourself? Press **a** on the options → Update row to switch
auto-update off; you'll still be told when a release is out. You can also press
ENTER there to check now, and ENTER again to install on the spot.

Where tuipet can't run pip for you — **iOS** sandboxes subprocesses, and a
source checkout has no release to install over — it hands you the command
instead of pretending it updated.

## Saving

Automatic — local save every 10 seconds and on quit, with backup generation.
With an account, that save syncs to the cloud in the background from whichever
device currently holds the pet (see [Online](#online)); any local save that a
cloud pull replaces is snapshotted first, so a wrong answer is undoable.

**A closed game is a stopped clock.** Nothing happens while you're away: your
pet doesn't age, grow, incubate, get hungry, or make a mess. Quit for five
minutes or five months and you reopen to exactly the pet you left. Time passes
only while you're actually playing — and only on the main view, since every
menu pauses the sim too.

## Asset pipeline

Raw game files live under `_extract/` (gitignored). Re-extract with:

```sh
python tools/extract_sprites.py     # rebuilds data/sprites.json.gz
python tools/preview.py Agumon      # preview a creature as halfblocks
python tools/allframes.py Agumon    # see all 11 frames
```

The atlases are 672×672, an 11×11 grid: each **column** is one creature, each of
the 11 **rows** is an animation frame. Creatures are authored at 3× scale on a
cyan LCD background; the extractor box-downsamples 3× (recovering native 16px
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

## License

**tuipet is open source, under the [MIT License](LICENSE).**

You can use it, read it, change it, fork it, publish your own version, or build
something commercial on top of it. You don't need to ask permission, and you
don't owe anyone anything for it. The only condition MIT asks for is that the
copyright notice travels with copies of the code.

Pull requests and forks are welcome — see the source layout in
[Run from source](#run-from-source).

One scoping note, because it isn't ours to give away: the MIT license covers
**tuipet's code**. It does not cover the Digimon sprites and game data, which
are © Bandai and derived from [DVPet](https://theundersigned.itch.io/dvpet) —
the bundled assets remain the property of their respective owners and are
not covered by the code's MIT license. The [Asset pipeline](#asset-pipeline)
describes regenerating source assets from your own copy of DVPet.
Details in [NOTICE](NOTICE).

## Credits & acknowledgments

tuipet stands on the shoulders of the **Digimon V-Pet fan community** — a whole
ecosystem of hobbyists who reverse-engineered, documented, and preserved these
devices. It draws on the work of many of them, including:

- **[DVPet](https://theundersigned.itch.io/dvpet)** by *theundersigned* —
  tuipet began as a study of this fan game, and its sprite bank and early
  data came from it.
- **[humulos.com/digimon](https://humulos.com/digimon)** — device evolution,
  egg, and roster documentation used to build and verify the lines.
- **MultiVPet** and **Digimon Unlimited** — community sprite/stat extractions
  cross-referenced during development.
- the wider V-Pet preservation scene whose archives made any of this possible.

Sincere thanks to every one of these creators and archivists — none of this
would exist without your work.

The **Digimon** franchise and all creature names, designs, and sprites are
© **Bandai**. tuipet is a **non-commercial fan project**, not affiliated with or
endorsed by Bandai or any project listed above.

**Are you one of these creators?** If you'd like different credit, a link added,
or your work removed, open an issue (or reach me) and I'll take care of it right
away — no hard feelings.
