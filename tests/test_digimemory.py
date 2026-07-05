"""Inheritance / DigiMemory — DVPet PhysicalState.setNewDigimemory / getDigimemory
(item 32, anim Inherit), ClockTic.onDie's UnlockInheritance gate, applyItem's
full-strength Inherit route; config.csv DigimemoryAttributeCoefficient=0.01,
DigimemoryLifeIncCoefficient=3600 (-> 60 game-sec, the BonusEvolutionLife scale)."""
import json

from tuipet.pet import Pet, DIGIMEMORY_LIFE_INC
from tuipet import data, persistence


def _pet(**kw):
    p = Pet(num=100, name="Gatomon", stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_departed_etches_powers_scaled_by_its_bonus():
    p = _pet(vaccine=500, data_power=300, virus=100, evol_bonus=10)
    mem = p.make_digimemory()
    assert mem["vaccine"] == 50 and mem["data"] == 30 and mem["virus"] == 10   # power*bonus*0.01
    assert mem["seconds"] == 10 * DIGIMEMORY_LIFE_INC                           # a bonus-hour each
    assert mem["name"] == "Gatomon" and mem["num"] == 100
    assert p.evol_bonus == 0                                                    # the bonus is spent


def test_no_bonus_means_no_inheritance():
    p = _pet(vaccine=500, evol_bonus=0)
    assert p.make_digimemory() is None       # onDie only unlocks inheritance with _bonus > 0


def test_the_bank_holds_exactly_one_memory():
    persistence.bank_digimemory({"name": "A", "num": 1, "vaccine": 1, "data": 0, "virus": 0, "seconds": 60.0})
    persistence.bank_digimemory({"name": "B", "num": 2, "vaccine": 2, "data": 0, "virus": 0, "seconds": 60.0})
    assert persistence.peek_digimemory()["name"] == "B"       # overwrite, never a stack
    assert persistence.take_digimemory()["name"] == "B"
    assert persistence.peek_digimemory() is None              # taken -> gone


def test_the_heir_redeems_the_full_payload():
    p = _pet(stage="Rookie")
    p.digimemory = {"name": "Elder", "num": 29, "vaccine": 50, "data": 30, "virus": 10, "seconds": 600.0}
    p.add_item("i:32")
    v0, d0, vi0, l0 = p.vaccine, p.data_power, p.virus, p.lifespan
    msg = p.use_item("i:32")
    assert "Elder" in msg and "Va+50" in msg
    assert (p.vaccine, p.data_power, p.virus) == (v0 + 50, d0 + 30, vi0 + 10)
    assert p.lifespan == l0 + 600.0
    assert not p.digimemory and "i:32" not in p.inventory     # consumed, one use


def test_a_blank_chip_does_nothing():
    p = _pet()
    p.add_item("i:32")
    assert p.use_item("i:32") == "The Digimemory is blank."
    assert "i:32" not in p.inventory


def test_the_digimemory_item_is_functional_but_unsellable():
    e = data.consumable_by_key("i:32")
    assert e["action"] == "Inherit" and data.item_is_functional(e)
    p = _pet()
    p.add_item("i:32")
    assert "can't be resold" in p.sell(e)                     # price 0: the memory has no market


def test_the_held_payload_survives_the_save_round_trip():
    p = _pet()
    p.digimemory = {"name": "Elder", "num": 29, "vaccine": 5, "data": 3, "virus": 1, "seconds": 60.0}
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.digimemory == p.digimemory


def test_memorial_conflict_asks_and_resolves():
    from tuipet.deathscreen import DeathPanel
    old = {"name": "Elder", "num": 29, "vaccine": 5, "data": 0, "virus": 0, "seconds": 60.0}
    new = {"name": "Gatomon", "num": 100, "vaccine": 50, "data": 30, "virus": 10, "seconds": 600.0}
    persistence.bank_digimemory(old)
    p = _pet(dead=True)
    pan = DeathPanel(p, new_mem=new, old_mem=old)
    # box-clip repin 2026-07-04: the memorial prompt rides the strip
    assert "One Digimemory only" in pan.strip()
    assert pan.key("n") is None                               # the prompt gates the memorial keys
    pan.key("e")                                              # etch the new data over the old
    assert persistence.peek_digimemory()["name"] == "Gatomon"
    assert pan.key("n") == ("done", "new")
    # ... and the keep branch
    persistence.bank_digimemory(old)
    pan2 = DeathPanel(p, new_mem=dict(new), old_mem=old)
    pan2.key("k")
    assert persistence.peek_digimemory()["name"] == "Elder"


def test_every_death_records_its_cause_and_the_memorial_tells_it():
    """Death audit 2026-07-05: six ways to die, and _die() recorded none of
    them -- the memorial couldn't say what happened."""
    from tuipet.deathscreen import DeathPanel

    def dead_pet(**kw):
        p = Pet(num=102, name="Devimon", stage="Champion", attribute="Virus")
        p.world_seconds = 12 * 60.0
        for k, v in kw.items():
            setattr(p, k, v)
        return p

    p = dead_pet(hunger=0)
    p._starve_t = 12 * 3600
    p._tick_mortality(1.0)
    assert p.dead and p.death_cause == "starvation"

    p = dead_pet(care_mistakes=20)
    p._tick_mortality(1.0)
    assert p.death_cause == "neglect"

    p = dead_pet(injuries=20)
    p._tick_mortality(1.0)
    assert p.death_cause == "its injuries"

    p = dead_pet(stage="Mega", care_mistakes=5)
    p.stage_seconds = p.LATE_STAGE_WINDOW
    p._tick_mortality(1.0)
    assert p.death_cause == "frailty"

    p = dead_pet()
    p.age_seconds = p.lifespan
    p._tick_mortality(1.0)
    assert p.death_cause == "old age"

    p = dead_pet(sick=True)
    p._malady_t = 360.0
    p._tick_recovery(1.0)
    assert p.dead and p.death_cause == "sickness"

    pan = DeathPanel(p)
    assert "of sickness" in pan.strip()            # the epitaph tells it
