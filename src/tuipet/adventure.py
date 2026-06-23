"""Adventure mode — travel the Digital World maps, fight wild encounters and
zone bosses (faithful to DVPet's WorldMap: steps, random encounters, a town that
restores adventure life, and a zone boss gating progress to the next zone)."""
from __future__ import annotations
import random
from . import data
from . import loot

LIVES = 3
# Wild-encounter rate. DVPet (Model.Zone.checkBattle) rolls every game-tick:
#   chance = C - (night ? C/NightCoeff : 0) + C/WalkCoeff ; encounter iff
#   Random.nextInt(ceil(chance)) == 0. Adventure travel is "walking" (travelSpeed 1).
# config RandomEncounter*Coefficient: Night 2, Walk 2 (C = RandomEncounterChance 7000).
_C, _NIGHT_COEFF, _WALK_COEFF = 7000.0, 2.0, 2.0
_CHANCE_DAY = _C + _C / _WALK_COEFF                        # 10500
_CHANCE_NIGHT = _C - _C / _NIGHT_COEFF + _C / _WALK_COEFF   # 7000
NIGHT_MULT = _CHANCE_DAY / _CHANCE_NIGHT                    # 1.5x as likely at night
# Per-leg base: a TUI pacing abstraction (DVPet rolls 1/chance per tick; we split a
# zone into LEGS discrete legs). Not a DVPet constant.
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
        if getattr(self.pet, "adv_seek", False):           # Disaster Transport: forced encounter
            self.pet.adv_seek = False
            pool = _real(self.zone["randoms"]) or _real(self.zone["bosses"])
            if pool:
                e = random.choice(pool)
                self.last = f"Ambush! {e['name']}!"
                return ("encounter", e)
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
        chance = ENCOUNTER_CHANCE * (NIGHT_MULT if self.pet.day_phase == "night" else 1.0)
        if self.zone["randoms"] and random.random() < chance:
            e = random.choice(_real(self.zone["randoms"]))
            self.last = f"Wild {e['name']} appeared!"
            return ("encounter", e)
        self.last = f"Travelling... ({self.pct}%)"
        return None

    def resolve(self, won, was_boss, enemy):
        """Apply a battle result to the run, rolling loot on a win."""
        self.loot = None
        if won:
            drop = loot.roll(enemy)
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
