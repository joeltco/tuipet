# DISTRIBUTION — the spread arc (plan, draft 1)

Joel 2026-07-23: "once thats refactored, we gotta spread them all out.
tiered rarities. zone shop exclusives, etc." → 2026-07-24: "lets move on
to distributions".

The items refactor is CLOSED (ITEMS_REFACTOR_PLAN §10, P1-P6, v0.5.218).
44 items, one grouping, `tier` declared and empty on every entry.

**Nothing here is agreed.**  §4 is the ruling list.

---

## 1. GROUND TRUTH, re-derived 2026-07-24 (two prior claims were STALE)

### ⚠ Corrections to what the old audit board says

- **Adventure loot is keyed by SCENE (biome), not by zone slot number.**
  `zone_finds()` reads `BIOME_FINDS[scene]`.  The 2026-07-23 diversity
  audit's F1 ("keyed to the zone's SLOT NUMBER, 1-1 == 2-1") describes a
  state that no longer exists, and I repeated it once before checking.
- **The endgame zones no longer dig one item.**  `FINAL_ZONE_FINDS` is 5
  items (anti_evo_chip, x_antibody, textbook, dna_crystal, steak), so
  audit F2 is also closed.

Do not plan against that board without re-deriving first.

### ⚠ P6 moved distribution as a SIDE EFFECT, before this arc started

`shopConsumable.csv` authors 22 town-shop overrides; entries whose icon
has no catalog key are silently dropped.  P6 added seven chips, so
**10 previously-dropped overrides now resolve** — kept went 5 → 12.
Consequence, unplanned and already live in v0.5.218:

| good | towns stocking it |
|------|-------------------|
| vaccine_chip | 16 |
| virus_chip | 16 |
| anti_evo_chip | 16 |

That is *canon-authored* placement (DVPet decided it, not me), so it is
defensible — but it was a side effect, not a decision, and this arc
should either ratify or override it.  **10 overrides are still dropped**:
`i:28 i:31 f:26 f:27 f:31 f:39 f:40 f:56 i:81 i:82`.

### The spread as it stands

**Zones** — 26 zones over **11 scenes**, very unevenly:

| scene | zones | | scene | zones |
|-------|-------|-|-------|-------|
| factorynight | **8** | | islandsea | 1 |
| mountains | 3 | | flowerfield | 1 |
| city | 3 | | desert | 1 |
| forestgate | 3 | | lakeside | 1 |
| underwater | 2 | | frozenpeak | 1 |
| greenhills | 2 | | | |

**Eight of 26 zones dig identical loot.**  That is the real texture
problem now — not slot-keying, but one scene owning a third of the map.

**Items** — 28 of 44 are findable somewhere; **16 never are**:
cake · cookie · cupcake · giga_meal · xylophone · port_potty ·
revive_floppy · digimemory · miracle_drink · and all 7 chips.

**Towns** — 35 distinct goods across 26 towns.  **9 items sit on no town
shelf at all**: ball · candy · cheese_burger · cookie · cupcake ·
digimemory · life_recovery · poison_mushroom · tuna.

**Coverage is lopsided by design-accident** (P2's map): `energy` is
touched by 12 items, `hunger` 10, `weight` 9 — while ~20 live stats have
exactly one item each.  Rarity that ignores this will feel arbitrary:
the singletons ARE the interesting items.

---

## 2. WHAT "TIERED RARITIES" COULD MEAN (the fork)

`tier` is declared and empty.  It can drive one or more of:

- **a) Stock rarity** — how often a town/home shelf carries it.
- **b) Find rarity** — its weight in a zone's loot roll (today every
  entry in a pool is equally likely).
- **c) Prize rarity** — raid/cup reward weighting.
- **d) Price** — tier implies a price band.

These are independent.  (d) is the most invasive: prices are canon-
derived for 20 of 44 items, and re-pricing would overwrite canon numbers
that P5/P6 deliberately took from the CSVs.

## 3. WHAT "ZONE SHOP EXCLUSIVES" COULD MEAN

Note the wording is **zone SHOP** exclusives, but zones do not have
shops — **towns** do, and towns sit ON zone legs (`town_legs`).  So this
is one of:

- **i)** each TOWN gets a signature good only it sells (a stronger
  version of the existing `_guest_deal`, which already deals 26 unique
  guest goods);
- **ii)** each ZONE gets a signature FIND only it drops (needs per-zone
  keying, since 8 zones currently share factorynight);
- **iii)** both.

With 44 items and 26 towns + 26 zones, **one exclusive each is
arithmetically impossible** without repeats or new items.  That is the
hard constraint this arc has to be designed around.

---

## 4. RULINGS NEEDED

- **D1 — what does `tier` DRIVE?**  Any of §2 a/b/c/d.  My read: (a)+(b)
  give the most felt change for the least risk; (d) fights the canon
  prices we just landed.
- **D2 — how many tiers, and what names?**  (e.g. common / uncommon /
  rare / legendary, or a 1-5 number.)
- **D3 — exclusives: towns, zones, or both?** (§3 i/ii/iii)
- **D4 — the 8 factorynight zones.**  Give them distinct loot (per-zone
  keying), or accept that one scene owns 8 zones?
- **D5 — the 16 never-found items.**  Do they become findable, stay
  shop-only, or is shop-only a deliberate tier in itself?
- **D6 — ratify or override P6's side effect** (chips in 16 towns).
- **D7 — the 10 still-dropped town overrides.**  Add those items (they
  include Elixir/Vitamin G, which R3 says must NOT be sold), leave them
  dropped, or re-point those town slots at existing goods?

## 5. WHAT I WILL NOT DO WITHOUT A NAMED ORDER

- Revive **Taste** (`_change_rank`) or **compensateAttributes** — both
  dormant, both pinned as deliberate refusals in `test_items_p6.py`.
- Re-price canon-derived items (D1d) — 20 of 44 prices come straight
  from the CSVs.
- Invent an economy: no new currencies, no gacha, no loot boxes.
- Sell an ailment cure (R3's symmetry) — this rules out the Elixir and
  Vitamin G that two of the dropped overrides want.
