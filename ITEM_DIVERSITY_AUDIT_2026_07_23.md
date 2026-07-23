# ITEM DIVERSITY AUDIT — 2026-07-23

Joel: "do a full blown item diversety audit. same with shops."
Scope: every acquisition path for every catalog item — home shop, 26
town shops (authored + guest good), town egg bands, adventure finds,
gifts, care treats, cup/raid prizes, inheritance.  Data pulled live
from shop.CATALOG, shop._town_rows, adventure.ZONES, the server's
RAID_ITEM_POOL, and load_requirements.

## The acquisition matrix (36 items + digimemory)

Every item is reachable — ZERO orphans.  Verified:
- give_item (evolution grant) is DORMANT in shipped data (no
  requirement sets it) — no raw `i:N` key can enter the bag.
- digimemory = inheritance-only BY DESIGN; cupcake/cookie =
  care-treat grants BY DESIGN (the 2026-07-18 catalog tier).
- Multi-path staples healthy: energy_drink and cake reach the bag
  5 ways; ball 5 ways.

## HEALTHY axes (leave alone)

- **Town egg market**: 26 distinct 6-egg bands, no two towns
  identical, 41 distinct eggs, each in 3-4 towns.  This is the
  diversity model the item shelves should match.
- **Raid prize pool**: 9 items, "no traps, no duds" rule holds.
- **Home shop**: 31 of 33 priced items always on the shelf; the 3
  Adventure items gate on map progress (deliberate).

## FINDINGS — where diversity is thin

- [x] F1 **Adventure find pools are 5 copy-paste templates keyed to
      the zone's SLOT NUMBER, not its identity.**  1-1 == 2-1 == 5-1
      exactly; Andromon's Desert, Kimeramon's Seafloor and Etemon's
      Mountains all dig the same Television + Music Player.  Only 15
      distinct loot items across 26 zones (plus the 3 road items
      everywhere); no item is unique to any zone.  Root: the authored
      DVPet tables were per-slot, and the catalog mapping drops 2/3
      of the authored entries (552 → 182 — correct filter, thin
      leftovers).
- [x] F2 **The four endgame zones dig ONE item** (Anti-Evo Chip).
      The hardest roads have the least interesting loot.
- [x] F3 **18 of 33 non-road items never appear as finds** — including
      every FOOD except tuna/candy.  The road never feeds you: no
      fish by the seafloor, nothing edible in the flower field.
- [x] F4 **The 26 towns' AUTHORED shelves are 2 variants one SKU
      apart** (transports + potty + anti_evo_chip | steak).  The
      guest good (gameplay polish #24) is the only per-town item
      character.
- [x] F5 **Guest-good collisions**: 8 items serve 2-3 towns each;
      towns 11 and 12 have the SAME authored shelf AND the same guest
      good (Xylophone) — two byte-identical shops.  caffeine_pill
      serves 3 towns.  (crc32 over a ~30 pool for 26 towns —
      birthday collisions.)
- [x] F6 **Town 18's one signature good is the Poison Mushroom** — a
      trap as the town's permanent character item.  (The home shop
      sells it too, so it may be deliberate comedy — Joel's call.)
- [x] F7 **Single-path items**: grow_capsule, vegetable, video_game
      exist ONLY on the home shelf — never a find, prize, gift or
      town good anywhere.

## PROPOSALS — ALL SHIPPED v0.5.192 (Joel: "do it all", 2026-07-23)

P1-P5 executed: BIOME_FINDS + FINAL_ZONE_FINDS in adventure.py (per-slot authored tables retired, dormant rand_items/rand_foods stay in data); shop._guest_deal (global no-replacement, trap excluded, all 26 unique); shop._MAP_SPECIALTY (cake/xylophone/x_antibody/revive_floppy/vitamin).  F6 resolved via the guest pool trap-exclusion; the home shop still sells the mushroom.

- P1 (fixes F1+F3): re-deal the find pools by BIOME from the EXISTING
  catalog — no new items, no new systems.  Seafloor digs fish/tuna/
  slim_drink; city digs video_game/television/energy_drink; desert
  digs energy/care goods; forest digs foods/toys; etc.  Road items
  stay everywhere.
- P2 (fixes F2): give the finals a rare-tier pool (anti_evo_chip +
  x_antibody + textbook + dna_crystal class) so the endgame dig pays.
- P3 (fixes F5, maybe F6): deal guest goods WITHOUT replacement per
  map (seeded, stable) so no two towns in a map share a guest and
  neighbors can't be identical; optionally exclude the poison trap.
- P4 (fixes F4): give each MAP one distinct authored SKU beyond the
  base (a regional specialty), so the 5 maps read differently even
  before the guest good.
- P5 (fixes F7): fold vegetable/video_game/grow_capsule into P1's
  biome pools and/or the guest pool weighting.
