"""Sickness/injury canon audit pins (2026-07-06) vs DVPet PhysicalState.

Found: the fresh-injury rolls were paraphrases ("overweight -> 50%" for
drills, "loss -> 30%" for battles) -- canon runs a weight x vitamin matrix
vs a 1000 bound plus additive mods (age, fatigue, exhaustion, home, +50 on a
battle LOSS) after EVERY drill and EVERY battle; worse-injury lacked the
additive term and travel wrongly used the exercise table (canon rides the
battle one); the sick rolls ignored the habitat/geriatric BOUND shaping and
the fatigue target pad; intolerant food rolled fresh x2 instead of
worse+fresh once each; injuries didn't sap energy; sick pets didn't burn
nutrition or race the bowels; and incMistake carried no sickness risks."""
import random

from tuipet.pet import (Pet, INJ_BATTLE, SICK_GERIATRIC_FACTOR, FATIGUE_MOD, INJURY_ENERGY_DEC)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _flat_home(monkeypatch):
    monkeypatch.setattr(Pet, "_compat_inj_change", lambda self: 0)


def test_old_age_thins_the_sick_bound(monkeypatch):
    seen = []
    monkeypatch.setattr(random, "randrange", lambda n: seen.append(n) or (n - 1))
    p = _pet()
    p._check_sick(10)
    young_bound = seen[-1]
    old = _pet()
    old.age_seconds = old.lifespan * 2                # deep geriatric
    assert old.is_geriatric
    old._check_sick(10)
    assert seen[-1] == young_bound - SICK_GERIATRIC_FACTOR


