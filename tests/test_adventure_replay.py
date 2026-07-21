"""REPLAY DIFFICULTY — the veteran road (2026-07-21).

Pins the last board item: re-running a CONQUERED zone makes the same
species fight like trained veterans — through the REAL hit-formula terms
(Side.hit_chance's trainings + winning-record legs), never invented stats
— and pays bounties half again for it.  No new persistence: "conquered"
is the tier.  Zone dicts are shared and cached: the scaling must copy.
"""
from tuipet import adventure
from tuipet.adventure import (Adventure, ZONES, VETERAN_TRAININGS,
                              VETERAN_RECORD)
from tuipet.pet import Pet


def _pet(prog=0):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.adv_progress = prog
    return p


def _wild_zone():
    return next(z for z in ZONES if z["randoms"] and z["bosses"])


def test_only_a_conquered_zone_is_a_veteran_road():
    z = _wild_zone()
    pos = adventure.PROGRESSION.index(adventure.zone_index(z))   # its ROAD stop
    assert not Adventure(_pet(prog=pos), zone=z).replay     # the frontier: fresh
    assert Adventure(_pet(prog=pos + 1), zone=z).replay     # conquered: veteran
    synth = {"name": "T", "scene": "greenhills", "steps": 40,
             "randoms": [], "bosses": [], "town_legs": (), "find_keys": ()}
    assert not Adventure(_pet(prog=26), zone=synth).replay  # unmapped: never


def test_veteran_foes_carry_the_trained_side_and_the_originals_stay_clean():
    z = _wild_zone()
    pos = adventure.PROGRESSION.index(adventure.zone_index(z))
    a = Adventure(_pet(prog=pos + 1), zone=z)
    b = a.boss
    assert b["veteran"] and b is a.boss                     # built once: identity
    s = b["side"]
    assert (s.trainings_cur, s.trainings_total) == VETERAN_TRAININGS
    assert (s.battles, s.wins) == VETERAN_RECORD
    assert "side" not in z["bosses"][0]                     # the shared dict is untouched
    fresh = Adventure(_pet(prog=pos), zone=z)
    assert fresh.boss is z["bosses"][0]                     # fresh runs: verbatim


def test_the_veteran_side_actually_hits_harder():
    from tuipet.battle import Side
    z = _wild_zone()
    num = z["randoms"][0]["num"]
    me = Side.of_pet(_pet())
    plain = Side.wild(num)
    vet = Side.wild(num)
    vet.trainings_cur, vet.trainings_total = VETERAN_TRAININGS
    vet.battles, vet.wins = VETERAN_RECORD
    assert vet.hit_chance(me) > plain.hit_chance(me)        # the REAL formula moves


def test_battle_consumes_the_veteran_side():
    from tuipet.battle import Battle
    z = _wild_zone()
    pos = adventure.PROGRESSION.index(adventure.zone_index(z))
    a = Adventure(_pet(prog=pos + 1), zone=z)
    bt = Battle(_pet(), a.boss)
    assert bt.foe.trainings_cur == VETERAN_TRAININGS[0]     # the side rode in


def test_veteran_bounties_pay_half_again():
    z = _wild_zone()
    pos = adventure.PROGRESSION.index(adventure.zone_index(z))
    a = Adventure(_pet(prog=pos + 1), zone=z)
    a.holiday = None
    a.chain(True)                                           # streak 1: mult 1.0
    assert a.award_bits({"name": "W", "bits": (8, 8)}) == 12   # 8 * 3//2
    f = Adventure(_pet(prog=pos), zone=z)
    f.holiday = None
    f.chain(True)
    assert f.award_bits({"name": "W", "bits": (8, 8)}) == 8    # fresh: unchanged


def test_the_picker_teases_the_veteran_road():
    from tuipet.adventurescreen import ZonePickPanel
    p = _pet(prog=3)                                        # 3 conquered, 4th frontier
    pk = ZonePickPanel(p)
    pk.cursor = 0                                           # a conquered zone
    assert "veteran road" in pk.text().plain
    pk.cursor = len(pk.indices) - 1                         # the frontier
    assert "veteran road" not in pk.text().plain
