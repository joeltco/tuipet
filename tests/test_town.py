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


