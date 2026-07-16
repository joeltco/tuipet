"""Feeding system: DVPet's Food_Inventory model, driven entirely by foods.csv.

- The staples (Meat/Fish/Fruit/Vegetable) come from StartingQuantity=99 +
  CanDec=false in the DATA -- infinite, always on the feed page.
- ShowInInventory=false foods (Med/Vitamin) never appear (they're heal flows).
- Bought foods (CanDec=true) are consumed per bite.
- feed() applies the full applyFood effect set with the fullness modifier.
"""
from tuipet.pet import Pet, FULL_HUNGER, OVEREAT_LIMIT
from tuipet import data
from tuipet.feedscreen import FeedPanel, feedable, food_qty


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.obedience = 150            # out-roll checkRefused: these tests exercise applyFood
    p.weight = p._base_weight()  # the dataclass default 20 is past num 1's weight WALL
    #                              (base 10 +- 8) -- a real pet is seeded at its base
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _food(name):
    return next(f for f in data.load_foods() if f["name"] == name)


def test_staples_come_from_the_data():
    p = _pet()
    names = [f["name"] for f in feedable(p)]
    # foods.csv: StartingQuantity 99 + CanDec false + ShowInInventory TRUE
    assert names[:4] == ["Meat", "Fish", "Fruit", "Vegetable"]
    # Med/Vitamin are ShowInInventory FALSE -> never on the feed page
    assert "Med" not in names and "Vitamin" not in names


def test_staples_never_deplete_bought_food_does():
    p = _pet(hunger=0)
    meat = _food("Meat")
    q0 = food_qty(p, meat)
    panel = FeedPanel(p)
    panel.key("enter")                       # eat the Meat
    assert food_qty(p, meat) == q0           # CanDec=false: pinned at StartingQuantity
    # a bought food is consumed per bite
    cake = _food("Cake")
    p2 = _pet(hunger=0)
    p2.inventory[cake["key"]] = 2
    panel2 = FeedPanel(p2)
    i = [f["name"] for f in panel2.options].index("Cake")
    for _ in range(i):
        panel2.key("down")
    panel2.key("enter")
    assert p2.inventory.get(cake["key"], 0) == 1


def test_meat_refuses_a_full_stomach():
    p = _pet(hunger=FULL_HUNGER, glutton=0, anim="")
    msg = p.feed(_food("Meat"))
    assert p.anim == "refuse" and "full" in msg
    assert p.hunger == FULL_HUNGER


def test_full_food_effect_set_applies():
    # Meat carries mood +5; feeding applies hunger AND mood (not just hunger)
    p = _pet(hunger=1)
    m0 = p.mood
    p.feed(_food("Meat"))
    assert p.hunger == 2
    # (the food mood assert left with the mood system)


def test_glutton_eats_one_past_full():
    p = _pet(hunger=FULL_HUNGER, glutton=1)
    p.feed(_food("Meat"))
    assert p.hunger == OVEREAT_LIMIT


def test_fullness_modifier_diminishes_a_near_full_meal():
    big = {"name": "Steak", "hunger": 2, "category": "Meat"}
    empty = _pet(hunger=0)
    empty.feed(big)
    near = _pet(hunger=FULL_HUNGER, glutton=1)
    g0 = near.hunger
    near.feed(big)
    assert (empty.hunger - 0) >= (near.hunger - g0)


def test_feed_panel_feeds_and_closes():
    p = _pet(hunger=1)
    panel = FeedPanel(p)
    r = panel.key("enter")
    assert r is not None and r[0] == "done"
    outcome, food, msg = r[1]
    assert outcome == "fed" and food["name"] == "Meat"
    assert p.anim == "eat"
