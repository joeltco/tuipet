"""Care actions on a SLEEPING pet: the first press is a disturbance, never the
action (PhysicalState.disturb()).  Canon disturb semantics: the pet WAKES
grumpy -- fully if it's nearly rested (or its energy bar is full), otherwise
its sleep is postponed and it drops back off shortly.  Either way the pressed
action does NOT apply on that press.

A disturb carries its OWN canon side effects (the worse-sick roll and the
wake roll -- pinned in test_mood_system); these tests pin the rolls to their
no-op tails so only the pressed action's effect is measured."""
import random

import pytest

from tuipet.pet import Pet


@pytest.fixture(autouse=True)
def _quiet_rolls(monkeypatch):
    monkeypatch.setattr(random, "randrange", lambda n: n - 1)


def _sleeping(energy=0):
    p = Pet(num=-1, stage="Rookie")
    p.energy = energy
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)                         # falls asleep via the pressure clock
    assert p.asleep
    p.poop = 3            # so clean would otherwise have work to do
    p.sick = True         # so heal would otherwise have work to do
    return p


def test_care_actions_disturb_instead_of_acting():
    # the DSprite rule (item-system clone 2026-07-16): feeding/healing a
    # sleeper DISTURBS it first and then APPLIES -- so feed/heal count the
    # disturb; play/clean still bounce off the sleeper entirely
    for action in ("feed", "heal"):
        p = _sleeping()
        d0 = p.disturb
        getattr(p, action)()
        assert p.disturb == d0 + 1, f"{action} did not disturb"
    for action in ("play", "clean"):
        p = _sleeping()
        sick0, poop0, hunger0 = p.sick, p.poop, p.hunger
        msg = getattr(p, action)()
        assert (p.sick, p.poop, p.hunger) == (sick0, poop0, hunger0), \
            f"{action} applied through the sleep"


def test_disturbing_sleep_costs_mood_and_counts():
    p = _sleeping()
    disturb0 = p.disturb
    p.play()                            # a disturbance, not a game
    assert p.disturb == disturb0 + 1
    # (the DisturbMoodDec assert left with the mood system)
    assert p.sick is True               # heal never fired through the sleep


def test_unrested_disturb_postpones_the_sleep():
    p = _sleeping(energy=0)             # barely slept: not fully-awake material
    p.awake_lapse = 0.0
    p.play()
    assert not p.asleep                 # woken grumpy...
    assert p.sleep_lapse > 0            # ...but bedtime is only postpone-minutes away


def test_care_works_again_once_awake():
    p = _sleeping()
    p.asleep = False
    assert "sleep" not in p.clean().lower()   # poop=3 -> actually cleans now
