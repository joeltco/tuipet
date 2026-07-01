"""Battle engine — the authentic DM20 model (see battle.py).

Power (species base + training) plus the Vaccine>Virus>Data triangle (+32) decide the
hit chance; the clash auto-resolves.  record_battle's persistence side effects are
sandboxed by the autouse fixture in conftest.
"""
import random

from tuipet import battle, species
from tuipet.battle import (Battle, beats, effective_power, hit_chance,
                           MAX_HEALTH, ATTR_BONUS)
from tuipet.pet import Pet


def _enemy(stage="Child", power=20, attribute="Data", hp=3, num=-1, boss=False):
    return {"num": num, "name": "Foe", "stage": stage, "attribute": attribute,
            "power": power, "hp": hp, "boss": boss}


def _pet(stage="Child", v=0, d=0, vi=0, attribute="Vaccine", wins=0):
    return Pet(num=-1, stage=stage, vaccine=v, data_power=d, virus=vi,
               attribute=attribute, wins=wins)


# ---- attribute triangle ----------------------------------------------------

def test_triangle_beats():
    assert beats("Vaccine", "Virus") and beats("Virus", "Data") and beats("Data", "Vaccine")
    assert not beats("Vaccine", "Data")          # Vaccine loses to Data
    assert not beats("Free", "Vaccine")          # Free has no advantage
    assert not beats("Vaccine", "Vaccine")


def test_effective_power_bonus():
    assert effective_power(50, "Vaccine", "Virus") == 50 + ATTR_BONUS
    assert effective_power(50, "Vaccine", "Data") == 50          # disadvantage: no bonus
    assert effective_power(50, "Free", "Virus") == 50


def test_hit_chance_scales_and_clamps():
    assert hit_chance(100, 100) == 0.72                          # even power (high base -> most land)
    assert hit_chance(200, 100) > hit_chance(120, 100)           # bigger gap -> more likely
    assert hit_chance(999, 0) == 0.95                            # clamped high
    assert hit_chance(0, 999) == 0.40                            # clamped low


# ---- pet power = species base + training -----------------------------------

def test_pet_power_is_base_plus_training():
    num = next(x["num"] for x in species.roster()
               if x["stage"] == "Child" and x.get("power"))
    p = Pet(num=num, stage="Child")
    p.vaccine, p.data_power, p.virus = 3, 4, 5
    assert p.power == species.base_power(num) + 12


# ---- setup -----------------------------------------------------------------

def test_hp_per_stage():
    assert Battle(_pet("Child"), _enemy()).pet_hp == MAX_HEALTH["Child"]
    assert Battle(_pet("Ultimate"), _enemy()).pet_hp == MAX_HEALTH["Ultimate"]


def test_effective_power_includes_triangle():
    b = Battle(_pet(attribute="Vaccine"), _enemy(attribute="Virus", power=20))
    assert b.pet_ep == b.pet_power + ATTR_BONUS   # Vaccine beats Virus -> +32
    assert b.enemy_ep == b.enemy_power            # Virus does not beat Vaccine


# ---- resolve ---------------------------------------------------------------

def test_resolve_terminates_and_stays_bounded():
    b = Battle(_pet("Adult", v=10), _enemy("Adult", power=60, hp=4))
    attacks = b.resolve(player_first=True, rng=random.Random(7))
    assert b.over and b.won in (True, False)
    assert 0 <= b.pet_hp <= b.pet_max and 0 <= b.enemy_hp <= b.enemy_max
    assert attacks and all(a["dmg"] in (0, 1, 2) for a in attacks)


def test_resolve_is_deterministic_with_seed():
    a1 = Battle(_pet("Child", v=5), _enemy()).resolve(player_first=True, rng=random.Random(99))
    a2 = Battle(_pet("Child", v=5), _enemy()).resolve(player_first=True, rng=random.Random(99))
    assert a1 == a2


def test_ko_ends_the_clash_immediately():
    """Every attack but the last leaves BOTH sides alive -- the bout ends the instant a
    side hits 0 (no attack lands after a KO)."""
    b = Battle(_pet("Adult", v=20), _enemy("Adult", power=50, hp=4))
    b.resolve(player_first=True, rng=random.Random(3))
    for a in b.attacks[:-1]:
        assert a["ph"] > 0 and a["fh"] > 0
    assert b.attacks[-1]["ph"] == 0 or b.attacks[-1]["fh"] == 0


def test_higher_power_usually_wins():
    """Over many seeds a hugely-favoured pet wins the clear majority."""
    wins = 0
    for s in range(40):
        b = Battle(_pet("Ultimate", v=300, attribute="Vaccine"),
                   _enemy("Ultimate", power=20, attribute="Virus", hp=5))
        b.resolve(player_first=True, rng=random.Random(s))
        wins += bool(b.won)
    assert wins >= 34, wins


# ---- win / loss ------------------------------------------------------------

def test_double_ko_is_a_loss():
    b = Battle(_pet(), _enemy())
    b.pet_hp = b.enemy_hp = 0
    b._finish()
    assert b.over and b.won is False


def test_surrender_is_neither_win():
    b = Battle(_pet(), _enemy(boss=True))
    n = b.pet.battles
    b.surrender()
    assert b.over and b.won is False and b.surrendered and b.pet.battles == n + 1
