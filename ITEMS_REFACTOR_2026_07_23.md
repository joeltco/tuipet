# ITEMS REFACTOR — scoping board

Joel 2026-07-23: "we gotta refactor the items system after we are done."

**STATUS: NOT STARTED.**  Nothing here is agreed — this is the MAP, written
before a session compaction so the work can start cold.  What the refactor
should actually *change* is Joel's call; §3 lists candidates only.

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
