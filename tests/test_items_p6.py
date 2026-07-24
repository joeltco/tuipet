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
        assert shop.CATALOG[key].category == "Evolution", key


def test_the_chips_are_eaten_like_every_other_food_sheet_consumable():
    for key in list(CHIPS) + ["omni_chip_g"]:
        assert shop.item_is_eaten(key), key


# ---- what was deliberately LEFT dark, and why -------------------------------

def test_the_paid_ailment_cures_stayed_out():
    """f:15 Elixir cures sickness and f:16 Vitamin G cures injury -- both
    real, both canon.  Adding them would have re-sold what R3 just made
    free, breaking the symmetry shipped hours earlier."""
    assert shop.key_for_icon("f:15") is None
    assert shop.key_for_icon("f:16") is None


def test_the_attribute_TRADE_items_stayed_out():
    """i:5 Board Game and i:8 Computer Game swap one power for another
    (vaccine -15 / data +15).  Canon handles the resulting negatives with
    compensateAttributes -- which is DORMANT here (`_compensate_attrs` is
    defined and never called).  Adding them would have required reviving
    a stripped system, which needs a named order."""
    assert shop.key_for_icon("i:5") is None
    assert shop.key_for_icon("i:8") is None


def test_the_itemevol_relics_stayed_dormant():
    """The 29 spirits and evolution relics are dormant DATA: shipped
    evolutions.csv has no item columns at all, so they could never fire."""
    for iid in (33, 34, 43, 53, 62):
        assert shop.key_for_icon("i:%d" % iid) is None


def test_the_plain_foods_stayed_out():
    """~20 dark foods are all 'hunger +1' with a different poop load.  The
    system that would tell them apart -- Taste (`_change_rank`) -- is
    dormant, so they would ship as filler, and reviving taste needs a
    named order."""
    import glob
    import re
    calls = []
    for path in glob.glob("src/tuipet/*.py"):
        for i, line in enumerate(open(path), 1):
            body = line.split("#")[0]
            if re.search(r"\b_change_rank\s*\(", body) and "def " not in body:
                calls.append(f"{path}:{i}")
    assert not calls, f"taste woke up: {calls}"
    for iid in (24, 29, 45, 46, 47, 48):
        assert shop.key_for_icon("f:%d" % iid) is None


def test_the_catalog_grew_by_exactly_the_chips():
    assert len(shop.CATALOG) == 44
    assert sum(1 for v in shop.CATALOG.values()
               if v.category == "Evolution") == 11
