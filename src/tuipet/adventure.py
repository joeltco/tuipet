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
waypoint refills lives, rests energy to at least half the tank and suppresses
encounters; and PROGRESSION --
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
SKIP_LEGS = 10            # the Zone Transport's safe lift (expansion 2026-07-26)
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
#                                  wrapped SURPRISE from the gift pool, not the
#                                  zone's loot -- home gifts are home-only, so
#                                  this is how the road celebrates (2026-07-24)
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
        # the GATE boss (bosses[0] -- the one Adventure.boss actually
        # fights), NOT max(location): zone 6 carries a second, unreachable
        # boss (Apocalymon) whose span sat past Piedmon's, so the run wore
        # a biome its own gate boss never stands in (audit 2026-07-25)
        bl = bosses[0].get("location", 0)
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


# THE BIOME LOOT TABLE (item diversity audit 2026-07-23, Joel: "do it
# all").  The authored DVPet tables were per-SLOT -- 1-1 == 2-1 == 5-1,
# so Andromon's Desert, Kimeramon's Seafloor and Etemon's Mountains all
# dug the same Television -- and the catalog filter dropped 2/3 of their
# entries anyway (552 authored -> 182 usable).  Pools now key on the
# zone's BIOME (its scene), dealt from the EXISTING catalog only: no new
# items, no new systems, and the road finally FEEDS you (fish by the
# water, steak in the mountains).  The 3 road items ride every pool --
# they're the run tools.  The FINAL zone of each map digs the RARE TIER
# instead: the endgame used to dig exactly one item (the chip).
_ROAD_KEYS = ("town_transport", "disaster_transport", "life_recovery")
# D5 (2026-07-24, Joel "make them findable"): cookie + cupcake join the
# gentle biomes alongside candy, the third grant-only treat -- which has
# ALWAYS been a road find here, so this only brings its two siblings in
# line.  (digimemory joined the data biomes the SAME day: the later wild-
# payload ruling gave a found chip a real 5-15 point payload
# (petcare.stash_wild_memory), so the old "a wild chip is a silent dud"
# objection died with it -- it sits in datatunnel/factorynight below,
# truthed 2026-07-25.)
BIOME_FINDS = {
    # the expansion rows (2026-07-26) join their fitting biomes: farmland
    # eggs and meat, forest nuts, mountain cheeses, a pepper by the lava --
    # the road FEEDS you in that biome's own voice, and two of the shy
    # capsules hide out where treasure hunters go.
    "greenhills":   ("fish", "vegetable", "ball", "candy", "cupcake",
                     "meat"),
    "flowerfield":  ("vegetable", "candy", "music_player", "ball", "cookie",
                     "honey", "fruit"),
    "forestgate":   ("poison_mushroom", "vegetable", "candy", "music_player"),
    "mountains":    ("dumbbell", "steak", "grow_capsule",
                     "cheese", "bread", "red_pepper"),
    "frozenpeak":   ("caffeine_pill", "steak", "vitamin"),
    "islandsea":    ("tuna", "fish", "skateboard", "ball", "cupcake",
                     "orange"),
    "lakeside":     ("fish", "tuna", "vegetable", "cookie"),
    "underwater":   ("fish", "tuna", "slim_drink", "capsule_b"),
    "city":         ("video_game", "television", "energy_drink",
                     "cheese_burger", "skateboard", "computer_game", "capsule_c"),
    "datatunnel":   ("energy_drink", "anti_evo_chip", "video_game",
                     "caffeine_pill", "digimemory", "computer_game",
                     "capsule_c"),
    "factorynight": ("anti_evo_chip", "dumbbell", "energy_drink",
                     "sleeping_pill", "digimemory", "capsule_d",
                     "supplement"),
    "volcano":      ("steak", "energy_drink", "dumbbell",
                     "red_pepper"),
    "desert":       ("tuna", "energy_drink", "vitamin", "slim_drink",
                     "yellow_pepper", "orange"),
}
FINAL_ZONE_FINDS = ("anti_evo_chip", "x_antibody", "textbook",
                    "dna_crystal", "steak", "hp_chip")

# the road's festival present pool: the ten authored capsule boxes -- eight
# honest, two AngrySurprise pranks, identical until opened (that IS the box)
_FESTIVAL_CAPSULES = ("capsule_a", "capsule_b", "capsule_c", "capsule_d",
                      "capsule_e", "capsule_f", "capsule_g", "capsule_h",
                      "prank_capsule_a", "prank_capsule_b")


def _find_keys(scene, is_final):
    """The zone's discoverable loot as CATALOG keys: its biome's pool (or
    the rare tier for a map's final zone), with the road items riding
    along.  (The per-slot authored tables retired 2026-07-23 -- see
    BIOME_FINDS above; dormant rand_items/rand_foods stay in the data.)"""
    pool = (FINAL_ZONE_FINDS if is_final
            else BIOME_FINDS.get(scene) or BIOME_FINDS[DEFAULT_SCENE])
    return list(_ROAD_KEYS) + list(pool)


@lru_cache(maxsize=1)
def _real_zones():
    """The 26 zones as run-zones: name (its biome + the gate boss that guards
    it), the one biome scene, a uniform ~40-leg crossing, the zone's OWN wild
    pool (its randoms), its town waypoints (leg-ranges that rest + suppress
    encounters), and its discoverable loot pool (find_keys)."""
    out = []
    for mp in data.load_maps():
        last = max(z["zone"] for z in mp["zones"])
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
                "find_keys": _find_keys(scene, z["zone"] == last),
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
# pet.adv_progress = zones CONQUERED (a count).  The road runs in DIFFICULTY
# ORDER (balance audit 2026-07-21, Joel's option b): the Monte-Carlo sweep
# over the real Battle engine showed zones.csv order was non-monotonic --
# Mega wilds in map 1's zone 3, an 11% boss at zone 2, the endgame map 5
# EASIER than map 1's back half, the all-Mega zone 16 cliff mid-game.  Win
# rate tracks the rosters' stage ranks, so PROGRESSION sorts by that key --
# self-documenting, roster-untouched, and it re-derives if the data changes.
# Zone IDENTITY (list index) is untouched: score bests, names, and the map
# field all stay keyed as before; only the ORDER you meet them changed.


def _difficulty(z):
    """The zone's deterministic difficulty key: mean wild stage rank + gate
    boss rank (the measured win-rate driver)."""
    from .battle import _RANK
    wilds = [e for e in z.get("randoms", ()) if not e.get("boss")]
    wr = (sum(_RANK.get(e.get("stage"), 3) for e in wilds) / len(wilds)
          if wilds else 3.0)
    bs = z.get("bosses") or []
    br = _RANK.get(bs[0].get("stage"), 3) if bs else 3
    return wr + br


PROGRESSION = sorted(range(len(ZONES)),
                     key=lambda i: (_difficulty(ZONES[i]), i))
_ORDER_POS = {zi: pos for pos, zi in enumerate(PROGRESSION)}


# ---------------------------------------------------------------------------
# ZONE SIGNATURES (distribution arc, 2026-07-24 -- Joel ruled D3 "both" and
# D4 "give them distinct loot").
#
# One item that ONLY this zone drops, appended to its biome pool.  A single
# mechanism answers both rulings: it makes every zone's loot unique, which
# is exactly what the eight factorynight zones needed -- they shared one
# scene and therefore dug identical loot, a third of the map reading the
# same.  Signatures are per-ZONE, so the shared scene stops mattering.
#
# The item is matched to the zone's DEPTH: the run's opening stops sign
# common goods, the last stops sign legendary ones, using the same tier
# ladder the shelves read (shop.tier_for_price).  Within a band, items that
# are currently found NOWHERE are handed out first -- so the signature pass
# also closes the "never a find" gap instead of needing its own mechanism.
#
# Deterministic: crc32 over the key, so a zone's signature is PERMANENT (the
# guest-good law -- a place's character must not reshuffle between runs).
# 8 + 8 + 5 + 5 = the 26 zones.  The rare band is exactly 5 because the five
# FINAL_ZONE_FINDS are held back from signing (see _assign_signatures): a
# signature is STRIPPED from every other pool, and signing x_antibody would
# have quietly robbed every map's final zone of the rare tier it exists to
# hand out.  The endgame table outranks the signature pass.
_SIG_BANDS = (("common", 8), ("uncommon", 8), ("rare", 5), ("legendary", 5))


def _assign_signatures():
    """Give every zone its own exclusive find.  Returns {zone_index: key}."""
    import zlib
    from . import shop
    # Read the BASE tables, never the live ZONES: this pass APPENDS to
    # find_keys, so reading the zones back would make the "unfound first"
    # sort depend on whether the pass had already run -- and a second call
    # would deal a different hand.  Signatures must be permanent.
    already = set(_ROAD_KEYS) | set(FINAL_ZONE_FINDS)
    for _pool in BIOME_FINDS.values():
        already.update(_pool)
    # never a signature: the road trio (they ride EVERY pool already), and
    # every GRANT-ONLY good -- the birthday treats and the Digimemory are
    # deliberately unbuyable gifts (item diversity audit 2026-07-23, "by
    # design"), and making them road loot would quietly undo that.
    # ...and never the endgame table: a signature is exclusive, so signing
    # one of these would strip it from every map's final zone.
    banned = set(_ROAD_KEYS) | set(FINAL_ZONE_FINDS)
    by_tier = {}
    for key, v in shop.CATALOG.items():
        if key in banned or v.price is None:
            continue
        by_tier.setdefault(v.tier or "common", []).append(key)
    for tier, keys in by_tier.items():
        # unfound first, then a stable crc32 shuffle
        keys.sort(key=lambda k: (k in already, zlib.crc32(f"sig:{k}".encode())))
    out, pos = {}, 0
    for tier, count in _SIG_BANDS:
        pool = by_tier.get(tier) or []
        for i in range(count):
            if pos >= len(PROGRESSION):
                break
            if not pool:
                pos += 1
                continue
            out[PROGRESSION[pos]] = pool[i % len(pool)]
            pos += 1
    return out


ZONE_SIGNATURE = _assign_signatures()
_SIGNED = set(ZONE_SIGNATURE.values())
for _zi, _z in enumerate(ZONES):
    _mine = ZONE_SIGNATURE.get(_zi)
    # EXCLUSIVE means exclusive: a signature is stripped from every OTHER
    # zone's pool.  Most signatures are drawn from items no biome carried,
    # but the deeper bands run out of those, and a "signature" the zone
    # next door also digs is just a label.
    _z["find_keys"] = [_k for _k in _z["find_keys"]
                       if _k not in _SIGNED or _k == _mine]
    if _mine and _mine not in _z["find_keys"]:
        _z["find_keys"].append(_mine)
    _z["signature"] = _mine

# THE HUMAN SPIRITS WAIT ON THE DEEP ROADS (item expansion 2026-07-26):
# the ten hardest zones by PROGRESSION each hide ONE Human spirit in their
# dig pool -- never sold, legendary-weighted (shop's override), element
# order matched to depth so the Dark spirit guards the very last road.
# Their Beast halves are CUP prizes (tournament.py): roads give Human,
# cups give Beast.
_HUMAN_SPIRITS = ("human_fire_spirit", "human_light_spirit",
                  "human_ice_spirit", "human_wind_spirit",
                  "human_thunder_spirit", "human_earth_spirit",
                  "human_water_spirit", "human_wood_spirit",
                  "human_metal_spirit", "human_dark_spirit")
for _pos, _zi in enumerate(PROGRESSION[-len(_HUMAN_SPIRITS):]):
    if _HUMAN_SPIRITS[_pos] not in ZONES[_zi]["find_keys"]:
        ZONES[_zi]["find_keys"].append(_HUMAN_SPIRITS[_pos])
def zone_index(zone):
    """The index of a zone dict in the ordered ZONES, or None (a test zone)."""
    try:
        return ZONES.index(zone)
    except ValueError:
        return None


def frontier(pet):
    """The ZONES index of the pet's current frontier zone: the next stop on
    the difficulty road (clamped to the last stop)."""
    prog = max(0, min(int(getattr(pet, "adv_progress", 0) or 0),
                      len(PROGRESSION) - 1))
    return PROGRESSION[prog]


def unlocked_indices(pet):
    """The zone indices the pet may embark on, in ROAD order: everything up
    to and including the frontier."""
    prog = max(0, min(int(getattr(pet, "adv_progress", 0) or 0),
                      len(PROGRESSION) - 1))
    return PROGRESSION[:prog + 1]


def is_conquered(pet, zi):
    """Has the pet already felled this zone's boss (its road position sits
    below the conquered count)?"""
    pos = _ORDER_POS.get(zi)
    return pos is not None and pos < int(getattr(pet, "adv_progress", 0) or 0)


def _veteran(enemy):
    """A conquered zone's foe, replayed: the SAME species carrying a
    trained veteran's Side -- the real hit-formula terms (trainings, a
    winning record), which Battle consumes via enemy['side'].  Returns a
    scaled COPY: zone dicts are shared and cached, never mutated."""
    from .battle import Side
    e = dict(enemy)
    s = Side.wild(e.get("num", 0), boss=bool(e.get("boss")))
    s.trainings_cur, s.trainings_total = VETERAN_TRAININGS
    s.battles, s.wins = VETERAN_RECORD
    e["side"] = s
    e["veteran"] = True
    return e


def is_map_cleared(pet, map_num):
    """Are ALL of a map's zones conquered (every one below the frontier)?  This
    is the profile `maps` signal that unlocks the road shop shelf + eggs."""
    idxs = [i for i, z in enumerate(ZONES) if z["map"] == map_num]
    # road-order aware (option b, 2026-07-21): a map is cleared when every
    # one of ITS zones is conquered, wherever they now sit on the road
    return bool(idxs) and all(is_conquered(pet, i) for i in idxs)


def record_win(pet, zone):
    """A boss felled: if it was the FRONTIER, the next stop on the road
    unlocks.  Replaying an already-conquered zone advances nothing.
    Returns True if a zone unlocked."""
    zi = zone_index(zone)
    prog = int(getattr(pet, "adv_progress", 0) or 0)
    if (zi is not None and prog < len(PROGRESSION)
            and _ORDER_POS.get(zi) == prog):
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

    # -- transport (in-run warp items) ----------------------------------------
    def _transport_kind(self, key):
        """'town' (Birdra), 'danger' (Garuda), 'life' (Life Recovery),
        'skip' (Zone Transport: a safe lift up the road) or 'camp'
        (Continent Transport: the Whamon rest) -- the CATALOG road items
        that mean something WITHIN a run -- else None.  (The expansion
        2026-07-26 gave the two worldmap warps run-jobs: the zone picker
        replaced map warping long ago, so their tickets buy road comfort
        instead -- a lift without an ambush, a rest without a town.)"""
        return {"town_transport": "town", "disaster_transport": "danger",
                "life_recovery": "life", "zone_transport": "skip",
                "continent_transport": "camp"}.get(key)

    def held_transports(self):
        """The run-usable road-item keys the pet is carrying, in bag order.
        Each row lists only when it BUYS something (the dead-menu-row rule,
        audit 2026-07-25): Life Recovery hides at full hearts, the Town
        Transport hides on town ground (the rest is already yours), and
        the Danger Warp hides within dash range of the gate (a dash that
        moves nothing).  The town warp reaches the NEAREST span in either
        direction, so late, drained and past the town -- exactly when a
        tamer reaches for it -- the ticket still buys a real town."""
        inv = getattr(self.pet, "inventory", {}) or {}
        return [k for k, n in inv.items() if n > 0 and self._transport_kind(k)
                and not (self._transport_kind(k) == "life"
                         and self.lives >= MAX_LIVES)
                # the ticket buys a TOWN: hidden only when you already
                # stand on town ground (audit 2026-07-25 -- the old
                # forward-only filter hid it at the gate in 26/26 zones,
                # so the gate refusal's promised warp-out never existed;
                # the road CAN double back for a rest)
                and not (self._transport_kind(k) == "town"
                         and (self._in_town(self.loc)
                              or not self.zone.get("town_legs")))
                # the dash buys DISTANCE: at the gate it moved nothing,
                # ate the ticket and forced a fight on a body the gate may
                # have just refused (audit 2026-07-25)
                and not (self._transport_kind(k) == "danger"
                         and self.loc >= self.total - 3)
                # the lift buys legs too: hidden at the gate (2026-07-26)
                and not (self._transport_kind(k) == "skip"
                         and self.loc >= self.total - 1)
                # the camp buys REST: hidden when the tank is already at
                # the half it restores to (the dead-menu-row rule)
                and not (self._transport_kind(k) == "camp"
                         and self.pet.energy >= self.pet.max_energy // 2)]

    def use_transport(self, key):
        """Spend a road item.  Town warp -> jump to the town and rest
        (lives + energy; the PANEL then offers the hub doors like any
        walked-in arrival).  Danger warp -> dash toward the boss and get
        ambushed on arrival.  Life Recovery -> hearts back to full where
        you stand.  Returns 'town-warp', ('encounter', enemy),
        'danger-warp', 'life-recovery', or None (not a run item / not
        held / hearts already full)."""
        kind = self._transport_kind(key)
        inv = getattr(self.pet, "inventory", {}) or {}
        if kind is None or inv.get(key, 0) <= 0 or self.done or self.failed:
            return None
        if kind == "life":
            if self.lives >= MAX_LIVES:        # defensive: menu already hides it
                return None
            self.pet.take_item(key)
            self.lives = MAX_LIVES
            self.last = "A second wind — lives restored!"
            return "life-recovery"
        if kind == "town" and (self._in_town(self.loc)
                               or not self.zone.get("town_legs")):
            # defensive, like the life warp's full-hearts guard: the menu
            # already hides it, and a ticket must never buy a rest you
            # already have (adventure audit 2026-07-25)
            return None
        if kind == "danger" and self.loc >= self.total - 3:
            # defensive: a dash that moves nothing is not for sale
            return None
        if kind == "skip" and self.loc >= self.total - 1:
            return None                        # defensive: nothing to skip
        if kind == "camp" and self.pet.energy >= self.pet.max_energy // 2:
            return None                        # defensive: nothing to rest
        if kind == "skip":
            # the SAFE lift (expansion 2026-07-26): ten legs forward, no
            # ambush, stopping shy of the gate -- the middle ticket between
            # walking and the danger dash
            self.pet.take_item(key)
            self.loc = min(self.total - 1, self.loc + SKIP_LEGS)
            self.last = "A Birdramon lift — the road slides by below."
            return "skip-lift"
        if kind == "camp":
            # the Whamon CAMP: a rest without a town -- energy to half the
            # tank where you stand.  Lives stay Life Recovery's job; the
            # win streak survives (that is this ticket's premium)
            self.pet.take_item(key)
            half = self.pet.max_energy // 2
            if self.pet.energy < half:
                self.pet._set_energy(half)
            self.last = "Camp pitched — rested where you stand."
            return "camp-rest"
        self.pet.take_item(key)
        if kind == "town":
            # the NEAREST town span, behind included: every zone's span
            # ends mid-road, so a forward-only jump left the whole back
            # half (and the gate) with a ticket that bought nothing.
            # Doubling back re-walks real legs -- the ticket's price on
            # top of its price (audit 2026-07-25).
            legs = list(self.zone.get("town_legs") or ())
            tgt = min(legs, key=lambda lg: min(abs(self.loc - lg[0]),
                                               abs(self.loc - lg[1])))
            self.loc = tgt[0]
            self._rest_up()
            self._resting = True
            self.last = "Warped to a town — rested up."
            return "town-warp"
        # danger: dash to just shy of the boss gate, then an ambush
        self.loc = max(self.loc, max(0, self.total - 3))
        pool = self._wild_pool()
        if pool:
            weights = [max(1, e.get("chance", 100)) for e in pool]
            enemy = random.choices(pool, weights=weights, k=1)[0]
            if self.replay:
                # the warp's ambusher is a VETERAN like every other wild on
                # a conquered road -- the raw entry slipped the wrap while
                # award_bits still paid the trained bounty (audit 2026-07-25)
                enemy = _veteran(enemy)
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
        # a FESTIVAL road present IS A CAPSULE now (item expansion
        # 2026-07-26, Joel: "rewire christmas presents to basically be
        # holiday versions of these"): the wrapped box lands in the bag and
        # is OPENED for its roll -- opened on the festival day, the roll
        # reaches a tier higher (petcare._capsule); two of the ten boxes
        # are the authored AngrySurprise pranks.  Home gifts stay home.
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
        """THE BATTLE DROP (item expansion 2026-07-26, Joel: "i even want
        battle drops in adventure") -- and it was AUTHORED all along:
        every enemies.csv row carries a LootTableID into dropRate.csv.
        Wilds shed attribute chips at 2-7%, elites shed the X-Program at
        100%, and each map's unique story boss drops its DIGIMENTAL.

        Rationing rides the bounty's own rules: a REPLAY boss whose daily
        veteran purse is spent drops nothing either (the road_bounty
        ledger, anti-printer) -- wilds stay live, a first conquest is
        untouched.  Returns the granted CATALOG key, or None."""
        if enemy.get("boss") and self.replay and self.bounty_spent:
            return None
        table = data.load_loot_tables().get(enemy.get("loot_table", -1))
        if not table:
            return None
        from . import shop
        from .pet import Pet
        roll, cum = random.random() * 100, 0
        for icon, rate in table:
            cum += rate
            if roll < cum:
                # a Digimental drop speaks the crest shelf's own key; all
                # else resolves through the one icon->key door
                iid = int(icon[2:]) if icon.startswith("i:") else -1
                crest = {v: k for k, v in Pet._CREST_IDS.items()}.get(iid)
                key = crest or shop.key_for_icon(icon)
                if key is None:
                    return None              # an unshipped row stays dormant
                self.pet.add_item(key)
                self.drops += 1
                return key
        return None

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
