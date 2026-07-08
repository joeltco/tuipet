"""Mood-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

Seven structural divergences surfaced by the audit; every fix is pinned here:
sticky-Depressed evolution checks, the raw moodLapse personality nudges + the
stale tier read, the restless-shaded disturb (with sick risks and the wake
roll on EVERY wake, naps included), the depth-scaled negative-energy
penalties + fatigue-on-red, BonusAttributePower, and the discipline-call
lifecycle (answer / placate / ignore)."""
import random

import pytest

from tuipet import data, evolution
from tuipet.pet import (Pet, FULL_HUNGER, DISTURB_MOOD_DEC,
                        BONUS_ATTRIBUTE_POWER, TRAIN_POWER_PER_HIT,
                        DISCIPLINE_CALL_MOOD_PENALTY, DISCIPLINE_CALL_OBED_DEC,
                        NEGATIVE_ENERGY_MOOD_DEC,
                        NEGATIVE_ENERGY_OBEDIENCE_DEC, FATIGUE_MOOD_DEC)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0        # mid-morning, awake
    p.weight = p._base_weight()        # Healthy: no weight lapse term
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- evolution mood requirement: the STICKY tier -----------------------------

def test_evolution_mood_req_uses_the_sticky_tier():
    """checkMoodReq reads getCurrentMood: a deeply-sad pet that never rolled
    into depression is Unhappy (the old threshold tier called it Depressed at
    <= -250 and failed every Mood=Unhappy row); a sticky-Depressed pet stays
    Depressed whatever its score climbed to."""
    reqs = data.load_requirements()
    unhappy_t = next(n for n, r in reqs.items() if r["mood"] == "Unhappy")
    sad = _pet(mood=-260)
    down = _pet(mood=-260, depressed=True)
    assert sad.current_mood() == "Unhappy" and down.current_mood() == "Depressed"
    assert (evolution.fulfilled(sad, unhappy_t)
            == evolution.fulfilled(down, unhappy_t) + evolution.R["mood"])
    happy_t = next(n for n, r in reqs.items() if r["mood"] == "Happy")
    bright = _pet(mood=200)
    stuck = _pet(mood=200, depressed=True)   # depression outran its score
    assert (evolution.fulfilled(bright, happy_t)
            == evolution.fulfilled(stuck, happy_t) + evolution.R["mood"])


# --- moodLapse: raw nudges, stale tier ---------------------------------------

def test_mood_lapse_nudges_take_no_disposition_kicker():
    """Canon applies the glutton/restless drift with raw `_mood +=`; routing
    it through setMood doubled (or zeroed) the +-1 for a +-1-disposition pet.
    Glutton overfed +1 raw, then Happy -10 via setMood (+1 disposition)."""
    p = _pet(mood=200, glutton=1, disposition=1, hunger=FULL_HUNGER + 1)
    p._mood_lapse(59.0)
    assert p.mood == 200 + 1 - 10 + 1

def test_mood_lapse_tier_reads_the_pre_nudge_mood():
    """The tier branch keys on _currentMood as of the last setMood -- BEFORE
    this lapse's raw drift.  A mellow pet at 149 drifts +1 to exactly 150 but
    still lapses as NEUTRAL (-1), not Happy (-10)."""
    p = _pet(mood=149, restless=-1, hunger=3)
    p._mood_lapse(59.0)
    assert p.mood == 149


# --- disturb: restless shading, naps, sick risks, the wake roll --------------

def test_disturb_mood_dec_is_restless_shaded(monkeypatch):
    """DisturbMoodDec{Restless,,NotRestless} = 0/10/20: the restless pet
    WANTED up; the mellow one hates it."""
    for restless, dec in DISTURB_MOOD_DEC.items():
        p = _pet(restless=restless, mood=0, enthusiasm=0, asleep=True)
        monkeypatch.setattr(type(p), "_wake", lambda self: None)
        p._disturbed()
        assert p.mood == -dec, f"restless={restless}"

def test_disturbing_a_nap_wakes_it_without_the_books():
    """Canon keeps the mood/spirit dec and setAsleep(false) OUTSIDE the !nap
    guard: a poked napper wakes and pays the dec, but no disturb count, no
    missed day, no postpone."""
    p = _pet(asleep=True, nap=True, enthusiasm=0)
    d0, m0 = p.disturb, p.mistake_day
    msg = p._disturbed()
    assert msg == "It stirs from its doze."
    assert not p.asleep and not p.nap
    assert p.disturb == d0 and p.mistake_day == m0

def test_the_fifth_disturb_risks_sickness(monkeypatch):
    p = _pet(asleep=True, disturb=4, enthusiasm=0)
    monkeypatch.setattr(random, "randrange", lambda n: 0)
    p._disturbed()
    assert p.sick        # checkSick(DisturbSickChance) from DisturbLimitCheckSick on

def test_a_disturbed_wake_still_rolls_the_morning():
    """Canon disturb() ends in setAsleep(false) -- the morning roll runs on a
    grumbled wake too (the old port skipped it)."""
    anims = set()
    for seed in range(60):
        random.seed(seed)
        p = _pet(asleep=True, mood=200, enthusiasm=0)
        p.energy = p.max_energy          # rested: wakes clean, keeps _wake's anim
        p._disturbed()
        anims.add(p.anim)
    assert {"sad", "happy", "surprise"} <= anims


# --- setEnergy: depth-scaled penalties + fatigue on red ----------------------

def test_energy_drop_into_the_red_scales_and_fatigues(monkeypatch):
    p = _pet(energy=2, obedience=30, mood=0, enthusiasm=0)
    monkeypatch.setattr(type(p), "_energy_bonus_save", lambda self, v: v)
    p._set_energy(-3)
    assert p.energy == -3
    assert p.obedience == 30 - (NEGATIVE_ENERGY_OBEDIENCE_DEC + 3)
    assert p.is_fatigued()               # canon fatigue(false): pushed past empty
    # mood: -(10+3) from setEnergy, then the fatigue's own -50
    assert p.mood == -(NEGATIVE_ENERGY_MOOD_DEC + 3) - FATIGUE_MOOD_DEC

def test_an_injured_pet_is_not_fatigued_by_the_red(monkeypatch):
    p = _pet(energy=1, inj_length=5.0)
    monkeypatch.setattr(type(p), "_energy_bonus_save", lambda self, v: v)
    p._set_energy(-2)
    assert not p.is_fatigued()

def test_fatigue_writes_energy_raw_no_recursion(monkeypatch):
    p = _pet()
    p.energy = -p.max_energy + 1         # already in the red
    monkeypatch.setattr(type(p), "_energy_bonus_save", lambda self, v: v)
    p._set_energy(-p.max_energy - 5)     # would recurse if _fatigue used _set_energy
    assert p.energy == -p.max_energy


# --- BonusAttributePower ------------------------------------------------------

_ENEMY = {"vaccine": 0, "data_power": 0, "virus": 5, "bits": (1, 1),
          "stage": "Champion", "hp": 5}

def test_happy_battle_win_in_the_favoured_attribute_lands_plus_two():
    p = _pet(mood=250, energy=5)
    v0 = p.virus
    msg = p.record_battle(True, enemy=dict(_ENEMY))
    assert p.virus == v0 + 1 + BONUS_ATTRIBUTE_POWER and "+2 Virus" in msg
    q = _pet(mood=0, energy=5)           # Neutral: the standard +1
    v0 = q.virus
    q.record_battle(True, enemy=dict(_ENEMY))
    assert q.virus == v0 + 1

def test_happy_training_in_the_favoured_attribute_doubles_the_award():
    p = _pet(mood=250, strength=0, energy=10)
    v0 = p.virus
    p.apply_training(3, 50, attribute="Virus", game="virus")
    assert p.virus == v0 + 3 * TRAIN_POWER_PER_HIT * (1 + BONUS_ATTRIBUTE_POWER)
    q = _pet(mood=0, strength=0, energy=10)
    v0 = q.virus
    q.apply_training(3, 50, attribute="Virus", game="virus")
    assert q.virus == v0 + 3 * TRAIN_POWER_PER_HIT

def test_none_attribute_pets_favour_their_attribute_preference():
    reqs = data.load_requirements()
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["attribute"] not in ("Vaccine", "Data", "Virus")
                and r["stage"] not in ("Egg", "Fresh", "InTraining")
                and reqs.get(n, {}).get("attr_pref", "None") != "None"), None)
    if num is None:
        pytest.skip("no None-attribute mon with an AttributePreference")
    rec = by[num]
    p = Pet(num=num, name=rec["name"], stage=rec["stage"], attribute=rec["attribute"])
    assert p._power_bonus_attr() == reqs[num]["attr_pref"]
    p.stage = "InTraining"               # the None-branch is gated past InTraining
    assert p._power_bonus_attr() == "None"


# --- the discipline call ------------------------------------------------------

def _tantrum(**kw):
    p = _pet(**kw)
    p.discipline_call = True
    p.scold_flag, p.scold_window, p.compliance = True, 0, False
    return p

def test_scold_answers_the_call():
    p = _tantrum(obedience=10)
    p.scold()
    assert not p.discipline_call
    assert not p.compliance              # scoldDisciplineCall overrides the correct-scold's True
    assert p.obedience > 10              # +ScoldObedienceInc +CorrectScold +DisciplineCallScold(+2)

def test_feeding_placates_the_call(monkeypatch):
    p = _tantrum(obedience=30, hunger=1)
    monkeypatch.setattr(type(p), "check_refused",
                        lambda self, **k: False)
    p.feed(data.load_foods()[0])
    assert not p.discipline_call
    assert not p.scold_flag              # the placate closes the window too
    assert p.obedience == 30 - DISCIPLINE_CALL_OBED_DEC

def test_an_ignored_call_sours_and_marks_the_day():
    # obedience >= DisciplineCallObedienceMax: the re-raise roll is exempt,
    # and the active call FREEZES the mood lapse (checkCall gate) but ALSO
    # DRAINS it (checkCallMinutes -1/window-min; sleep-screens audit
    # 2026-07-06) -- the single 200s chunk lands one drain beside the -25
    from tuipet.pet import CALL_MOOD_DEC
    p = _tantrum(obedience=60, mood=100)
    m0, d0 = p.mood, p.mistake_day
    p._tick_mood_discipline(200.0)       # past _minutesToDisciplinePenalty
    assert not p.discipline_call
    assert p.mistake_day == d0 + 1
    assert p.mood == m0 - DISCIPLINE_CALL_MOOD_PENALTY - CALL_MOOD_DEC

def test_the_call_lights_the_attention_bubble_and_survives_a_save():
    from tuipet import persistence
    p = _tantrum()
    p.scold_flag = False                 # the call alone must light it
    assert p.needs_attention()
    q, _ = persistence.pet_from_save(persistence.to_save_dict(p), catch_up=False)
    assert q.discipline_call
