"""Adventure — the MARCH engine, rebuilt 2026-10-14 as tuipet's own world.

⛔ OWN-GAME LAW: DVPet is NOT canon for adventures.

30 maps (data/adventure_maps.json, one per scene background), ONE MAP = ONE
RUN: the MARCH (~INTERACTIVE_STEPS travel legs) with WILD ENCOUNTERS from the
map's own pool (its tier, its terrain's fields), hazards and FINDS (food and
care items for the terrain); a TOWN halfway (rest, shop, eggs, bag); and the
BOSS at the end -- felling it clears the map, pays its reward the first time,
and opens the next map (pet.adv_progress = maps cleared).  Lives, the travel
drain, win streaks, veteran replays and the run score ride on top.  Road
items: Life Recovery, Shortcut, Rest Kit.
"""
from __future__ import annotations
import random
from functools import lru_cache

from . import data


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
# THE ENERGY FLOOR LAW (D3 ruling 2026-07-23): a SPEND floors at zero, a
# KNOCK pushes past it.  Marching and battling are exertion the pet chooses
# to pay -- an empty tank can't fund them, so both floor at 0 (_march_drain
# here, record_battle in petbattle.py).  A hazard pounce is DAMAGE -- being
# blindsided can knock the pet past empty (hazard_hit, unfloored), and only
# that: negative energy is what plants its feet (check_stop_travel) and
# strands the run on the refuse strip's outs (T warp / ESC home -- and the
# warp reaches the nearest town in EITHER direction since 2026-07-25, so
# the out is real anywhere on the road, not just before the span).
# REPLAY DIFFICULTY (Joel 2026-07-21 "do the replay difficulty scaling"): a
# CONQUERED zone re-run is a VETERAN ROAD -- the same species fight TRAINED,
# through the real hit-formula terms (Side.hit_chance's trainings + winning-
# record legs, the very ones the pet earns), never invented stats; bounties
# pay half again for it.  No new persistence: "conquered" IS the tier.
VETERAN_TRAININGS = (500, 5000)   # trainings_cur/total: half each trained ceiling
VETERAN_RECORD = (100, 75)        # battles/wins: a 75% career (+wr term)
REPLAY_BITS_NUM, REPLAY_BITS_DEN = 3, 2   # veteran bounties: +50%

# the RUN SCORE (arcade arc, Joel 2026-07-21 "do the run score"): one number
# rolled from the tallies the summary card already shows, so a run can chase
# the zone's standing best (persistence.zone_bests).  Bits ride 1:1 (already
# streak/festival-scaled); the rest weight what the run DID.
SCORE_WIN = 10            # per fight won
SCORE_FIND = 5            # per find dug up
SCORE_LIFE = 25           # per adventure life still held at the end
SCORE_STREAK = 10         # per chained win past the first (the run's best chain)
SCORE_CONQUEST = 100      # the boss fell -- the run's whole point

STREAK_STEP = 0.25        # WIN STREAK (arcade arc, Joel 2026-07-21 "do the win
#                           streak bonus"): each chained win past the first
#                           adds +25% to bounties...
STREAK_CAP = 2.0          # ...capped at DOUBLE (the festival double's scale).
#                           A loss or a flee breaks the chain; so does any town
#                           rest -- and the mid-zone waypoint rests on ARRIVAL,
#                           so every crossing's chain resets there by design
#                           (truthed 2026-07-25: there is no push-on choice at
#                           the waypoint; the cap is earned on the far side).
HOLIDAY_BITS_MULT = 2     # festival purse: bounties pay double on a holiday
HOLIDAY_FIND_MULT = 2     # more loot spills on the road during a festival
FESTIVAL_PRESENT_CHANCE = 0.34   # ...and a third of festival finds are a
#                                  wrapped SURPRISE capsule, not the map's
#                                  loot -- how the road celebrates (kept in
#                                  the 2026-10-14 rebuild, Joel: "3")
# the road's festival present pool: the ten authored capsule boxes -- eight
# honest, two AngrySurprise pranks, identical until opened (that IS the box)
_FESTIVAL_CAPSULES = ("capsule_a", "capsule_b", "capsule_c", "capsule_d",
                      "capsule_e", "capsule_f", "capsule_g", "capsule_h",
                      "prank_capsule_a", "prank_capsule_b")
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
TOWN_REST_ENERGY = 6      # a town rest's top-up when already above half a tank;
#                           the rest itself reaches AT LEAST max_energy // 2
#                           (D1 ruling 2026-07-23 -- see _rest_up)

# ---------------------------------------------------------------------------
# THE WORLD (rebuild 2026-10-14, Joel: "it was built with an older llm ...
# needs to be built from scratch").  The DVPet frame -- 5 maps x 26 zones off
# zones.csv/enemies.csv/towns.csv, auto-named "<boss>'s <biome>" zones, crc32
# signature loot, TVs dug out of the road, warp tickets, town cups -- is gone.
# tuipet's own world is data/adventure_maps.json (built by
# tools/build_adventure_maps.py): 30 maps, ONE PER SCENE BACKGROUND, and ONE
# MAP = ONE RUN -- the march, a town halfway, the boss at the end.  The road
# is the list order; felling a map's boss opens the next.
# ---------------------------------------------------------------------------
DEFAULT_SCENE = "greenhills"
TIERS = ("Rookie", "Champion", "Ultimate", "Mega")
# bounties per enemy STAGE -- the medians of the retired enemies.csv purses,
# so the economy stays where it was
WILD_BITS = {"Rookie": (12, 25), "Champion": (41, 82), "Ultimate": (45, 91),
             "Mega": (50, 93)}
BOSS_BITS = {"Champion": (200, 200), "Ultimate": (750, 750), "Mega": (1500, 1500)}
FINAL_BOSS_BITS = (3000, 3000)        # the last map's gate
FINAL_PARADE_MSG = "You saved the Digital World!"
TOWN_LEG = INTERACTIVE_STEPS // 2 - 1   # the town sits halfway (legs 19-21)
ROAD_ITEMS = ("life_recovery", "shortcut", "rest_kit")
MAPS_PER_AREA = 6   # the profile `maps` signal (eggs, AREA atoms, the road
#                     shelf) speaks 5 areas: area n = the first 6(n+1) maps


def _enemy(num, boss=False, final=False):
    """One road foe as the engine reads it -- a plain species card; the
    battle builds its Side from the dex (Side.wild)."""
    _, by = data.load_sprites()
    rec = by[num]
    stage = rec["stage"]
    if boss:
        bits = FINAL_BOSS_BITS if final else BOSS_BITS.get(stage, BOSS_BITS["Mega"])
    else:
        bits = WILD_BITS.get(stage, WILD_BITS["Rookie"])
    return {"num": num, "name": rec["name"], "stage": stage,
            "attribute": rec["attribute"], "boss": boss, "bits": bits,
            "chance": 100, "loot_table": -1,
            "parade_msg": FINAL_PARADE_MSG if final else ""}


@lru_cache(maxsize=1)
def _load_maps():
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "data", "adventure_maps.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    _, by = data.load_sprites()
    out = []
    for i, m in enumerate(rows):
        final = i == len(rows) - 1
        out.append({
            "index": i,
            "id": m["id"],
            "name": m["name"],
            "scene": m["scene"],
            "tier": m["tier"],
            "steps": INTERACTIVE_STEPS,
            "randoms": [_enemy(n) for n in m["wilds"] if n in by],
            "bosses": [_enemy(m["boss"], boss=True, final=final)],
            "town_legs": [(TOWN_LEG, TOWN_LEG + 2, i)],
            "find_keys": list(m["finds"]),
            "reward": list(m["reward"]),
            "map": i // MAPS_PER_AREA + 1,     # its AREA (1-based)
        })
    return out


_FALLBACK_ZONE = {"index": 0, "id": DEFAULT_SCENE, "name": "Green Hills",
                  "scene": DEFAULT_SCENE, "tier": "Rookie",
                  "steps": INTERACTIVE_STEPS, "randoms": [], "bosses": [],
                  "town_legs": [], "find_keys": [], "reward": [], "map": 1}
MAPS = tuple(_load_maps()) or (_FALLBACK_ZONE,)
ZONES = MAPS          # the engine's older name for the same list
PROGRESSION = tuple(range(len(MAPS)))   # the road IS the list order


def map_tier(i):
    """The tier of map index i (a road town's id IS its map index)."""
    return MAPS[max(0, min(int(i), len(MAPS) - 1))]["tier"]


def active_holiday(today=None):
    """Today's festival name (double bits + more finds on the road), or None.
    Reuses the cup's date/holiday cadence -- ONE source for 'what day is it'."""
    from . import tournament
    return tournament.holiday(today)


def pick_zone(pet):
    """The pet's frontier map -- the newest one unlocked (a default embark;
    the picker lets the player choose any unlocked map)."""
    return MAPS[frontier(pet)]


def zone_index(zone):
    """The index of a map dict, or None (a test zone)."""
    i = zone.get("index") if isinstance(zone, dict) else None
    if isinstance(i, int) and 0 <= i < len(MAPS) and MAPS[i] is zone:
        return i
    try:
        return MAPS.index(zone)
    except ValueError:
        return None


def _progress(pet):
    return max(0, int(getattr(pet, "adv_progress", 0) or 0))


def frontier(pet):
    """The pet's frontier map: the first one not yet cleared (clamped to the
    last)."""
    return min(_progress(pet), len(MAPS) - 1)


def unlocked_indices(pet):
    """The map indices the pet may embark on, in road order."""
    return tuple(range(frontier(pet) + 1))


def is_conquered(pet, zi):
    """Has the pet already felled this map's boss?"""
    return zi is not None and 0 <= zi < _progress(pet)


def _veteran(enemy):
    """A conquered map's foe, replayed: the SAME species carrying a
    trained veteran's Side -- the real hit-formula terms (trainings, a
    winning record), which Battle consumes via enemy['side'].  Returns a
    scaled COPY: map dicts are shared and cached, never mutated."""
    from .battle import Side
    e = dict(enemy)
    s = Side.wild(e.get("num", 0), boss=bool(e.get("boss")))
    s.trainings_cur, s.trainings_total = VETERAN_TRAININGS
    s.battles, s.wins = VETERAN_RECORD
    e["side"] = s
    e["veteran"] = True
    return e


def is_map_cleared(pet, area):
    """Is AREA `area` (1-based, MAPS_PER_AREA maps each) fully cleared?  The
    profile `maps` signal that unlocks eggs, AREA atoms and the road shelf."""
    return area >= 1 and _progress(pet) >= min(len(MAPS), area * MAPS_PER_AREA)


def record_win(pet, zone):
    """A boss felled: if it was the FRONTIER map, the next one unlocks.
    Replaying a cleared map advances nothing.  Returns True if a map
    unlocked."""
    zi = zone_index(zone)
    prog = _progress(pet)
    if zi is not None and zi == prog and prog < len(MAPS):
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
        self.bounty_spent = False        # the replay boss bounty was already claimed today
        self.fights = 0                  # fights entered this run (wild + boss)
        self.wins = 0                    # ...of those, won
        self.finds = 0                   # loot dug up this run
        self.drops = 0                   # battle drops bagged this run (2026-07-26)
        self.streak = 0                  # chained wins alive RIGHT NOW (run-local)
        self.best_streak = 0             # the run's longest chain (the summary line)
        self.holiday = active_holiday()  # a festival today? double bits + more finds
        zi = zone_index(self.zone)
        self.replay = zi is not None and is_conquered(pet, zi)   # a VETERAN road
        self._vboss = None               # the veteran gate boss, built once
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
        b = bs[0] if bs else None          # one gate boss per run (the first listed)
        if b is not None and self.replay:
            if self._vboss is None:        # built once: the gate keeps identity
                self._vboss = _veteran(b)
            return self._vboss
        return b

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
        """The road's wild mons: THIS map's own pool."""
        return [e for e in self.zone.get("randoms", ()) if not e.get("boss")]

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
        # grace is LEGS, not fights dodged: it spends on town ground too,
        # else a pre-town fight banked a bonus free leg on the far side
        # (audit 2026-07-25)
        if self._immunity > 0:
            self._immunity -= 1
            return None
        # the roll guards the leg being WALKED (the destination) -- the
        # same leg find/hazard test after the step.  The old pre-step read
        # made the walk OUT of town encounter-free and the walk IN
        # ambushable on the doorstep, the town's safe ground off by one in
        # one direction only (audit 2026-07-25)
        if self._in_town(self.loc + 1):
            return None                     # town ground: no wilds
        if random.random() >= ENCOUNTER_CHANCE:
            return None
        pool = self._wild_pool()
        if not pool:
            return None
        weights = [max(1, e.get("chance", 100)) for e in pool]
        e = random.choices(pool, weights=weights, k=1)[0]
        return _veteran(e) if self.replay else e

    # -- road items (rebuild 2026-10-14) ----------------------------------------
    # Three tickets, one job each: Life Recovery refills the hearts, the
    # Shortcut jumps to the boss gate (no ambush -- the old Disaster/Zone
    # transports' job), the Rest Kit rests energy to half a tank where you
    # stand (the old Town/Continent transports' job).
    def _transport_kind(self, key):
        return {"life_recovery": "life", "shortcut": "shortcut",
                "rest_kit": "rest"}.get(key)

    def held_transports(self):
        """The road items the pet carries that would DO something right now
        (a menu row that buys nothing is never listed)."""
        inv = getattr(self.pet, "inventory", {}) or {}
        out = []
        for k, n in inv.items():
            kind = self._transport_kind(k)
            if n <= 0 or kind is None:
                continue
            if kind == "life" and self.lives >= MAX_LIVES:
                continue
            if kind == "shortcut" and (self.loc >= self.total or self.boss is None):
                continue
            if kind == "rest" and self.pet.energy >= self.pet.max_energy // 2:
                continue
            out.append(k)
        return out

    def use_transport(self, key):
        """Spend a road item.  Returns 'life-recovery', ('boss', boss) for the
        Shortcut (the gate opens at once), 'rest', or None (not usable)."""
        if key not in self.held_transports() or self.done or self.failed:
            return None
        kind = self._transport_kind(key)
        self.pet.take_item(key)
        if kind == "life":
            self.lives = MAX_LIVES
            self.last = "A second wind — lives restored!"
            return "life-recovery"
        if kind == "rest":
            self.pet._set_energy(self.pet.max_energy // 2)
            self.last = "A short rest by the road."
            return "rest"
        self.loc = self.total
        self._resting = False
        self.last = f"A shortcut — {self.boss_name} guards the gate!"
        return ("boss", self.boss)

    def _roll_find(self):
        """A loot key spotted on the road this step, or None (no finds in a
        town -- the pet is resting, not scavenging)."""
        pool = self.zone.get("find_keys") or ()
        if not pool or self._in_town(self.loc):
            return None
        chance = FIND_CHANCE * (HOLIDAY_FIND_MULT if self.holiday else 1)
        if random.random() >= chance:
            return None
        # a FESTIVAL road present is a capsule: the wrapped box lands in the
        # bag and is opened for its roll (petcare._capsule)
        if self.holiday and random.random() < FESTIVAL_PRESENT_CHANCE:
            return (random.choice(_FESTIVAL_CAPSULES), True)
        # TIERED FIND RARITY (D1, 2026-07-24): the pool used to be a flat
        # random.choice, so a zone's legendary signature turned up exactly as
        # often as its cheapest snack.  Weighted by the same tier ladder the
        # shelves read -- common 8 : uncommon 4 : rare 2 : legendary 1.
        from . import shop
        weights = [shop.tier_weight(k) for k in pool]
        return (random.choices(list(pool), weights=weights, k=1)[0], False)

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
        # the zone's authored AppearanceChance weights, same as the walk
        # and warp picks -- this was the one unweighted draw (audit 2026-07-25)
        weights = [max(1, e.get("chance", 100)) for e in pool]
        return random.choices(pool, weights=weights, k=1)[0]

    def score(self):
        """The run's arcade score, from the tallies the card already shows."""
        return (self.bits_earned
                + SCORE_WIN * self.wins
                + SCORE_FIND * self.finds
                + SCORE_LIFE * self.lives
                + SCORE_STREAK * max(0, self.best_streak - 1)
                + (SCORE_CONQUEST if self.done else 0))

    def _rest_up(self):
        """A town rest, wherever it comes from (waypoint or warp): lives back,
        energy rested to at least HALF the tank (topped by TOWN_REST_ENERGY
        when already above it) -- and the WIN STREAK breaks.  One rest, one
        price, both doors (the waypoint rests on arrival -- there is no
        push-on choice there; truthed 2026-07-25).  (D1 ruling
        2026-07-23: the old flat +6 was one battle's worth -- "rested up" that
        a single fight erased; half a tank makes the words true, and a pet
        KNOCKED past empty warping in comes back standing.)"""
        self.lives = MAX_LIVES
        self.pet._set_energy(max(self.pet.energy + TOWN_REST_ENERGY,
                                 self.pet.max_energy // 2))
        # THE TOWN IS THE ROAD'S SICKBED (audit 2026-07-25): injury is the
        # one ailment a run itself inflicts (fight rolls), and with the
        # clock parked it could never heal -- measured, an ideal pet was 4x
        # likelier to be turned back hurt at the gate than to lose the
        # boss.  A rest patches it, and cures a sickness carried in (the
        # sick trudge's pilgrimage; the home cures are free too, so the
        # town gives away nothing the F menu doesn't).  Mirrors the cure
        # verbs' own writes (petcare pill/bandage) exactly.
        self.pet.sick = False
        self.pet.injured = False
        self.pet.inj_length = 0.0
        self.streak = 0

    def chain(self, won):
        """Advance the WIN STREAK: a chained win grows it (and the run's
        best); a loss or a flee breaks it."""
        if won:
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0

    def streak_mult(self):
        """The chained-win bounty multiplier: +STREAK_STEP per win past the
        first, capped at STREAK_CAP."""
        return min(STREAK_CAP, 1 + STREAK_STEP * max(0, self.streak - 1))

    def hazard_hit(self):
        """Eat the pounce: the small energy toll.  Single source -- the panel
        reports the missed dodge, the ENGINE applies the cost.  UNFLOORED by
        the energy floor law (a KNOCK, not a spend): this is the one road
        source that pushes past empty and trips the planted-feet refusal."""
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
            amt = round(amt * self.streak_mult())   # the chained-win bonus
        if amt and self.replay:
            amt = amt * REPLAY_BITS_NUM // REPLAY_BITS_DEN   # veteran bounty
            if enemy.get("boss"):
                # THE REPLAY BOUNTY IS RATIONED (anti-printer, audit
                # 2026-07-25): a conquered boss pays its veteran purse once
                # per real day per zone -- the town_bought idiom.  Unbounded,
                # the festival x streak x veteran stack paid ~18,000b per
                # repeatable 8-minute run against a 51,677b whole-catalog;
                # every other earner is rationed (cup: the hour; town rows:
                # the daily cap; raid: attempts).  Wilds still pay, and a
                # FIRST conquest is untouched.
                from . import shop
                zi = zone_index(self.zone)
                if zi is not None:
                    day = shop._today_ordinal()
                    led = dict(getattr(self.pet, "road_bounty", None) or {})
                    if led.get("day") != day:
                        led = {"day": day}
                    if led.get(str(zi)):
                        amt, self.bounty_spent = 0, True
                    else:
                        led[str(zi)] = 1
                    self.pet.road_bounty = led
        if amt:
            self.pet.bits += amt
            self.bits_earned += amt
        return amt

    def award_drop(self, enemy):
        """THE BOSS REWARD (rebuild 2026-10-14): a map's boss hands over the
        map's reward items -- once, on the FIRST conquest (a replayed map
        pays bits only, so the deep maps' spirits and chips can't be
        farmed).  Wilds drop nothing; the road's loot is its finds.
        Returns the granted catalog keys (possibly empty)."""
        if not enemy.get("boss") or self.replay:
            return []
        got = []
        for key in self.zone.get("reward") or ():
            self.pet.add_item(key)
            self.drops += 1
            got.append(key)
        return got

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
        if getattr(p, "tonic_lapse", 0.0) <= 0:         # Gold Pill: spends are free
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
        if self.pet.check_stop_travel():
            # canTravel (restored 2026-07-21): a pet pushed PAST EMPTY plants
            # its feet -- today's deliberately-soft calibration (petcare:
            # negative energy only), NEVER the old chance-based refusal
            self.last = f"{self.pet.name} refuses to walk!"
            return ("refused", None)
        enemy = self._roll_encounter()
        if enemy is not None:
            self.last = f"A wild {enemy['name']} blocks the road!"
            return ("encounter", enemy)
        self.loc += 1
        self._march_drain()              # the leg's toll: energy / calories / effort
        if self._in_town(self.loc):
            if not self._resting:        # just stepped into a town: rest up
                self._resting = True
                self._rest_up()
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
        # DANGER ROLLS BEFORE TREASURE (audit 2026-07-25): the find used to
        # shadow the hazard, so doubling FIND_CHANCE on a festival quietly
        # cut ambushes ~14% -- a festival must never make the road SAFER
        haz = self._roll_hazard()
        if haz is not None:
            self.last = "Something rustles ahead!"
            return ("hazard", haz)
        find = self._roll_find()
        if find is not None:
            key, present = find
            self.last = ("A present sits on the road!" if present
                         else "Something glints on the road.")
            return ("find", key, present)
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
