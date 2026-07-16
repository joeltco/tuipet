"""The checkRefused obedience roll (PhysicalState.checkRefused / refused())."""
import math
from tuipet.pet import Pet, REFUSE_CHANCE
from tuipet import data, jogress


def _pet(**kw):
    p = Pet(num=4, name="Test", stage="Rookie", attribute="Vaccine")
    p.hunger = 0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _meat():
    return next(f for f in data.load_foods() if f["name"] == "Meat")


def test_compliance_skips_roll_and_is_consumed_by_feed():
    p = _pet(compliance=True, obedience=0)
    assert not p.check_refused(food=_meat())        # compliant: never refuses
    msg = p.feed(_meat())
    assert "refuses" not in msg
    assert p.compliance is False                    # checkCompliant spent it...
    assert p.praise_flag                            # ...and opened the praise window


def test_fresh_pet_starts_noncompliant():
    p = Pet(num=4, name="T", stage="Rookie", attribute="Vaccine")
    assert p.compliance is False                    # resetToEgg: _compliance = false


def test_obedient_pet_never_refuses():
    p = _pet(compliance=False, obedience=200)       # >> RefuseChance roll range
    for _ in range(50):
        assert not p.check_refused(food=_meat())
        assert not p.check_refused(attr="Data")
        assert not p.check_refused()


def test_refusal_opens_scold_window():
    p = _pet(compliance=False, obedience=-500)      # force the roll to lose
    assert p.check_refused()
    assert p.scold_flag and p.scold_window == 0     # _scold = true
    assert p.anim == "refuse"


def test_fair_scold_restores_compliance():
    p = _pet(compliance=False, obedience=-500)
    p.check_refused()
    p.scold()
    assert p.compliance is True
    assert not p.check_refused()                    # next command obeyed


def test_fav_food_when_hungry_never_refused():
    p = _pet(compliance=False, obedience=-500, favorite_food="Meat", hunger=0)
    for _ in range(20):
        assert not p.check_refused(food=_meat())


def test_fav_attribute_spirited_never_refuses_training():
    """refused(Attribute) keys on the EMERGENT favourite (training audit
    2026-07-06): canon's Taste inits favourite to None, so the species
    attribute earns no grace until a real taste forms."""
    p = _pet(compliance=False, obedience=-500, enthusiasm=2)
    p.favorite_attr = "Vaccine"                     # the emergent favourite
    for _ in range(20):
        assert not p.check_refused(attr="Vaccine")  # spirited favourite: never
    p.enthusiasm = 0                                # dispirited: the +20 grace line rolls
    assert p.check_refused(attr="Vaccine")
    p2 = _pet(compliance=False, obedience=-500, enthusiasm=2)
    assert not p2.favorite_attr                     # nothing emerged yet...
    assert p2.check_refused(attr="Vaccine")         # ...species attr gets NO pass


def test_energy_shortfall_auto_refuses_jogress():
    p = _pet(compliance=False, obedience=500)       # perfectly obedient...
    p._set_energy(0)
    ec = -jogress.JOGRESS_ENERGY_COST
    assert p.energy + math.ceil(ec * p.max_energy) < 0
    assert p.check_refused(energy_change=ec)        # ...but too tired to fuse


def test_docile_pet_battles_low_disposition_grace():
    # disposition -1 gets the +50 grace: obedience 40 loses to r>=90 only
    p = _pet(compliance=False, obedience=REFUSE_CHANCE, disposition=-1)
    refusals = sum(p.check_refused() for _ in range(50))
    assert refusals == 0                            # obed 100 + 50 grace >= any roll


# ---- travel (canTravel / checkStopTravel) -----------------------------------

def test_compliant_pet_never_stops_walking():
    p = _pet(compliance=True)
    assert not any(p.check_stop_travel() for _ in range(200))


def test_rested_pet_essentially_never_stops():
    # full energy: refuse needs r <= ~(cap - obed + mods), r starts AT cap
    p = _pet(compliance=False, obedience=50)
    stops = sum(p.check_stop_travel() for _ in range(500))
    assert stops == 0


def test_drained_disobedient_pet_plants_its_feet():
    p = _pet(compliance=False, obedience=-200, disposition=1)
    p._set_energy(0)                                # energy_mod ~ 1/max
    assert any(p.check_stop_travel() for _ in range(300))
    assert p.scold_flag and p.anim == "refuse"      # _scold: correct it


def test_travel_refusal_halts_the_journey():
    from tuipet.adventure import Adventure
    p = _pet(compliance=False, obedience=-100000)   # forces the very first fire
    p._set_energy(0)
    adv = Adventure(p)
    ev = adv.travel()
    assert ev == ("refused", None)
    assert adv.location == 0                        # not a single step taken


# ---- refusal recalibration (playability divergence, Joel 2026-07-08) ----------
# A normally-raised pet obeys care commands; a neglected one still visibly
# rebels; and a stride-long walk press is not a coin-flip.  See
# REFUSE_OBEDIENCE_GRACE (pet.py) and the stop_fires note (adventure.py).

def _obey_rate(p, call, n=3000):
    refused = 0
    for _ in range(n):
        p.compliance = False
        if call(p):
            refused += 1
    return 1.0 - refused / n


def test_normally_raised_pet_mostly_obeys_care():
    # obedience 60 (a middling, decently-raised Rookie) obeys the great majority
    # of feeds and drills — the pre-grace rate here was ~40-55% refusal.
    p = _pet(obedience=60, mood=0)
    p._set_energy(p.max_energy)
    assert _obey_rate(p, lambda q: q.check_refused(food=_meat())) >= 0.80
    assert _obey_rate(p, lambda q: q.check_refused(attr="Data")) >= 0.80


def test_neglected_pet_still_rebels():
    # the grace lifts the floor, it does not remove the mechanic: an untrained
    # pet (obedience 0) still refuses a meaningful share of commands.
    p = _pet(obedience=0, mood=0)
    p._set_energy(p.max_energy)
    assert _obey_rate(p, lambda q: q.check_refused(food=_meat())) <= 0.75


def test_walk_press_is_not_a_coin_flip_at_reasonable_energy():
    # a half-energy, middling pet used to refuse ~50% of travel PRESSES because
    # the stop roll composed over the whole ~2250-fire stride; now it composes
    # over WALK_STEP_MIN fires, so a press almost always walks.
    import random
    from tuipet.adventure import Adventure
    random.seed(7)
    p = _pet(compliance=False, obedience=50)
    adv = Adventure(p)
    refused = 0
    for _ in range(300):
        p._set_energy(p.max_energy // 2)            # hold at half energy
        adv.location = 0                            # keep re-pressing from the start
        p.compliance = p.refused = False
        if adv.travel() == ("refused", None):
            refused += 1
    assert refused <= 15                            # << the old ~150/300
