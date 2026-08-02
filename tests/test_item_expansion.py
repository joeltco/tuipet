"""THE GREAT ITEM EXPANSION (2026-07-26, Joel: "bring in all 99 unused
items ... spread out ... battle drops ... your call") -- the own-door pins
the generic sweep skips, and the new distribution channels.  Board:
ITEM_EXPANSION_2026_07_26.md."""
import random

from tuipet import adventure as adv
from tuipet import data, shop, tournament
from tuipet.pet import Pet
from tuipet.petcare import _Refused


def _pet(stage="Rookie", num=100, **kw):
    p = Pet(num=num, stage=stage, attribute="Vaccine")
    p.name, p.line_id = "Testmon", ""
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# ---- the ailment doors -------------------------------------------------------

def test_the_med_cures_sickness_and_only_sickness():
    p = _pet(sick=True)
    p.add_item("med")
    assert not isinstance(p.use_item("med"), _Refused)
    assert not p.sick and p.inventory.get("med", 0) == 0
    p2 = _pet()
    p2.add_item("med")
    assert isinstance(p2.use_item("med"), _Refused)     # kept on refusal
    assert p2.inventory.get("med") == 1


def test_the_bandage_stayed_cut_and_h_stays_free():
    """The expansion revived a 10b bandage item for about an hour; Joel
    cut it on sight ("its supposed to just be used for the animations
    for heal").  The wrap = the H show; the key resolves nowhere."""
    assert "bandage" not in shop.CATALOG
    assert shop.key_for_icon("i:80") is None
    q = _pet(injured=True, bits=0)
    q.inj_length = 400.0
    assert not isinstance(q.heal_bandage(), _Refused)
    assert not q.injured


def test_the_premiums_do_what_no_free_button_can():
    """⭐REPOINTED by the ITEM REFACTOR (2026-08-02).  These two were "premium
    COMBOS" -- they bundled a free button with a cheap item and charged for the
    pair.  A combo is not a capability: the Elixir's cure is the free F pill
    and its tank is the 200b drink; Vitamin G's heal is the free H.

    Now each does something no button and no cheaper item can: the Elixir wipes
    the ENTIRE care-mistake slate, and Vitamin G makes the injury roll
    impossible for a day.  Full behaviour pinned in test_item_refactor.py."""
    p = _pet(sick=True)
    p.energy = 0
    p._inc_mistake("left hungry too long")
    p._inc_mistake("the lights left on")
    p.add_item("elixir")
    p.use_item("elixir")
    assert p.pardon_lapse > 0            # the WARD (the wipe moved to the drink)
    assert p.sick, "the cure is FREE -- the elixir must not sell it"
    assert p.energy == 0, "the tank is 200b -- the elixir must not sell it"
    q = _pet(injured=True)
    q.inj_length, q.strength = 400.0, 0
    q.add_item("vitamin_g")
    q.use_item("vitamin_g")
    assert q.strength == 4 and q.ward_lapse > 0
    assert q.injured, "H heals for FREE -- vitamin_g prevents, it does not cure"


# ---- the evolution keys ------------------------------------------------------

def _holder_of(item_id):
    """A species whose graph carries an evol_item == item_id target."""
    reqs = data.load_requirements()
    evs = data.load_evolutions()
    _, by_num = data.load_sprites()
    for num, targets in evs.items():
        for t in targets:
            if reqs.get(t, {}).get("evol_item", -1) == item_id \
                    and num in by_num and t in by_num:
                return num, t
    return None, None


def test_a_spirit_key_opens_its_authored_door_and_wakes_the_beast():
    """The Frontier chain: the Human spirit evolves its holder, and the
    BEAST half lands in the bag (roads give Human, the Human gives Beast)."""
    num, target = _holder_of(43)                 # the Human Fire Spirit
    assert num is not None, "the corpus lost its fire-spirit road"
    p = _pet(stage=data.load_sprites()[1][num]["stage"], num=num)
    p.add_item("human_fire_spirit")
    out = p.use_item("human_fire_spirit")
    assert not isinstance(out, _Refused), out
    assert p.num == target
    assert p.inventory.get("beast_fire_spirit") == 1
    assert p.inventory.get("human_fire_spirit", 0) == 0


def test_a_spirit_refusal_keeps_the_item():
    p = _pet()                                   # no spirit road from here
    p.add_item("human_dark_spirit")
    assert isinstance(p.use_item("human_dark_spirit"), _Refused)
    assert p.inventory.get("human_dark_spirit") == 1


def test_a_direct_relic_evolves_only_a_graph_neighbour():
    # Grey Claws names Greymon (93): find a species adjacent to it
    evs = data.load_evolutions()
    _, by_num = data.load_sprites()
    holder = next(n for n, ts in evs.items() if 93 in ts and n in by_num)
    p = _pet(stage=by_num[holder]["stage"], num=holder)
    p.add_item("grey_claws")
    assert not isinstance(p.use_item("grey_claws"), _Refused)
    assert p.num == 93
    q = _pet()                                   # not adjacent: refused, kept
    q.add_item("grey_claws")
    assert isinstance(q.use_item("grey_claws"), _Refused)
    assert q.inventory.get("grey_claws") == 1


def test_eating_an_orange_can_wake_citramon():
    """The FOOD evolution door (processFoodEvol) had zero callers; the
    expansion wired it through the new snack family.  One corpus form
    gates on evol_food 42 -- the Orange."""
    reqs = data.load_requirements()
    target = next(n for n, r in reqs.items() if r.get("evol_food") == 42)
    evs = data.load_evolutions()
    holder = next(n for n, ts in evs.items() if target in ts)
    _, by_num = data.load_sprites()
    p = _pet(stage=by_num[holder]["stage"], num=holder)
    p.hunger = 0
    from tuipet import evolution
    if evolution.check(p, target, food=42):      # gates pass on this fixture
        p.add_item("orange")
        p.use_item("orange")
        assert p.num == target
    else:                                        # gates authored tighter: the
        p.add_item("orange")                     # meal still lands as a meal
        assert not isinstance(p.use_item("orange"), _Refused)


# ---- the capsules ------------------------------------------------------------

def test_a_capsule_grants_a_real_item_and_never_a_box():
    random.seed(7)
    p = _pet()
    for _ in range(40):
        p.add_item("capsule_a")
        out = p.use_item("capsule_a")
        assert not isinstance(out, _Refused)
    granted = {k for k in p.inventory if k != "capsule_a"}
    assert granted, "forty boxes granted nothing"
    for k in granted:
        assert k in shop.CATALOG
        assert "capsule" not in k, "a box inside a box"


def test_a_prank_capsule_pays_from_the_junk_drawer():
    random.seed(3)
    p = _pet()
    p.add_item("prank_capsule_a", 20)
    for _ in range(20):
        p.use_item("prank_capsule_a")
    granted = {k for k in p.inventory if not k.startswith("prank_")}
    assert granted <= set(Pet._PRANK_POOL)
    assert granted, "a prank still grants SOMETHING"


def test_a_festival_open_reaches_one_tier_higher(monkeypatch):
    from tuipet import tournament as t
    seen = set()
    monkeypatch.setattr(t, "holiday", lambda today=None: "Christmas Festival")
    random.seed(11)
    p = _pet()
    for _ in range(300):
        p.add_item("capsule_b")
        p.use_item("capsule_b")
    tiers = {shop.CATALOG[k].tier or "common"
             for k in p.inventory if k != "capsule_b"}
    seen |= tiers
    assert "rare" in seen, "a festival open never reached the rare tier"


def test_chocolate_egg_eats_and_grants_a_common_toy():
    random.seed(5)
    p = _pet()
    p.hunger = 0
    p.add_item("chocolate_egg")
    out = p.use_item("chocolate_egg")
    assert "toy inside" in str(out)
    assert p.hunger == 1
    granted = [k for k in p.inventory if k != "chocolate_egg"]
    assert len(granted) == 1
    assert (shop.CATALOG[granted[0]].tier or "common") == "common"


# ---- the battle drops --------------------------------------------------------

def test_the_authored_drop_tables_load_and_bound_at_100():
    lt = data.load_loot_tables()
    assert len(lt) == 41
    for tid, rows in lt.items():
        assert sum(r for _i, r in rows) <= 100, tid
    assert lt[0] == [("i:15", 100)]              # the courage boss table


def test_a_unique_boss_drops_its_digimental():
    p = _pet()
    run = adv.Adventure(p, zone=adv.ZONES[0])
    key = run.award_drop({"loot_table": 0, "boss": True})
    assert key == "egg_of_courage"
    assert p.inventory.get("egg_of_courage") == 1
    assert run.drops == 1


def test_replay_boss_drops_ride_the_bounty_ration():
    p = _pet()
    run = adv.Adventure(p, zone=adv.ZONES[0])
    run.replay, run.bounty_spent = True, True
    assert run.award_drop({"loot_table": 0, "boss": True}) is None
    # wilds stay live on a veteran road
    random.seed(1)
    hits = sum(1 for _ in range(400)
               if run.award_drop({"loot_table": 11, "boss": False}))
    assert hits > 0


def test_wild_drop_rates_match_the_authored_numbers():
    p = _pet()
    run = adv.Adventure(p, zone=adv.ZONES[0])
    random.seed(9)
    n = 4000
    hits = sum(1 for _ in range(n)
               if run.award_drop({"loot_table": 13, "boss": False}))
    assert 0.05 <= hits / n <= 0.09              # authored 7%


# ---- the cup prizes ----------------------------------------------------------

def test_the_authored_prize_ids_all_resolve():
    for t in data.load_tournies():
        if t["item"] >= 0:
            k = tournament._prize_key("i", t["item"])
            assert k in shop.CATALOG or k.startswith("egg_of_"), t["item"]
        if t["food_id"] >= 0 and t["food_amt"] > 0:
            assert tournament._prize_key("f", t["food_id"]) in shop.CATALOG


def test_a_digimental_cup_pays_the_crest_itself():
    assert tournament._prize_key("i", 24) == "egg_of_miracles"


# ---- the futon ---------------------------------------------------------------

def test_the_futon_deepens_the_doze_to_a_full_tank():
    p = _pet()
    p.energy = 0
    p.add_item("futon")
    out = p.use_item("futon")
    assert not isinstance(out, _Refused)
    assert p.asleep and p.futon_doze
    # the recovery-doze hold now reads the flag: it holds below FULL
    assert p.energy < p.max_energy
    p._wake()
    assert not p.futon_doze                      # spent on wake


def test_the_futon_never_disturbs_a_sleeper():
    p = _pet()
    p._fall_asleep()
    d0 = p.disturb
    p.add_item("futon")
    out = p.use_item("futon")
    assert not isinstance(out, _Refused)
    assert p.disturb == d0                       # the sleep family's 4th member
    assert p.futon_doze


def test_futon_doze_rides_the_save():
    from dataclasses import asdict
    p = _pet()
    p.futon_doze = True
    assert asdict(p)["futon_doze"] is True


# ---- the road tools ----------------------------------------------------------

def test_the_safe_lift_moves_ten_legs_and_no_ambush():
    p = _pet()
    p.add_item("zone_transport")
    run = adv.Adventure(p, zone=adv.ZONES[0])
    run.loc = 5
    assert run.use_transport("zone_transport") == "skip-lift"
    assert run.loc == 15
    assert p.inventory.get("zone_transport", 0) == 0


def test_the_camp_rests_to_half_and_hides_when_pointless():
    p = _pet()
    p.energy = 0
    p.add_item("continent_transport")
    run = adv.Adventure(p, zone=adv.ZONES[0])
    assert "continent_transport" in run.held_transports()
    assert run.use_transport("continent_transport") == "camp-rest"
    assert p.energy == p.max_energy // 2
    p.add_item("continent_transport")
    assert "continent_transport" not in run.held_transports()   # nothing to rest


# ---- the spread itself -------------------------------------------------------

def test_the_deep_roads_hide_the_ten_human_spirits():
    placed = [(zi, k) for zi, z in enumerate(adv.ZONES)
              for k in z["find_keys"] if k.startswith("human_")]
    assert len(placed) == 10
    assert len({k for _zi, k in placed}) == 10   # one each, no twins
    deep = set(adv.PROGRESSION[-10:])
    assert {zi for zi, _k in placed} == deep     # only the hardest roads
    for k in ("human_fire_spirit", "human_dark_spirit"):
        assert shop.tier_weight(k) == shop.TIER_WEIGHT["legendary"]


def test_the_pranks_and_the_boxes_reach_the_road_on_festivals():
    a = adv.Adventure(_pet(), zone=adv.ZONES[0])
    a.holiday = "Christmas Festival"
    random.seed(2)
    seen = set()
    for _ in range(600):
        a.loc = 3                                # stay mid-road
        f = a._roll_find()
        if f and f[1]:
            seen.add(f[0])
    assert seen and seen <= set(adv._FESTIVAL_CAPSULES)

# ---- the anti-printer ration -------------------------------------------------

def test_the_home_capsule_shelf_is_rationed(isolate_save):
    """Measured (expansion audit 2026-07-26): a capsule's contents resell
    for ~123b against its 100b price, so an unlimited home shelf would be
    a printer.  The box rides the daily tier ration instead -- three a
    day, then sold out until tomorrow; every other home row stays
    unlimited as ever.

    ⭐The ration TIGHTENED 2026-08-02 when rarity was decoupled from price: the
    box is 100b, so the price ladder called it common (3 a day).  Its AUTHORED
    supply is 0.1 expected copies -- the scarcest good in the game -- so it is
    legendary now and the shelf parts with ONE.  Exactly the decoupling Joel
    asked for, landing on the item that most needed it."""
    p = _pet(bits=10_000)
    row = next(e for e in shop.home_stock(pet=p) if e["key"] == "capsule_a")
    ration = shop.tier_stock("capsule_a")
    assert row.get("left") == ration == 1
    for i in range(ration):
        msg, sfx = shop.town_buy(p, row)
        assert sfx == "confirm", (i, msg)
    msg, sfx = shop.town_buy(p, row)
    assert sfx == "error" and "Sold out" in msg
    plain = next(e for e in shop.home_stock(pet=p) if e["key"] == "fish")
    assert plain.get("left") is None             # the reliable shelf, untouched


def test_the_chocolate_egg_pays_a_toy_never_a_food():
    """Authored 'Toy Inside' (bug 2026-07-28: the pool was 62% foods, one of
    them ANOTHER chocolate egg, plus tierless grant treats leaking through
    the None-reads-as-common hole).  Every prize: a priced, common, non-Feed
    item."""
    import random
    from tuipet import shop
    from tuipet.pet import Pet
    random.seed(3)
    seen = set()
    for _ in range(120):
        p = Pet(num=100, stage="Rookie", attribute="Vaccine")
        p.name, p.line_id = "T", ""
        p.hunger = 2
        p.add_item("chocolate_egg")
        p.use_item("chocolate_egg")
        prize = next(k for k in p.inventory if k != "chocolate_egg")
        seen.add(prize)
        v = shop.CATALOG[prize]
        assert v.category != "Feed", f"the egg paid food: {prize}"
        assert v.price is not None and v.tier == "common", prize
    assert len(seen) >= 4, "the toy pool collapsed to a coin flip"


def test_the_surprise_cheer_holds_the_prize_sprite():
    """Joel 2026-07-28: "shouldnt we see the prize sprite? not just an
    announcement?"  A capsule or chocolate egg parks its prize on
    pet.pending_prize; the following cheer carries the icon and the painter
    grounds it beside the pet at hand size -- LEFT floor, clear of the
    16px mon and the right-edge emote."""
    from tuipet import arenafx
    from tuipet.arenafx import _FxCtx, PET_BASE_X, SCREEN_ROWS
    from tuipet.pet import Pet
    p = Pet(num=29, stage="Rookie", attribute="Vaccine")
    p.name, p.line_id = "T", ""
    w = object.__new__(arenafx.FxMixin)
    c = _FxCtx(); c.px_h = SCREEN_ROWS * 2
    c.overlay = []; c.free = []; c.xshift = 0; c.yshift = 0; c.mirror = False
    arenafx.FxMixin._fxk_cheer(w, p, {"kind": "cheer", "step": 0,
                                      "icon": "i:2", "good": True}, 0, c)
    from tuipet import grid
    pet_left = PET_BASE_X + c.xshift
    prize = [(x, y) for x, y in c.overlay if x < pet_left]
    assert prize, "no prize pixels beside the pet"
    assert all(x < pet_left - 1 for x, _y in prize), "prize touches the mon"
    assert all(x >= grid.X0 for x, _y in prize), \
        "prize outside the window -- the clip would eat it (report 07-28)"
    assert pet_left + 16 <= grid.X1, "the step-right pushed the pet out"
    assert max(y for _x, y in prize) <= c.px_h - 2, "prize sank through the floor"
    # ...and a cheer WITHOUT an icon is untouched (every other cheer in the game)
    c2 = _FxCtx(); c2.px_h = SCREEN_ROWS * 2
    c2.overlay = []; c2.free = []; c2.xshift = 0; c2.yshift = 0; c2.mirror = False
    arenafx.FxMixin._fxk_cheer(w, p, {"kind": "cheer", "step": 6, "good": True}, 6, c2)
    assert not [pt for pt in c2.overlay if pt[0] < PET_BASE_X]


def test_the_openers_park_their_prize_for_the_cheer():
    import random
    from tuipet.pet import Pet
    random.seed(5)
    p = Pet(num=100, stage="Rookie", attribute="Vaccine")
    p.name, p.line_id = "T", ""
    p.hunger = 2
    p.add_item("chocolate_egg")
    p.use_item("chocolate_egg")
    assert p.pending_prize and p.pending_prize in p.inventory
    q = Pet(num=100, stage="Rookie", attribute="Vaccine")
    q.name, q.line_id = "T", ""
    q.add_item("capsule_a")
    q.use_item("capsule_a")
    assert q.pending_prize and q.pending_prize in q.inventory
