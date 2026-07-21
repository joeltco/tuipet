"""Adventure — the MARCH engine (rebuild phase 2, 2026-07-20).

⛔ OWN-GAME LAW (Joel 2026-07-13, carried forward): DVPet is NOT canon for
adventures.  One biome per run, start to the goal, no mid-run scenery swap.

Built: the MARCH (cross a zone in ~INTERACTIVE_STEPS travel actions, the journey
on a ribbon, arrival ends the run); WILD ENCOUNTERS (a per-leg roll from the
zone's own enemy table, lives, win/flee/loss/fail); and the real 26-ZONE
GEOGRAPHY -- the zones come from data/zones.csv + enemies.csv (data.load_maps),
each wearing ONE biome (its gate boss's terrain, no mid-zone span-hopping) with
its own wild pool; the zone BOSS FIGHT -- reaching the end opens the gate boss
(resolve_boss), and FELLING it is the real victory (a loss costs a life, 0 lives
fails, a survivable loss lets the pet face it again); TRAVEL DRAIN -- each
marched leg tires (energy), burns the calorie buffer (weight trims toward base)
and tops the effort gauge, so a run comes home spent; TOWNS -- a mid-zone
waypoint refills lives + energy and suppresses encounters; and PROGRESSION --
pet.adv_progress tracks zones conquered (the frontier index); felling a zone's
boss unlocks the next, and the ZonePickPanel lets the player embark on any
unlocked zone; and FINDS -- a marched step may spot loot from the zone's own
table (rand_items/rand_foods) to dig up or pass; the home STATUS CARD (statusbox.adventure_line: Quest
N/26 on the home screen); and TRANSPORT items -- a town warp (Birdra) jumps to
the town and rests, a danger warp (Garuda) dashes toward the boss and gets
ambushed.
"""
from __future__ import annotations
import math
import random
from functools import lru_cache

from . import data
from . import backgrounds

INTERACTIVE_STEPS = 40    # a zone is crossed in ~40 travel actions (the compression
#                           knob the old engine used -- kept as the pacing unit)
MAX_LIVES = 3             # adventure lives (canon MaxAdventureLife): a loss costs one
ENCOUNTER_CHANCE = 0.20   # per leg -- ~8 wild fights over a 40-leg zone (the old
#                           engine's target, reached here with a clean per-leg roll
#                           instead of the per-controller-fire compound -- rebuilt,
#                           not cloned)
FIND_CHANCE = 0.12        # per marched step -- a chance to spot loot on the road
#                           (Zone.checkItem), ~3-4 finds over a zone; the player
#                           digs it up (into the bag) or walks on
HAZARD_CHANCE = 0.06      # per marched step -- an ambush pounce on the road
#                           (arcade arc, Joel 2026-07-21 "do the hazard dodges"):
#                           a zone wild telegraphs and lunges; SPACE ducks it,
#                           eating it costs a small energy toll
HAZARD_ENERGY = 2         # the toll for eating a pounce (a SMALL hit -- the
#                           march drain is 1 per 4 legs for scale)
HOLIDAY_BITS_MULT = 2     # festival purse: bounties pay double on a holiday
HOLIDAY_FIND_MULT = 2     # more loot spills on the road during a festival
POST_FIGHT_GRACE = 1      # legs of encounter immunity after ANY fight (canon
#                           getBattleImmunity on a win, widened so the pet always
#                           takes a clear step between fights -- no same-spot re-jump)
# travel drain (WorldMap.checkEnergyDec, rebuilt clean): the march itself has a
# toll -- it tires (energy), burns the calorie buffer (weight trims toward base),
# and tops the effort gauge (travel is light training).  A drain tick lands every
# few legs so a full zone costs a real chunk of energy without being brutal; the
# old per-fire 80*fullHP threshold is replaced by this leg cadence (own-game).
WALK_DRAIN_EVERY = 4      # a drain tick every N marched legs
TRAVEL_ENERGY_DEC = 1     # energy spent per drain tick
TRAVEL_CALORIE_DEC = 1    # calories burned per drain tick
TRAVEL_EFFORT_CAP = 4     # walking tops the effort gauge (pet.strength) up to here
TOWN_REST_ENERGY = 6      # a town waypoint restores this much energy on top of lives

# the 26 real zones (5 maps: 7/7/3/2/7) are built from data/zones.csv +
# enemies.csv (data.load_maps).  Each run wears ONE biome (own-game law): the
# terrain its GATE BOSS stands in, NOT the mid-zone BackgroundsAndRange scenery
# the device span-hopped through.  habitats.csv habitat id -> a backgrounds.py
# scene key (the old habitat system left with BASIC VPET, so we re-map here):
HABITAT_SCENE = {
    0: "datatunnel",    # Hard Disk -- the net
    1: "mountains",     # Sky -- warm & high; no sky scene, so open mountains
    2: "greenhills",    # Plains
    3: "mountains",     # Canyon -- rugged rock
    4: "forestgate",    # Forest -- the tree path
    5: "frozenpeak",    # Tundra
    6: "islandsea",     # Ocean -- the coast
    7: "lakeside",      # Lake
    8: "underwater",    # Underwater -- the seafloor
    9: "factorynight",  # Evil Castle -- dark iron
    10: "flowerfield",  # Field
    11: "city",         # City
    12: "islandsea",    # Cliffside -- rock over open sea
    13: "greenhills",   # Town (unused as a zone biome, kept for completeness)
    14: "volcano",      # Volcano
    15: "desert",       # Desert
}
DEFAULT_SCENE = "greenhills"


def _boss_biome_hid(zone):
    """The zone's ONE biome habitat id: the terrain its gate boss STANDS in --
    the bgs span holding the boss's Location (bosses gate the zone's end).  No
    boss -> the terrain the pet spends the most steps in (dominant span)."""
    spans = sorted(zone.get("bgs", ()))
    if not spans:
        return None
    bosses = zone.get("bosses", ())
    if bosses:
        bl = max(b.get("location", 0) for b in bosses)
        for lo, hi, hid in spans:
            if lo <= bl <= hi:
                return hid
        return spans[-1][2]                 # past the last span: the gate terrain
    cover = {}
    for lo, hi, hid in spans:
        cover[hid] = cover.get(hid, 0) + max(0, hi - lo)
    return max(cover, key=lambda h: (cover[h], -h))


def _town_legs(z):
    """The zone's town step-spans mapped onto the ~40 interactive legs:
    [(leg_lo, leg_hi, town_id)] -- a mid-zone rest waypoint / visitable hub."""
    ts = max(1, z.get("total_steps", 1))
    out = []
    for lo, hi, tid in z.get("towns", ()):
        a = int(lo / ts * INTERACTIVE_STEPS)
        b = max(a, math.ceil(hi / ts * INTERACTIVE_STEPS))
        out.append((a, min(INTERACTIVE_STEPS - 1, b), tid))
    return out


def _find_keys(z):
    """The zone's discoverable loot as CATALOG keys.  The loot table is authored
    by data id (rand_items -> i:<id>, rand_foods -> f:<id>), but the bag/use
    system speaks CATALOG keys, so each icon is mapped back to its real, usable
    entry (shop.key_for_icon); unmapped loot (nothing the game models) is
    dropped -- finds only ever give items the player can see and use."""
    from . import shop
    icons = ([f"i:{i}" for i in z.get("rand_items", []) if i >= 0]
             + [f"f:{f}" for f in z.get("rand_foods", []) if f >= 0])
    out, seen = [], set()
    for ic in icons:
        k = shop.key_for_icon(ic)
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


@lru_cache(maxsize=1)
def _real_zones():
    """The 26 zones as run-zones: name (its biome + the gate boss that guards
    it), the one biome scene, a uniform ~40-leg crossing, the zone's OWN wild
    pool (its randoms), its town waypoints (leg-ranges that rest + suppress
    encounters), and its discoverable loot pool (find_keys)."""
    out = []
    for mp in data.load_maps():
        for z in mp["zones"]:
            hid = _boss_biome_hid(z)
            scene = HABITAT_SCENE.get(hid, DEFAULT_SCENE)
            label = backgrounds.name(scene)
            bosses = z.get("bosses", [])
            name = f"{bosses[0]['name']}'s {label}" if bosses \
                else f"{label} {z['map']}-{z['zone']}"
            out.append({
                "name": name,
                "scene": scene,
                "steps": INTERACTIVE_STEPS,
                "randoms": z.get("randoms", []),
                "bosses": bosses,
                "town_legs": _town_legs(z),
                "find_keys": _find_keys(z),
                "map": z["map"], "zone": z["zone"],
            })
    return out


# a safe fallback if the world data is missing (pre-setup): one plain zone so
# the panel never crashes on an empty roster.
_FALLBACK_ZONE = {"name": "Green Hills", "scene": DEFAULT_SCENE,
                  "steps": INTERACTIVE_STEPS, "randoms": [], "bosses": [],
                  "town_legs": [], "find_keys": []}
ZONES = tuple(_real_zones()) or (_FALLBACK_ZONE,)


def active_holiday(today=None):
    """Today's festival name (double bits + more finds on the road), or None.
    Reuses the cup's date/holiday cadence -- ONE source for 'what day is it'."""
    from . import tournament
    return tournament.holiday(today)


def pick_zone(pet):
    """A zone when none is chosen (tests, or a default embark): the pet's
    frontier zone -- the newest one it has unlocked.  The zone-pick UI lets the
    player choose any UNLOCKED zone instead (progression phase)."""
    idx = unlocked_indices(pet)
    return ZONES[idx[-1]] if idx else ZONES[0]


# -- progression --------------------------------------------------------------
# pet.adv_progress = zones CONQUERED = the index of the current FRONTIER zone.
# Unlocked = 0..frontier (inclusive); conquered = strictly below the frontier.
def zone_index(zone):
    """The index of a zone dict in the ordered ZONES, or None (a test zone)."""
    try:
        return ZONES.index(zone)
    except ValueError:
        return None


def frontier(pet):
    """The index of the pet's current frontier zone (clamped into range)."""
    return max(0, min(int(getattr(pet, "adv_progress", 0) or 0), len(ZONES) - 1))


def unlocked_indices(pet):
    """The zone indices the pet may embark on: 0..frontier."""
    return list(range(frontier(pet) + 1))


def is_conquered(pet, zi):
    """Has the pet already felled this zone's boss (it sits below the frontier)?"""
    return zi < int(getattr(pet, "adv_progress", 0) or 0)


def is_map_cleared(pet, map_num):
    """Are ALL of a map's zones conquered (every one below the frontier)?  This
    is the profile `maps` signal that unlocks the road shop shelf + eggs."""
    prog = int(getattr(pet, "adv_progress", 0) or 0)
    idxs = [i for i, z in enumerate(ZONES) if z["map"] == map_num]
    return bool(idxs) and all(i < prog for i in idxs)


def record_win(pet, zone):
    """A boss felled: if it was the FRONTIER, the next zone unlocks.  Replaying
    an already-conquered zone advances nothing.  Returns True if a zone unlocked."""
    zi = zone_index(zone)
    prog = int(getattr(pet, "adv_progress", 0) or 0)
    if zi is not None and zi == prog and prog < len(ZONES):
        pet.adv_progress = prog + 1
        return True
    return False


class Adventure:
    """One expedition across one zone.  The march only: `travel()` advances a
    step toward the goal; `done` flips on arrival.  The view reads `name`,
    `scene`, `pct`, `ribbon()` and `last`."""

    def __init__(self, pet, zone=None):
        self.pet = pet
        self.zone = zone if zone is not None else pick_zone(pet)
        self.loc = 0                     # travel actions taken, 0..steps
        self.done = False
        self.failed = False              # 0 lives -> the run is lost (retreat home)
        self.lives = MAX_LIVES
        self._immunity = 0               # legs left before a wild can roll again
        self._drain_acc = 0              # marched-legs accumulator toward a drain tick
        self._resting = False            # currently standing inside a town span
        self.bits_earned = 0             # bits won this run (wild bounties + the boss)
        self.fights = 0                  # fights entered this run (wild + boss)
        self.wins = 0                    # ...of those, won
        self.finds = 0                   # loot dug up this run
        self.holiday = active_holiday()  # a festival today? double bits + more finds
        self.last = f"Setting out for {self.name}."

    @property
    def name(self):
        return self.zone["name"]

    @property
    def scene(self):
        return self.zone["scene"]        # the run's ONE backdrop (own-game law)

    @property
    def total(self):
        return max(1, self.zone["steps"])

    @property
    def pct(self):
        return min(100, int(self.loc / self.total * 100))

    @property
    def boss(self):
        bs = self.zone.get("bosses") or []
        return bs[0] if bs else None       # one gate boss per run (the first listed)

    @property
    def boss_name(self):
        b = self.boss
        return b["name"] if b else self.name

    def ribbon(self, width=14):
        """The journey at a glance -- progress lives HERE, not on the pet, so
        the pet is free to just walk (the old engine's doctrine).  '◆' is you,
        '⚑' the goal, '·' the untrod road."""
        cells = ["·"] * width
        goal = width - 1
        cells[goal] = "⚑"
        pos = min(goal, int(self.loc / self.total * goal))
        cells[pos] = "◆"                 # the pet wins a shared cell (you outrank the goal)
        return "".join(cells)

    # -- wild encounters ------------------------------------------------------
    def _wild_pool(self):
        """The road's wild mons: THIS zone's own random-encounter table
        (enemies.csv, filtered to its map/zone by data.load_maps).  Falls back
        to stage-matched roster enemies only if a zone ships no randoms."""
        pool = [e for e in self.zone.get("randoms", ()) if not e.get("boss")]
        if pool:
            return pool
        return [e for e in data.enemies_for_stage(self.pet.stage) if not e.get("boss")]

    def _in_town(self, loc):
        """Is this leg inside a town waypoint span (rest + no encounters)?"""
        return any(a <= loc <= b for a, b, _t in self.zone.get("town_legs", ()))

    def town_at(self, loc):
        """The town id whose span holds this leg, or None (for the town hub)."""
        for a, b, tid in self.zone.get("town_legs", ()):
            if a <= loc <= b:
                return tid
        return None

    def _roll_encounter(self):
        """A wild enemy this leg, or None.  A town is safe ground (no roll);
        immunity after a fight is spent first; then a per-leg roll, the pick
        weighted by AppearanceChance."""
        if self._in_town(self.loc):
            return None                     # town ground: no wilds
        if self._immunity > 0:
            self._immunity -= 1
            return None
        if random.random() >= ENCOUNTER_CHANCE:
            return None
        pool = self._wild_pool()
        if not pool:
            return None
        weights = [max(1, e.get("chance", 100)) for e in pool]
        return random.choices(pool, weights=weights, k=1)[0]

    # -- transport (in-run warp items) ----------------------------------------
    def _transport_kind(self, key):
        """'town' (Birdra) or 'danger' (Garuda) -- the two CATALOG transports
        that mean something WITHIN a run -- else None.  Zone/Continent warps are
        obsolete: the zone picker replaced worldmap warping."""
        return {"town_transport": "town", "disaster_transport": "danger"}.get(key)

    def held_transports(self):
        """The run-usable transport keys the pet is carrying, in bag order."""
        inv = getattr(self.pet, "inventory", {}) or {}
        return [k for k, n in inv.items() if n > 0 and self._transport_kind(k)]

    def use_transport(self, key):
        """Spend a transport to skip ahead.  Town warp -> jump to the town and
        rest (lives + energy).  Danger warp -> dash toward the boss and get
        ambushed on arrival.  Returns 'town-warp', ('encounter', enemy),
        'danger-warp', or None (not a run transport / not held)."""
        kind = self._transport_kind(key)
        inv = getattr(self.pet, "inventory", {}) or {}
        if kind is None or inv.get(key, 0) <= 0 or self.done or self.failed:
            return None
        self.pet.take_item(key)
        if kind == "town":
            legs = self.zone.get("town_legs") or ()
            if legs:
                self.loc = max(self.loc, legs[0][0])   # forward only, never backward
            self.lives = MAX_LIVES
            self.pet._set_energy(self.pet.energy + TOWN_REST_ENERGY)
            self._resting = self._in_town(self.loc)
            self.last = "Warped to a town — rested up."
            return "town-warp"
        # danger: dash to just shy of the boss gate, then an ambush
        self.loc = max(self.loc, max(0, self.total - 3))
        pool = self._wild_pool()
        if pool:
            weights = [max(1, e.get("chance", 100)) for e in pool]
            enemy = random.choices(pool, weights=weights, k=1)[0]
            self.last = f"Warped ahead — ambushed by {enemy['name']}!"
            return ("encounter", enemy)
        self.last = "Warped ahead."
        return "danger-warp"

    def _roll_find(self):
        """A loot key spotted on the road this step, or None (no finds in a
        town -- the pet is resting, not scavenging)."""
        pool = self.zone.get("find_keys") or ()
        if not pool or self._in_town(self.loc):
            return None
        chance = FIND_CHANCE * (HOLIDAY_FIND_MULT if self.holiday else 1)
        if random.random() >= chance:
            return None
        return random.choice(pool)

    def _roll_hazard(self):
        """An ambush pounce this leg, or None: town ground is safe, and the
        pouncer is one of THIS zone's own wilds (real roster art -- the
        hazard never invents a creature)."""
        if self._in_town(self.loc):
            return None
        if random.random() >= HAZARD_CHANCE:
            return None
        pool = self._wild_pool()
        if not pool:
            return None
        return random.choice(pool)

    def hazard_hit(self):
        """Eat the pounce: the small energy toll.  Single source -- the panel
        reports the missed dodge, the ENGINE applies the cost."""
        self.pet._set_energy(self.pet.energy - HAZARD_ENERGY)
        self.last = "Ambushed on the road!"

    def award_bits(self, enemy):
        """Pay out a beaten enemy's bounty (enemies.csv BitsWon range): a wild
        pays a little, a gate boss pays a lot.  Adds to the pet's purse and the
        run tally, returns the amount."""
        lo, hi = enemy.get("bits") or (1, 5)
        lo, hi = min(lo, hi), max(lo, hi)
        amt = random.randint(lo, hi) if hi > 0 else 0
        if amt and self.holiday:
            amt *= HOLIDAY_BITS_MULT        # festival purse
        if amt:
            self.pet.bits += amt
            self.bits_earned += amt
        return amt

    def resolve(self, won, fled=False):
        """Settle a wild fight.  Every fight grants a grace leg so the next
        step is clear.  won -> march on; fled -> got away, no penalty, no
        progress; lost -> a life, and at 0 lives the run FAILS (retreat home).
        Returns 'won' | 'fled' | 'lost' | 'failed'."""
        self._immunity = max(self._immunity, POST_FIGHT_GRACE)
        if won:
            self.last = "The road clears."
            return "won"
        if fled:
            self.last = f"{self.pet.name} slips away."
            return "fled"
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.failed = True
            self.last = f"Overwhelmed in {self.name}."
            return "failed"
        unit = "life" if self.lives == 1 else "lives"
        self.last = f"Beaten back — {self.lives} {unit} left."
        return "lost"

    # -- travel drain ---------------------------------------------------------
    def _march_drain(self):
        """One marched leg's toll: it tires (energy), burns the calorie buffer
        (weight trims toward the species base when it bottoms out), and tops the
        effort gauge -- travel is light training.  Applied on a leg cadence."""
        from .pet import CALORIE_LIMIT
        self._drain_acc += 1
        if self._drain_acc < WALK_DRAIN_EVERY:
            return
        self._drain_acc = 0
        p = self.pet
        p._set_energy(max(0, p.energy - TRAVEL_ENERGY_DEC))
        p.calories -= TRAVEL_CALORIE_DEC
        if p.calories <= -CALORIE_LIMIT:            # buffer bottomed: shed a weight unit
            p.calories = CALORIE_LIMIT
            p._set_weight(max(p._base_weight(), p.weight - 1))
        if p.strength < TRAVEL_EFFORT_CAP:          # light training tops the effort gauge
            p.strength += 1

    # -- the march ------------------------------------------------------------
    def travel(self):
        """Advance one step down the road -- unless a wild blocks it.  Returns
        ('encounter', enemy) when one fires (no progress that leg), 'arrived'
        on the step that reaches the goal (the run is `done`), 'step'
        otherwise, None if the run is already over."""
        if self.done or self.failed:
            return None
        enemy = self._roll_encounter()
        if enemy is not None:
            self.last = f"A wild {enemy['name']} blocks the road!"
            return ("encounter", enemy)
        self.loc += 1
        self._march_drain()              # the leg's toll: energy / calories / effort
        if self._in_town(self.loc):
            if not self._resting:        # just stepped into a town: rest up
                self._resting = True
                self.lives = MAX_LIVES
                self.pet._set_energy(self.pet.energy + TOWN_REST_ENERGY)
                self.last = f"Reached a town in {self.name} — rested up."
                return "town"
        else:
            self._resting = False
        if self.loc >= self.total:
            self.loc = self.total
            if self.boss is not None:
                # the boss GATES the end -- crossing is not the win, felling it is
                self.last = f"{self.boss_name} guards the gate!"
                return ("boss", self.boss)
            self.done = True             # a bossless zone: the crossing is the win
            self.last = f"{self.name} crossed!"
            return "arrived"
        find = self._roll_find()
        if find is not None:
            self.last = "Something glints on the road."
            return ("find", find)
        haz = self._roll_hazard()
        if haz is not None:
            self.last = "Something rustles ahead!"
            return ("hazard", haz)
        self.last = f"{self.name} — {self.pct}%"
        return "step"

    def resolve_boss(self, won, fled=False):
        """Settle the gate boss.  won -> the zone is CONQUERED (done); fled ->
        turned back at the gate, no victory (not a failure); lost -> a life, and
        at 0 lives the run FAILS; 'retry' keeps the pet at the gate to try
        again.  Returns 'won' | 'fled' | 'lost'... 'retry' | 'failed'."""
        if won:
            self.done = True
            self.last = f"{self.boss_name} felled — {self.name} conquered!"
            return "won"
        if fled:
            self.last = f"Retreated from {self.boss_name}."
            return "fled"
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.failed = True
            self.last = f"{self.boss_name} was too strong."
            return "failed"
        unit = "life" if self.lives == 1 else "lives"
        self.last = f"Knocked back by {self.boss_name} — {self.lives} {unit} left."
        return "retry"
