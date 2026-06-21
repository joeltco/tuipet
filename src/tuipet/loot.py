"""Loot drops — winning battles out in the Digital World turns up consumables.

Drops come from the same food/item pool the shop sells, split by price into
common / uncommon / rare tiers. Wild wins drop occasionally and favour the
common end; zone bosses always drop and lean rare."""
from __future__ import annotations
import random
from . import data

WILD_DROP_CHANCE = 0.30           # chance a normal wild win yields a drop

_WILD_WEIGHTS = (72, 24, 4)       # (common, uncommon, rare)
_BOSS_WEIGHTS = (20, 40, 40)      # bosses lean rare and always drop


def tiers():
    """Split the consumable pool into (common, uncommon, rare) lists by price."""
    pool = sorted((e for e in data.load_shop() if e.get("key")),
                  key=lambda e: e["price"])
    if not pool:
        return [], [], []
    n = len(pool)
    a, b = max(1, n // 3), max(2, (2 * n) // 3)
    return pool[:a], pool[a:b], pool[b:]


def roll(was_boss):
    """Return a dropped consumable entry, or None when nothing drops."""
    if not was_boss and random.random() > WILD_DROP_CHANCE:
        return None
    groups = tiers()
    weights = _BOSS_WEIGHTS if was_boss else _WILD_WEIGHTS
    choices = [(g, w) for g, w in zip(groups, weights) if g]
    if not choices:
        return None
    tier = random.choices([g for g, _ in choices], weights=[w for _, w in choices])[0]
    return random.choice(tier)
