"""Adventure mode -- a faithful port of DVPet's WorldMap/Zone step-based travel.

DVPet adventure is a slow real-time grind: while travelling the pet steps through a
zone of `TotalSteps` (e.g. 10000), the world rolls a wild-encounter EVERY game-tick
(Zone.checkBattle), travel periodically drains energy/calories past a threshold
(WorldMap.checkEnergyDec), stepping into a town restores adventure life to full
(WorldMap.step), and a zone boss gates progress to the next zone.

A TUI can't run that per-tick over real hours, so the ONE compression here is
INTERACTIVE_STEPS: a zone is crossed in ~40 player travel actions instead of
`TotalSteps` ticks. Each travel action advances `stride = TotalSteps/INTERACTIVE_STEPS`
real steps, and every per-tick mechanic is applied over that stride using the REAL
DVPet constants/formulas (verified in config.csv + WorldMap/Zone bytecode):
  - encounter chance: compound the real per-tick 1/chance over `stride` ticks, where
    chance = RandomEncounterChance(7000) +/- the night/walk coefficients (=2). Day-walk
    = 10500, night-walk = 7000 -> night is exactly 1.5x as likely.
  - travel drain: accrue (stride + WalkEnergyDec) into _energy_dec; on crossing
    TravelEnergyDecMaxCoefficient(80) * fullHP, apply -TravelEnergyDec(1) energy and
    -TravelCalorieDec(1) calories (col0: TravelWeightDec=0, so weight only moves via the
    calorie buffer, same as PhysicalState.setCaloriesAndChangeWeight).
  - towns restore adventure life to MaxAdventureLife(3) (WorldMap.step).
  - a lost battle costs an adventure life; at 0 life, applyLifePenalty retreats the pet
    to the closest town (reset to zone start, life refilled) -- it does NOT end the run.
APPROXIMATION: tuipet's vendored zone data does not carry the town's step-location or the
boss time-gates, so the rest-town is placed at zone midpoint and the zone boss sits at the
end; mid-zone location/time-gated bosses are not yet modelled.
"""
from __future__ import annotations
import random
from . import data
from . import loot
from .battle import MAX_HEALTH, MAX_HEALTH_DEFAULT

# --- DVPet config.csv (column 0), verified ---
MAX_LIFE = 3                         # MaxAdventureLife
ENC_C = 7000.0                       # RandomEncounterChance
NIGHT_COEFF = 2.0                    # RandomEncounterNightCoefficient (-C/coeff)
WALK_COEFF = 2.0                     # RandomEncounterWalkCoefficient  (+C/coeff)
_CHANCE_DAY = ENC_C + ENC_C / WALK_COEFF                       # 10500 -> 1/10500 per tick
_CHANCE_NIGHT = ENC_C - ENC_C / NIGHT_COEFF + ENC_C / WALK_COEFF  # 7000 -> 1/7000 (1.5x day)
TRAVEL_ENERGY_DEC_MAX_COEFF = 80     # TravelEnergyDecMaxCoefficient
TRAVEL_ENERGY_DEC = 1                # TravelEnergyDec
TRAVEL_CALORIE_DEC = 1               # TravelCalorieDec
WALK_ENERGY_DEC = 1                  # WalkEnergyDec (per step-event accrual addend)

# The one TUI compression: interactive travel actions to cross a zone.
INTERACTIVE_STEPS = 40


def _real(enemies):
    pool = [e for e in enemies if not data.is_placeholder(e["num"])]
    return pool or enemies


def _pick_weighted(enemies):
    """Wild-encounter pick weighted by each enemy's AppearanceChance (enemies.csv)."""
    pool = _real(enemies)
    if not pool:
        return None
    weights = [max(1, e.get("chance", 100)) for e in pool]
    return random.choices(pool, weights=weights, k=1)[0]


class Adventure:
    def __init__(self, pet):
        self.pet = pet
        self.maps = data.load_maps()
        self.mi = max(0, min(getattr(pet, "adv_map", 0), len(self.maps) - 1))
        zones = self.maps[self.mi]["zones"]
        self.zi = max(0, min(getattr(pet, "adv_zone", 0), len(zones) - 1))
        self.life = MAX_LIFE
        self.location = 0            # real DVPet step units within the zone (0..total_steps)
        self.boss_pending = False
        self.done = False
        self.last = "Adventure begins!"
        self.loot = None
        self._energy_dec = 0
        self._town_done = False      # the zone's rest-town has been reached this pass

    # --- zone helpers ---
    @property
    def zone(self):
        return self.maps[self.mi]["zones"][self.zi]

    @property
    def total_steps(self):
        return max(1, self.zone.get("total_steps", 10000))

    @property
    def stride(self):
        return max(1, self.total_steps // INTERACTIVE_STEPS)

    @property
    def pct(self):
        return min(100, int(self.location / self.total_steps * 100))

    @property
    def lives(self):                 # the view reads `lives`
        return self.life

    def _full_hp(self):
        return MAX_HEALTH.get(self.pet.stage, MAX_HEALTH_DEFAULT)

    def _save(self):
        self.pet.adv_map, self.pet.adv_zone = self.mi, self.zi

    # --- per-tick mechanics applied over one interactive stride ---
    def _encounter_roll(self):
        """Zone.checkBattle: compound the real per-tick 1/chance over `stride` ticks."""
        denom = _CHANCE_NIGHT if self.pet.day_phase == "night" else _CHANCE_DAY
        p_none = (1.0 - 1.0 / denom) ** self.stride
        return random.random() < (1.0 - p_none)

    def _travel_drain(self):
        """WorldMap.checkEnergyDec: accrue, and on crossing 80*fullHP drain energy+calories."""
        self._energy_dec += self.stride + WALK_ENERGY_DEC
        if self._energy_dec >= TRAVEL_ENERGY_DEC_MAX_COEFF * self._full_hp():
            self._energy_dec = 0
            self.pet._set_energy(self.pet.energy - TRAVEL_ENERGY_DEC)
            self._calorie_dec(TRAVEL_CALORIE_DEC)

    def _calorie_dec(self, n):
        """PhysicalState.setCaloriesAndChangeWeight: spend the calorie buffer; when it
        bottoms out, drop a unit of weight and refill (mirrors the metabolism lapse)."""
        from .pet import CALORIE_LIMIT
        self.pet.calories -= n
        if self.pet.calories <= -CALORIE_LIMIT:
            self.pet.weight = max(1, self.pet.weight - 1)
            self.pet.calories = CALORIE_LIMIT

    def travel(self):
        """Advance one interactive step. Returns ('encounter'|'boss', enemy) or ('town'|None)."""
        if self.boss_pending or self.done:
            return None
        # Disaster Transport: a forced ambush on arrival (kept from the transport hook).
        if getattr(self.pet, "adv_seek", False):
            self.pet.adv_seek = False
            e = _pick_weighted(self.zone["randoms"]) or _pick_weighted(self.zone["bosses"])
            if e:
                self.last = f"Ambush! {e['name']}!"
                return ("encounter", e)
        prev = self.location
        self.location = min(self.total_steps, self.location + self.stride)
        self._travel_drain()
        # Town at zone midpoint restores adventure life to full (WorldMap.step in a town).
        mid = self.total_steps // 2
        if not self._town_done and prev < mid <= self.location:
            self._town_done = True
            self.life = MAX_LIFE
            self.last = "Reached a town -- adventure life restored."
            return ("town", None)
        # Zone boss gates the end of the zone.
        if self.location >= self.total_steps:
            self.boss_pending = True
            boss = _pick_weighted(self.zone["bosses"]) or _pick_weighted(self.zone["randoms"])
            self.last = f"Zone boss: {boss['name']}!"
            return ("boss", boss)
        # Wild encounter (real chance formula).
        if self.zone["randoms"] and self._encounter_roll():
            e = _pick_weighted(self.zone["randoms"])
            self.last = f"Wild {e['name']} appeared!"
            return ("encounter", e)
        self.last = f"Travelling... ({self.pct}%)"
        return None

    def resolve(self, won, was_boss, enemy):
        """Apply a battle result; roll loot on a win, lose adventure life on a loss."""
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
            self._lose_life(f"Lost to {enemy['name']}...")
        elif not won:
            self._lose_life("Knocked back!")
        else:
            self.last = f"Beat {enemy['name']}!"
            if self.loot:
                self.last += f"  Loot: {self.loot['name']}!"
        return None

    def _lose_life(self, msg):
        """A lost adventure battle costs one adventure life; at 0, applyLifePenalty."""
        self.life -= 1
        self.last = msg
        if self.life <= 0:
            self._apply_life_penalty()

    def _apply_life_penalty(self):
        """WorldMap.applyLifePenalty: retreat to the closest town (zone start), refill life.
        Does NOT end the run -- the pet regroups and may press on."""
        self.location = 0
        self._town_done = False
        self.life = MAX_LIFE
        self.boss_pending = False
        self.last = "Out of life -- retreated to town to regroup."

    def _complete_zone(self):
        zones = self.maps[self.mi]["zones"]
        self.location = 0
        self._town_done = False
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
