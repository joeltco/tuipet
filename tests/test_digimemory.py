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


def test_the_held_payload_survives_the_save_round_trip():
    p = _pet()
    p.digimemory = {"name": "Elder", "num": 29, "vaccine": 5, "data": 3, "virus": 1, "seconds": 60.0}
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.digimemory == p.digimemory


def test_memorial_conflict_asks_and_resolves():
    """The chained prompts (digimemory audit 2026-07-06): first canon's
    DigiMemory_Validation (etch vs carry the bonus), THEN -- after an etch with
    old data standing -- the only-one choice of which generation survives."""
    from tuipet.deathscreen import DeathPanel
    old = {"name": "Elder", "num": 29, "vaccine": 5, "data": 0, "virus": 0, "seconds": 60.0}
    new = {"name": "Gatomon", "num": 100, "vaccine": 50, "data": 30, "virus": 10, "seconds": 600.0}
    persistence.bank_digimemory(old)
    p = _pet(dead=True)
    pan = DeathPanel(p, new_mem=new, old_mem=old, grade_kept=4)
    assert "etch" in pan.strip() and "bonus" in pan.strip()   # prompt 1: the Validation
    assert pan.key("n") is None                               # the prompt gates the memorial keys
    pan.key("e")                                              # Yes: etch...
    # box-clip repin 2026-07-04: the memorial prompt rides the strip
    assert "Only one" in pan.strip()                          # prompt 2: only one survives
    pan.key("e")                                              # ...the new data over the old
    assert persistence.peek_digimemory()["name"] == "Gatomon"
    assert pan.key("n") == ("done", "new")
    # ... and the keep-the-elder branch
    persistence.bank_digimemory(old)
    pan2 = DeathPanel(p, new_mem=dict(new), old_mem=old, grade_kept=4)
    pan2.key("e")
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

    # (the injuries death cap left with the injury system)

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
    # the epitaph field MARQUEES (menu-bounds 2026-07-07): the cause scrolls
    # through the 22-char window -- roll a full loop and catch it
    seen = ""
    for _ in range(120):
        pan.anim()
        seen += pan.strip()
    assert "of sickness" in seen                   # the epitaph tells it


def test_declining_the_etch_carries_the_bonus():
    """Canon DigiMemory_Validation is a real Yes/No (digimemory audit
    2026-07-06): B declines the etch -- the kept care grade re-banks as the
    heir's seed and the default-banked memory is withdrawn."""
    from tuipet.deathscreen import DeathPanel
    new = {"name": "Gatomon", "num": 100, "vaccine": 50, "data": 30, "virus": 10, "seconds": 600.0}
    persistence.bank_digimemory(new)                 # the app's etch default
    persistence.bank_bonus_seed(2)                   # ...and its spent-grade default
    p = _pet(dead=True)
    pan = DeathPanel(p, new_mem=new, old_mem=None, grade_kept=9, banked_new=True)
    pan.key("b")                                     # No: the bonus carries instead
    assert persistence.peek_digimemory() is None     # the memory was withdrawn
    assert persistence.take_bonus_seed() == 9        # the kept grade replaced the spent one
    assert pan.new_mem is None and "R.I.P." in pan.strip()


def test_a_held_unused_payload_is_device_lifetime(monkeypatch):
    """Canon item 32 + its payload survive resetToEgg.  A pet that dies still
    HOLDING an unspent inheritance re-banks it (the grandchild inherits), and
    the heir never gets a second husk for one payload."""
    from tuipet import app as app_mod
    held = {"name": "Elder", "num": 29, "vaccine": 5, "data": 3, "virus": 1, "seconds": 60.0}
    persistence.bank_digimemory(held)
    heir = Pet.new_egg(generation=3)
    heir.inventory["i:32"] = 1                       # the estate bag carried the husk
    app = app_mod.TuiPetApp.__new__(app_mod.TuiPetApp)
    app._grant_digimemory(heir)
    assert heir.digimemory == held
    assert heir.inventory.get("i:32") == 1           # one payload, ONE chip
    fresh = Pet.new_egg(generation=1)                # no husk in the bag ->
    persistence.bank_digimemory(held)
    app._grant_digimemory(fresh)
    assert fresh.inventory.get("i:32") == 1          # ...the grant supplies it


def test_a_live_retire_banks_the_full_grade():
    """action_new on a LIVING pet (Options -> new egg): canon resetDigimon runs
    careBonusOnReset dead or alive with NO etch offer -- the full adjusted
    bonus seeds the heir (this seed used to be silently lost)."""
    from tuipet import app as app_mod
    persistence.take_bonus_seed()                    # start the slot empty
    p = _pet(care_mistakes=0, mood=200, obedience=100, evol_bonus=3)
    assert not p.dead
    app = app_mod.TuiPetApp.__new__(app_mod.TuiPetApp)
    app.pet = p
    called = {}
    app._open_mode = lambda *a, **k: called.setdefault("open", True)
    app_mod.TuiPetApp.action_new(app)
    assert persistence.take_bonus_seed() == p.final_care_grade()


def test_longevity_truncates_toward_zero():
    """careBonusOnReset's longevity leg: Java long division truncates toward
    ZERO -- a life 0.4 days short loses nothing, not a whole floored day."""
    p = _pet(care_mistakes=0, mood=0, obedience=60, evol_bonus=0)
    p.age_seconds = p._growth_period() - 0.4 * 1440  # 0.4 days short of the curve
    base = p.final_care_grade()
    p.age_seconds = p._growth_period() - 1.4 * 1440  # 1.4 days short: ONE whole day
    assert p.final_care_grade() == max(0, base - 1)
