"""Adventure mode -- tuipet's OWN expedition game over the real zone data.

⛔ OWN-GAME LAW (Joel 2026-07-13): the classic V-pet is NOT canon for adventures.  One
biome per adventure, start to boss -- the run wears the terrain its gate boss
stands in and never swaps scenery mid-run.  The step/encounter/drain MECHANICS
below still run on the real device constants (they are data, and they play
well); the FLOW -- scenery, placements, pacing, beats -- is tuipet's own.

(The original port notes, kept for the mechanics' provenance:)

the classic V-pet adventure is a slow real-time grind: while travelling the pet steps through a
zone of `TotalSteps` (e.g. 10000), the world rolls a wild-encounter EVERY game-tick
(Zone.checkBattle), travel periodically drains energy/calories past a threshold
(WorldMap.checkEnergyDec), stepping into a town restores adventure life to full
(WorldMap.step), and a zone boss gates progress to the next zone.

A TUI can't run that per-tick over real hours, so the ONE compression here is
INTERACTIVE_STEPS: a zone is crossed in ~40 player travel actions instead of
`TotalSteps` ticks. Each travel action advances `stride = TotalSteps/INTERACTIVE_STEPS`
real steps, and every per-tick mechanic is applied over that stride using the REAL
the classic V-pet constants/formulas (verified in config.csv + WorldMap/Zone bytecode):
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

from . import persistence as _persist

# --- the classic V-pet config.csv (column 0), verified ---
MAX_LIFE = 3                         # MaxAdventureLife
ENC_C = 7000.0                       # RandomEncounterChance
NIGHT_COEFF = 2.0                    # RandomEncounterNightCoefficient (-C/coeff)
WALK_COEFF = 2.0                     # RandomEncounterWalkCoefficient  (+C/coeff)
_CHANCE_DAY = ENC_C + ENC_C / WALK_COEFF                       # 10500 -> 1/10500 per tick
# (the 1.5x night encounter rate retired with the day/night system, v0.3.0)
TRAVEL_ENERGY_DEC_MAX_COEFF = 80     # TravelEnergyDecMaxCoefficient
TRAVEL_ENERGY_DEC = 1                # TravelEnergyDec
TRAVEL_CALORIE_DEC = 1               # TravelCalorieDec
WALK_ENERGY_DEC = 1                  # WalkEnergyDec (accrued per LOCATION step)
WALK_STEP_MIN = 9                    # WalkStepMin: controller fires per location step at walk
# the discover system (Zone.checkInvestigate / checkItem): mid-journey the pet
# may spot something off the path -- investigate for a zone-pool find, at the
# risk that 1 in InvestigateEnemyChance it's an ambush instead
INVESTIGATE_CHANCE = 30000           # InvestigateChance (roll seed, per controller fire)
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
# THE EXPEDITION BIOME, per zone -- authored to match each zone's NAME
# (Joel 2026-07-13: "coastlands looking like a castle purple cloud area" --
# span coverage picked Evil Castle for Cliffside Approach; the zone's name IS
# its identity, so the look is authored, not derived).  Habitat ids per
# habitats.csv: 1 Sky, 2 Plains, 3 Canyon, 4 Forest, 5 Tundra, 7 Lake,
# 8 Underwater, 9 Evil Castle, 10 Field, 11 City, 12 Cliffside, 15 Desert.
ZONE_BIOME = {
    (1, 1): 12,   # Cliffside Approach -- the coastal cliffs
    (1, 2): 3,    # Sunken Gorge      -- a gorge is a canyon
    (1, 3): 11,   # Harbor City
    (1, 4): 8,    # The Tide Deep     -- underwater
    (1, 5): 4,    # Seabound Forest
    (1, 6): 11,   # Dock Ward
    (1, 7): 9,    # The Drowned Keep  -- the castle finale
    (2, 1): 2,    # Rust Plains
    (2, 2): 2,    # Coldiron Flats    -- cold iron, still flats
    (2, 3): 7,    # Foundry Lake
    (2, 4): 4,    # Gearwood
    (2, 5): 11,   # Voltage Row
    (2, 6): 12,   # Scrap Bluffs      -- bluffs are cliffs
    (2, 7): 9,    # The Iron Spire
    (3, 1): 2,    # Windmere Plains
    (3, 2): 3,    # Redrock Gorge
    (3, 3): 1,    # Skyfall Pass      -- the Sky ascent
    (4, 1): 3,    # Ashen Canyon
    (4, 2): 9,    # The Black Keep
    (5, 1): 10,   # Verdant Field
    (5, 2): 15,   # Sunscorch Dunes   -- desert
    (5, 3): 7,    # Mirrormere        -- a mere is a lake
    (5, 4): 4,    # Tanglewood
    (5, 5): 5,    # Frostreach        -- tundra
    (5, 6): 4,    # Gloomwood         -- a dark wood is still a wood
    (5, 7): 9,    # Nightmare's End
}

# Diversity floor (Joel 2026-07-13, "a diverse enemy/item/shop/boss system"):
# a zone whose wild roster is thinner than this borrows the map's EARLIER
# wilds -- they roam forward into it (zone 5-3's three Lake natives walk with
# the Field and Desert wilds from the road already travelled).
MIN_WILDS = 6


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


# stage tier per map index: deeper regions field older wilds
_TIER = ("Child", "Adult", "Perfect", "Ultimate-Super Ultimate")


def _recast(e, mi, zi, boss=False):
    """The zone rosters predate the atlas -- recast each foe as a REAL atlas
    species, deterministically (same zone slot -> same face every run):
    stage by the map's tier, bosses one stage up."""
    import random as _r
    from . import data as _d
    ladder = list(_TIER)
    st = ladder[min(mi, len(ladder) - 1)]
    if boss:
        st = ladder[min(mi + 1, len(ladder) - 1)] if mi + 1 < len(ladder)             else "Ultimate-Super Ultimate"
    pool = [r for r in _d.load_sprites()[0] if r["stage"] == st]
    rec = _r.Random(f"{mi}:{zi}:{e.get('num', 0)}:{boss}").choice(pool)
    out = dict(e)
    out["num"], out["name"] = rec["num"], rec["name"]
    out["stage"], out["attribute"] = rec["stage"], rec["attribute"]
    out["boss"] = boss
    return out


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
        # canon _isHome (teleportArrive toggles it): the pet is OUT while it
        # adventures -- the AI assistant neither bills nor visits away from
        # home (auto-care audit 2026-07-06)
        pet.away = True
        # the live run's backref (Life Recovery reads/tops adventure life
        # through it; gated on pet.away so a stale ref after homecoming is
        # inert -- transient, never serialized)
        pet._adventure = self
        self.biome = self._zone_biome()
        self._pad_wilds()

    def _zone_biome(self):
        """One biome per adventure (own-game law): the expedition wears the
        AUTHORED biome of its zone -- ZONE_BIOME, written from each zone's
        name, so Cliffside Approach looks like cliffs and Skyfall Pass like
        the sky (12 distinct biomes across the world).  Unnamed/synthetic
        zones fall back to the dominant span terrain, then the gate span,
        then Plains."""
        habs = data.load_habitats()
        authored = ZONE_BIOME.get((self.maps[self.mi].get("map"),
                                   self.zone.get("zone")))
        if authored in habs:
            return authored
        spans = sorted(self.zone.get("bgs", ()))
        cover = {}
        for lo, hi, hid in spans:
            if hid in habs:
                cover[hid] = cover.get(hid, 0) + (hi - lo)
        if cover:
            return max(cover, key=lambda h: (cover[h], -h))
        gate = next((hid for _lo, _hi, hid in reversed(spans) if hid in habs), None)
        return 2 if gate is None else gate        # Plains when the zone is silent

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

    def ribbon(self, width=17):
        """The zone at a glance -- REAL geography only (legibility arc
        2026-07-07: the engine walked towns.csv spans and enemies.csv boss
        steps while the player saw a bare percentage).  A fixed-width track:
        'T' at each town gate, 'B' at each still-standing boss (a cleared one
        leaves the road), '◆' the pet.  The pet wins a shared cell -- where
        YOU are outranks what stands there (the strip already names it)."""
        cells = ["·"] * width
        scale = lambda step: min(width - 1, max(0, int(step / self.total_steps * width)))
        for lo, _hi, _t in self.zone.get("towns", ()):
            cells[scale(lo)] = "T"
        for b in self.zone["bosses"]:
            if b["num"] not in self._cleared:
                cells[scale(self._boss_loc(b))] = "B"
        cells[scale(self.location)] = "◆"
        return "".join(cells)

    def _full_hp(self):
        return 5                    # the HP race: everyone fights from 5

    def _save(self):
        self.pet.adv_map, self.pet.adv_zone = self.mi, self.zi

    # --- per-tick mechanics applied over one interactive stride ---
    def _encounter_roll(self):
        """Zone.checkBattle rolls per CONTROLLER FIRE (14/s), 9 fires per walked
        step -- compound the real per-fire 1/chance over stride*WalkStepMin
        fires.  A fresh WILD win suppresses the roll (getBattleImmunity)."""
        if getattr(self, "_immunity_steps", 0.0) > 0:
            return False
        denom = _CHANCE_DAY
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
            self.pet.weight = max(1, self.pet.weight - 1)   # the road burns

    def _in_town(self, loc):
        return any(lo <= loc <= hi for lo, hi, _t in self.zone.get("towns", ()))

    def _pad_wilds(self):
        """The MIN_WILDS diversity floor: pad a thin zone's roster with the
        map's earlier roamers (full-zone wanderers, never placed ambushers)."""
        natives = {e["num"] for e in self.zone["randoms"]
                   if not data.is_placeholder(e["num"])}
        extras = []
        if len(natives) < MIN_WILDS:
            for z in self.maps[self.mi]["zones"][:self.zi]:
                for e in z["randoms"]:
                    if e["num"] not in natives and not data.is_placeholder(e["num"]):
                        natives.add(e["num"])
                        extras.append(dict(e, location=0))
                if len(natives) >= MIN_WILDS:
                    break
        self._extra_wilds = extras

    def _wilds(self, prev=None):
        """Eligible randoms (canon re-audit 2026-07): Enemy.location is a POINT
        territory ([loc,loc] -- checkBattle's location[0] <= cur <= location[1]),
        not a floor.  Location 0 roams the whole zone; a placed random is a SET
        AMBUSHER at its exact step.  Strides cross steps, so a point counts when
        the last stride's span swept it."""
        lo = self.location - self.stride if prev is None else prev
        return [e for e in (list(self.zone["randoms"])
                            + list(getattr(self, "_extra_wilds", ())))
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
                e = _recast(e, self.mi, self.zi)
                self.last = f"Ambush! {e['name']}!"
                return ("encounter", e)
        # Discover/encounter mechanics compound per controller fire over the WHOLE
        # stride (stride x WalkStepMin), matching canon's per-tick roll count.
        fires = max(1, self.stride) * WALK_STEP_MIN
        # Zone.checkInvestigate: a happier, better-raised pet spots more
        # (obedience+mood SHRINK the seed); night makes finds rarer
        seed = max(1, int(INVESTIGATE_CHANCE + INVESTIGATE_WALK))
        if random.random() < 1.0 - (1.0 - 1.0 / seed) ** fires:
            self.last = f"{self.pet.name} noticed something off the path!"
            return ("discover", None)
        prev = self.location
        self.location = min(self.total_steps, self.location + self.stride)
        # the post-battle immunity wears off with the walking
        self._immunity_steps = max(0.0, getattr(self, "_immunity_steps", 0.0) - self.stride)
        self._travel_drain()
        # Bosses stand at their REAL steps (Zone.checkBattle: location[0] == step) --
        # the walk stops AT the first uncleared boss the stride would cross.
        # Events resolve in POSITION order (major audit 2026-07-07): a town-start
        # BEFORE the boss in the same stride is reached first, exactly as the
        # per-step canon walks it -- the old boss-first ordering let the town
        # event carry the pet PAST an unfought gate (no shipped zone places the
        # two within one stride today; the guard is for the data's future).
        boss_hit = next(((self._boss_loc(b), b)
                         for b in sorted(self.zone["bosses"], key=self._boss_loc)
                         if b["num"] not in self._cleared
                         and prev < self._boss_loc(b) <= self.location), None)
        town_hit = next(((lo, tid)
                         for lo, hi, tid in sorted(self.zone.get("towns", ()))
                         if lo not in self._rested and prev < lo <= self.location), None)
        if boss_hit and town_hit and town_hit[0] < boss_hit[0]:
            # the town gate comes first: stop AT it (the boss re-arms next stride)
            self.location = town_hit[0]
            boss_hit = None
        if boss_hit:
            bloc, b = boss_hit
            self.location = bloc
            self.boss_pending = True
            b = _recast(b, self.mi, self.zi, boss=True)
            self._boss = b
            self.last = f"Zone boss: {b['name']}!"
            return ("boss", b)
        # Towns at their REAL step-spans (towns.csv TownRange): entering one rests the
        # pet (adventure life + energy, WorldMap.step), and no encounters roll inside.
        if town_hit:
            lo, tid = town_hit
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
            e = _recast(_pick_weighted(here), self.mi, self.zi)
            self.last = f"Wild {e['name']} appeared!"
            return ("encounter", e)
        # A quiet stride narrates REAL state only (legibility arc 2026-07-07 --
        # never invented flavor): the battle-immunity calm (no random rolls
        # while it holds).  One biome per run: no terrain to narrate.
        if getattr(self, "_immunity_steps", 0.0) > 0:
            self.last = f"Calm road… {self.pct}%"    # setBattleImmunity holds
        else:
            self.last = f"Travelling… {self.pct}%"   # 16-18 wide: strip budget (2026-07-07)
        return None

    def flee(self, enemy, was_boss=False):
        """the classic V-pet canEscape success -> WorldMap.lossPenalty(enemy.Penalty): an
        escape is a KNOCKBACK, not a free pass.  This is also what re-arms a
        fled gate boss (prev < bloc <= location can fire again); a penalty-0
        foe still steps back one so a boss can never be skipped by fleeing."""
        back = max(int(enemy.get("penalty", 0)), 1 if was_boss else 0)
        self.location = max(0, self.location - back)
        if was_boss:
            self.location = min(self.location, self._boss_loc(enemy) - 1)
        self.boss_pending = False

    def investigate(self):
        """A find off the path: usually an item from the catalog's cheap
        shelves, sometimes an AMBUSH instead."""
        from . import shop as _shop
        pool = [e for e in _shop.catalog()
                if e["category"] in ("Food", "Care") and e["price"] <= 1000]
        found = random.choice(pool) if pool else None
        if random.randrange(INVESTIGATE_ENEMY_CHANCE) == 0:
            found = None
        if found is None:
            e = _pick_weighted(self._wilds()) or _pick_weighted(self.zone["randoms"]) \
                or _pick_weighted(self.zone["bosses"])
            e = _recast(e, self.mi, self.zi) if e else None
            if e:
                self.last = f"An ambush! {e['name']}!"
                return ("enemy", e)
            self.last = "Nothing there after all."
            return (None, None)
        self.pet.add_item(found["key"])
        rare = " — a RARE find!" if found.get("price", 0) >= 1000 else "!"
        self.last = f"{self.pet.name} dug up {found['name']}{rare}"
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
            purse = 100 + 50 * self.mi + (150 if was_boss else 0)
            self.pet.add_bits(purse)
            self._purse = purse
            if not was_boss and random.random() < 0.10:
                from . import shop as _shop
                pool = [e for e in _shop.catalog() if e["price"] <= 2000]
                if pool:
                    drop = random.choice(pool)
                    self.pet.add_item(drop["key"])
                    self.loot = drop
        if was_boss:
            self.boss_pending = False
            if won:
                self._cleared.add(enemy["num"])            # this boss no longer blocks
                self.life = MAX_LIFE                       # a zone-boss win refills adventure life
                if self.location >= self.total_steps:      # the gate boss falls -> zone done
                    res = self._complete_zone()
                    self.last += self._loot_note()
                    return res
                self.last = f"{enemy['name']} falls! The path is open."
                self.last += self._loot_note()
                return None
            self._lose_life(f"Lost to {enemy['name']}…", enemy.get("penalty", 0))
        elif not won:
            self._lose_life(f"Lost to {enemy['name']}…", enemy.get("penalty", 0))
        else:
            self.last = f"Beat {enemy['name']}!"
            self.last += self._loot_note()
        return None

    def _loot_note(self):
        """The drop's line on the strip -- an expensive drop says RARE instead
        of blending in with every Oats (price tier; sweep 2026-07-14)."""
        note = f"  +{getattr(self, '_purse', 0)}b" if getattr(self, "_purse", 0) else ""
        if self.loot:
            note += f"  Loot: {self.loot['name']}!"
        return note

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
        self.retreated = True     # the view plays Retreat_Town's fade over this
        self.last = "Out of life — retreated to town to regroup."

    def _complete_zone(self):
        zones = self.maps[self.mi]["zones"]
        self.location = 0
        self._rested.clear()
        self._cleared.clear()
        if self.zi + 1 < len(zones):
            self.zi += 1
            self.biome = self._zone_biome()
            self._pad_wilds()
            from . import world
            nm = world.zone_name(self.maps[self.mi]["map"], zones[self.zi]["zone"])
            self.last = f"Zone cleared! On to {nm}."
            self._save()
            return "zone"
        from . import persistence
        if self.mi + 1 < len(self.maps):
            persistence.map_complete_add(self.mi)        # this map is cleared
            self.mi += 1
            self.zi = 0
            self.biome = self._zone_biome()
            self._pad_wilds()
            from . import world
            self.last = f"REGION CLEARED! {world.region_name(self.maps[self.mi]['map'])} unlocked!"
            self._save()
            return "map"
        persistence.map_complete_add(self.mi)
        for _m in range(len(self.maps)):
            persistence.map_complete_add(_m)             # conquered everything
        self.done = True
        self.last = "You conquered the Digital World!"
        return "all"
