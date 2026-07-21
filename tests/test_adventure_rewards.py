"""Adventure rebuild — REWARDS: bits for conquering (phase 12, 2026-07-20).

Pins the purse: beating a wild pays its small bounty, felling the gate boss pays
its large one, both accrue to the pet's bits and the run tally, and the
homecoming verdict shows the run's take.
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _boss_zone():
    return next(z for z in ZONES if z["bosses"] and z["randoms"])


class _Win:
    won = True


def _panel_at_boss(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=_boss_zone())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            return pan
    raise AssertionError("boss never opened")


def test_award_bits_pays_the_enemy_bounty():
    z = _boss_zone()
    p = _pet()
    p.bits = 0
    a = Adventure(p, zone=z)
    boss = z["bosses"][0]
    lo, hi = boss["bits"]
    amt = a.award_bits(boss)
    assert lo <= amt <= hi                             # within the boss's BitsWon range
    assert p.bits == amt and a.bits_earned == amt      # purse + run tally both move


def test_a_zero_bounty_enemy_pays_nothing():
    a = Adventure(_pet(), zone=_boss_zone())
    assert a.award_bits({"name": "X", "bits": (0, 0)}) == 0
    assert a.bits_earned == 0


def test_bits_accumulate_across_fights():
    z = _boss_zone()
    a = Adventure(_pet(), zone=z)
    w = z["randoms"][0]
    total = a.award_bits(w) + a.award_bits(w) + a.award_bits(z["bosses"][0])
    assert a.bits_earned == total and a.pet.bits == total


def test_felling_the_boss_pays_out_and_the_verdict_shows_it(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    p = pan.pet
    p.bits = 0
    pan.sub = None
    pan._battle_done(_Win())
    lo, hi = pan.adv.boss["bits"]
    assert lo <= p.bits <= hi                           # the boss bounty landed
    assert p.bits == pan.adv.bits_earned
    assert f"+{pan.adv.bits_earned}b" in pan._home_msg  # ...and rides the verdict


def test_a_wild_win_pays_its_bounty_too(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    p = _pet()
    p.bits = 0
    pan = AdventurePanel(p, zone=_boss_zone())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 20):
        pan.anim()
        if pan.sub is not None:                         # a wild fight opened
            break
    assert not pan._fighting_boss                       # a wayside wild, not the gate
    pan.sub = None
    pan._battle_done(_Win())
    assert p.bits > 0 and pan.adv.bits_earned == p.bits
