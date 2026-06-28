# DVPet decompiled source — the canonical reference for porting

tuipet is a port of **DVPet** (a fan-made Java Digimon v-pet).  The authoritative
behaviour lives in the decompiled DVPet source, NOT in tuipet's reconstruction.
**When porting or fixing a mechanic, read the DVPet source first** — don't guess the
structure from the animations or from tuipet's existing code.

## Where the source is

Both trees are gitignored (copyrighted, large) and live beside the repo:

| dir | scope | use |
|---|---|---|
| `_decompiled/` | **COMPLETE** — the full app jar: `Model/` + `Controller/` + `View/`, all real bodies | **canonical — use this** |
| `_audit_src/` | PARTIAL — `View/` only; `Model/` & `Controller/` are empty stubs | legacy; View matches `_decompiled/View` |

`_audit_src` was decompiled from `/tmp/view.jar` (View package only), so its
`Controller.java` / `Model/*.java` came out as empty stubs.  Working from it is the
reason early training/structure ports were *guessed* — the code that defines the
structure (the controller + model) simply wasn't there.

## Regenerate

```sh
cd _extract/game/DVPetTest/jar          # the exploded full app
jar cf /tmp/dvpet_full.jar .
java -jar ~/cfr.jar /tmp/dvpet_full.jar --outputdir _decompiled
```

## The high-value classes I kept needing

- **`Model/PhysicalState.java`** (~9k lines) — the entire pet life-sim: stats, lapses,
  poop/sick/sleep, evolution triggers, care effects.  tuipet `pet.py` ports this.
- **`Model/Config.java`** (~2k lines) — every game constant; each field maps to a
  `config.csv` column (`info[N]`), and the values live in `raw_model/config.csv`.
- **`Controller/ClockTic.java`** (~3.7k lines) — the real controller: input handling,
  menu flow, the training/battle state machine (`onPreTrain`/`onPreFinish`/`onAttack`/
  `onHPTrainingAttribute`/`checkSuccess`/`onExerciseFinish`).  This defines *structure*.
- **`View/SpriteAnim.java`** (~18k lines) — all the on-screen animation timelines
  (the `_interval = targetFPS/10` clock; see `ANIMATION_SPEC.md`).
- `Model/Battle.java`, `Model/Evolution.java`, `Model/Tournament.java`, `Model/Enum.java`,
  `Model/Habitat.java`, `Model/DNA.java`, `Model/Consumable.java`, `Model/FoodType.java`.

## The official guide — the VISUAL ground truth (use this!)

`_extract/game/DVPetTest/guide.pdf` (82 pages) is the official manual with **actual
screenshots of every screen** — training minigames, battle, menus, stats.  Reading
decompiled code and *guessing what it renders to* is how the training came out
"nothing like" DVPet through v0.2.0-0.2.7.  **Before building/fixing any screen, look
at its guide page** (`Read` the PDF — it renders the images), then match the layout.

- Training minigames: pages 51-53.  Vaccine = hit an orb ("Hit!!"); Data = a cannon
  aims high/low, raise the matching shield (two shield slots); Virus = stop a sweeping
  marker in a target range on a horizontal bar; HP = match the shown attribute, 5 wins.
- Verify your build by SCREENSHOTTING the running app (`app.run_test()` →
  `save_screenshot` → cairosvg→PNG → Read) and comparing to the guide page.

## Other DVPet data (already vendored)

- **CSV tables** → `raw_model/*.csv` (digimon, evolutions, foods, items, tournies,
  zones, careEffect, config, …) — vendored into `src/tuipet/data/`.
- **Sprites** → `raw_resources/*.png` — extracted via `tools/extract_*.py`.
- **Sounds** → swapped from MultiVPet, in `src/tuipet/data/sounds/`.
