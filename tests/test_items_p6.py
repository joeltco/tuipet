"""THE ATTRIBUTE CHIPS — items refactor P6 (2026-07-23).

Joel: "do p6".

P6 was "R5 additions, if any" from the dark-sprite pool (87 packaged DVPet
rips that nothing could reach).  The bar I held them to is the one that
worked for the Miracle Drink: an addition must be CANON DATA landing on a
LIVE stat -- never an invented effect, never a revived system.

Of the 86 candidates, 70 have some live-looking leg, but almost all were
ruled out for a stated reason (see the board).  What survived is the
attribute chips, because Va/D/Vi is the biggest live lever in the game
with nothing buyable behind it: hundreds of evolution rows gate on it,
battle power reads it, and the only ways to move it were +1 per battle
win and the inheritance-only Digimemory.

Deliberately NOT added, and each pin below records why, so a later pass
doesn't quietly undo the reasoning.
"""
import csv

from tuipet import shop
from tuipet.pet import Pet

CHIPS = {
    "vaccine_chip": ("f:10", "vaccine", 15),
    "data_chip": ("f:11", "data_power", 15),
    "virus_chip": ("f:12", "virus", 15),
    "vaccine_chip_g": ("f:20", "vaccine", 30),
    "data_chip_g": ("f:21", "data_power", 30),
    "virus_chip_g": ("f:22", "virus", 30),
}


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    return p


def _foods():
    return {r["FoodIdentificationNum"]: r
            for r in csv.DictReader(open("src/tuipet/data/foods.csv"))}


def test_every_chip_is_backed_by_its_canon_row():
    """Price and magnitude both come from foods.csv -- nothing was tuned."""
    foods = _foods()
    for key, (icon, _stat, amount) in CHIPS.items():
        row = foods[icon[2:]]
        entry = shop.CATALOG[key]
        assert entry.icon == icon
        assert entry.price == int(row["DefaultPrice"]), key
        col = {"vaccine": "Vaccine", "data_power": "Data",
               "virus": "Virus"}[CHIPS[key][1]]
        assert int(row[col]) == amount, key


def test_the_omni_chip_is_canon_too():
    row = _foods()["33"]
    e = shop.CATALOG["omni_chip_g"]
    assert e.icon == "f:33" and e.price == int(row["DefaultPrice"])
    for col in ("Vaccine", "Data", "Virus"):
        assert int(row[col]) == 30


def test_each_chip_moves_only_its_own_power():
    for key, (_icon, stat, amount) in CHIPS.items():
        p = _pet()
        p.add_item(key)
        p.use_item(key)
        for f in ("vaccine", "data_power", "virus"):
            assert getattr(p, f) == (amount if f == stat else 0), (key, f)


def test_the_omni_chip_moves_all_three():
    p = _pet()
    p.add_item("omni_chip_g")
    p.use_item("omni_chip_g")
    assert (p.vaccine, p.data_power, p.virus) == (30, 30, 30)


def test_the_chips_are_uncapped_like_the_win_path_they_shortcut():
    """record_battle just does `self.vaccine += inc` with no ceiling, so
    inventing one here would be inventing a rule."""
    p = _pet()
    for _ in range(4):
        p.add_item("vaccine_chip_g")
        p.use_item("vaccine_chip_g")
    assert p.vaccine == 120


def test_a_chip_is_worth_about_fifteen_wins():
    """The balance claim, pinned: the battle path grants +1 in the foe's
    attribute, so a 1500b chip should be worth roughly fifteen of them."""
    p = _pet()
    p.add_item("vaccine_chip")
    p.use_item("vaccine_chip")
    assert p.vaccine == 15


def test_the_chips_declare_their_live_touches():
    for key, (_icon, stat, _amt) in CHIPS.items():
        assert shop.CATALOG[key].touches == (stat,), key
    assert set(shop.CATALOG["omni_chip_g"].touches) == {
        "vaccine", "data_power", "virus"}


def test_the_chips_landed_in_evolution():
    """They steer attribute-GATED evolutions; that is what they are for."""
    for key in list(CHIPS) + ["omni_chip_g"]:
        assert shop.CATALOG[key].category == "Power", key   # chips move battle POWER, 2026-07-27


def test_the_chips_are_eaten_like_every_other_food_sheet_consumable():
    for key in list(CHIPS) + ["omni_chip_g"]:
        assert shop.item_is_eaten(key), key


# ---- what was deliberately LEFT dark, and why -------------------------------

def test_the_paid_ailment_cures_arrived_as_premium_combos():
    """SUPERSEDED (item expansion 2026-07-26, Joel: "bring them all in...
    your call"): Elixir and Vitamin G are in -- as premium COMBOS that do
    strictly more than the free buttons, so nothing basic is paywalled
    (the free-cure spirit holds; see test_catalog_touches)."""
    assert shop.key_for_icon("f:15") == "elixir"
    assert shop.key_for_icon("f:16") == "vitamin_g"
    assert shop.CATALOG["elixir"].price == 2000
    assert shop.CATALOG["vitamin_g"].price == 2000


def test_the_attribute_TRADE_items_refuse_an_empty_bank():
    """SUPERSEDED (item expansion 2026-07-26): the converters are in.
    The old objection was canon's negative-handling (compensateAttributes,
    dormant); the shipped answer needs no revival -- a converter REFUSES
    below its 15-point stake, so a negative can never be minted."""
    assert shop.key_for_icon("i:5") == "board_game"
    assert shop.key_for_icon("i:8") == "computer_game"
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Rookie", attribute="Vaccine")
    p.line_id = ""
    p.vaccine = p.virus = 14                 # one under the stake
    p.add_item("board_game"); p.add_item("computer_game")
    assert "Not enough" in str(p.use_item("board_game"))
    assert "Not enough" in str(p.use_item("computer_game"))
    assert p.vaccine == 14 and p.virus == 14 and p.data_power == 0


def test_the_itemevol_relics_are_live_keys():
    """SUPERSEDED (item expansion 2026-07-26, Joel: "Wire fully"): the
    spirits and relics are catalog keys now, wired to the evolution
    graph's own item gates (load_requirements carries evol_item for 33
    and 43-62; items.csv DigimonID names the direct forms)."""
    for iid, key in ((33, "digitron"), (34, "horn_helmet"),
                     (43, "human_fire_spirit"), (53, "beast_fire_spirit"),
                     (62, "beast_dark_spirit")):
        assert shop.key_for_icon("i:%d" % iid) == key


def test_the_plain_foods_are_in_but_taste_stays_dormant():
    """Taste (`_change_rank`) stays dormant -- the foods are told apart by
    their authored LIVE columns instead (expansion 2026-07-26)."""
    import glob
    import re
    calls = []
    for path in glob.glob("src/tuipet/*.py"):
        for i, line in enumerate(open(path), 1):
            body = line.split("#")[0]
            if re.search(r"\b_change_rank\s*\(", body) and "def " not in body:
                calls.append(f"{path}:{i}")
    assert not calls, f"taste woke up: {calls}"
    # SUPERSEDED half (item expansion 2026-07-26): the plain foods ARE in
    # now -- differentiated by their authored live columns (weight from
    # calories, obedience, energy), NOT by waking taste; the dormant-taste
    # assertion above is the half that still stands
    for iid in (24, 29, 45, 46, 47, 48):
        assert shop.key_for_icon("f:%d" % iid) is not None


def test_the_catalog_holds_the_whole_authored_corpus():
    """44 -> 132 (item expansion 2026-07-26): every authored consumable is
    a catalog key except the 11 crest-shelf Digimentals (one door) and
    i:35 Blue Crystal (its rip is the shipped dna_crystal's)."""
    # 131 -> 114 (refactor 2026-07-27): 18 keys retired by named order --
    # every one converts to its heir via shop.RETIRED, no authored channel
    # goes dark (key_for_icon successor fallback), and cold_compress joined
    # 114 -> 112 (adventure rebuild 2026-10-14): the four transports retire
    # into two road items (shortcut, rest_kit), converting via shop.RETIRED
    assert len(shop.CATALOG) == 112
    # Evolution split on the axis it serves: the DOORS stay Evolve, the
    # stat chips are POWER (they move battle meters, not destinations)
    assert sum(1 for v in shop.CATALOG.values() if v.category == "Evolve") == 34
    assert sum(1 for v in shop.CATALOG.values() if v.category == "Power") == 12
