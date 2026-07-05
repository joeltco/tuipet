"""Town economies vs DVPet Town.java (shops, sell gates, the town tournament)."""
import random
from tuipet.pet import Pet
from tuipet import data, shop, tournament
from tuipet.townscreen import TownPanel


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500, bits=99999)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_town_shop_applies_the_override_econ():
    random.seed(0)
    p = _pet()
    town = data.load_towns()[0]
    ov = data.load_shop_overrides()
    by_cid = {ov[s]["consumable_id"]: ov[s] for s in town["foods_override"]
              if ov.get(s) and ov[s]["is_food"]}
    for _ in range(6):                                # rolls are random: scan a few
        for slot in shop.roll_town_shop(p, town, True):
            e = shop.entry(slot["key"])
            if e["id"] in by_cid:
                assert slot["price"] == by_cid[e["id"]]["price"]   # the TOWN's price
                return
    raise AssertionError("no overridden food ever rolled")


def test_town_shop_respects_town_inventory_size():
    random.seed(1)
    p = _pet()
    town = data.load_towns()[0]
    assert len(shop.roll_town_shop(p, town, True)) <= town["food_max"]
    assert len(shop.roll_town_shop(p, town, False)) <= town["item_max"]


def test_town_cups_forced_trophies_always_open():
    p = _pet()
    town = dict(data.load_towns()[0], tournament_limit=25, forced_trophies=[3])
    sched = tournament.town_schedule(p, town)
    assert len(sched) == 25
    assert sched[24] == 3                              # forced pin at the tail
    assert tournament.town_slot_open(p, 24)            # past 23: always open
    hour = tournament._hour(p)
    assert tournament.town_slot_open(p, hour)
    assert not tournament.town_slot_open(p, (hour + 1) % 24)


def test_town_panel_buy_and_sell_gates():
    random.seed(2)
    p = _pet()
    panel = TownPanel(p, 0)
    assert panel.food_slots and panel.item_slots
    panel.phase = "food"
    panel.cursor = 0
    bits0 = p.bits
    panel._activate(panel._rows())
    assert p.bits < bits0                              # bought at the town price
    # selling honours the town's CanSell flags
    panel.town = dict(panel.town, can_sell_food=False)
    p.inventory["f:8"] = 1
    panel.phase, panel.cursor = "sell", 0
    rows = panel._rows()
    panel.cursor = rows.index("f:8")
    panel._activate(rows)
    assert p.inventory.get("f:8") == 1                 # refused: the town won't buy food


def test_town_shop_pages_share_the_home_shop_icon_view():
    """Refactor 2026-07-05: the town shelves rendered nameplates only while the
    home shop drew item icons.  Both now ride menu.icon_info + shop.slot_info
    -- pin the block (bold name + stock line) and the home shop's 3-row window."""
    from tuipet import menu
    random.seed(4)
    p = _pet()
    panel = TownPanel(p, 0)
    panel.phase, panel.cursor = "food", 0
    txt = panel.text().plain
    e = panel._slot_entry(panel.food_slots[0])
    assert e["name"][:menu.W - menu.IC_W - 2] in txt        # the info column
    assert "stock x" in txt or "SOLD OUT" in txt            # slot_info's stock line
    assert shop.slot_label(e) in txt                        # the shared row format
    assert len(txt.split("\n")) <= 12                       # inside the LCD
    # the sell counter pays the TOWN econ in its info block too
    p.inventory["f:8"] = 2
    panel.phase, panel.cursor = "sell", 0
    rows = panel._rows()
    panel.cursor = rows.index("f:8")
    stxt = panel.text().plain
    assert "sell " in stxt or "can't resell" in stxt


def test_shop_slot_label_and_buy_are_the_shared_seam():
    """shop.slot_label is the ONE shelf-row format; shop.buy is the ONE
    bits-delta sfx rule (reward when bits moved, error when broke)."""
    lbl = shop.slot_label({"name": "Meat", "stock": 0, "sale": 0, "price": 40})
    assert "OUT" in lbl and lbl.endswith("40b")
    lbl = shop.slot_label({"name": "Meat", "stock": 3, "sale": 25, "price": 40})
    assert "x3*" in lbl and lbl.endswith("25b")             # sale tag + sale price
    p = _pet()
    slot = {"key": "f:8", "stock": 1, "sale": 0}
    p.bits = 0
    msg, sfx = shop.buy(p, slot)
    assert sfx == "error"                                   # broke: nothing moved
    p.bits = 10_000
    msg, sfx = shop.buy(p, slot)
    assert sfx == "reward" and p.bits < 10_000
