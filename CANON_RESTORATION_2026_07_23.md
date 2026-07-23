# CANON RESTORATION — 2026-07-23

Joel: "it was wrongfully stripped. what other canon features were
taken?" → "whatever is canon bring back."

Ruling: of the fifteen systems the BASIC VPET strip (2026-07-16/17)
removed, the ones the REAL BANDAI HARDWARE has come back.  The
app-invented systems (weather, mood, enthusiasm, spirit, fatigue,
nutrition macros, taste, element, habitat, timeRanks, day/night
tinting) stay stripped — that part of the strip was correct.  Standing
rulings untouched: DSprite mortality (no lifespan clock), TIME LAW,
soft refusals, LINES_SPEC = the evolution contract.

Method: rebuilt to HARDWARE rules on today's architecture — the
pre-strip DVPet machine (recovered from git, 5a853e4~1) is the
CONSTANTS reference, not a paste-back: it was woven through the very
app systems that stay dead.

## RELEASE A — INJURY (the second ailment)              [x] v0.5.205

- [x] A1 `injured` state + lifetime `injuries` count.  Battles can
      wound (LOCAL recorded bouts; online stays L17 body-billing
      only).  The roll adapts the decompile's BattleInjury table
      (/1000): condition good 3 / bad 100 (bad = starving, drained,
      weight ≥8g off base, or already sick), +50 on a LOSS, +10 for
      an elder (age ≥ 15d) or an InTraining baby.  A live VITAMIN
      zeroes the good case and caps the bad at 25 (the decompile's
      good_v/bad_v column — the vitamin's canon second job).
- [x] A2 THE BANDAGE — items.csv row 80, real DVPet item, dormant
      since the strip, now in the TUIPET catalog (Care, 300b).  One
      bandage cures (the DSprite one-dose grammar, same as the pill);
      refused when nothing is hurt.  The PILL stays sick-only, the
      BANDAGE is injury-only — two ailments, two meds, the device
      pair restored.
- [x] A3 Consequences: `battle_condition` refuses ("Too hurt to
      fight."), the death hazard whispers while injured (same scale
      as sick), `status_word` says "hurt", and the injury rides the
      same care-alarm cascade as sickness.
- [x] A4 Board/help/news + pins (test_canon_injury.py).

## RELEASE B — DISCIPLINE (praise & scold)              [x] v0.5.206

- [x] B1 The GAUGE: the frozen `obedience` field (0..100) is live
      again; `_set_obedience` clamps instead of no-opping, so the
      standing canon write-sites (clean's reward, etc.) resume paying.
- [x] B2 The TANTRUM: `discipline_call` fires on an awake, home pet
      (adapted checkDisciplineCall cadence ~1/90 game-min), grumble
      anim + care alarm.  Open ~10 game-min; IGNORED → a care
      mistake (canon: ignored calls cost) + obedience −5.
- [x] B3 The VERBS: `p discipline` opens the two-row Praise/Scold
      picker (new panel: smoke walk + card + all four key surfaces).
      SCOLD a tantrum: obedience +25, call clears, the scolded sulk.
      SCOLD a calm pet: it sulks, nothing gained.  PRAISE inside a
      praise window (opens on a local battle WIN or a mega drill):
      obedience +10, the cheer.  PRAISE outside one: nothing (the
      no-praise-farming rule, from the pre-strip audit).
- [x] B4 What obedience does NOT touch: refusals (soft-refusal
      calibration is a standing HARD RULE) and LINES_SPEC gates.  It
      is the tantrum economy + the gauge on the DigiCore PERSON page.
- [x] B5 Pins (test_canon_discipline.py) + surfaces.

## Deliberately NOT restored (with reasons)

- Sickness worsening ladder / multi-dose meds: the shipped DSprite
  rule is pill-cured-only, one dose — pinned truth since 2026-07-18.
  Bandage follows the same grammar.
- Injury from exercise (decompile InjuryChance on drills): the drill
  is the 0.5 timing bar now; wounding a training montage fights the
  Pen20 pure-upside ruling.  Battles wound; drills don't.
- Obedience-driven refusals: Joel's soft-refusal recalibration stands
  unless he names otherwise.
