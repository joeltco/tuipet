"""Battle round resolution for the authentic mono v-pet model.

Mono Digital Monster battles have NO attack-effect "chips" (the DVPet Name:Effect:
Condition system came from digimon.csv / colour-device data, absent from the humulos
corpus). A round is simply: each side throws its attribute attack, initiative decides
who strikes first (checkFirst), and damage is the attribute-triangle + strength math
already computed in battle.py. This module keeps only that initiative rule.
"""
from __future__ import annotations
import random


def _check_first(b):
    """Battle.checkFirst: weighted (attack-sum * health-fraction); tie = coin flip."""
    ps = sum(b._pet_counts.values()) * (b.pet_hp / b.pet_max if b.pet_max else 1.0)
    es = sum(b._enemy_counts.values()) * (b.enemy_hp / b.enemy_max if b.enemy_max else 1.0)
    if ps > es:
        return True
    if ps < es:
        return False
    return random.random() < 0.5


def resolve(b, player_attr, enemy_attr, pdmg, edmg):
    """One round: initiative + non-negative damage. No effect chips (authentic mono)."""
    return {
        "pdmg": max(0, pdmg), "edmg": max(0, edmg),
        "enemy_attr": enemy_attr, "player_first": _check_first(b),
        "phc": 0, "ehc": 0, "effect_fired": None,
    }
