# TUIPET ITEMS — the catalog contract (BUILT 2026-07-18)

> STATUS: SHIPPED in v0.5.60; taglines (the CATALOG's 6th field, shown in
> the live dossier) followed in v0.5.61.  shop.CATALOG is the single
> source; this doc is the design record.
> Law of the redo: **DSprite is the mechanics grammar, DVPet is the art.**
> Every item below wears a REAL DVPet atlas strip (verified: all 59 foods and
> all 84 items carry 4-frame rips — zero quiet cells needed). No effect below
> invents a system: each acts on a meter or hook that is LIVE today.

## ⚠ UPDATE 2026-07-23 — read this before trusting anything below

The catalog is **37 entries** now (Food 11 · Care 9 · Toy 7 · Evolution 5
· Adventure 3 · Medical 2).  Three things in the original text went
stale the same day:

1. **"obedience ... injuries" are no longer dead systems.**  The canon
   restoration brought INJURY back (v0.5.205: battles wound, the
   BANDAGE cures, a Vitamin guards) and DISCIPLINE back (v0.5.206: the
   obedience gauge is live, 0..150).  Any DVPet effect column speaking
   to those two is now addressable rather than a corpse.
2. **THE BANDAGE joined the catalog** (`i:80`, Care, 300b) — the real
   DVPet item, dormant since the 2026-07-16 strip.
3. **The Vitamin gained its canon second job**: a live vitamin guards
   against battle injury for a game-day.

### Item SHOWS are no longer hand-mapped (v0.5.207-209)

`shop.TOY_SCRIPTS` — a 7-entry hand-map — is **RETIRED**.  Two doors
decide what an item plays, both derived from data:

* `shop.item_is_eaten(key)` → the `f:` sheet.  foods.csv carries no
  AnimationType **because eating IS the animation**, so every food-sheet
  item (the 11 foods + both drinks, both pills, the vitamin, the
  anti-evo chip) plays the eat fx with its own icon.
* `shop.item_script(key)` → items.csv's own `AnimationType` column,
  reached through the icon key (**`i:N` IS the row id**).  Excluded by
  key: digimemory, both transports, life_recovery, revive_floppy (own
  doors).  Writing a new `itemfx.SCRIPTS` entry **auto-wires** the item.

**Never reintroduce a hand-map.**

## The sources, in one breath

* **DSprite** ships 17 consumables + 11 Digimentals + dormant relics
  (miracle egg / miracle fruit / VIP ticket) + 28 theme skins. Text-only shop
  — no item art anywhere. Its EFFECT vocabulary: fill/curb hunger, energy,
  weight, force/limit sleep, wake, trainings, stage-time, evolution block,
  X-antibody, revive, auto-clean, mistake eraser, a kill-trap fruit,
  route-selector fruits.
* **DVPet** ships 59 foods + 84 items, every one with a real 4-frame strip —
  but its effect columns speak dead systems (mood, enthusiasm, nutrition
  macros, obedience, temperature, injuries, adventure life, transports).
  The art is gold; the numbers are corpses.

TUIPET items = DSprite's (proven) effect grammar + tuipet's own live systems,
each carried by the DVPet item that owns the art.

## FOOD tab (eaten on the LCD — every strip is a real 4-frame shrink)

| Item | Art | Price | Effect (live mechanics only) | Lineage |
|---|---|---|---|---|
| Fish | f:1 | 50b | hunger +1 | the cheap staple beyond free Meat |
| Vegetable | f:3 | 150b | hunger +1, weight −1 | the diet food |
| Tuna | f:14 | 400b | hunger +2, energy +1 | the hearty meal |
| Cake | f:6 | 300b | hunger +1, energy +2, weight +2 | the treat |
| Cheese burger | f:57 | 50b | hunger → FULL, weight +4, care blemish +1 | DSprite junk_food, art as shipped |
| Giga Meal | f:28 | 800b | hunger → FULL, energy +4, weight +6 | the feast |
| Steak | f:8 | 2000b | hunger → FULL + 12h satiety | DSprite premium_meat, art as shipped |
| Poison Mushroom | f:13 | 200b | **KILLS. "Looks delicious. DO NOT FEED."** | the canon trap (deadly_fruit successor) |

Birthday-only treats (never sold; fixes the broken birthday grants):
**Cupcake f:55 / Cookie f:54 / Candy f:7** — hunger +1, energy +1 each.

## ITEMS tab

| Item | Art | Price | Effect | Lineage |
|---|---|---|---|---|
| Energy Drink | f:17 | 200b | energy → max | as shipped |
| Slim Drink | f:23 | 100b | weight −10 (floor: species base) | replaces Spr.Carrot, exact-name DVPet art |
| Vitamin | f:5 | 500b | Effort → full (strength → 4) | new; the meter is live |
| Sleeping Pill | f:34 | 300b | force sleep + lights | as shipped |
| Caffeine Pill | f:38 | 300b | tonight's bedtime pushed later | live sleep_lapse nudge |
| Music Player | i:9 | 300b | clean wake, no grudge | alarm_clock re-skinned to real art |
| Textbook | i:0 | 1500b | erase **ALL** care mistakes | eraser at DSprite's canon strength, Study anim |
| Dumbbell | i:7 | 300b | stage trainings **+10** (cap 999) | Training Pack at canon value, art as shipped |
| Grow Capsule | i:78 | 500b | stage time +120 game-min | time_gear re-skinned to real art |
| Anti-Evo Chip | f:32 | 1000b | evolution block toggle | as shipped |
| X-Antibody | i:79 | 2000b | X-state → Permanent (once) | as shipped |
| Rev. Floppy | i:32 | 2500b | revive the dead | as shipped |
| Port. Potty | i:83 | 2000b | clean now + 24h auto-clean | Smart Potty wearing its TRUE art (icon only — the furniture system stays dead) |
| DNA Crystal | i:35 | 1500b | +10 banked DNA in the pet's own Field | tuipet-original on the live DNA bank |

## TOYS tab-mates (Joel: "so the toys are worthless?" — every toy turns a
live dial; exercise sheds weight, couch time buys energy at a weight price)

| Item | Art | Price | Effect | Show |
|---|---|---|---|---|
| Ball | i:3 | 100b | weight −1 | Bounce |
| Skateboard | i:6 | 500b | weight −2, energy −1 | Ride |
| Xylophone | i:63 | 800b | energy +2 | the recital |
| Video Game | i:65 | 600b | energy +2, weight +1 | Play |
| Television | i:10 | 1000b | energy +3, weight +1 | the couch |
| Bubble Bath | i:26 | 400b | washes the filth | Bathe |
| Cold Shower | i:67 | 300b | wake (rude) + energy +2 | Shower |

## EGGS tab — unchanged
The 11 Digimentals (i:15–25, real art, wave gates) stay exactly as shipped.

## What leaves the shelf
best/normal/worst fruit (the 1000b food duds — their canon route-selector job
is NOT revived: lines + DNA divergence own evolution steering), deadly_fruit
(succeeded by Poison Mushroom), super_carrot (→ Slim Drink), premium_meat
(→ Steak), junk_food (→ Cheese burger), care_mistake_eraser (→ Textbook),
alarm_clock (→ Music Player), time_gear (→ Grow Capsule). Old saves: a
save-heal maps owned old keys to their successors 1:1 (no one loses goods).

## Acquisition map (all existing faucets, re-pointed)
* Shop: everything above except birthday treats.
* Gift roll: Fish / Cake / Energy Drink / Ball (cheap, cheerful).
* Birthday: Cupcake / Cookie / Candy.
* Cup prizes: Energy Drink + Cake (item/food slots).
* Raid item pool: Energy Drink / Vitamin / Textbook / DNA Crystal (rank),
  Fish (consolation tier).

## Rulings as built (Joel delegated: "whatever you want")
Power chips OUT (powers grow only via battle — the standing ruling).  Toys
IN with live dials.  DNA Crystal IN.  Poison Mushroom IN.  Port. Potty
icon-only IN.  Textbook resets ALL.  Prices as tabled.  VIP Ticket /
Miracle relics stay dormant.  Old bags heal 1:1 via shop.LEGACY_KEYS.
