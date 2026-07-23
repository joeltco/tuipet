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

## ⚠ PLAN AUDIT (2026-07-23, Joel: "audit the plan")

The plan was written without checking the clock, and the clock breaks
it.  Findings, severity first.  **THE UNIT LAW below governs every
duration constant in this arc.**

### THE UNIT LAW — dt IS GAME-MINUTES, 1:1

`tick(dt)`'s dt is world-SECONDS, and one world-second IS one
game-minute.  Confirmed three independent ways:
- `SICK_POOP_P` is documented "per minute" and coded `random() < p*dt`
- `awake_limit 480 + sleep_limit 960 = 1440 = DAY_LENGTH` (a game day
  of 1440 game-min in 1440 world-seconds)
- `sleep_lapse += dt * ...` accumulates straight against `sleep_limit`

**Therefore tuipet's clock runs 60× faster than the device's**, and a
canon duration constant CANNOT be copied as-is.  The codebase already
knew: `FILTH_SICK_BOUND = 200  # FilthSickChanceBound 12000 real-min
-> /60 game scale`, and petbase:76 warns a faithful port "collapses
mood within ~15 real-min on the compressed clock."

### P0 — TWO SHIPPED BUGS (v0.5.205/206), fix before any new work

- [x] **P0a — SHIPPED v0.5.207.  The Vitamin's injury guard was
      effectively PERMANENT.**
      `_vitamin` sets `vitamin_lapse = 1440.0` (intended: 1 game-day)
      and `petbody:592` decays it `dt / 60.0`.  Under the unit law
      that is 60× too slow: it needs **86,400 game-min ≈ 24 real hours
      of play** to expire.  One 500b Vitamin disarms the entire injury
      system shipped one release earlier.  Fix: decay by `dt`.
- [x] **P0b — SHIPPED v0.5.207 (comments corrected; THE UNIT LAW is
      now written at the tick site).  Unit mislabels in shipped
      comments (and in this board's first draft).**  The tantrum's `dt / (60.0*90.0)` is one per
      5400 game-min (= ~90 REAL min of play), not the "~1/90 game-min"
      the comment claims.  `praise_window`/`scold_window = +600.0` are
      600 game-min (= 10 real min), not "10 game-min".  The BEHAVIOUR
      is what Joel was told; only the labels are wrong — but D1 was
      specced in these same wrong units, so correct them before
      anyone copies the pattern again.

### P1 — D1 AS WRITTEN WOULD BREAK D3 (the plan contradicts itself)

Canon fade at face value, on tuipet's 60×-compressed clock:
- neutral cadence 120 game-min → **−2 every 2 real min = −60/hour**
- tantrum reward +25 per ~90 real min ≈ **+17/hour**
- **net ≈ −43/hour → every gauge parks at 0**

With D3 layered on, *every* pet ends permanently disobedient — the
exact inverse of D3's promise ("a well-raised pet NEVER refuses").
D1 must **scale** the cadence (the `/60` precedent) and be sized
against the measured reward rate, not copied.

### P2 — D3's "ONE DOOR" CLAIM IS FALSE, and the real doors leak

`check_refused` has exactly three callers: `pet.py:741` (mode change),
`jogress.py:143`, and `petbattle.py:219` (`can_battle`).
**Feed and train never call it.**  So:
- "feed/train/battle only" needs NEW plumbing at feed and train —
  materially bigger than boarded
- the two existing callers are **jogress and mode-change, both OUTSIDE
  the approved scope**; making `check_refused` manners-aware would
  silently start refusing evolution paths.  Any D3 work needs an
  explicit carve-out so those two keep their energy-only behaviour.

### P3 — OBEDIENCE SCALE COLLISION (shipped, and it poisons D3)

Canon `MAX_OBEDIENCE = 150`; v0.5.206 clamps 0..100 and the card reads
"/100".  Canon seeds are `ROOKIE_OBED_DEFAULT = 25` and
`ROOKIE_OBED_BAD = 0` — so under D3's proposed "under ~25" threshold a
freshly-evolved Rookie is **born at or below the disobedience line**.
That is inherited, not earned.  Rule the scale (rescale seeds to /100,
or raise the clamp to 150) BEFORE picking D3's threshold.

### P4 — INJURY SHIPPED WITHOUT ITS CANON RECOVERY

Canon heals injuries on a clock: `MIN/MAX_INJ_LENGTH = 1,12` recovery
lapses × `INJ_LAPSE_MIN = 29` game-min, and the pre-strip code ticked
`inj_length` down ("injLapse: the injury heals over time").  **The
`inj_length` field is still in every save, dormant.**  Shipped
behaviour: `injured` clears ONLY via the Bandage (`petcare:482`).
Consequences:
- the sibling ailment has a FREE, infinite cure (the F-menu pill)
  while injury's only cure is a **300b shop-only item** — asymmetric
- not a hard softlock (adventure/raid/train are not injury-gated, so
  bits stay earnable) but a broke+injured player grinds while hurt
- [ ] RULE IT: restore the canon lapse (revive `inj_length`), or keep
      bandage-only and say so on the board as a deliberate deviation.

### P5 — "TOO HURT TO FIGHT" ISN'T LITERALLY TRUE

`battle_condition` blocks chosen bouts and every cup door, but
adventure is not injury-gated and road ambushes are ungated by design
— so an injured pet still fights wilds.  Consistent with the energy
grammar (same carve-out), but the wording overpromises.  Ruling
wanted, not necessarily a fix.

### Revised order (supersedes "Suggested order" below)

0. **P0a + P0b** (shipped bugs; P0a silently disables injury)
1. **P4 ruling** (injury recovery) — cheap, and it changes D's shape
2. **D2** (overfeed) — genuinely independent, small, no clock risk
3. **P3 ruling**, then **D1 with a SCALED cadence**
4. **D3** only after D1's real numbers are observed, with feed/train
   plumbing built and the jogress/mode-change carve-out pinned
5. **E1 + E2**, then **E3 + E4**

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
      ⚠⚠ SUPERSEDED BY THE AUDIT (P1): those cadences are DEVICE
      real-minutes.  Copied onto tuipet's 60×-compressed clock they
      drain −60/hour against a +17/hour reward — every gauge parks at
      0 and D3 inverts.  The cadence MUST be scaled (`/60` precedent)
      and sized against measured reward rates.  Also see P3: the
      0..100 vs canon 0..150 scale must be ruled first.

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
      - ⚠⚠ CORRECTED BY THE AUDIT (P2): `check_refused` is NOT the one
        door.  Feed and train never call it; its only callers are
        mode-change, jogress and `can_battle`.  Feed/train need NEW
        plumbing, and jogress/mode-change need an explicit carve-out
        so they keep their energy-only behaviour.  The energy
        auto-refuse stays as-is everywhere.
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

### E1 — Praise & scold need their shows  ✅ SHIPPED v0.5.210
[Joel named this]

- [x] `pet.praise()` set `_set_anim("happy")` and `pet.scold()` sets
      `_set_anim("sad")` — but an ANIM is the LCD pose, not the SHOW.
      Every sibling verdict in the game fires an **fx** on the house
      screen: training uses `cheer`/`jeer`/`spit`, the cup uses
      `cheer`/`losing`, the m-battle now uses `cheer`/`losing`.
      Discipline fires NOTHING.
- [x] Wired `_after_discipline` to the same grammar it already follows
      elsewhere: praise-that-landed → `cheer`; scold-that-landed →
      `jeer`; wrong-moment verbs → the small pose only (no fx), since
      nothing happened.

### E2 — Bandage animation  ✅ SHIPPED v0.5.209
[Joel offered this: "theres a bandage sprite with animation sequence"]

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

### E2b — THE ITEM-SHOW GAP (measured 2026-07-23, Joel: "we have the
### vitamin sprite, correct? is all of that already wired in?")

No — and it is not just the vitamin.  **All 26 non-food catalog items
carry a full 4-frame ripped strip.  Only 7 (every one of them a toy)
play any show at all.**  The other 19 flash a line of text.

The canon mapping is FREE, we simply never read it: our icon key
`i:N` **is** the items.csv row id, and that sheet has an
`AnimationType` column for every row.  Verified:

| item | canon AnimationType | script written? | wired? |
|------|--------------------|-----------------|--------|
| bandage | `Bandaging` | **yes (v0.5.209)** | **yes** |
| music_player | `Play` | **yes** | NO |
| textbook | `Study` | **yes** | NO |
| dumbbell | `Lift` | **yes** | NO |
| grow_capsule | `Study` | **yes** | NO |
| revive_floppy | `Play` | **yes** | NO |
| port_potty | `PortToilet` | no | NO |
| x_antibody / dna_crystal | `ItemEvol` | no | NO |
| digimemory | `Inherit` | no (has its own flow) | NO |
| town/disaster transport | `*Transport` | no (own flows) | NO |
| life_recovery | `Recover` | no | NO |
| the 7 toys | (various) | yes | yes |

- [x] **SHIPPED v0.5.207 — FOUR of the five (revive_floppy excluded:
      its canon type is Play, but it is used on a DEAD pet and the bag
      is unreachable at the grave, so that show could never play).
      Wired by READING THE CANON COLUMN, and `shop.TOY_SCRIPTS` is
      retired — `shop.item_script()` is the one source now.
      ~~FIVE FREE WINS~~ — art exists, script already written in
      `itemfx.SCRIPTS`, only the wiring is missing**: `music_player`
      → Play, `textbook` → Study, `dumbbell` → Lift, `grow_capsule`
      → Study, `revive_floppy` → Play.  Zero new animation work.
- [x] **SHIPPED v0.5.208 — the Vitamin (and every `f:` consumable).**
      `f:5` is literally the DVPet "Vitamin" (4 frames, 24×24) — but
      **foods.csv has NO AnimationType column**, because food-sheet
      items are EATEN.  Their canon show is the `eat` fx we already
      ship (the pill rides exactly this: "the pill is EATEN, the
      source's EATING action, same as meat").  Fix: let `f:` Care
      consumables fire the `eat` fx with their own icon — today
      `shopscreen` gates that on `FOOD_KEYS`, so Care items fall
      through to a bare text flash.  Covers vitamin, energy_drink,
      slim_drink, sleeping_pill, caffeine_pill, anti_evo_chip.
- [x] **DONE v0.5.207 — retire the hand-map.**  `shop.TOY_SCRIPTS` is a 7-entry
      hand-maintained partial duplicate of a canon column that exists
      for all 26 items.  Read `AnimationType` off the icon key
      instead (single-source rule), keeping `itemfx.NO_FX` +
      own-flow items as the explicit exclusions.

### E3 — Dead show code (measured, not guessed)

fx kinds the painter fully implements but **nothing ever fires**:

| fx | state |
|----|-------|
| `heal` | painter gone (44c6405); E2 restores the show |
| `toilet` | orphaned by the staple-props strip (2026-07-17) |
| `poopdance` | ✅ WIRED v0.5.211 (gauge >= 80%) |
| `yawn` | ✅ WIRED v0.5.211 (bedtime nears); the 3 anim sites keep their simple pose |

- [x] poopdance + yawn WIRED v0.5.211 (Joel's order).  ⬜ `toilet`
      still unruled -- a deletion needs a NAMED order (removals rule).
      ~~Rule each: wire it to the moment it belongs to, or delete it.~~
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

1. ~~D1 fade rate~~ → superseded by P1: the question is now **how far
   to scale** the cadence, answered after the reward rate is measured.
2. D2: care mistake on every stuffing, or only on repeat stuffing?
3. ~~D3 refusable commands~~ → still feed/train/battle (recommended),
   but see P2: it needs real plumbing plus a jogress/mode-change
   carve-out, and P3's scale ruling first.
4. F: bag-only Bandage (recommended), or spend bar cells?
5. E3: wire or delete `poopdance` / `yawn` / `toilet`?
   (⚠ a deletion needs a NAMED order — the removals rule.)
6. **P3: obedience scale** — rescale the canon seeds onto 0..100, or
   raise the clamp to canon's 150?
7. **P4: injury recovery** — restore the canon heal-over-time lapse
   (`inj_length`, still dormant in every save), or keep bandage-only
   as a deliberate deviation?
8. **P5:** should injury block the ROAD too, or is "too hurt to fight"
   understood as chosen-fights-only (matching the energy grammar)?
