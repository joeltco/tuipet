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
  - encounter chance: Zone.checkBattle rolls on EVERY controller step-fire
    (StepSecondCoefficient = 14/s), while the location advances only once per
    WalkStepMin(9) fires -- so each walked step carries NINE rolls, not one.
    Compound the real per-fire 1/chance over `stride * 9` fires, where chance =
    RandomEncounterChance(7000) +/- the night/walk coefficients (=2): day-walk
    10500, night-walk 7000 (1.5x).  Real pacing: one location step per 9/14s ~=
    0.64s, a 10000-step zone = ~1h47m of device walking with ~8.6 encounters;
    tuipet's 40 actions give the same ~8-9 fights at ~19%/action.
  - travel drain: accrue (stride + WalkEnergyDec) into _energy_dec; on crossing
    TravelEnergyDecMaxCoefficient(80) * fullHP, apply -TravelEnergyDec(1) energy and
    -TravelCalorieDec(1) calories (col0: TravelWeightDec=0, so weight only moves via the
    calorie buffer, same as PhysicalState.setCaloriesAndChangeWeight).
  - towns restore adventure life to MaxAdventureLife(3) (WorldMap.step).
  - a lost battle costs an adventure life; at 0 life, applyLifePenalty retreats the pet
    to the closest town (reset to zone start, life refilled) -- it does NOT end the run.
Towns, bosses and random territories all use the REAL data: towns.csv TownRange
step-spans (rest + encounter suppression inside), enemies.csv Location as each
boss's exact step (multi-boss zones like Piedmon@18000 + Apocalymon@22000 work)
and each random's territory floor (they only roam from their Location onward --
the zone's difficulty curve).  Time gates are all 'None' in this dataset.
"""
from __future__ import annotations
import random
from . import data
from . import loot
from . import persistence as _persist
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
WALK_ENERGY_DEC = 1                  # WalkEnergyDec (accrued per LOCATION step)
WALK_STEP_MIN = 9                    # WalkStepMin: controller fires per location step at walk
# the discover system (Zone.checkInvestigate / checkItem): mid-journey the pet
# may spot something off the path -- investigate for a zone-pool find, at the
# risk that 1 in InvestigateEnemyChance it's an ambush instead
INVESTIGATE_CHANCE = 30000           # InvestigateChance (roll seed, per controller fire)
INVESTIGATE_NIGHT = 15000            # InvestigateNightFactor (rarer at night)
INVESTIGATE_WALK = -5000             # InvestigateWalkFactor (walking spots more)
INVESTIGATE_ENEMY_CHANCE = 3         # InvestigateEnemyChance: nextInt(3)==0 -> ambush
TRAVEL_EXERCISE_LIMIT = 4            # TravelExerciseChangeLimit: walking tops effort up to 4
TRAVEL_EXERCISE_INC = 1              # TravelExerciseInc
# BattleImmunitySeconds 90 (adventure audit 2026-07-06): a WILD win buys ~90
# controller-seconds of no random encounters -- bosses and investigations
# bypass it.  In walked steps: 90s x 14 fires/s / WalkStepMin 9 fires/step.
BATTLE_IMMUNITY_STEPS = 90.0 * 14 / WALK_STEP_MIN

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
        # transport arrival (canon PhysicalState.transport sets the zone's
        # currentLocation): a warp lands AT its destination step, consumed here
        self.location = max(0, min(int(getattr(pet, "adv_loc", 0) or 0), self.total_steps - 1))
        pet.adv_loc = 0
        self.boss_pending = False
        self.done = False
        self.last = "Adventure begins!"
        self.loot = None
        self._energy_dec = 0
        self._rested = set()         # town spans already rested at this pass
        self._cleared = set()        # zone bosses beaten this pass (by enemy num)
        # the CURRENT habitat follows the road (habitat audit 2026-07-06:
        # canon WorldMap.step -> setCurrentHabitat(zone background)) --
        # climate, compatibility odds, the comfort mood and the current-
        # habitat evolution gate all travel with the pet
        if pet.home_habitat < 0:
            pet.home_habitat = pet.habitat        # old-save backfill
        # canon _isHome (teleportArrive toggles it): the pet is OUT while it
        # adventures -- the AI assistant neither bills nor visits away from
        # home (auto-care audit 2026-07-06)
        pet.away = True
        self._set_zone_habitat()

    def _set_zone_habitat(self):
        """setCurrentHabitat(zone.getCurrentLocationBackground())."""
        for lo, hi, hid in self.zone.get("bgs", ()):
            if lo <= self.location <= hi:
                if hid != self.pet.habitat and hid in data.load_habitats():
                    self.pet.habitat = hid
                    self.pet._weather_day = -1    # a fresh sky on the new terrain
                return

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
        return getattr(self.pet, "full_health", 0) or MAX_HEALTH.get(self.pet.stage, MAX_HEALTH_DEFAULT)

    def _save(self):
        self.pet.adv_map, self.pet.adv_zone = self.mi, self.zi

    # --- per-tick mechanics applied over one interactive stride ---
    def _encounter_roll(self):
        """Zone.checkBattle rolls per CONTROLLER FIRE (14/s), 9 fires per walked
        step -- compound the real per-fire 1/chance over stride*WalkStepMin
        fires.  A fresh WILD win suppresses the roll (getBattleImmunity)."""
        if getattr(self, "_immunity_steps", 0.0) > 0:
            return False
        denom = _CHANCE_NIGHT if self.pet.day_phase == "night" else _CHANCE_DAY
        p_none = (1.0 - 1.0 / denom) ** (self.stride * WALK_STEP_MIN)
        return random.random() < (1.0 - p_none)

    def _travel_drain(self):
        """WorldMap.checkEnergyDec: accrue WalkEnergyDec per LOCATION step; on
        crossing 80*fullHP drain energy+calories, and walking tops the effort
        hearts up to TravelExerciseChangeLimit (travel is light training)."""
        self._energy_dec += self.stride * WALK_ENERGY_DEC
        if self._energy_dec >= TRAVEL_ENERGY_DEC_MAX_COEFF * self._full_hp():
            self._energy_dec = 0
            self.pet._set_energy(self.pet.energy - TRAVEL_ENERGY_DEC)
            self._calorie_dec(TRAVEL_CALORIE_DEC)
            if self.pet.strength < TRAVEL_EXERCISE_LIMIT:
                self.pet.strength += TRAVEL_EXERCISE_INC
            # checkSickInj + the disliked-time leg (canon re-audit 2026-07):
            # walking UNWELL sours (-1) and risks worsening (1%); marching
            # through the hated hour costs mood -10 and spirit -1
            if self.pet.sick or self.pet.is_injured() or self.pet.is_fatigued():
                self.pet._set_mood(self.pet.mood - 1)          # WalkUnwellMoodDec
            # checkWorseSick(WalkWorseSickChance 1) rides the BOUND machinery
            # (fatigue pads the target, old age thins the bound) -- and canon
            # rolls it every walk lapse, well or unwell (it no-ops when healthy)
            self.pet._check_worse_sick(1)
            self.pet._check_worse_injury("travel")             # checkWorseTravelInj
            #   (canon rides the BATTLE table with won=True, not the exercise one)
            if self.pet.disliked_time() == self.pet.day_phase:
                self.pet._set_mood(self.pet.mood - 10)         # DislikedTimeTravelMoodChange
                self.pet._set_enthusiasm(self.pet.enthusiasm - 1)  # ...EnthusiasmChange

    def _calorie_dec(self, n):
        """PhysicalState.setCaloriesAndChangeWeight: spend the calorie buffer; when it
        bottoms out, drop a unit of weight and refill (mirrors the metabolism lapse)."""
        from .pet import CALORIE_LIMIT
        self.pet.calories -= n
        if self.pet.calories <= -CALORIE_LIMIT:
            self.pet.weight = max(1, self.pet.weight - 1)
            self.pet.calories = CALORIE_LIMIT

    def _in_town(self, loc):
        return any(lo <= loc <= hi for lo, hi, _t in self.zone.get("towns", ()))

    def _wilds(self, prev=None):
        """Eligible randoms (canon re-audit 2026-07): Enemy.location is a POINT
        territory ([loc,loc] -- checkBattle's location[0] <= cur <= location[1]),
        not a floor.  Location 0 roams the whole zone; a placed random is a SET
        AMBUSHER at its exact step.  Strides cross steps, so a point counts when
        the last stride's span swept it."""
        lo = self.location - self.stride if prev is None else prev
        return [e for e in self.zone["randoms"]
                if e.get("location", 0) == 0
                or lo < e.get("location", 0) <= self.location]

    def _boss_loc(self, b):
        return b.get("location") or self.total_steps     # unplaced boss guards the gate

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
        # WorldMap.step: checkStopTravel rolls per controller fire (9 per walked
        # step, like the encounter roll) -- a refusal halts the journey in place
        # per-fire mechanics compound over the WHOLE stride (stride x WalkStepMin
        # fires), exactly like the encounter roll -- rolling only 9 fires made
        # walk-refusals and discovers ~stride-times rarer than canon (audit 2026-07)
        fires = max(1, self.stride) * WALK_STEP_MIN
        p_stop = self.pet.stop_travel_prob()
        if p_stop > 0 and random.random() < 1.0 - (1.0 - p_stop) ** fires:
            self.pet.stop_travel_effects()
            self.last = f"{self.pet.name} refuses to walk!"
            return ("refused", None)
        # Zone.checkInvestigate: a happier, better-raised pet spots more
        # (obedience+mood SHRINK the seed); night makes finds rarer
        seed = max(1, int(INVESTIGATE_CHANCE + INVESTIGATE_WALK
                          + (INVESTIGATE_NIGHT if self.pet.day_phase == "night" else 0)
                          - (self.pet.obedience + self.pet.mood)))
        if random.random() < 1.0 - (1.0 - 1.0 / seed) ** fires:
            self.last = f"{self.pet.name} noticed something off the path!"
            return ("discover", None)
        prev = self.location
        self.location = min(self.total_steps, self.location + self.stride)
        self._set_zone_habitat()                  # the terrain (and its sky) shifts underfoot
        # the post-battle immunity wears off with the walking
        self._immunity_steps = max(0.0, getattr(self, "_immunity_steps", 0.0) - self.stride)
        self._travel_drain()
        # Bosses stand at their REAL steps (Zone.checkBattle: location[0] == step) --
        # the walk stops AT the first uncleared boss the stride would cross.
        for b in sorted(self.zone["bosses"], key=self._boss_loc):
            bloc = self._boss_loc(b)
            if b["num"] not in self._cleared and prev < bloc <= self.location:
                self.location = bloc
                self.boss_pending = True
                self._boss = b
                self.last = f"Zone boss: {b['name']}!"
                return ("boss", b)
        # Towns at their REAL step-spans (towns.csv TownRange): entering one rests the
        # pet (adventure life + energy, WorldMap.step), and no encounters roll inside.
        for lo, hi, tid in self.zone.get("towns", ()):
            if lo not in self._rested and prev < lo <= self.location:
                self._rested.add(lo)
                self.life = MAX_LIFE
                self.pet._set_energy(self.pet.max_energy)
                self.last = "Reached a town — rested (life + energy)."
                return ("town", tid)
        if self.location >= self.total_steps:              # gate clear, path clear -> done
            return self._advance_or_finish()
        # Wild encounter (real chance formula); towns suppress it, and each random
        # only roams its territory (from its Location step onward).
        here = self._wilds(prev)
        if here and not self._in_town(self.location) and self._encounter_roll():
            e = _pick_weighted(here)
            self.last = f"Wild {e['name']} appeared!"
            return ("encounter", e)
        self.last = f"Travelling... ({self.pct}%)"
        return None

    def flee(self, enemy, was_boss=False):
        """DVPet canEscape success -> WorldMap.lossPenalty(enemy.Penalty): an
        escape is a KNOCKBACK, not a free pass.  This is also what re-arms a
        fled gate boss (prev < bloc <= location can fire again); a penalty-0
        foe still steps back one so a boss can never be skipped by fleeing."""
        back = max(int(enemy.get("penalty", 0)), 1 if was_boss else 0)
        self.location = max(0, self.location - back)
        if was_boss:
            self.location = min(self.location, self._boss_loc(enemy) - 1)
        self.boss_pending = False

    def investigate(self):
        """Zone.checkItem: a uniform draw across the zone's RandomFood +
        RandomItems pools -- then 1 in InvestigateEnemyChance the find is an
        AMBUSH instead.  A carried-home find opens the praise window
        (ReturnItem -> giftEnd -> setPraise)."""
        pool = ([("f", i) for i in self.zone.get("rand_foods", [])]
                + [("i", i) for i in self.zone.get("rand_items", [])])
        found = None
        if pool:
            kind, cid = random.choice(pool)
            e = data.consumable_by_key(f"{kind}:{cid}")
            if e and e.get("can_inc", True):
                found = e
        if random.randrange(INVESTIGATE_ENEMY_CHANCE) == 0:
            found = None
        if found is None:
            e = _pick_weighted(self._wilds()) or _pick_weighted(self.zone["randoms"]) \
                or _pick_weighted(self.zone["bosses"])
            if e:
                self.last = f"An ambush! {e['name']}!"
                return ("enemy", e)
            self.last = "Nothing there after all."
            return (None, None)
        self.pet.add_item(found["key"])
        _persist.shop_unlock_add(found["key"])   # a wild find unlocks its shop listing
        self.pet._open_praise()                  # it brought you something: praise it!
        self.last = f"{self.pet.name} dug up {found['name']}!"   # no article: "a Oats" read wrong
        return ("item", found)

    def _advance_or_finish(self):
        res = self._complete_zone()
        return (res, None) if res else None

    def resolve(self, won, was_boss, enemy):
        """Apply a battle result; roll loot on a win, lose adventure life on a loss."""
        self.loot = None
        if won and not was_boss:
            # setBattleImmunity: a WILD win buys breathing room -- ~90 canon
            # seconds of walking with no random encounters (bosses and
            # investigations bypass it; adventure audit 2026-07-06)
            self._immunity_steps = BATTLE_IMMUNITY_STEPS
        if won:
            drop = loot.roll(enemy)
            if drop:
                self.pet.add_item(drop["key"])
                # canon unlockItem/unlockFood: the drop unlocks its home-shop
                # listing for good (the Digimental progression)
                _persist.shop_unlock_add(drop["key"])
                self.loot = drop
        if was_boss:
            self.boss_pending = False
            if won:
                self._cleared.add(enemy["num"])            # this boss no longer blocks
                self.life = MAX_LIFE                       # a zone-boss win refills adventure life
                if self.location >= self.total_steps:      # the gate boss falls -> zone done
                    res = self._complete_zone()
                    if self.loot:
                        self.last += f"  Loot: {self.loot['name']}!"
                    return res
                self.last = f"{enemy['name']} falls! The path is open."
                if self.loot:
                    self.last += f"  Loot: {self.loot['name']}!"
                return None
            self._lose_life(f"Lost to {enemy['name']}...", enemy.get("penalty", 0))
        elif not won:
            self._lose_life(f"Lost to {enemy['name']}...", enemy.get("penalty", 0))
        else:
            self.last = f"Beat {enemy['name']}!"
            if self.loot:
                self.last += f"  Loot: {self.loot['name']}!"
        return None

    def _lose_life(self, msg, penalty=0):
        """A lost adventure battle costs one adventure life; with life remaining the
        enemy's Penalty knocks the pet BACK that many steps (WorldMap.lossPenalty);
        at 0, applyLifePenalty retreats to the closest town."""
        self.life -= 1
        self.last = msg
        if self.life <= 0:
            self._apply_life_penalty()
        elif penalty > 0:
            self.location = max(0, self.location - penalty)
            self.last = msg + f"  Knocked back {penalty} steps!"

    def _apply_life_penalty(self):
        """WorldMap.applyLifePenalty: toClosestTown() -- retreat to the nearest town at
        or behind the pet (zone start when none), refill life.  Does NOT end the run."""
        behind = [lo for lo, hi, _t in self.zone.get("towns", ()) if lo <= self.location]
        self.location = max(behind) if behind else 0
        self._rested.clear()
        self.life = MAX_LIFE
        self.boss_pending = False
        self.pet._set_energy(self.pet.max_energy)       # regrouped at a town -> rested
        self.last = "Out of life — retreated to town to regroup."

    def _complete_zone(self):
        zones = self.maps[self.mi]["zones"]
        self.location = 0
        self._rested.clear()
        self._cleared.clear()
        if self.zi + 1 < len(zones):
            self.zi += 1
            self.last = "Zone cleared! Onward."
            self._save()
            return "zone"
        from . import persistence
        if self.mi + 1 < len(self.maps):
            persistence.map_complete_add(self.mi)        # this map is cleared
            self.mi += 1
            self.zi = 0
            self.last = "MAP COMPLETE! New region unlocked!"
            self._save()
            return "map"
        persistence.map_complete_add(self.mi)
        for _m in range(len(self.maps)):
            persistence.map_complete_add(_m)             # conquered everything
        self.done = True
        self.last = "You conquered the Digital World!"
        return "all"
