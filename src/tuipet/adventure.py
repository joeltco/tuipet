"""Adventure mode — travel the Digital World maps, fight wild encounters and
zone bosses (faithful to DVPet's WorldMap: steps, random encounters, a town that
restores adventure life, and a zone boss gating progress to the next zone)."""
from __future__ import annotations
import random
from . import data
from . import loot

LIVES = 3
ENCOUNTER_CHANCE = 0.22
LEGS = 24  # travel ticks to cross a zone


def _real(enemies):
    pool = [e for e in enemies if not data.is_placeholder(e["num"])]
    return pool or enemies


class Adventure:
    def __init__(self, pet):
        self.pet = pet
        self.maps = data.load_maps()
        self.mi = max(0, min(getattr(pet, "adv_map", 0), len(self.maps) - 1))
        self.zi = getattr(pet, "adv_zone", 0)
        zones = self.maps[self.mi]["zones"]
        self.zi = max(0, min(self.zi, len(zones) - 1))
        self.progress = 0.0
        self.lives = LIVES
        self.boss_pending = False
        self.done = False
        self.last = "Adventure begins!"
        self.loot = None

    @property
    def zone(self):
        return self.maps[self.mi]["zones"][self.zi]

    @property
    def pct(self):
        return min(100, int(self.progress / LEGS * 100))

    def _save(self):
        self.pet.adv_map, self.pet.adv_zone = self.mi, self.zi

    def travel(self):
        """Advance one leg. Returns ('encounter'|'boss', enemy) or ('town'|None)."""
        if self.boss_pending or self.done:
            return None
        # travelling tires the pet (like exercise)
        self.pet.energy = max(0, self.pet.energy - 2)
        self.pet.weight = max(1, self.pet.weight - 1) if random.random() < 0.3 else self.pet.weight
        self.progress += 1
        if self.progress >= LEGS:
            self.boss_pending = True
            boss = random.choice(_real(self.zone["bosses"]) or _real(self.zone["randoms"]))
            self.last = f"Zone boss: {boss['name']}!"
            return ("boss", boss)
        if self.progress == LEGS // 2:
            self.lives = LIVES
            self.last = "Reached a town — rested!"
            return ("town", None)
        if self.zone["randoms"] and random.random() < ENCOUNTER_CHANCE:
            e = random.choice(_real(self.zone["randoms"]))
            self.last = f"Wild {e['name']} appeared!"
            return ("encounter", e)
        self.last = f"Travelling... ({self.pct}%)"
        return None

    def resolve(self, won, was_boss, enemy):
        """Apply a battle result to the run, rolling loot on a win."""
        self.loot = None
        if won:
            drop = loot.roll(was_boss)
            if drop:
                self.pet.add_item(drop["key"])
                self.loot = drop
        if was_boss:
            self.boss_pending = False
            if won:
                res = self._complete_zone()
                if self.loot:
                    self.last += f"  Loot: {self.loot['name']}!"
                return res
            self.lives -= 1
            self.progress = LEGS * 0.6
            self.last = f"Lost to {enemy['name']}... regrouping."
        else:
            if not won:
                self.lives -= 1
                self.progress = max(0, self.progress - 4)  # penalty steps
                self.last = "Knocked back!"
            else:
                self.last = f"Beat {enemy['name']}!"
                if self.loot:
                    self.last += f"  Loot: {self.loot['name']}!"
        if self.lives <= 0:
            self._retreat()
        return None

    def _complete_zone(self):
        zones = self.maps[self.mi]["zones"]
        self.progress = 0
        if self.zi + 1 < len(zones):
            self.zi += 1
            self.last = "Zone cleared! Onward."
            self._save()
            return "zone"
        if self.mi + 1 < len(self.maps):
            self.mi += 1
            self.zi = 0
            self.last = "MAP COMPLETE! New region unlocked!"
            self._save()
            return "map"
        self.done = True
        self.last = "You conquered the Digital World!"
        return "all"

    def _retreat(self):
        self.lives = LIVES
        self.progress = 0
        self.boss_pending = False
        self.last = "Out of life — retreated to town."
