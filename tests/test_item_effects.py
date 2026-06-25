"""Item effects ported faithfully from DVPet applyConsumable: lifespan (Seconds),
temperature (Temp, clamped 0..MaxTemp), forced sleep (Sleep flag), and the
fatigue/depression relief flags (whose CSV column name differs food vs item)."""
from tuipet import data
from tuipet.pet import Pet
from tuipet import weather as wx


def _key(name):
    f, i = data._load_consumables()
    for lab, d in (("f", f), ("i", i)):
        for k, e in d.items():
            if e["name"] == name:
                return f"{lab}:{k}"
    raise KeyError(name)


def _use(name, **pet_kw):
    p = Pet.from_num(29); p.stage = "Rookie"
    for k, v in pet_kw.items():
        setattr(p, k, v)
    key = _key(name)
    p.add_item(key); p.use_item(key)
    return p


def test_seconds_changes_lifespan():
    base = Pet.from_num(29).lifespan
    assert _use("Gold Pill").lifespan == base + 43200      # +12h
    assert _use("Vitamin").lifespan == base - 3600         # -1h


def test_temp_shifts_temperature_within_range():
    assert _use("Ice Cream", temp=50).temp == 40           # -10
    assert _use("Chicken Soup", temp=50).temp == 60        # +10
    # DVPet guard: an out-of-range result is rejected, not clamped
    assert _use("Chicken Soup", temp=wx.MAX_TEMP).temp == wx.MAX_TEMP


def test_sleep_flag_puts_pet_to_sleep_and_item_is_functional():
    f, i = data._load_consumables()
    pill = next(dict(e, key=k) for k in (_key("Sleeping Pill"),)
                for e in [data.consumable_by_key(k)])
    assert data.item_is_functional(pill)                   # was filtered out before
    assert _use("Sleeping Pill", asleep=False).asleep is True


def test_removes_fatigue_clears_fatigue_without_refilling_energy():
    # Bitter Herbs: FatiguedRelieved=TRUE, Energy=0 -> clears fatigue, energy untouched
    p = _use("Bitter Herbs", energy=2, fatigue_length=100.0)
    assert p.fatigue_length == 0.0
    assert p.energy == 2 and p.energy != p.max_energy


def test_food_fatigue_and_depression_columns_are_read():
    f, _ = data._load_consumables()
    by = {e["name"]: e for e in f.values()}
    assert by["Steak"]["unfatigue"] is True                # foods.csv FatiguedRelieved
    assert by["Cake"]["undepressed"] is True               # foods.csv DepressedRelieved
