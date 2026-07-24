"""FESTIVAL ROAD PRESENTS — the surprise reaches the road (2026-07-24).

Joel: "what about in adventure mode? on the road?"

Home gifts are home-only (checkGiftCall gates on _isHome), so a pet never
hands you a present while adventuring.  The road already had festival
BONUSES (2x loot, 2x bits); this adds the SURPRISE: on a festival, a third
of road finds are a wrapped present from the same gift pool -- dug up like
loot, revealed like a gift, capped at rare.
"""
import collections
import random

from tuipet import adventure as adv, shop
from tuipet.adventure import ZONES
from tuipet.adventurescreen import AdventurePanel
from tuipet.arenafx import _PRESENT
from tuipet.pet import Pet


def _adv(holiday):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=75)
    a = adv.Adventure(p, zone=ZONES[adv.PROGRESSION[3]])
    a.holiday = holiday
    a.loc = 5                       # on the road, not resting in a town
    return a


def _finds(holiday, n=6000):
    a = _adv(holiday)
    random.seed(9)
    pres, norm, keys = 0, 0, collections.Counter()
    for _ in range(n):
        r = a._roll_find()
        if r is None:
            continue
        key, is_present = r
        if is_present:
            pres += 1
            keys[key] += 1
        else:
            norm += 1
    return pres, norm, keys


def test_no_road_presents_on_an_ordinary_day():
    pres, norm, _ = _finds(None)
    assert pres == 0 and norm > 0


def test_a_third_of_festival_finds_are_presents():
    pres, norm, _ = _finds("Christmas Festival")
    frac = pres / (pres + norm)
    assert 0.25 < frac < 0.45, frac


def test_road_presents_draw_from_the_festival_gift_pool():
    _pres, _norm, keys = _finds("Halloween Festival")
    assert len(keys) >= 10, "a present is a surprise, not one item"
    hi = max(shop.TIER_ORDER.index(shop.CATALOG[k].tier or "common") for k in keys)
    assert shop.TIER_ORDER[hi] == "rare"          # festival cap, same as home
    banned = {"poison_mushroom", "digimemory", "revive_floppy",
              "town_transport", "disaster_transport", "life_recovery"}
    assert not (set(keys) & banned)


def test_travel_carries_the_present_flag():
    a = _adv("Christmas Festival")
    random.seed(2)
    saw_find = False
    for _ in range(400):
        r = a.travel()
        if isinstance(r, tuple) and r[0] == "find":
            saw_find = True
            assert len(r) == 3 and isinstance(r[2], bool)
    assert saw_find


def test_a_present_find_digs_up_wrapped_and_reveals_the_surprise():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=75)
    pan = AdventurePanel(p, zone=ZONES[adv.PROGRESSION[3]])
    pan._find = "cupcake"
    pan._find_present = True
    pan._dig()
    assert pan._scene["icon"] == _PRESENT            # the wrapper, not the item
    assert "present" in pan._find_msg.lower()
    assert p.inventory.get("cupcake") == 1           # the surprise is banked
    assert pan._find_present is False                # flag consumed


def test_a_plain_find_still_shows_its_own_icon():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=75)
    pan = AdventurePanel(p, zone=ZONES[adv.PROGRESSION[3]])
    pan._find = "steak"
    pan._find_present = False
    pan._dig()
    assert pan._scene["icon"] != _PRESENT
    assert "Dug up" in pan._find_msg


def test_the_road_still_has_its_bonus_multipliers():
    """The present is ADDED to the festival road, not instead of the loot/
    bits boosts that were already there."""
    assert adv.HOLIDAY_FIND_MULT == 2
    assert adv.HOLIDAY_BITS_MULT == 2
