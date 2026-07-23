# REAL VPET ARC — 2026-07-23

Joel: "i need this to feel like a real vpet. the dual pet mechanic wont
work for our game. but the others." → "lets do it. praise and scold
should have happy and sad animations (that whole animation system needs
to be heavily audited, i dont think its being used in all the right
places)... and if you want, theres a bandage sprite with animation
sequence if you wanna hook that up for injuries... idk where youd but
the action, the action menu is running out of room...."

Follows CANON_RESTORATION_2026_07_23.md (injury v0.5.205, discipline
v0.5.206, both CLOSED).  ⛔ RULED OUT BY JOEL, do not pitch again: the
DM20 dual-pet mechanic ("wont work for our game").  Standing rulings
still untouched: TIME LAW, DSprite mortality, LINES_SPEC.

---

## D — THE CARE LOOP (the "real vpet" trio)

The three that make a creature: the gauge breathes, feeding is a
decision, and a neglected pet has a will of its own.

- [ ] **D1 — DISCIPLINE FADE** (canon `obedienceLapse`, recovered from
      git 5a853e4~1).  Manners drains while AWAKE so discipline is a
      practice, not a high-water mark.  Canon numbers, verbatim:
      - `OBEDIENCE_LAPSE_DEC = 2` per fire
      - cadence is disposition-shaded: `{sunny: 180, neutral: 120,
        sour: 60}` game-min (`OBEDIENCE_LAPSE_MIN`)
      - each fade event ALSO bills the mess:
        `OBEDIENCE_FILTH_SCALE = -1` × piles
      - never while asleep (canon `MinObedienceAsleep == MaxObedience`
        makes the lapse unreachable in sleep — a shipped-config quirk,
        keep it)
      - TIME LAW-clean: it rides the sim tick, so it only runs on the
        main view like everything else.
      ⚠ OPEN: canon's scale is 0..150 with 150 the cap; tuipet's
      restored gauge is 0..100.  Either rescale the dec (2 → ~1.3) or
      keep 2 and accept a slightly brisker fade.  **Recommend: keep 2**
      — brisker is better for a session game, and it makes D3 reachable.

- [ ] **D2 — OVERFEED PENALTY.**  Today a full-belly feed is a free
      head-shake that quietly ticks `overeat` for the evolution OF
      gates (`petcare.feed_meat`, the `hunger >= FULL_HUNGER` branch,
      explicitly "penalty-free").  Canon `overeatPenalty`: weight +1
      and a care mistake.  Restore both so stuffing is a real choice.
      ⚠ OPEN: mistake on EVERY stuffing, or only past a threshold
      (e.g. 3 in a row)?  **Recommend: weight +1 every time, care
      mistake every time** — canon shape, and the head-shake already
      warns you before it costs anything.

- [ ] **D3 — EARNED DISOBEDIENCE.**  ⚠ AMENDS the soft-refusal ruling
      — Joel gave the explicit yes ("lets do it") on the shape below,
      and ONLY this shape:
      - a pet refuses commands ONLY when manners are genuinely
        neglected (gauge under ~25), never above it
      - a well-raised pet NEVER refuses (this is what the original
        recalibration was protecting — the old spam punished good
        raising, this punishes neglect)
      - the cure is raising, not waiting: answer tantrums, scold, the
        gauge climbs, obedience returns
      - `check_refused` is the ONE door (it already exists as the
        stub the strip left); the energy auto-refuse stays as-is
      - refusal shows the head-shake + costs nothing else (no mistake,
        no meter hit) — the refusal IS the consequence
      ⚠ OPEN: which commands can be refused?  **Recommend: feed,
      train, battle only** — never clean (the player must always be
      able to fix filth) and never the pill/bandage (never block
      medicine).  A pet that can't be cleaned or healed is a softlock,
      not a personality.

**D depends on nothing; D3 depends on D1** (without the fade, manners
only climbs, so under-25 is unreachable after the first few scolds).

---

## E — THE ANIMATION AUDIT

Joel: "that whole animation system needs to be heavily audited, i dont
think its being used in all the right places."  He is right; first pass
of evidence below.

### E1 — Praise & scold need their shows  [Joel named this]

- [ ] `pet.praise()` sets `_set_anim("happy")` and `pet.scold()` sets
      `_set_anim("sad")` — but an ANIM is the LCD pose, not the SHOW.
      Every sibling verdict in the game fires an **fx** on the house
      screen: training uses `cheer`/`jeer`/`spit`, the cup uses
      `cheer`/`losing`, the m-battle now uses `cheer`/`losing`.
      Discipline fires NOTHING.
- [ ] Wire `_after_discipline` to the same grammar it already follows
      elsewhere: praise-that-landed → `cheer`; scold-that-landed →
      `jeer`; wrong-moment verbs → the small pose only (no fx), since
      nothing happened.

### E2 — Bandage animation  [Joel offered this: "theres a bandage
sprite with animation sequence"]

- [ ] The frames exist and are REAL rips: `i:80` is a 4-frame medicine
      strip (items.csv row 80, `AnimationType = Bandaging`), and
      `effects.json.gz` carries `st_bandage`.
- [ ] The canon script exists in git and was REMOVED, not lost:
      `_fxk_heal` (the DVPet `bandage()` port) died in **44c6405**
      ("pill anim: the pill is EATEN — heal/bandage fx removed").
      Recovered beats: med drops in beside the pet, application strip
      steps at 0/8/13/18 while the pet holds the hurt pose (9), ends
      23, chains into `cheer`.
- [ ] ⚠ THE REMOVAL'S REASON MUST NOT SHIP AGAIN: that port drew the
      strip at y0–4, **above the window top (y6)** — an out-of-window
      draw.  The rebuild must anchor in-window (`layout: "beside"`,
      the shower/`Shower` script's proven anchor) and carry a pixel
      pin.
- [ ] Home: rebuild as an `itemfx.SCRIPTS["Bandaging"]` entry (the
      per-AnimationType table) rather than a bespoke `_fxk_*`, so it
      rides the shipped `item_use` rail: bag → `("item_use", icon,
      script, msg)` → the LCD show.  `NO_FX`'s comment currently
      excuses Bandaging as "rides its existing flow" — that flow is
      the thing that no longer exists; update the comment.
- [ ] Add `"bandage": "Bandaging"` to `shop.TOY_SCRIPTS` (rename that
      constant — it is now the item→script map, not just toys).

### E3 — Dead show code (measured, not guessed)

fx kinds the painter fully implements but **nothing ever fires**:

| fx | state |
|----|-------|
| `heal` | painter gone (44c6405); E2 restores the show |
| `toilet` | orphaned by the staple-props strip (2026-07-17) |
| `poopdance` | never wired |
| `yawn` | fires as an ANIM (3 sites) but the FX never plays |

- [ ] Rule each: wire it to the moment it belongs to, or delete it.
      **Recommend: wire `poopdance` + `yawn`** (both are pure charm and
      the pet already has the moments — a fresh poop, a sleepy pet),
      **delete `toilet`** (its system is gone by ruling).
      ⚠ Status-box liveness law applies: a deletion means the
      same-day sweep of every display that mentions it.

### E4 — The systematic pass (the real audit Joel asked for)

- [ ] Build the **moment × show matrix**: every player-visible outcome
      in the game (care verbs, item uses, battle results, evolution,
      adventure beats, cup/raid/lobby verdicts, death, hatching) ×
      what anim + what fx it fires today.  Then find:
      - moments with NO show (discipline was one; expect more)
      - moments with an anim but no fx (the E1 class)
      - shows firing on the WRONG moment
      - poses that exist in the rips but are never posed
- [ ] Pose coverage check: `_set_anim` fires only 11 distinct poses
      today (`refuse` 17×, `happy` 13×, `yawn`/`sad` 3×, `poop`/`eat`/
      `angry` 2×, `wash`/`tantrum`/`idle`/`hatch` 1×).  The DVPet rips
      carry more pose indices than that (the fx painters index up to
      pose 10).  Catalogue what the sheets have vs what we use.
- [ ] Deliverable: a table in this file, then a ruled fix list.

---

## F — THE ACTION BAR IS FULL  [Joel: "the action menu is running out
## of room"]

Measured, current build (`keys_markup()` vs the `#keys` box: width 75
− 2 border − 2 padding = **71 content cells**):

| line | cells | spare |
|------|-------|-------|
| 1 — care + battle | **71** | **0** |
| 2 — explore + grow | 69 | 2 |
| 3 — manage | 65 | 6 |

Line 1 is **exactly at the ceiling** — `p discipline` (v0.5.206) took
the last cell.  There is no room for a bandage key (or any future
action) without restructuring.  The box is 5 rows tall (2 border + 3
content), so a 4th line would need a taller box too.

Options:
- **(a) No new key — the Bandage is a BAG item** (`i` → Items → use).
  It already works this way today; the injury alarm already points
  there ("[I] — a Bandage from the bag").  Zero bar cost.
  **← Recommend.**  Meds that are consumables belong in the bag, and
  the alarm is the discoverability path.
- (b) Shorten labels to buy cells (e.g. "feed (meat·pill)" → "feed").
  Cheap, but the parenthetical is real teaching text.
- (c) Grow the box to 4 content lines (height 5 → 6).  Costs vertical
  space on small terminals — Termux is Joel's daily driver, so this
  needs a real check at his size before anyone commits to it.
- (d) A submenu (a "care" key that opens feed/clean/pill/bandage).
  Most room, most keystrokes; fights the one-press care grammar.

⚠ WHICHEVER: the four hand-maintained key surfaces move together —
the bar (`keys_markup`), Help (`helpscreen.HELP`), README `## Keys`,
and Options→Keys (auto from BINDINGS).  Pinned by tests.

---

## Suggested order

1. **D1 + D2** (small, pure canon, no design risk) — one release.
2. **E1 + E2** (the shows Joel named; E2 needs the pixel pin) — one
   release, with F resolved as option (a) = no bar change.
3. **D3** (the ruling-amending one; wants D1 shipped first so neglect
   is reachable, and wants a careful refusal-surface list).
4. **E3 + E4** (the audit proper — its own arc; E4 produces a table
   before any fix ships).

## Open questions for Joel (nothing ships on these until ruled)

1. D1 fade rate: keep canon dec 2 on a 0..100 gauge (brisker), or
   rescale to canon's 0..150 feel?
2. D2: care mistake on every stuffing, or only on repeat stuffing?
3. D3: refusable commands — feed/train/battle only (recommended), or
   wider?
4. F: bag-only Bandage (recommended), or spend bar cells?
5. E3: wire or delete `poopdance` / `yawn` / `toilet`?
