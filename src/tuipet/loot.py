"""Loot drops — the classic V-pet loot tables.

Every enemy carries a LootTableID (enemies.csv). Winning a battle rolls that
table once: a single 0..100 draw walks the drop-rate slices in order, and the
slack below 100 is the chance nothing drops. Tables and rates come straight from
the classic V-pet's lootTable.csv + dropRate.csv (see data.load_loot_tables)."""
from __future__ import annotations
import random
from . import data


def roll(enemy):
    """Roll an enemy's loot table once. Returns a consumable entry
    ({key, name, rate}) to award, or None when nothing drops."""
    table = data.load_loot_tables().get((enemy or {}).get("loot_table", -1))
    if not table:
        return None
    r = random.uniform(0.0, 100.0)
    for entry in table:
        if r < entry["rate"]:
            return entry
        r -= entry["rate"]
    return None
