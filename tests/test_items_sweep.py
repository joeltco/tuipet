"""THE ITEM SWEEP — the end-to-end pins (2026-07-24).

Joel: "audit the item sweep. it should be finished. look at everything and
harden."  The refactor (P1-P6) and the distribution arc (D1-D7) both closed
on STATIC pins: the catalog's shape, its tiers, its declared `touches`.
Nothing walked an item from the shelf to the belly and asked whether the
three agreed.  These do, and they are the ratchets for the five things the
sweep found:

  1. a raid's prize line named its goods out of vitems.json -- a file that
     since 2026-07-18 holds the Digimentals and the RETIRED shelf, so the
     biggest moment in the game printed "Energy.D, vitamin, dna_crystal";
  2. the road shelf's map-clear gate held in the home shop and nowhere
     else -- the first town on the road sold both warps at zero progress;
  3. Life Recovery was the one buyable good no town in the world stocked;
  4. the Grow Capsule advanced the growth clock by 2.5 stages while its
     shelf text said "+120min" -- and vaulted the pet into the Pen20
     frailty window on the way;
  5. the home daily deal (half off, unlimited) sold under the price the
     towns pay on demand (70%), an uncapped bits printer.

The `touches` pin at the bottom is the general one: it stops being a
DECLARATION and becomes a measurement.
"""
import copy
import dataclasses

import pytest

from tuipet import shop, persistence
from tuipet.pet import Pet
from tuipet.petbase import _Refused


def _pet(**kw):
    kw.setdefault("stage", "Champion")
    p = Pet(num=100, attribute="Vaccine", **kw)
    p.bits = 1_000_000
    return p


# ---- 4. the Grow Capsule ---------------------------------------------------

def test_the_grow_capsule_buys_a_quarter_of_the_STAGE():
    """Priced on Joel's word (2026-07-24: "make the grow capsule worth
    500b").  A FRACTION, because the stages run 180..2880 game-minutes and
    any flat figure worth having at Ultimate skips a baby stage whole.

    ⚠ THE UNIT LAW still governs the constant it replaced: 7200 was
    "+120min" read as REAL minutes, 2.5x the longest stage in the game."""
    from tuipet.petbase import GROW_CAPSULE_FRACTION
    for stage in ("InTraining", "Rookie", "Champion", "Ultimate"):
        p = _pet(stage=stage)
        p.stage_seconds = 0.0
        p.add_item("grow_capsule")
        out = p.use_item("grow_capsule")
        dur = p.STAGE_DURATION[stage]
        assert p.stage_seconds == dur * GROW_CAPSULE_FRACTION, stage
        assert p.stage_seconds < dur, f"one capsule completes {stage}"
        assert f"+{int(dur * GROW_CAPSULE_FRACTION)}min" in out   # it SAYS how far


def test_capsules_hurry_the_wait_but_never_END_it():
    """The invariant that keeps the priced version from becoming the bug it
    replaced: the push stops one tick short of the gate, so no stack of
    capsules evolves a pet outright -- and at Ultimate, whose stage length
    IS LATE_STAGE_WINDOW, that same stop is what keeps capsules from arming
    the Pen20 frailty death (5 care mistakes = dead) by themselves."""
    for stage in ("Rookie", "Champion", "Ultimate"):
        p = _pet(stage=stage)
        p.stage_seconds = 0.0
        for _ in range(8):                    # far more than it takes
            p.add_item("grow_capsule")
            p.use_item("grow_capsule")
        assert p.stage_seconds < p.STAGE_DURATION[stage], stage
    assert p.stage_seconds < p.LATE_STAGE_WINDOW          # the Ultimate run
    # and a capsule against a full clock refuses instead of vanishing
    p.add_item("grow_capsule")
    held = p.inventory.get("grow_capsule")
    assert isinstance(p.use_item("grow_capsule"), _Refused)
    assert p.inventory.get("grow_capsule") == held        # kept, not burned


def test_a_final_form_refuses_the_capsule_instead_of_taking_the_bits():
    """A Mega has no growth clock to hurry, and stage_seconds only feeds
    FRAILTY there -- so selling it a capsule would sell a pure downside."""
    p = _pet(stage="Mega")
    p.stage_seconds = 0.0
    p.add_item("grow_capsule")
    out = p.use_item("grow_capsule")
    assert isinstance(out, _Refused) and "nothing left to hurry" in out
    assert p.stage_seconds == 0.0 and p.inventory.get("grow_capsule") == 1


# ---- 5. the home deal ------------------------------------------------------

def test_the_home_deal_is_rationed_by_tier():
    p = _pet()
    key = shop.home_deal_key()
    ration = shop.tier_stock(key)
    rows = {e["key"]: e for e in shop.home_stock(pet=p)}
    assert rows[key]["deal"] and rows[key]["left"] == ration
    for _ in range(ration):
        msg, sfx = shop.town_buy(p, {e["key"]: e
                                     for e in shop.home_stock(pet=p)}[key])
        assert sfx == "confirm", msg
    after = {e["key"]: e for e in shop.home_stock(pet=p)}[key]
    assert not after.get("deal") and after.get("deal_spent")
    assert after["price"] == shop.CATALOG[key].price   # full price, still open


def test_no_deal_price_undercuts_what_a_town_pays_on_demand():
    """THE ANTI-PRINTER LAW.  A town pays TOWN_DEMAND (70%) for a good it
    does not stock; the home deal sells at 50%.  That gap is real profit,
    so the number of copies it can be run through has to be bounded -- the
    town counters have been bounded since the shops arc, and the home deal
    landed later without one.  This pins the BOUND, not the gap: an
    unrationed row that undercuts demand is the printer."""
    for key, v in shop.CATALOG.items():
        if v.price is None or v.category == "Adventure":
            continue
        pay = max(1, v.price // shop.HOME_DEAL_FACTOR)
        best = max(shop.town_sell_price(key, t) for t in shop._town_maps())
        if best > pay:                       # a profitable flip exists...
            assert shop.tier_stock(key) <= shop.TOWN_DAILY_CAP   # ...but bounded
    # and the FULL-price shelf is never a profitable flip anywhere
    for key, v in shop.CATALOG.items():
        if v.price is None:
            continue
        best = max(shop.town_sell_price(key, t) for t in shop._town_maps())
        assert best <= v.price, key


def test_a_spent_deal_warns_before_it_charges_full_price(monkeypatch):
    """The one-press guard (the bag's `_retarget` grammar): the ration runs
    out mid-mash and the row keeps selling at full price -- so the next
    ENTER must SAY the price changed instead of quietly taking 4x."""
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    key = shop.home_deal_key()
    p.town_bought = {"day": shop._today_ordinal(),
                     f"{shop.HOME_SHOP_ID}:{key}": shop.tier_stock(key)}
    pan = ShopPanel(p)
    pan._deal_guard = key
    row = None
    for t in range(len(pan._tabs())):
        pan.tab = t
        rows = pan._rows()
        for i, r in enumerate(rows):
            if r.get("key") == key:
                row, pan.cursor = r, i
                break
        if row:
            break
    assert row is not None and not row.get("deal")
    card = "\n".join(pan._info(row, 26))        # the new card state RENDERS
    assert "deal gone today" in card
    pan.text()                                  # and the panel walks
    bits = p.bits
    pan.key("enter")
    assert p.bits == bits and "deal's gone" in pan.msg   # ate the press
    pan.key("enter")
    assert p.bits == bits - row["price"]                 # the second one buys


# ---- 6. no paid no-ops -----------------------------------------------------

def test_the_caffeine_pill_refuses_a_dose_that_would_do_nothing():
    """The no-duds rule, applied to the one care item that broke it: both
    branches could spend the pill and move NOTHING while claiming "Wide
    awake for a while yet."  """
    p = _pet()                                   # nowhere near bedtime
    p.sleep_lapse = 0.0
    p.add_item("caffeine_pill")
    out = p.use_item("caffeine_pill")
    if p._in_sleep_window() is None:             # pressure pet: no pressure yet
        assert isinstance(out, _Refused)
        assert p.inventory.get("caffeine_pill") == 1     # kept
    p2 = _pet()
    p2.sleep_lapse = 100.0
    p2.add_item("caffeine_pill", 2)
    first = p2.use_item("caffeine_pill")
    assert not isinstance(first, _Refused)
    # a SECOND pill on a line pet is already-held grace: refused, kept
    if p2._in_sleep_window() is not None:
        assert isinstance(p2.use_item("caffeine_pill"), _Refused)
        assert p2.inventory.get("caffeine_pill") == 1


# ---- 2 + 3. the road shelf -------------------------------------------------

def test_the_gate_that_holds_at_home_holds_on_the_road(monkeypatch):
    monkeypatch.setattr(persistence, "get_progress", lambda: {"maps": set()})
    home = {e["key"] for e in shop.catalog()}
    for tid in sorted(shop._town_maps()):
        town = {e["key"] for e in shop.town_stock(tid)}
        gated = {k for k in shop.ADVENTURE_GATES}
        assert not (town & gated - home), f"town {tid} sells around the gate"


# ---- 1. the prize line -----------------------------------------------------

def test_every_raid_prize_key_resolves_to_a_shelf_NAME():
    """The server's pool is CATALOG keys; the claim line must speak the
    catalog's names.  A key that resolves to nothing prints itself."""
    pool = ["energy_drink", "vitamin", "textbook", "dna_crystal", "fish"]
    for k in pool:
        e = shop.entry(k)
        assert e and e["name"] and e["name"] != k
        assert e["name"] == shop.CATALOG[k].name      # the shelf's own word


# ---- the general ratchet: touches is MEASURED, not declared ----------------

# Animation plumbing and the bag itself: never an "effect".
_BOOKKEEPING = frozenset({
    "anim", "anim_t", "anim_ttl", "anim_until", "idle_fx", "_fx_busy",
    "inventory", "gift",
    "pending_prize",   # reveal plumbing (2026-07-28): the cheer's hand-off,
    #                    not an effect -- the prize itself lands in inventory
})
# The shared helpers' OWN billing, which shop._TOUCHES deliberately does
# not list ("those belong to those helpers, not to the item"): _set_energy
# stings obedience when a drop lands in the red, _inc_mistake stamps the
# day, _die names the cause, clean() pays its own obedience reward.  These
# may appear WITHOUT being declared -- but nothing declared may go missing.
_SIDE_CHANNELS = frozenset({"mistake_day", "death_cause", "obedience"})
# Items whose declared stats are ALTERNATIVES, not a checklist: the
# Caffeine Pill pushes bedtime through the grace clock for a line pet and
# through sleep_lapse for a pressure pet, and no pet is both.  At least one
# must move.
_EITHER_OR = {"caffeine_pill",
              # the expansion combos (2026-07-26): each half refuses only
              # when BOTH halves are pointless, so on the permissive pet
              # one declared leg may legitimately sit still (the fixture
              # is neither sick nor hurt; effort starts at its floor)
              "elixir", "vitamin_g", "x_program", "burnt_food"}

# own-door expansion keys: the evolution keys refuse on a pet with no
# matching road (their landing is pinned in test_item_expansion.py), the
# med/bandage pair needs an ailment the permissive fixture doesn't carry,
# and the futon is the sleep family's fourth member
_EXPANSION_OWN_DOORS = frozenset(
    {"med", "futon"}
    | {k for k in shop.CATALOG
       if k.startswith(("human_", "beast_")) or k in
       ("digitron", "horn_helmet", "grey_claws", "water_bottle",
        "torn_tatter", "white_wings", "black_wings", "metal_armor",
        "flaming_wings")})


@pytest.mark.parametrize("key", sorted(shop.CATALOG))
def test_declared_touches_match_what_the_handler_actually_moves(key):
    """P2 declared `touches` by READING the handlers; nothing has ever
    checked the reading.  This uses the item on a permissive pet and diffs
    the dataclass: an entry that claims a stat it never moves (or moves one
    it never claimed) fails here, which is the drift the whole refactor was
    for."""
    v = shop.CATALOG[key]
    if v.where == "road" or key in _EXPANSION_OWN_DOORS \
            or key in ("poison_mushroom", "revive_floppy",
                       "digimemory", "sleeping_pill",
                       "music_player", "cold_shower"):
        # own doors and the sleep family need a pet in a state this fixture
        # cannot hold at the same time (asleep AND awake); they carry their
        # own dedicated pins (test_sleep_system, test_item_heal, C1's
        # inherit pins) and are exercised there.
        return
    fields = [f.name for f in dataclasses.fields(Pet)]
    p = _pet()
    p.hunger, p.energy = 1, 2
    p.weight = p._base_weight() + 10
    p.care_mistakes, p.poop, p.poop_sizes = 3, 2, [1, 1]
    # the birthday tally too: the whole-slate wipe clears BOTH counters, and a
    # declaration is only checkable against a field that has somewhere to move
    p.mistake_day = 3
    p.strength, p.obedience = 0, 50
    p.vaccine = p.data_power = p.virus = 50   # a bank the converters can trade
    p.sleep_lapse = 100.0        # some bedtime pressure for the Caffeine Pill
    if key == "cold_compress":
        p._set_energy(20)        # the compress CHARGES the tank (its whole
        #                          design: relief you sleep off) -- the
        #                          fixture's 2-energy floor would refuse it
    p.dna_owned = {}
    p.field = p.field if p.field not in ("", "None") else "Nature"
    # deep-copied: the DNA bank and the poop list are MUTATED in place, and
    # a shallow snapshot would show them as unchanged (a false pass)
    before = {f: copy.deepcopy(getattr(p, f, None)) for f in fields}
    p.add_item(key)
    out = p.use_item(key)
    assert not isinstance(out, _Refused), f"{key} refused: {out}"
    moved = {f for f in fields
             if f not in _BOOKKEEPING and before[f] != getattr(p, f, None)}
    declared = set(v.touches)
    extra = moved - declared - _SIDE_CHANNELS
    if key in _EITHER_OR:
        assert declared & moved, \
            f"{key} moved none of its declared {sorted(declared)}"
    else:
        assert not (declared - moved), \
            f"{key} declares {sorted(declared - moved)} but never moves it"
    assert not extra, f"{key} moves undeclared {sorted(extra)}"


# ---- the last gap: the shelf's NUMBERS, not just its stats ----------------
#
# `touches` proves WHICH meter an item moves.  The dossier prose promises HOW
# FAR ("hunger +1 · weight -1"), and that half was hand-maintained with only
# 10 of the 29 numeric claims spot-checked anywhere -- so `_snack(weight=-1)`
# edited to -2 left the Vegetable's card lying with the whole suite green.
# This reads the claim out of the shelf text and measures it.
#
# The METER MAP is the only hand-written part, and it is guarded: any digit
# in an effect string that no rule below claims FAILS the test rather than
# passing vacuously, so a new item cannot bring an unchecked number with it.
_METERS = {
    "hunger": "hunger",
    "energy": "energy",
    "weight": "weight",
    "training": "stage_trainings",
    "obedience": "obedience",
    "effort": "strength",           # the expansion's word for the 0-4 gauge
    "vaccine power": "vaccine",
    "data power": "data_power",
    "virus power": "virus",
    # the play shelf's payout since the item refactor 2026-08-02: DP is the
    # jogress meter, and nothing but a night's sleep otherwise fills it
    "DP": "dp",
}
_HOURS = {"satiety": "full_until", "auto-clean": "auto_clean_until"}


def _claims(effect):
    """(field -> delta, leftovers) read out of a shelf blurb."""
    import re
    want, rest = {}, effect
    for phrase, field in _METERS.items():                    # "weight -1"
        for m in re.finditer(rf"{phrase}\s*([+-]\d+)", rest, re.I):
            want[field] = want.get(field, 0) + int(m.group(1))
        rest = re.sub(rf"{phrase}\s*[+-]\d+", "", rest, flags=re.I)
    for m in re.finditer(r"all three powers\s*([+-]\d+)", rest, re.I):
        for f in ("vaccine", "data_power", "virus"):         # the Omni chip
            want[f] = want.get(f, 0) + int(m.group(1))
    rest = re.sub(r"all three powers\s*[+-]\d+", "", rest, flags=re.I)
    for word, field in _HOURS.items():                       # "12h satiety"
        for m in re.finditer(rf"(\d+)h[^·]*{word}|{word}[^·]*?(\d+)h",
                             rest, re.I):
            want[field] = int(m.group(1) or m.group(2)) * 3600
        rest = re.sub(rf"(\d+)h[^·]*{word}|{word}[^·]*?(\d+)h", "", rest,
                      flags=re.I)
    m = re.search(r"([+-]\d+)\s*own-Field DNA", rest, re.I)  # the DNA Crystal
    if m:
        want["dna_owned"] = int(m.group(1))
        rest = re.sub(r"[+-]\d+\s*own-Field DNA", "", rest, flags=re.I)
    return want, rest


_NUMERIC = sorted(k for k, v in shop.CATALOG.items()
                  if any(c.isdigit() for c in v.effect))


@pytest.mark.parametrize("key", _NUMERIC)
def test_the_shelf_text_promises_the_number_the_handler_delivers(key):
    v = shop.CATALOG[key]
    want, leftovers = _claims(v.effect)
    assert not any(c.isdigit() for c in leftovers), (
        f"{key}: the blurb claims {leftovers.strip()!r} and no rule in "
        f"_METERS/_HOURS measures it -- teach this test the claim, don't "
        f"let an unchecked number onto the shelf")
    assert want, key

    p = _pet()
    p.hunger, p.energy = 1, 0
    # AT the species base: _set_weight clamps to base +- round(base * 0.75),
    # so an inflated start silently eats a gain against the ceiling (that
    # cost this test five false failures before the fixture was right)
    p.weight = p._base_weight()
    p.care_mistakes, p.poop, p.poop_sizes = 3, 2, [1, 1]
    # the birthday tally too: the whole-slate wipe clears BOTH counters, and a
    # declaration is only checkable against a field that has somewhere to move
    p.mistake_day = 3
    p.obedience, p.strength = 50, 0
    p.vaccine = p.data_power = p.virus = 50   # a bank the converters can trade
    p.dna_owned = {}
    before = {f: (dict(getattr(p, f)) if f == "dna_owned" else getattr(p, f))
              for f in want}
    p.add_item(key)
    out = p.use_item(key)
    assert not isinstance(out, _Refused), f"{key} refused: {out}"
    for field, delta in want.items():
        if field == "dna_owned":
            got = p.dna_owned.get(p.field, 0) - before[field].get(p.field, 0)
        elif field in _HOURS.values():
            got = getattr(p, field) - p.world_seconds     # a wall-clock stamp
        else:
            got = getattr(p, field) - before[field]
        assert got == delta, (
            f"{key}: the shelf says {field} {delta:+}, the handler moved it "
            f"{got:+} — the card and the belly disagree")


def test_every_item_is_consumed_exactly_once_on_a_landing_use():
    """The other half of the refusal law: a use that LANDS spends one, a
    use that refuses spends none (consume-on-refusal burned Rev.Floppies
    once and must never return)."""
    for key in shop.CATALOG:
        p = _pet()
        p.add_item(key, 2)
        out = p.use_item(key)
        left = p.inventory.get(key, 0)
        assert left == (2 if isinstance(out, _Refused) else 1), f"{key}: {out}"
