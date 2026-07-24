# ITEMS REFACTOR — scoping board

Joel 2026-07-23: "we gotta refactor the items system after we are done."

**STATUS: SUPERSEDED / CLOSED.**  This was the pre-compaction MAP.  The
actual work ran through `ITEMS_REFACTOR_PLAN_2026_07_23.md` (P1-P6, closed
§10, shipped v0.5.216-218) and then `DISTRIBUTION_PLAN_2026_07_24.md`
(D1-D7, closed, shipped v0.5.219-221).  Kept for the survey below; the
candidate list in §3 is history, not open work.

---

## 1. Where item knowledge lives today (SEVEN places)

| # | place | holds |
|---|-------|-------|
| 1 | `shop.CATALOG` | the authored 37, as a **6-tuple**: `(name, icon, price, category, effect_text, flavor)` |
| 2 | `petcare.use_item()` | a 37-branch dispatch dict mapping key → handler; **the real effects** |
| 3 | `data_shop._load_consumables()` | the DVPet csv rows (foods.csv / items.csv), reached by `data.consumable_by_key("i:80")` — carries `action` (= AnimationType), sale value, Disturb, etc. |
| 4 | `shop` town shelves | `_MAP_SPECIALTY`, `_guest_deal()`, `_base_rows()`, `_town_rows()`, `_econ_stub()` |
| 5 | `adventure` loot | `BIOME_FINDS`, `FINAL_ZONE_FINDS`, `_ROAD_KEYS` |
| 6 | `shop.LEGACY_KEYS` | 13 retired keys → their heirs (save migration, `_heal_bag`) |
| 7 | `itemfx.SCRIPTS` + `shop.item_script/item_is_eaten` | what an item PLAYS |

Derived views (cheap, fine): `FOOD_KEYS`, `ICON_KEYS`, `EFFECTS`, `FLAVORS`,
`CATEGORY_ORDER`, `ADVENTURE_GATES`, `DIGIMENTAL_GATES`.

## 2. The invariants a refactor must not break

- **`shop.CATALOG` is the single source** for what exists and what it costs.
- **Effect TEXT ↔ effect CODE is hand-maintained.**  `CATALOG[k][4]` is prose
  that must mirror `use_item`'s actual behaviour; shop.py's own docstring
  says the shelf, the bag and the belly "can never disagree".  Nothing
  enforces it.  ← the most likely refactor prize
- **`i:N` IS the items.csv row id** — that identity powers the show lookup
  and the sale value.  Do not abstract the icon key into an opaque handle
  without keeping this.
- **Shows are DERIVED, never mapped** (see TUIPET_ITEMS.md).
- **Refusal keeps the item**: `_Refused` must not consume (`use_item` only
  calls `take_item` on a non-refused result).  Burned Rev.Floppies once.
- **Sleeper law**: an item on a sleeper WAKES it — exempt only
  `music_player`, `sleeping_pill`, `cold_shower`.
- **Dormant data stays dormant**: `rand_items`/`rand_foods` and the retired
  per-slot loot tables must not be resurrected.
- **Own-door items** (digimemory, both transports, life_recovery,
  revive_floppy) are excluded from the generic show path BY KEY.
- Road items refuse from the home bag and vice versa.

## 3. Candidate problems (NOT decisions — for Joel to rule)

- **P-A The 6-tuple is positional.**  `v[3] == "Food"`, `v[4]` = effect text,
  `v[5]` = flavor read at ~8 call sites.  A dataclass/NamedTuple would name
  the fields without changing the data.
- **P-B `use_item` is one 37-branch dict** built fresh on every call, mixing
  lambdas and bound methods, with the life-state guards after it.
- **P-C Effect text can silently drift from effect code** (see §2).  Could be
  generated from, or pinned against, the handler.
- **P-D Category strings are magic values** (`"Food"`, `"Care"`, `"Toy"`,
  `"Evolution"`, `"Adventure"`, `"Medical"`) spread across shop, shopscreen
  and the bag tabs.
- **P-E Two "is it X" families**: `FOOD_KEYS`/`item_is_eaten` overlap, and
  category vs sheet-prefix both answer questions about the same item.
- **P-F Where an item can be USED** (home bag / road / town) is encoded as
  refusal strings inside handlers rather than as data.

## 4. Ground truth to re-derive at the start (do not trust this file)

```
PYTHONPATH=src python3 -c "
from tuipet import shop
print(len(shop.CATALOG), len(next(iter(shop.CATALOG.values()))))
from collections import Counter; print(Counter(v[3] for v in shop.CATALOG.values()))"
```

Tests that will catch a bad refactor: `test_itemfx.py` (the show doors),
`test_town_shop_economy.py`, `test_adventure_finds.py`, `test_feed.py`,
`test_canon_injury.py`, `test_shop*.py`.  Full suite ~1635 at time of
writing; lint baseline 263.

---

## 5. SPRITE SURVEY — 2026-07-23 (Joel: "see if there're unused item
## sprites from dvpet and dsprite")

### DSprite contributes ZERO sprites — by standing rule

`ANIM_REFERENCE.md`: "DSprite = DESIGN reference only (**its art is
banned**)".  `TUIPET_ITEMS.md`: "DSprite is the mechanics grammar, DVPet
is the art."  shopscreen's `_icon` docstring says the same from the code
side: "DSprite consumables have no rips → the cell stays quiet."  There
is no DSprite item art in the repo to go looking for.  **All item art is
and stays DVPet.**

### The DVPet extraction is COMPLETE — nothing is left in the sheets

Verified by geometry, not by assumption:

| sheet | cells | claimed by a csv row | unclaimed |
|-------|-------|---------------------|-----------|
| `spritesFood0.png` (24px, 6px gutter, 4/col) | 57 cols | 57 | **0** |
| `spritesItems0.png` (16px, 1px gutter, 9/col) | 84 cols | 84 | **0** |

`foods.csv` = 59 rows, `items.csv` = 84 rows; `icons.json.gz` packages
**143 = 59 + 84**.  Every food and item DVPet ships already has its
frame-0 rip in the package.  (Two food columns are shared: Supplement/AI
Supplement and Food Pill/AI Food Pill sit on the same art.)

### But 87 of the 143 packaged sprites are DARK

Reachability computed over ALL paths, per the E4 METHOD RULE — not a
literal grep.  Counted as reachable: `shop.CATALOG` icons (37), raw-key
literals in src (8: `f:0 f:43 f:44 f:58 i:14 i:66 i:81 i:82`), and the
Digimental crests, which reach the screen through a VARIABLE
(`shopscreen._icon` builds `"i:%d" % iid` from `Pet._CREST_IDS`, 11 ids
i:15-25).  Also confirmed dark-by-data: `evolutions.csv` as shipped has
**no item columns at all**, so no `ev_item` / `give_item` path revives
anything.  Town shelves resolve only through `key_for_icon` → CATALOG.

**Reachable 56 · ORPHANED 87.**  Full list:
`/tmp/.../scratchpad/orphans.txt`, regenerable from §4's command.

| group | n | examples |
|-------|---|----------|
| Real FOODS with no tuipet presence | 22 | Fruit, Banana, Bread, Rice, Milk, Egg, Cheese, Salmon, Broccoli, Beans, Nuts, Oats, Honey, Ice Cream, Chicken Soup, Orange, Guava, 3 Peppers, Bitter Herbs, Burnt Food |
| MED / attribute-chip family | 16 | Med, Elixir, **Vitamin G ("Recovers Injury")**, Miracle Drink, Gold Pill, Supplement, Food Pill, HP Chip (+G), Vaccine/Data/Virus Chip (+G), Omni Chip G |
| Spirit evolution items | 20 | i:43-62, the 10 Human + 10 Beast spirits |
| Other ItemEvol relics | 9 | Digitron, Horn Helmet, Grey Claws, Water Bottle, Torn Tatter, White/Black Wings, Metal Armor, Flaming Wings |
| Capsules (gacha, "A random surprise") | 10 | i:68-77, two of them `AngrySurprise` |
| Toys / Study / Interact | 8 | Hedonism 101, Book, Stuffed Animal, Board Game, Computer Game, Toy Car, Balloon, Trampoline |
| Transports | 2 | Zone Transport (i:28), Continent Transport (i:31) |

Notes that matter for the refactor, NOT proposals:
- **`f:16 Vitamin G` is literally "Recovers Injury"** — DVPet's own art
  for the ailment restored today.  The Bandage (i:80) took that slot.
- The chip family is welded to attributes/stress/mood, and **mood and
  stress are app-invented systems that stay stripped** (CANON
  RESTORATION ruling).  Most of those 16 have no live stat to move.
- The 29 ItemEvol relics are dormant because the DATA is dormant, which
  is a standing rule ("dormant data stays dormant"), not an oversight.
- **17 of the 22 authored `shopConsumable.csv` town overrides are
  DROPPED** at load because the catalog has no entry for them (`i:28`,
  `i:31`, and 15 chips/foods) — only 5 survive.  That is the mechanical
  root of diversity-audit F4 ("the towns' authored shelves are 2
  variants one SKU apart").

### One more un-extracted thing: FRAMES, not items

`tools/extract_icons.py` pulls **4 frames per item column; all 84
columns have all 9 painted** (755 painted frames in the sheet).  DVPet
addresses them as `spriteNum + k` down the column (`SpriteObj` line 191:
`col = spriteNum / sheetRows`), and offsets up to +10 appear in the View
code — so rows 4-8 are plausibly real animation steps for some
`AnimationType`s.  **Which types actually step past frame 3 has NOT been
established** and must be read out of the item flow, not guessed.

**Nothing above is a decision.**  Joel names what gets built.
