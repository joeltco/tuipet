# Gameplay polish board — 2026-07-22 (v0.5.163 baseline)

Five-area gameplay audit of tuipet as ITS OWN THING (no external-canon
comparisons; shipped behavior = the only canon).  This file is the living
checklist: `[x]` = shipped, `[~]` = in progress, `[J]` = waiting on a design
call from Joel, `[ ]` = queued.

Closed rulings honored throughout (time law, DSprite mortality, killed
features, the never-cut list, no invented systems, no new art).  Dormant
code stays dormant unless named.

## Bugs (verified in code, not taste)

- [x] **B1 — Adventure shelf unobtainable.** *(shipped v0.5.164)* `GROUPS` (shopscreen.py:41)
  carries no tab with the `Adventure` category, and home shop, town
  counters AND the bag all filter rows through those tab groups
  (shopscreen.py:113-135).  `town_transport` (500b), `disaster_transport`
  (250b) and `life_recovery` (1000b) can never be bought or seen anywhere;
  the T-menu / use_transport plumbing and the map-clear gates
  (shop.py:79) are unreachable shipped code.  Side effects: the town
  daily deal rolls onto an invisible item ~half of all days; family-A
  towns render a blank Food tab.
  **Fix:** put `Adventure` in the Items tab group — one edit flows to
  home shop, town counters, and bag.

- [x] **B2 — `life_recovery` has no consume path.** *(shipped v0.5.164)*  Home use refuses with
  "use it on the road" (petcare.py:348) but the road only recognizes the
  two transports (adventure.py:426).  **Fix:** road T-menu offers Life
  Recovery when held → restores lives (refuse at full), consumes one.

- [x] **B3 — Digicore lies under an armed divergence.** *(shipped v0.5.165)*  `_maybe_evolve`
  honors `divergence_target` first (pet.py:557) but the CORE silhouette
  and EVOLVES checklist read only the line chart (digicore.py:135-212).
  **Fix:** when a divergence is armed, the gaze + EVOLVES page show the
  armed corpus target (dnascreen already computes the state).

## Combat feel

- [J] **1 — Show why you won/lost.**  `hit_chance` (battle.py:123) reads
  seven hidden terms; the result screen shows none.  Proposal: post-fight
  one-liner naming the biggest drag (weight off-base / rank gap / low
  trainings), sourced from the same Side terms the engine computed.
- [J] **2 — Coaching text points at the wrong formula.**  "Good care
  widens the mega zone" describes the bar (battlescreen.py:68-81, reads
  age); the fight is decided by hit_chance (reads weight/trainings).
  Proposal: reword the ready-screen hint toward the real levers.
- [J] **3 — Timing bar is nearly cosmetic** (EV 1.9/1.5/1.2; drill grades
  stat-identical, petbattle.py:179-201).  Balance call.
- [J] **4 — Normal cups flatline vs untrained fields** (battle.py:79-88);
  only title defenses field trained foes.  Balance call.
- [J] **5 — Close fights look like blowouts** — no HP-margin readout;
  draw-as-loss invisible (battle.py:220-227).

## Care loop / main view

- [J] **6 — Energy is a dead gauge on the home loop** (no passive decay,
  deliberate at petbody.py:252).  Design call: earn the gauge or accept.
- [x] **7 — Lone poop pile is silent friction** *(shipped v0.5.168: quiet idle nudge, no beep)* — nag only at ≥3 piles
  (~135 min, pet.py:508).
- [J] **8 — Every alarm is the same beep** (app.py:1106-1112).  Which
  existing sound maps to which need is a taste call — proposal: keep
  alarm.wav as the base, differentiate by PATTERN (single/double/triple)
  rather than sample, or name the mapping you want.
- [x] **9 — Frailty (the lethal state) has no beep** *(shipped v0.5.168: onset alarm, no re-nag)* (app.py:1119) while
  harmless needs chirp every 90s.
- [J] **10 — Good care suppresses idle personality** — `_special_idle`
  bails at strength > 2 (petbody.py:770).  Design call.
- [x] **11 — Bad mornings are invisible** *(shipped v0.5.168: morning-tier HUD note)* — wake roll can dump 150 mood
  with only a pose (petbody.py:703-708).

## Growth / DNA

- [x] **12 — Teach that divergence IS the point of DNA** for line pets *(shipped v0.5.166)*
  (dnascreen.py:234,253).
- [x] **13 — "Charges clear at evolution" warning missing from the Charge
  screen / DNA home** (only on the Divergence page, dnascreen.py:313).
- [x] **14 — ARMED divergence never reaches the HUD/status card.**
- [ ] **15 — Album "???" has no route home** — name the line/egg (or
  jogress/armor/divergence) that reaches an unseen form
  (albumscreen.py:138; lines.py knows membership).
- [x] **16 — CORE number has no unit** *(shipped v0.5.167)* — countdown vs age share one bare
  glyph (digicore.py:37-57).
- [x] **17 — POWER page still frames Va/D/Vi as evolution gates** *(comment-only; fixed v0.5.167)*
  (digicore.py:307-311); those gates were dropped — battle stats now.

## New-player experience

- [ ] **18 — Teach the care-mistake counter** — `✗N` steers evolution and
  20 is lethal; meaning appears nowhere (statusbox.py:154-158).
- [ ] **19 — Key hints in need messages** — hungry/sick/cleaning name no
  key; lights does (app.py:1219-1223).
- [ ] **20 — "? = help" pointer is a 4-second flash** a care nag can
  overwrite (appactions.py:70).
- [ ] **21 — Egg wait is a dead zone** — 19 lit keys refuse identically,
  no hatch ETA (pet.py:535).
- [ ] **22 — Assistant bills silently** — `v` starts a metered retainer;
  help says only "v assistant" (petbase.py:626-629, helpscreen.py:15).

## Economy / world

- [J] **23 — Gen-1 starts broke with faucets gated** (0 bits; adventure
  needs Rookie; cups need a stake).  Balance call.
- [J] **24 — Two town-shop variants game-wide** (one SKU apart).  B1
  restores the transports to every counter; further variety = design call.
- [J] **25 — Late-game bits go inert** after honors/DNA/eggs cap.  New
  rungs on existing ladders = Joel's call (no invented economies).

## Noted, deliberately untouched

- Attribute-rank ledger inert (petbattle.py:76-105, acknowledged at
  pet.py:889) — dormant stays dormant.
- `status_word` fatigued/injured branches unreachable (pet.py:893-899) —
  self-documented.
- Energy no-passive-decay is commented deliberate — listed as #6 only for
  the design question, not as a defect.
