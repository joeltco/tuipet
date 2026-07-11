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
    p.obedience = 500        # out-roll the canon item refusal (audit 2026-07)
    for k, v in pet_kw.items():
        setattr(p, k, v)
    key = _key(name)
    p.add_item(key); p.use_item(key)
    return p


def test_seconds_changes_lifespan():
    """Seconds converts real-sec -> game /60, the SAME rate feed() applies:
    the raw add made a bag-used Gold Pill 60x an eaten one (audit 2026-07-13)."""
    base = Pet.from_num(29).lifespan
    assert _use("Gold Pill").lifespan == base + 43200 / 60   # +12h real = +720
    assert _use("Vitamin").lifespan == base - 3600 / 60      # -1h real = -60


def test_bag_food_still_nudges_bedtime_and_dp():
    """The bag door dropped SleepLapse and the protein DP entirely (audit
    2026-07-13): a Caffeine Pill used from its natural medicine tab changed
    nothing about bedtime, and a strength food banked no DP toward jogress."""
    p = _use("Caffeine Pill", sleep_lapse=100.0)
    assert p.sleep_lapse < 100.0, "the pill must nudge bedtime from the bag"
    f, _ = data._load_consumables()
    protein = next(f"f:{k}" for k, e in f.items() if e.get("strength", 0) > 0)
    q = Pet.from_num(29); q.stage = "Rookie"
    q.obedience = 500; q.dp = 0
    q.add_item(protein); q.use_item(protein)
    assert q.dp == 1, "a strength food banks Pen20 DP from the bag like feed"


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


# ---- canon useItem disturb rule (Joel 2026-07-08) ---------------------------
# PhysicalState.useItem opens with `if (item.disturb()) this.disturb()`: a
# Disturb-flagged item WAKES a sleeping pet before it applies.  items.csv marks
# EVERY item Disturb=TRUE except the Futon (the one sleep aid).  The item still
# lands; the wake is the side effect.

def _futon_key():
    _, i = data._load_consumables()
    return next(f"i:{k}" for k, e in i.items() if e["name"] == "Futon")


def test_disturb_flag_is_plumbed_from_items_csv():
    assert data.consumable_by_key(_key("Ball"))["disturb"] is True
    assert data.consumable_by_key(_futon_key())["disturb"] is False


def test_disturb_item_wakes_a_sleeping_pet_then_applies():
    p = Pet.from_num(29); p.stage = "Rookie"; p.obedience = 500
    p._fall_asleep()
    assert p.asleep
    key = _key("Ball")
    p.add_item(key)
    msg = p.use_item(key)
    assert p.asleep is False                 # canon this.disturb() woke it
    assert "wants nothing" not in msg        # ...and the toy still landed


def test_futon_slides_under_a_sleeper_without_waking_it():
    p = Pet.from_num(29); p.stage = "Rookie"; p.obedience = 500
    p._fall_asleep()
    assert p.asleep
    key = _futon_key()
    p.add_item(key)
    p.use_item(key)
    assert p.asleep is True                   # Disturb=FALSE: the one item that lets it doze
    assert p.effect_id >= 0                    # the futon care buff applied
    assert p.anim != "happy"                   # no grin on a sleeping pet
