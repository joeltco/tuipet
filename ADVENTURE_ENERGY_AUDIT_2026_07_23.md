# ADVENTURE ENERGY AUDIT — 2026-07-23

Joel: "im noticing weird things in adventure energy. audit town
transition and energy behavior, other transtions too, i seen it fill
energy, then go to 0 after a battle? i coukd be wrong."

He was not wrong.  Method: traced every `_set_energy` call through a
scripted run (instrumented spy), read every transition (town arrive,
town visit, town warp, danger warp, wild fight, boss, cup match,
hazard, march, refuse, go-home), and probed the road-sleep path.

## The complete energy map of the road

COSTS
- March: −1 per drain cadence, FLOORED at 0 (marching can never push
  past empty)
- Hazard pounce eaten: −2, NOT floored (the ONLY road source of
  negative energy)
- Every battle: −5 (record_battle), floored at 0 — wild, boss, and
  EVERY cup match alike
- Wild fights are ungated (ambushes aren't a choice) — the pet fights
  at 0 energy freely, forever
- Cups have NO energy gate at all (can_enter checks young/asleep/
  no-cup only) — a bracket is 3-5 matches = −15..−25

GAINS
- Town waypoint arrival / town-warp: rest to at least HALF the tank,
  +6 (TOWN_REST_ENERGY) top-up when already above it (D1 ruling
  2026-07-23; was a flat +6 — one battle's worth).
- Energy Drink (bag): set to FULL — but the bag is only reachable
  inside town hubs on the road
- Nothing else.  The pet's life sim is PAUSED in every mode (the TIME
  LAW one-law freeze), so there is NO sleep regen on the road.

## What Joel saw

"Fill energy, then 0 after a battle": both halves are real arithmetic.
A town says "⌂ rested up" but gives +6 — a single battle (−5) erases
the whole rest, and the next hazard (−2) lands past it.  A cup melts a
half-full tank to 0.  The doc at the top of adventure.py even says the
waypoint "refills" energy — the words promise a refill, the math gives
one battle's worth.

## BUGS — fixed this round (v0.5.194)

- [x] B1 **Sleep Pill on the road = PERMANENT softlock.**  The
      roadside-nap branch waits out `pet.asleep`, but nothing ticks
      sleep in a mode — the pill froze the march forever (ESC home the
      only exit).  Repro'd live.  The pill is now REFUSED on the road
      ("Not on the road — no bed out here.", pill kept).
- [x] B2 **The refuse strip promised "rest refills ⚡" — a lie on the
      road** (there is no rest out there; see the map above).  It now
      names the only real outs: `T warp · ESC home`.

## DESIGN FINDINGS — RULED 2026-07-23 (Joel: "lets fix d1-4 however
## you recommend") — shipped v0.5.195

- [x] D1 **Town rest is one battle's worth** → **(b) rest to at least
      HALF the tank.**  `_rest_up` is now
      `max(energy + 6, max_energy // 2)`: a spent (even knocked-
      negative) pet leaves town standing on half a tank — two battles
      and change, not one — while an above-half pet keeps the +6
      top-up, clamped at full.  "Rested up" and the module doc now
      tell the truth.  A full tank was rejected (it would zero the
      Energy Drink and make towns a total reset; the streak break
      should gate a REST, not a refuel-to-max).  Pins:
      test_adventure_towns half-tank + top-up tests.
- [x] D2 **"Energy stops mattering at 0"** → **the board OVERSTATED —
      the consequence already ships.**  Side._condition (battle.py)
      bills the energy meter into every hit roll: a full ten-point
      hit-chance swing between a fresh tank and an empty one, and
      coach_line reports "energy ran low".  Option (b) was already
      built; nothing added.  Now pinned:
      test_an_empty_tank_already_fights_worse.
      (Unflooring battles — option (a) — was rejected on arithmetic:
      ~8 wilds/zone × −5 = −40 on a 24 tank; every ordinary run would
      strand mid-zone.)
- [x] D3 **Inconsistent floors** → **named THE ENERGY FLOOR LAW: a
      SPEND floors at zero, a KNOCK pushes past it.**  Marching and
      battling are exertion the pet chooses to pay — an empty tank
      can't fund them, so both floor at 0.  A hazard pounce is DAMAGE
      — being blindsided knocks past empty, and ONLY that plants the
      pet's feet (the refusal system's trigger stays rare and
      dramatic, per the soft-refusal calibration).  The floors were
      never inconsistent, just unnamed.  Law documented at
      adventure.py's constants block + hazard_hit + record_battle;
      pinned: test_the_energy_floor_law_spend_vs_knock.
- [x] D4 **"Cups have no energy gate"** → **the board was WRONG —
      every cup door already gates.**  can_enter alone doesn't check
      energy, but every ENTRY path runs battle_condition (the ONE
      bout-condition source, audit 2026-07-19): hourly
      eligibility (tournament.py:283), eligibility_at (:297),
      eligibility_featured (:305), and the town cup
      (townscreen.py:99).  A pet under BATTLE_MIN_ENERGY (10) never
      starts a bracket.  A bracket entered at 10 can floor at 0
      mid-cup — by the floor law that's "comes home spent", and the
      D2 hit-term makes late matches honestly harder.  Kept; pinned:
      test_a_drained_pet_is_refused_at_every_cup_door (+ the town
      door's existing pin in test_town_cup).

## Verified clean

- No double-billing anywhere: one `record_battle` per bout
  (Battle._finish's `over` guard holds; surrender guarded 2026-07-19).
- Town hub visits (shop/eggs/sell/cup doors) touch no energy
  themselves; re-entering a town span does not re-pay the +6
  (`_resting` latch).
- Boss resolve, danger warp, go-home, summary: no hidden energy moves.
- `_go_home`/`_after_adventure` clears `away` correctly; no offline
  catch-up anywhere (TIME LAW holds).
