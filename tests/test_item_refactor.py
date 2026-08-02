"""THE ITEM REFACTOR (Joel, 2026-08-02: "we need a full blown item refactor,
dude.... you made shitty items" -> "MAKING ALL ITEMS BALANCED").

His constraints, stated on the same thread: ⛔no repricing, ⛔no deleting,
✅change what items DO.  So every fix here is a CAPABILITY the cheap items and
the free buttons cannot copy -- because the disease was that the 44->132
expansion (v0.5.283-284) read effects off the authored CSV columns and prices
off the authored price columns and never checked the two against each other.

Measured before the refactor, on the real handlers:
  * Gold Pill      10000b legendary -> energy +12, vs Energy Drink 200b common
                   -> a FULL tank.  50x the price, a third of the effect.
  * Elixir          2000b -> cures sickness + full tank = the FREE F pill plus
                   the 200b drink.
  * Vitamin G       2000b -> heals injury + effort + guard = the FREE H heal
                   plus the 500b Vitamin.
  * Miracle Drink   7777b -> -1 slip + energy = the 2000b Compress plus the
                   200b drink.
  * Book            1000b -> obedience +5, vs Textbook 1500b -> +20.
  * Xylophone 800b / Video Game 600b / Television 1000b -> energy +2/+2/+3,
                   against the 200b full tank.

⭐THE RULE THIS FILE FENCES: an item earns its slot by doing something the free
buttons and the CHEAPER items cannot.  Four of the six answers reuse ONE shape
the game already proved with the Vitamin -- a game-min lapse counter that ticks
down in _tick_body and reads `> 0` at a single point of effect.
"""
import random

from tuipet.petbase import BATTLE_ENERGY_COST, DP_MAX, TRAIN_ENERGY_COST
from tuipet.pet import Pet

GUARDS = ("tonic_lapse", "ward_lapse", "pardon_lapse", "manners_lapse")


def _pet(cm=0, **kw):
    p = Pet(num=399, name="O", stage="Mega", attribute="Vaccine", obedience=60)
    p.world_seconds = 3600.0
    p.max_energy = 38
    p._set_energy(20)
    p.hunger = p.strength = 2
    for _ in range(cm):
        p._inc_mistake("left hungry too long")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _use(p, key):
    p.add_item(key)
    return p.use_item(key)


# ---- the shared shape -------------------------------------------------------

def test_every_guard_burns_on_the_body_clock():
    """All four new guards tick down beside vitamin_lapse -- one mechanic, not
    four.  A guard that never expires is a permanent buff, which is not what
    any of these items are."""
    p = _pet()
    for g in GUARDS:
        setattr(p, g, 10.0)
    for _ in range(10):
        p.tick(1.0)
    for g in GUARDS:
        assert getattr(p, g) == 0.0, g


# ---- 1. the Elixir: Joel's own call ----------------------------------------

def test_the_care_mistake_ladder_matches_the_rarity_ladder():
    """⭐THE SECOND PASS (Joel: "isnt a full care mistake wipe kind of over
    powered? this is the kind of shit im talking about dude").

    He was right, and it was worse than overpowered.  The wipe first landed on
    the ELIXIR at 2000b -- THE SAME PRICE as the Cold Compress, which scrubs
    ONE slip -- so it deleted a sibling item's whole reason to exist, and it
    undid the death clock for less than raising the dead (2500b).

    The effect was not wrong, it was on the wrong item.  The biggest effect
    belongs to the SCARCEST item, which is exactly what decoupling rarity from
    price (v0.5.337) made expressible.  The ladder now runs with the supply
    ladder, not against it."""
    from tuipet import shop
    rungs = [("cold_compress", "common"), ("elixir", "uncommon"),
             ("miracle_drink", "legendary")]
    for key, tier in rungs:
        assert shop.CATALOG[key].tier == tier, key
    # cheap + common: ONE slip
    p = _pet(cm=4)
    _use(p, "cold_compress")
    assert p.care_mistakes == 3
    # mid + uncommon: PREVENTS, does not cure
    q = _pet(cm=4)
    _use(q, "elixir")
    assert q.care_mistakes == 4 and q.pardon_lapse > 0
    q._inc_mistake("the lights left on")
    assert q.care_mistakes == 4
    # scarce + dear: the whole slate, BOTH counters
    r = _pet(cm=4)
    assert r.mistake_day == 4
    msg = _use(r, "miracle_drink")
    assert "4 slips" in str(msg)
    assert r.care_mistakes == 0 and r.mistake_day == 0
    # ...and the wipe is dearer than raising the dead, as an undo of the death
    # clock should be
    assert shop.CATALOG["miracle_drink"].price > shop.CATALOG["revive_floppy"].price
    # the elixir still sells NEITHER of the things Joel first called redundant
    z = _pet(sick=True)
    z._set_energy(3)
    _use(z, "elixir")
    assert z.sick is True and z.energy == 3


# ---- 2. the Miracle Drink: prevention, not another cure ---------------------

def test_the_ward_stops_every_slip_landing():
    """The ward sits on the ELIXIR (uncommon, five a shelf) since the second
    pass.  While it runs, NO care mistake can be booked at all -- the lights
    can burn all night."""
    p = _pet()
    _use(p, "elixir")
    assert p.pardon_lapse > 0
    for why in ("the lights left on", "left hungry too long",
                "empty effort gauge"):
        p._inc_mistake(why)
    assert p.care_mistakes == 0 and p.mistake_day == 0
    p.pardon_lapse = 0.0
    p._inc_mistake("left hungry too long")
    assert p.care_mistakes == 1                    # expired: slips land again
    assert "already warded" in str(_use(_pet(pardon_lapse=5.0), "elixir"))


# ---- 3. the Gold Pill: the tank stops mattering -----------------------------

def test_the_gold_pill_makes_a_days_spends_free():
    """There is no passive energy DRAIN in tuipet to guard, so the guard sits
    on the SPENDS: battles, drills and the road march cost nothing while it
    runs.  That is what 10000b buys over a 200b full tank -- a day where the
    tank does not matter (which also holds the pet above the injury line)."""
    p = _pet()
    _use(p, "gold_pill")
    assert p.energy == p.max_energy and p.tonic_lapse > 0
    p.record_battle(True)
    assert p.energy == p.max_energy, "a battle must cost nothing while gilded"
    p.train("Vaccine") if hasattr(p, "train") else None
    assert p.energy == p.max_energy
    # the road march too
    from tuipet import adventure
    a = adventure.Adventure(p, zone=adventure.ZONES[0])
    for _ in range(20):
        a._march_drain()
    assert p.energy == p.max_energy, "the march must cost nothing while gilded"
    # ...and it all comes back when the day ends
    p.tonic_lapse = 0.0
    e0 = p.energy
    p.record_battle(True)
    assert p.energy == e0 - BATTLE_ENERGY_COST
    assert TRAIN_ENERGY_COST > 0                   # (the drill's own toll, live)


# ---- 4. Vitamin G: prevent the wound, don't sell a free button --------------

def test_vitamin_g_makes_the_injury_roll_impossible():
    """`H` heals injury for FREE, so "heals injury" was never worth 2000b.
    It PREVENTS instead -- and prevention is the valuable half: the road audit
    measured 40% of adventure runs coming home wounded."""
    p = _pet()
    _use(p, "vitamin_g")
    assert p.ward_lapse > 0 and p.strength == 4
    random.seed(1)
    for _ in range(400):                           # the worst body there is
        p.injured = False
        p.hunger, p.strength = 0, 0
        p._set_energy(0)
        p.record_battle(False)
        assert not p.injured, "warded: the roll must not fire"
    p.ward_lapse = 0.0
    random.seed(1)
    hurt = 0
    for _ in range(400):
        p.injured = False
        p.record_battle(False)
        hurt += p.injured
    assert hurt > 20, f"unwarded, the same 400 bouts should wound: {hurt}"


# ---- 5. the Book: hold the gauge instead of competing on the number --------

def test_the_book_holds_manners_instead_of_nudging_them():
    """1000b for +5 against the Textbook's 1500b for +20 was a dead rung.  It
    stops competing on the number: for a day the obedience LAPSE cannot fire."""
    def drift(book):
        p = _pet()
        p.sleep_limit = 9e9        # the lapse only ticks AWAKE -- a sleeper
        #                            drifts nowhere and proves nothing
        if book:
            _use(p, "book")
        o0 = p.obedience
        for _ in range(1200):                      # inside the guard
            p.discipline_call = False              # isolate from the tantrum
            p.hunger = p.strength = 2
            p.tick(1.0)
        return o0, p.obedience

    a0, a1 = drift(True)
    b0, b1 = drift(False)
    assert a1 == a0, f"warded manners must not drift: {a0} -> {a1}"
    assert b1 < b0, f"unwarded manners must drift: {b0} -> {b1}"
    assert "still fresh" in str(_use(_pet(manners_lapse=5.0), "book"))


# ---- 6. the play shelf: DP, which only sleep otherwise fills ----------------

def test_the_toys_pay_dp():
    """600-1000b for energy +2/+2/+3 against a 200b full tank.  DP is the
    jogress meter and NOTHING but a night's sleep touches it, so the play shelf
    now builds fusion power -- the one payout no cheaper item can copy."""
    for key, want in (("xylophone", 1), ("video_game", 1), ("television", 2)):
        p = _pet()
        p.dp = 0
        e0 = p.energy
        _use(p, key)
        assert p.dp == want, key
        assert p.energy == e0, f"{key} must not pay energy any more"
    assert "already full" in str(_use(_pet(dp=DP_MAX), "television"))


# ---- the dossier law: every blurb still true -------------------------------

def test_the_blurbs_match_the_new_jobs():
    """Shop blurbs are a maintained truth surface (the dossier law).  Six
    items changed jobs; six blurbs had to change with them."""
    from tuipet import shop
    for key, must, mustnt in (
        ("elixir", ("NO care slips",), ("sickness", "energy to FULL")),
        ("miracle_drink", ("WHOLE slate",), ("ONE care slip",)),
        ("gold_pill", ("nothing tires",), ("+12",)),
        ("vitamin_g", ("CANNOT be wounded",), ("heals injury",)),
        ("book", ("HOLD",), ()),
        ("xylophone", ("DP",), ("energy",)),
        ("television", ("DP",), ("energy",)),
        ("video_game", ("DP",), ("energy",)),
    ):
        line = shop.effect_line(shop.entry(key) or {})
        for m in must:
            assert m in line, f"{key}: {m!r} missing from {line!r}"
        for m in mustnt:
            assert m not in line, f"{key}: stale {m!r} still in {line!r}"
