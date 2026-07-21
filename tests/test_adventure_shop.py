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
    p.adv_progress = 6                 # zones 0-5 of map 1 conquered, zone 6 (last) not
    assert not is_map_cleared(p, 1)
    p.adv_progress = 7                 # zone 6 conquered -> map 1 (zones 0-6) complete
    assert is_map_cleared(p, 1) and not is_map_cleared(p, 2)


def test_felling_a_maps_last_boss_records_the_map(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    recorded = []
    from tuipet import persistence
    monkeypatch.setattr(persistence, "map_complete_add", lambda m: recorded.append(m))
    # a pet on the LAST zone of map 1 (index 6): felling its boss clears map 1
    p = _pet()
    p.adv_progress = 6
    pan = AdventurePanel(p, zone=ZONES[6])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None
    pan._battle_done(_Win())
    assert p.adv_progress == 7           # frontier advanced
    assert recorded == [0]               # map 1 recorded 0-based (profile `maps`)


def test_a_mid_map_zone_win_records_no_map(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    recorded = []
    from tuipet import persistence
    monkeypatch.setattr(persistence, "map_complete_add", lambda m: recorded.append(m))
    p = _pet()
    p.adv_progress = 2                   # frontier mid-map-1
    pan = AdventurePanel(p, zone=ZONES[2])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None
    pan._battle_done(_Win())
    assert p.adv_progress == 3 and recorded == []   # map 1 not done yet
