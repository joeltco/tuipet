"""Consumable 'Recovered' (battle-HP restore) must NOT be treated as injury healing.

DVPet applyConsumable: Healed -> injLength=0 (clears an injury); Recovered ->
restores battle health points only. tuipet has no persistent battle-HP stat, so a
Recovered item must leave injuries alone -- only DVPet 'Healed' items (Vitamin G) cure.
"""
from tuipet import data


def test_recovered_items_do_not_cure_injuries():
    foods, items = data._load_consumables()
    healers = {e["name"] for d in (foods, items) for e in d.values() if e["healed"]}
    # Vitamin G is the only Healed=TRUE consumable in DVPet's data
    assert "Vitamin G" in healers
    # Recovered=TRUE foods/items must NOT be flagged as injury healers
    for nm in ("Steak", "Tuna", "Energy Drink", "Honey", "Orange", "Guava",
               "Bath", "Cold Shower", "Futon"):
        assert nm not in healers, f"{nm} is Recovered (HP), not Healed (injury)"


def test_recovered_food_does_not_clear_an_injury_on_use():
    from tuipet.pet import Pet
    foods, _ = data._load_consumables()
    steak = next(k for k, e in foods.items() if e["name"] == "Steak")
    p = Pet.from_num(29); p.stage = "Rookie"
    p.injuries = 1; p.inj_length = 100.0
    p.add_item(f"f:{steak}")
    p.use_item(f"f:{steak}")
    assert p.injuries == 1 and p.inj_length == 100.0   # the steak fed it, didn't mend it
