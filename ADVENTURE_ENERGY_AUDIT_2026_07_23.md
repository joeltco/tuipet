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
- Town waypoint arrival / town-warp: +6 (TOWN_REST_ENERGY).  That is
  ALL a town gives.
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

## DESIGN FINDINGS — Joel's ruling wanted

- [ ] D1 **Town rest is one battle's worth.**  +6 vs battle −5; the
      arrival strip says "rested up", the module doc says "refills".
      Options: (a) town rest = FULL tank (it already costs the win
      streak — that's the gamble); (b) rest to HALF tank, floor +6;
      (c) keep 6, reword the strip/doc to stop over-promising.
- [ ] D2 **Energy stops mattering at 0 on the road.**  Battles floor
      at 0 and wilds are ungated, so a pet on empty chain-fights all
      day with zero consequence.  Options: (a) fighting on an empty
      tank pushes past empty (unfloor battle cost → the planted-feet
      system finally fires from fighting, not just hazards);
      (b) an empty-tank fighter takes a hit-chance penalty (the
      weight/belly lever grammar); (c) keep — energy is march fuel
      only.
- [ ] D3 **Inconsistent floors**: march and battle floor at 0, the
      hazard's −2 does not.  Hazards being the only negative source
      makes the refusal system nearly unreachable.  Resolve with D2's
      choice (one floor rule for all three).
- [ ] D4 **Cups have no energy gate and bill −5 per match** (home and
      town cups both).  A chosen SINGLE battle gates at energy ≥ 10;
      a 5-match bracket gates at nothing.  Options: (a) can_enter
      requires ≥ 10 like any chosen fight; (b) cup matches bill less
      (−2) since the bracket multiplies them; (c) keep.

## Verified clean

- No double-billing anywhere: one `record_battle` per bout
  (Battle._finish's `over` guard holds; surrender guarded 2026-07-19).
- Town hub visits (shop/eggs/sell/cup doors) touch no energy
  themselves; re-entering a town span does not re-pay the +6
  (`_resting` latch).
- Boss resolve, danger warp, go-home, summary: no hidden energy moves.
- `_go_home`/`_after_adventure` clears `away` correctly; no offline
  catch-up anywhere (TIME LAW holds).
