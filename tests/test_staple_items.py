"""The DVPet staple props (items.csv 81-83), wired 2026-07-17 (Joel: "look at
what dsprite has for items. should be like a toilet, and a few other things").

The items audit found the whole toilet system was DEAD CODE: training needed a
manual visit and no manual path existed, so the starting 100 flushes never
spent and self-toilet never armed.  These tests pin the restored loop."""
from tuipet import shop
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_staples_are_on_the_shelf_and_described():
    cat = {e["key"]: e for e in shop.catalog()}
    assert cat["i:82"]["name"] == "Toilet" and cat["i:82"]["price"] == 1000
    assert cat["i:83"]["name"] == "Port. Potty" and cat["i:83"]["price"] == 100
    assert cat["i:81"]["name"] == "Futon" and cat["i:81"]["price"] == 1000
    for k in ("i:81", "i:82", "i:83"):
        assert shop.effect_line(cat[k]) != "a curiosity"
        assert shop.entry(k) is not None            # the bag can render them


def test_buying_the_toilet_stocks_flushes_and_caps():
    p = _pet(bits=5000)
    msg, sfx = shop.buy(p, shop.entry("i:82"))
    assert sfx == "confirm" and p.inventory["i:82"] == 100
    msg, sfx = shop.buy(p, shop.entry("i:82"))
    assert p.inventory["i:82"] == 199               # csv MaxUses caps the second buy
    msg, sfx = shop.buy(p, shop.entry("i:82"))
    assert sfx == "error" and "stocked" in msg      # full: no bits burned
    assert p.inventory["i:82"] == 199


def test_fixtures_never_resell():
    p = _pet()
    p.add_item("i:82")
    msg, sfx = shop.sell(p, shop.entry("i:82"))
    assert sfx == "error" and p.inventory["i:82"] == 1


def test_manual_visit_trains_during_intraining():
    """The restored training path: one urgent visit while InTraining teaches
    it (MinToiletUsesToTrain 1); a trained Rookie+ then goes by itself."""
    p = Pet(num=100, stage="InTraining", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.add_item("i:82")
    assert "doesn't need to go" in p.use_item("i:82")   # not urgent: refused
    assert p.inventory["i:82"] == 1                     # refusal keeps the flush
    p._poop_t = p._poop_interval * 0.9                  # the urgency window
    out = p.use_item("i:82")
    assert "bowl" in out
    assert p.toilet_trained == 1 and p._poop_t == 0.0
    assert p.inventory.get("i:82", 0) == 0              # the flush spent
    p.stage = "Rookie"
    assert p.is_toilet_trained()


def test_trained_pet_self_toilets_from_stock():
    p = _pet(toilet_trained=1)
    p.add_item("i:82")
    p._poop_t = p._poop_interval - 0.5
    p.tick(1.0)
    assert p.poop == 0                                  # no pile: it went by itself
    assert p.inventory.get("i:82", 0) == 0              # one flush spent
    assert p._toilet_event == "i:82"


def test_futon_tucks_in_a_sleeper_without_disturbing():
    p = _pet()
    p.add_item("i:81")
    assert "bedtime" in p.use_item("i:81")              # awake: pointless, kept
    assert p.inventory["i:81"] == 1
    p.asleep, p.anim = True, "sleep"
    out = p.use_item("i:81")
    assert "Tucked in" in out
    assert p.asleep and p.anim == "sleep"               # the ONE no-disturb item
    assert p.effect_id == 0 and p.effect_t > 0
    assert p.inventory.get("i:81", 0) == 0
    e0 = p.energy
    for _ in range(120):                                # two effect cadences
        p.tick(1.0)
    assert p.energy >= e0                               # the buff feeds the sleeper
    p.asleep = False                                    # stirring ends the tuck-in
    p.tick(1.0)
    assert p.effect_id == -1


def test_gen_one_still_starts_with_the_three_staples():
    egg = Pet.new_egg(generation=1, egg_type=0)
    assert egg.inventory["i:82"] == 100
    assert egg.inventory["i:80"] == 99
    assert egg.inventory["i:81"] == 100
