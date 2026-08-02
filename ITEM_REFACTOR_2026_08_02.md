# ITEM REFACTOR — the board

**Joel, 2026-08-02: "shits fucked up... we need a full blown item refactor,
dude.... you made shitty items. make a plan, send me the list"**

Constraints he set, on the same thread:
- ⛔ **No repricing.** ("i didnt want to reprice")
- ⛔ **No deleting.** ("or delete my guy")
- ✅ **Change what items DO.** ("chamge what it does maybe")

Nothing below is implemented. This is the list; each row waits on his word.

---

## How the rot happened

The catalog went 44 → 132 in one autonomous overnight build (v0.5.283-284,
2026-07-26). Effects were read off the authored CSV columns and priced off the
authored price columns — **but never checked against each other, or against the
free buttons.** So the shelf has items that cost 50× a sibling and do a third
as much, and premium "combos" that bundle a keypress you already own.

The measurement behind every row here: `use_item` run through the REAL handler
on a maximally needy pet (sick, hurt, starving, drained, filthy, 3 care slips),
114 items, deltas recorded field by field.

## The one rule I'd apply

**An item earns its slot by doing something the free buttons and the cheaper
items CANNOT — a capability, not a bigger number.**

Capabilities that already exist in tuipet and are fair to lean on:
duration/guards (the Vitamin's injury guard), no-weight-cost (the free pill
charges +5 weight a use), works-while-asleep, works-on-the-road, and undoes
something otherwise permanent.

---

## THE LIST

### 1. Gold Pill — 10000b, legendary tier

| | |
|---|---|
| does now | energy **+12** |
| beaten by | **Energy Drink, 200b, common** — energy to **FULL** |
| verdict | 50× the price for a third of the effect. The worst row on the shelf. |

**Proposed job:** full tank **and it HOLDS** — the energy drain pauses for a
game-day. Nothing in the game stops the drain; the Vitamin already proves the
"guard" shape works. A legendary tank item should mean you stop thinking about
energy, not that you sip 12.

### 2. Elixir — 2000b

| | |
|---|---|
| does now | cures sickness · energy to FULL |
| beaten by | **free F pill** (cures sickness) **+ Energy Drink 200b** (full tank) |
| verdict | 2000b for 200b and a keypress. This is the one Joel spotted. |

**Proposed job:** the cure that **works on a sleeping pet without waking it.**
All five cure paths in the game call `_disturbed()` first — the free pill, the
bandage, everything. Nothing can treat a sleeper. That is a real, empty niche,
and it fits "the pill, perfected".

### 3. Vitamin G — 2000b

| | |
|---|---|
| does now | heals injury · effort FULL · injury guard |
| beaten by | **free H heal** (heals injury) **+ Vitamin 500b** (effort + guard) |
| verdict | 1500b for a button you already have. |

**Proposed job:** injury **immunity** for a long stretch — prevention, not
repair. `H` already heals for free; the road audit measured **40% of adventure
runs coming home wounded**, so "cannot be wounded" is worth a premium in a way
"heals a wound" never can be.

### 4. Miracle Drink — 7777b, legendary tier

| | |
|---|---|
| does now | −1 care mistake · energy +12 |
| beaten by | **Cold Compress 2000b** (−1 care mistake) **+ Energy Drink 200b** |
| verdict | 7777b for 2200b of parts. |

**Proposed job:** the **complete** undo. A care mistake is counted twice — the
running total (frail at 5, dead at 20) and today's tally (which decides the
birthday result and feeds `evol_bonus`). Both erasers only clear the first, so
today's slip survives a 7777b drink. Let the Miracle Drink clear **both** and
be the only full undo in the game; the Compress stays the cheap partial.
(Keeps Joel's 2026-07-23 "one at a time" ruling — still one slip.)

### 5-7. Xylophone 800b · Video Game 600b · Television 1000b

| | |
|---|---|
| do now | energy **+2 / +2 / +3** (the last two also +1 weight) |
| beaten by | **Energy Drink 200b** — full tank |
| verdict | the play shelf is priced like utilities and pays like rounding errors. |

**Proposed job:** these three are the only items that fire a SHOW, and that is
their real identity — so give the stat line something the drink cannot do
rather than a bigger energy number. My pick: **play trims the weight the free
pill piles on** (the pill charges +5 weight every use; six pills to fill a tank
is +30, straight into the hit formula's weight term). A toy shelf that undoes
the cost of the free cure is a shelf with a reason to exist.
⚠ Lowest-confidence row on this list — say if you'd rather they just paid real
energy.

### 8. Book — 1000b

| | |
|---|---|
| does now | obedience **+5** |
| beaten by | **Textbook 1500b** — obedience **+20** |
| verdict | two-thirds the price, a quarter of the effect. A dead rung. |

**Proposed job:** an obedience **guard** — manners hold steady for a stretch
instead of drifting. "A well-thumbed guide" you keep consulting, against the
Textbook's one big cram. Same guard shape as the Vitamin.

---

## NOT TOUCHING — measured and coherent

- **The attribute chips.** 1500b→+15, 3000b→+30, HP/Omni scale the same way.
  Perfectly linear. Leave them.
- **The food shelf.** Overlapping with meat is the POINT — different
  magnitudes, weights and side effects. A flavour catalog, not redundancy.
- **The traps** — Hedonism 101 (obedience −80) and the poison mushroom. Both
  authored, both labelled in their own blurbs, both go down without refusing on
  the mushroom's precedent. Working as intended.
- **Med 100b · Vitamin 500b · Cold Compress 2000b · Energy Drink 200b ·
  Slim Drink 100b · Supplement 100b.** All cheap, all doing exactly one thing
  the free buttons don't do as well or as fast.
- **Road tickets, evolution keys, capsules, spirits.** Out of scope; the road
  set was audited 2026-07-31 and is coherent.
- **Chocolate Egg 300b.** Looks like Bread at 3× the price until you measure
  the inventory — it really does grant a toy, as its blurb promises. Fine.
- **Toy Oven 500b.** Hunger −1 reads like a bug and is not: "+Appetite", makes
  room for another meal. Niche and steeply priced, but it does what it says.

## Order of work, once he rules

1. Miracle Drink (self-contained, and the finding is already confirmed)
2. Elixir (needs a no-disturb path through the cure handlers)
3. Vitamin G (needs an immunity window; reuse `vitamin_lapse`'s shape)
4. Gold Pill (needs an energy-drain guard — new lapse field)
5. Book (obedience guard — same shape as 4)
6. The toys (lowest confidence; wants his call first)

Every row: behaviour only. No price moves, no deletions, blurbs updated in
lockstep (the dossier-blurbs-are-TRUE law), pins per item.
