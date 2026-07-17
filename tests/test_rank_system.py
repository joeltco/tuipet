"""Taste/rank drift canon audit pins (2026-07-06) -- the standing "rank system
unported" deferral, closed.

Already live before this arc: the FOOD ledger (a faithful simplified port) and
the TIME ledger (Joel's tuned adaptation after the misbehaving-ratchet
incident -- kept, with canon's sicken/injure hour-sours added).  Ported here:
the ATTRIBUTE ledger (drills warm, injuries and forced training sour, +-200
emergence feeding the Happy power bonus and the exercise spirit branches),
the WEAK injury tables keyed on the static species aversion, the food
forced-meal decs, and the PERSONALITY TRACKER (childhood energy/weight/mood
tallies re-rolling the temperament at the Champion evolution)."""
import random

from tuipet import data
from tuipet.pet import (Pet, RANK_LIMIT, RANK_INJ_BATTLE_LOST, RANK_TIME_SICK,
                        PCHAMP_RANK, INJ_EXERCISE, INJ_WEAK_EXERCISE)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    p.energy = 10
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- the attribute ledger ---------------------------------------------------------

def test_drills_warm_the_attribute_stage_scaled():
    p = _pet()                                    # Champion: no stage bonus
    p._change_attr_rank("Data")                   # neither pref nor aversion for 102?
    base = p.attr_ranks["Data"]
    q = _pet(stage="Fresh")                       # a pup forms tastes +3 faster
    q._change_attr_rank("Data")
    assert q.attr_ranks["Data"] == base + 3

def test_species_preference_biases_the_drift():
    p = _pet()
    pref = p._phys().get("attr_pref")             # Devimon: Virus
    aver = p._phys().get("attr_aversion")
    p._change_attr_rank(pref)
    p._change_attr_rank(aver)
    assert p.attr_ranks[pref] - p.attr_ranks[aver] == 4   # +2 pref vs -2 aversion bias

def test_a_rank_at_the_limit_becomes_the_emergent_favorite():
    p = _pet()
    p.attr_ranks["Data"] = RANK_LIMIT - 1
    p._change_attr_rank("Data")
    assert p.favorite_attr == "Data"
    p._dec_attr_rank("Data", RANK_LIMIT * 2)      # ...and souring to the floor flips it
    assert p.disliked_attr == "Data" and p.favorite_attr == ""

def test_forced_training_sours_the_attribute():
    p = _pet(strength=0, compliance=True)
    p.apply_training(0, 0, attribute="Data", game="data")   # a failed FORCED drill
    # +change_rank (1, Data is neither pref nor aversion... computed) then -2 forced
    assert p.attr_ranks["Data"] < p._rank_stage_inc() + 3   # net below the warm-only path

def test_a_battle_injury_sours_the_opponents_attribute(monkeypatch):
    monkeypatch.setattr(random, "randrange", lambda n: 0)   # the injury roll hits
    monkeypatch.setattr(Pet, "_compat_inj_change", lambda self: 0)
    p = _pet()
    p._check_battle_injury(won=False, opp_attr="Data")
    assert p.is_injured()
    assert p.attr_ranks["Data"] == -RANK_INJ_BATTLE_LOST

def test_the_emergent_favorite_feeds_the_power_bonus():
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    num = next(n for n, r in by.items()
               if r["attribute"] not in ("Vaccine", "Data", "Virus")
               and r["stage"] == "Champion")
    p = Pet(num=num, name=by[num]["name"], stage="Champion", attribute=by[num]["attribute"])
    p.favorite_attr = "Data"                      # an emergent taste outranks the seed
    assert p._power_bonus_attr() == "Data"


# --- weak injury tables (the static aversion) ---------------------------------------

def test_drilling_the_aversion_rides_the_weak_tables(monkeypatch):
    roll = (INJ_EXERCISE["bad_nv"] + INJ_WEAK_EXERCISE["bad_nv"]) // 2   # 15: between tables
    monkeypatch.setattr(random, "randrange", lambda n: roll)
    monkeypatch.setattr(Pet, "_compat_inj_change", lambda self: 0)
    monkeypatch.setattr(Pet, "_phys", lambda self: {"attr_aversion": "Data"})
    over = lambda p: p._base_weight() + round(p._base_weight() * 0.6)
    safe = _pet(energy=5)
    safe.weight = over(safe)
    safe._check_exercise_injury(attr="Vaccine")   # the normal table: 15 >= 10
    assert not safe.is_injured()
    hurt = _pet(energy=5)
    hurt.weight = over(hurt)
    hurt._check_exercise_injury(attr="Data")      # the AVERSION: 15 < 20
    assert hurt.is_injured()


def test_falling_ill_sours_the_hour():
    p = _pet()
    ph = p.day_phase
    t0 = p.time_pref.get(ph, 0)
    p._sicken()
    assert p.time_pref[ph] == max(-90, t0 - RANK_TIME_SICK)


# --- the personality tracker ---------------------------------------------------------

def test_the_trait_roll_seeds_the_tracker():
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p._rand_personality_traits()
    assert p.mood_rank == p.disposition * PCHAMP_RANK
    assert p.energy_rank == p.restless * PCHAMP_RANK
    assert p.weight_rank == p.glutton * PCHAMP_RANK

def test_childhood_care_is_tallied_but_only_while_young():
    p = Pet(num=1, stage="Rookie", attribute="Vaccine", energy=24, max_energy=24)
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p._tick_mood_discipline(59.0)
    # (the Happy mood_rank leg left with the mood system; energy still tallies)
    assert p.energy_rank == 1
    q = _pet(energy=24, max_energy=24)            # Champion: the tally is closed
    q._tick_mood_discipline(59.0)
    assert q.energy_rank == 0 and q.mood_rank == 0

def test_the_champion_evolution_cashes_in_the_tally():
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    p.mood_rank, p.energy_rank, p.weight_rank = PCHAMP_RANK + 5, -PCHAMP_RANK - 5, 0
    p.disposition, p.restless, p.glutton = -1, 1, 1        # the pup's rolled traits...
    p.evolve_to(102)                                        # ...re-roll at Champion
    assert p.stage == "Champion"
    assert p.disposition == 1                               # kept happy: turns sunny
    assert p.restless == -1                                 # kept drained: turns mellow
    assert p.glutton == 0                                   # middling weight: neutral
