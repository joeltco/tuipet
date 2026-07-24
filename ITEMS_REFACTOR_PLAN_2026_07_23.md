# ITEMS REFACTOR — THE PLAN (draft 1, audited)

Joel 2026-07-23: "take all items, make sure theyre in catagories, and we
gotta redo them all to fit everything we got going on. eggs are fine.
once thats refactored, we gotta spread them all out. tiered rarities.
zone shop exclusives, etc."

**Scope of THIS board: the refactor only.**  Distribution (tiers, zone
exclusives, spread) is the NEXT arc — §7 holds only the hooks the
refactor must leave behind for it, not the distribution design.

**Eggs are out of scope by Joel's word.**  Confirmed safe to leave alone:
the `Armor-Spirit` category is NOT a dead entry — it is applied to
dynamically-built egg rows (`shop.py:292`), never to a CATALOG item, so
its absence from CATALOG is correct.  Do not "clean it up."

Nothing below is agreed.  §6 is the ruling list; everything in §3-§5 is
a proposal waiting on it.

---

## 1. VERIFIED GROUND TRUTH (re-derived today, not recalled)

37 items · 6-tuple `(name, icon, price, category, effect_text, flavor)` ·
categories: Food 11 · Care 9 · Toy 7 · Evolution 5 · Adventure 3 ·
Medical 2.

### 1a. THREE disagreeing groupings exist right now

This is the core of "make sure they're in categories" — the app already
has three category systems that do not line up:

| # | where | groups |
|---|-------|--------|
| 1 | `shop.CATALOG[k][3]` | **6**: Food, Care, Toy, Evolution, Adventure, Medical |
| 2 | `petcare.use_item` section comments | **5**: FOOD, CARE, **GROWTH**, TOYS, ADVENTURE |
| 3 | `shopscreen.GROUPS` (the tab bar) | **4**: Food, Items, Eggs, Honors |

Grouping 2's "GROWTH" holds both Evolution and Medical.  Grouping 3
folds **Care + Evolution + Medical + Toy + Adventure into one "Items"
tab**.

### 1b. Therefore: categories are currently INVISIBLE to the player

`v[3]` never reaches the screen as a heading.  It is read for shelf
gating (`_base_rows`), the `is_food` flag, and the Eggs tab — never as a
label the player sees.  **Categorising items changes nothing on its own
unless R1 (§6) says the player should see them.**

### 1c. Two genuinely dead references (safe to delete, low value)

- Category `"Fruit"` appears in `shopscreen.GROUPS` and in
  `shop.py:486`'s `is_food` test.  **No CATALOG item has it.**  (It is
  NOT the same namespace as `data_shop.FOOD_CATEGORIES`, which is
  DVPet's food *Type* column and IS live for `food_ranks`.)

### 1d. The LIVE-STAT LEDGER — what an item is allowed to move

Measured by counting real read/write sites outside `pet.py` and the
persistence layer.  "Redo them all to fit everything we got going on"
has to mean fitting THIS column, so it is the plan's yardstick.

**LIVE (an item may move these):** hunger · strength · energy · weight ·
calories · poop/poop_sizes · asleep · lights · sick · injured +
`inj_length` + `vitamin_lapse` · obedience + `discipline_call` +
praise/scold windows · care_mistakes · overeat · bits · dna_owned /
dna_applied · stage_trainings · saved_hit_type · wins/battles ·
dp (jogress) · x_antibody · auto_care · adventure energy + lives.

**DERIVED — no meter, cannot be "set":** mood (`_set_mood` is a verified
NO-OP; `current_mood()` reads live state) · condition() · enthusiasm
(`_set_enthusiasm` also a NO-OP).

**DORMANT — zero read/write sites; standing rule says LEAVE THEM:**
depressed · nutr_protein/mineral/vitamin · fatigue_length ·
bandage_lapse · compliance · food_eaten · mood_rank · praise_flag /
scold_flag (the live discipline path uses the *windows*, not the flags).

**READ-ONLY today** (displayed, never written by an item): injuries ·
exp · total_trainings · disturb · attr_ranks · food_ranks · trophies ·
mega_kills · disposition · glutton · restless.

### 1e. The asymmetry nobody has ruled on

**The sickness cure is not an item.**  `feed_pill()` lives on the free
`F` menu — infinite, free, always available.  The injury cure (Bandage)
is a 300b catalog item.  Two ailments, two completely different
economies.  This is a FACT, not a complaint — R3 decides it.

### 1f. Nothing in the catalog touches obedience

The discipline system came back today.  **Zero of 37 items move
`obedience`.**  Related: DVPet's own `items.csv` row 0 (Textbook) is
`+Obedience -Mood +Stress`; tuipet repurposed it as "erase ALL care
mistakes."  R4 decides whether that stands.

### 1g. Effect text drifts by construction

`CATALOG[k][4]` is hand-written prose that must mirror `use_item`.
Nothing enforces it.  12 of 37 items are simple stat-movers (7 `_snack`
+ 5 `_toy` lambdas); the other 25 are bespoke handlers, 3 of which are
pure road-refusals.

---

## 2. WHAT THE REFACTOR IS FOR

Three goals, in priority order.  If a proposed change serves none of
them it does not belong in this arc:

1. **One grouping, not three** (§1a) — so "which category is this in"
   has exactly one answer.
2. **Every item earns its slot against the LIVE ledger** (§1d) — no item
   whose whole point is a dead stat, no live system with zero item
   support.
3. **Leave a distribution hook** (§7) — tiers and zone exclusives must
   be attachable without a second refactor.

---

## 3. PROPOSAL A — the record (mechanical, low risk)

Replace the positional 6-tuple with a `NamedTuple` (drop-in: it still
indexes `v[3]`, so nothing breaks in one commit) carrying the existing
six fields plus:

- `tier` — rarity slot, **declared now, populated in the distribution
  arc**.  Default `None` = unranked.
- `where` — where it can be used: home / road / town.  Today this is
  encoded as refusal STRINGS inside three handlers (P-F on the scoping
  board); as data it becomes checkable.
- `touches` — the tuple of LIVE stats the item moves.

`touches` is the load-bearing one: it makes goal 2 testable (a pin can
assert no item touches a dormant stat), and it lets category membership
be **validated** rather than just asserted.

**Risk:** `touches` is a second hand-maintained mirror of `use_item` —
the same disease as `effect_text` (§1g) unless it is either generated or
pinned.  See R6.

## 4. PROPOSAL B — the category set

Only meaningful if R1 says categories become visible.  Candidate set,
cut so each category maps to a LIVE system rather than to vibes:

| category | what it moves | today's members |
|----------|---------------|-----------------|
| **Food** | hunger, calories, weight | the 11 |
| **Medicine** | sick, injured | bandage, vitamin (+ whatever R3 rules) |
| **Care** | sleep, lights, filth, care_mistakes | sleep pill, caffeine, music player, port potty, textbook |
| **Training** | strength, weight, drills | dumbbell, slim drink, energy drink |
| **Play** | energy, weight, (obedience? R4) | the 7 toys |
| **Evolution** | evolution gates, DNA, growth | anti-evo chip, x-antibody, dna crystal, grow capsule |
| **Legacy** | death, inheritance | rev. floppy, digimemory |
| **Adventure** | road only | the 3 |
| **Armor-Spirit** | eggs — UNTOUCHED | (dynamic rows) |

That is **8 item categories + eggs**, up from 6.  It fixes the two
category names that currently lie: "Medical" holds death/inheritance
rather than medicine, and "Evolution" holds the dumbbell.

**This is the proposal I am least confident in** — see the audit,
finding A2.

## 5. PROPOSAL C — the effect model

Make the 12 simple stat-movers **declarative** (`(stat, delta)` pairs)
and generate their `effect_text` from the spec.  Leave the 25 bespoke
handlers as code with a hand-written string, but pin every one of them.

Rejected outright: an all-declarative model.  port_potty's 24h
auto-clean, anti_evo's toggle, x_antibody, digimemory's inheritance and
the transports are real logic; pretending they are data would be a lie
that costs more than the drift it prevents.

---

## 6. RULINGS NEEDED (Joel's call — I will not pick these)

- **R1 — Do categories become VISIBLE?**  Today they are not (§1b).
  Options: (a) leave invisible, categories stay bookkeeping; (b) group
  the Items tab under sub-headers; (c) more tabs.  ⚠ **(c) is ruled out
  by arithmetic** — the tab bar is 38 cells and silently truncates;
  today's 4 tabs use 27, and 8 would need 68 (audit A2).  (b) is the
  only option that scales past ~5 categories.
- **R2 — the category set** (§4), and specifically whether "Medical" and
  "Evolution" get renamed/re-cut or just re-populated.
- **R3 — the ailment economy** (§1e): does the free infinite Pill stand
  beside the 300b Bandage, or do the two ailments get symmetric cures?
- **R4 — obedience items** (§1f): does anything sell obedience, and does
  the Textbook go back to canon `+Obedience` or keep the tuipet
  mistake-eraser?
- **R5 — the 87 dark sprites** (survey in `ITEMS_REFACTOR_2026_07_23.md`
  §5): which families, if any, are in bounds to build?  My read of what
  is *available* — 22 real foods and 8 toys are usable as-is; the 16
  chips are welded to dead stats; the 29 ItemEvol relics are dormant
  DATA (standing rule: leave dormant); the 10 capsules would require
  inventing a gacha system (standing rule: never invent systems).
  **Availability is not a recommendation** — R5 is Joel's.
- **R6 — drift control**: generated text, or pinned text, or accept it?
- **R7 — grant-only items**: cupcake / cookie / candy / digimemory have
  `price = None` (unbuyable, grant-only).  Does that survive the
  distribution arc, or do they get prices and shelves?

---

## 7. HOOKS THE REFACTOR MUST LEAVE FOR DISTRIBUTION

Not the distribution design — just what must exist so it needs no second
refactor:

- `tier` field present and defaulted (§3).
- Town shelf assembly already resolves through `key_for_icon` → CATALOG,
  so a tier field is immediately readable by `_base_rows` / `_guest_deal`.
- **The 17 dropped town overrides.**  `shopConsumable.csv` authors 22
  town-shop overrides; **17 are silently dropped** because the catalog
  has no entry for that icon.  Any item added in this refactor may
  un-drop one.  That is the mechanical root of diversity-audit F4 and
  the single biggest lever the distribution arc has.
- Adventure loot (`BIOME_FINDS`) is keyed to zone SLOT NUMBER, not zone
  identity (diversity-audit F1) — zone exclusives will need that keying
  changed, which is a distribution-arc job, not this one.

---

## 8. PHASES (each ships on the house flow: pin → pytest → lint-gate →
## WHATS_NEW → commit → deploy)

- **P1** Record swap (§3), `touches` unpopulated. Pure mechanics, no
  behaviour change. Pins: catalog shape, every existing item test green.
- **P2** Populate `touches` + a pin that no item touches a DORMANT stat
  (§1d). This is where §2 goal 2 gets teeth.
- **P3** Category re-cut per R2 — data only, no UI.
- **P4** R1's UI work, if any.
- **P5** The effect pass: R3, R4, and any per-item rebalance against the
  live ledger.
- **P6** R5 additions, if any.
- **P7** Kill the dead `"Fruit"` branches (§1c) — trailing cleanup,
  deliberately last so it never masks a real failure.

**Test surface that must stay green throughout:** `test_itemfx.py`,
`test_town_shop_economy.py`, `test_adventure_finds.py`, `test_feed.py`,
`test_canon_injury.py`, `test_shop*.py`. Suite ~1635; lint baseline 263.

---

## 9. SELF-AUDIT OF THIS PLAN

Run against the draft above; findings folded back in where marked.

- **A1 — I nearly filed `Armor-Spirit` as a dead category.**  It is
  live; it is applied to dynamic egg rows, not CATALOG entries.  Caught
  by grepping its use sites instead of trusting the CATALOG diff.  Fixed
  in the header.  *(Same class as the E4 miss: absence from one table is
  not absence from the app.)*
- **A2 — Proposal B grows categories 6 → 8 while the UI shows 4, and the
  tab bar SILENTLY TRUNCATES.**  Measured, not estimated:
  `shopscreen._bar_text` builds `[Active] Other  Other ` and returns
  **`bar[:menu.W]`** with `menu.W = 38`.  Today's 4 tabs cost 27 of 38
  cells.  Proposal B's 8 labels cost **68** — the bar would be cut at 38
  and tabs 5-8 would vanish **with no error and no test failure**.  The
  bar holds roughly **five short labels**, so 8 visible categories is
  not achievable as tabs at any label length worth reading.  B is
  therefore **contingent on R1**, not independent of it — and R1's
  option (c) "more tabs" is effectively ruled out by arithmetic.  If R1
  says "stay invisible", a finer cut is pure bookkeeping and P3/P4
  should probably not run at all.
- **A3 — `touches` is a new drift surface.**  §3 proposes it to fight
  hand-maintained mirrors and then adds one.  Honest position recorded
  in §3; R6 must cover `touches`, not just `effect_text`.
- **A4 — P1's "drop-in, nothing breaks" is true for the swap and FALSE
  for the new fields.**  Grepped rather than assumed: there is exactly
  one unpacking site, `shop.py:283` —
  `for k, (name, _icon, price, cat, _eff, _fl) in CATALOG.items():`.
  A 6-field NamedTuple unpacks there fine, so the swap alone is safe.
  But **adding `tier`/`where`/`touches` takes it to 9 fields and breaks
  that line outright** (ValueError at import).  So §3 is really two
  steps: swap to a NamedTuple (safe), then widen it (touches that site).
  P1 must fix `shop.py:283` before P2 populates anything.
- **A5 — The phase order buries the highest-value item.**  §1g (drift)
  and §1f (no obedience items) are the two findings with real gameplay
  consequences, and they sit in P5, behind three phases of bookkeeping.
  If R1 comes back "invisible", P3/P4 vanish and P5 should be promoted
  to first.  Flagged rather than reordered, because the order depends on
  R1.
- **A6 — "redo them all" is not scoped by anything I can verify.**  The
  plan assumes it means "re-fit every item's effect to the live ledger"
  (§2 goal 2).  It could equally mean re-price, re-name, or rebalance.
  **This is the largest ambiguity in the plan** and is why §6 asks for
  rulings before P5 rather than after.
- **A7 — No pin currently proves the three groupings agree.**  Even
  after P3, nothing stops grouping 2's comments or grouping 3's tabs
  drifting from CATALOG again.  P3 should ship with a pin that the tab
  map's category names all exist in CATALOG — that pin would have caught
  `"Fruit"` years ago.
