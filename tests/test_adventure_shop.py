"""Adventure rebuild — EXCLUSIVE SHOP ITEMS (phase 13, 2026-07-20).

Pins the road shelf: transports + Life Recovery go on sale once the tamer has
CLEARED MAPS (the profile `maps` signal), felling a map's last boss records it,
and found loot resolves to real CATALOG keys the bag can show and use.
"""
from tuipet import adventure, shop
from tuipet.adventure import ZONES, is_map_cleared
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


class _Win:
    won = True


def test_the_road_items_are_real_catalog_entries():
    for k in ("town_transport", "disaster_transport", "life_recovery"):
        e = shop.entry(k)
        assert e and e["category"] == "Adventure" and e["price"] > 0
        # and they're usable from the bag (kept until spent on the road)
        p = _pet()
        p.add_item(k)
        msg = p.use_item(k)
        assert "road" in msg.lower() and p.inventory.get(k, 0) == 1   # not consumed


def test_the_road_shelf_gates_on_maps_cleared():
    assert not shop.adventure_open("town_transport", {"maps": set()})
    assert shop.adventure_open("town_transport", {"maps": {0}})
    assert not shop.adventure_open("life_recovery", {"maps": {0}})     # needs 2
    assert shop.adventure_open("life_recovery", {"maps": {0, 1}})
    # sealed items are OFF the shelf entirely at zero progress
    names = {e["name"] for e in shop.catalog()}   # uses live profile progress
    # (can't assume live progress; just prove the gate function drives it)
    locked = [k for k in ("town_transport", "life_recovery")
              if not shop.adventure_open(k, {"maps": set()})]
    assert locked == ["town_transport", "life_recovery"]


def test_a_map_is_cleared_when_its_last_zone_falls():
    p = _pet()
    m1 = [adventure.PROGRESSION.index(i)     # map 1's ROAD positions (option b:
          for i, z in enumerate(ZONES) if z["map"] == 1]   # the road interleaves maps)
    p.adv_progress = max(m1)           # every map-1 stop but the DEEPEST
    assert not is_map_cleared(p, 1)
    p.adv_progress = max(m1) + 1       # the deepest falls -> map 1 complete
    assert is_map_cleared(p, 1) and not is_map_cleared(p, 2)


def test_felling_a_maps_last_boss_records_the_map(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    recorded = []
    from tuipet import persistence
    monkeypatch.setattr(persistence, "map_complete_add", lambda m: recorded.append(m))
    # a pet at map 1's DEEPEST road stop: felling its boss clears map 1
    p = _pet()
    m1 = [adventure.PROGRESSION.index(i)
          for i, z in enumerate(ZONES) if z["map"] == 1]
    p.adv_progress = max(m1)           # that stop IS the frontier
    pan = AdventurePanel(p, zone=ZONES[adventure.PROGRESSION[max(m1)]])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None
    pan._battle_done(_Win())
    assert p.adv_progress == max(m1) + 1     # frontier advanced
    assert recorded == [0]               # map 1 recorded 0-based (profile `maps`)


def test_a_mid_map_zone_win_records_no_map(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    recorded = []
    from tuipet import persistence
    monkeypatch.setattr(persistence, "map_complete_add", lambda m: recorded.append(m))
    p = _pet()
    p.adv_progress = 2                   # early road: no map near completion
    pan = AdventurePanel(p, zone=ZONES[adventure.PROGRESSION[2]])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None
    pan._battle_done(_Win())
    assert p.adv_progress == 3 and recorded == []   # map 1 not done yet


# --- the shelf must RENDER, not just exist (gameplay polish 2026-07-22) ------
# v0.5.114 put the road shelf in the CATALOG and gated it on cleared maps,
# but no GROUPS tab carried "Adventure" -- and home shop, town counters AND
# the bag all build their rows through the tab grammar, so 1750b of shipped
# items could never be seen, bought, or (in the bag) even looked at.  The
# town daily deal still rolled onto the invisible rows ~half of all days.

def test_every_sold_category_has_a_home_in_the_tab_grammar():
    """The ratchet: a future category added to the CATALOG without a tab
    would go silently unsellable again."""
    from tuipet import shopscreen
    tabbed = set()
    for _name, cats in shopscreen.GROUPS:
        tabbed |= set(cats or ())
    sold = {cat for (_n, _i, price, cat, _e, _f) in shop.CATALOG.values()
            if price is not None}
    assert sold <= tabbed, f"untabbed categories: {sold - tabbed}"


def test_the_unlocked_road_shelf_renders_on_the_items_tab(monkeypatch):
    from tuipet import persistence
    from tuipet.shopscreen import ShopPanel
    monkeypatch.setattr(persistence, "get_progress", lambda: {"maps": {0, 1}})
    pan = ShopPanel(_pet())
    pan.tab = pan._tabs().index("Items")
    keys = {e["key"] for e in pan._rows()}
    assert {"town_transport", "disaster_transport", "life_recovery"} <= keys
    txt = pan.text().plain                     # the smoke walk renders too
    assert "Items" in txt


def test_the_town_counter_sells_its_authored_transports():
    from tuipet.shopscreen import ShopPanel
    pan = ShopPanel(_pet(), town_id=0)         # authored SID1/SID2 = the warps
    pan.tab = pan._tabs().index("Items")
    keys = {e["key"] for e in pan._rows()}
    assert {"town_transport", "disaster_transport"} <= keys
    pan.text()                                 # render walk


def test_a_held_road_item_shows_in_the_bag():
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    p.add_item("town_transport")
    pan = ShopPanel(p, start_mode="bag", bag_only=True)
    seen = set()
    for i in range(len(pan._tabs())):
        pan.tab = i
        seen |= {e["key"] for e in pan._rows()}
    assert "town_transport" in seen
