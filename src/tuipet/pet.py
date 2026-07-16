"""The pet simulation (the clone rebuild, 2026-07-15).

REAL-TIME: one wall-clock minute is one sim tick -- the mon lives while the
terminal is closed (offline minutes replay on load, capped at 3 days).  The
per-minute model below is the rule set ripped from multiple fan games,
transcribed EXACTLY -- rates, thresholds and side-effects carry cite
comments so an audit can re-check every number.

The spine:
- meters: hunger 0-4, strength 0-4, energy 0-energy_max(+bonus), weight
- decay: hunger-1 AND strength-1 every 60 awake stage-minutes
- calls: an empty meter (or bedtime lights) rings for 20 minutes; ignoring
  it is a CARE MISTAKE (latched -- one mistake per call)
- poop: 0.002/min, cap 2 on screen; sickness from filth/overweight
- death: probabilistic per minute from mistakes + sickness + age; a pet
  with <5 mistakes, healthy, under age 15 CANNOT die
- sleep: a fixed clock window per stage; waking refills energy to max
- evolution: time-in-stage gates with best/middle/worst branches from the
  growth chart; evolving banks energyBonus += trainings/5 and resets
  time/trainings/mistakes
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field as _dcf

from . import data


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class _Refused(str):
    """A use_item result that did NOT consume the item.  Reads as a plain
    message everywhere else -- only use_item's consume check looks at the
    type (audit 2026-07-15: every refusal string used to burn the item)."""


# ---- the per-minute rule constants (offline-replay grain; the live 800ms
# rates are exactly these /75) ----
POOP_P = 0.002                 # poop roll per awake minute (cap 2 piles)
SICK_POOP_P = 0.015            # sickness per minute while filth is present
SICK_OVERWEIGHT_P = 0.00375    # per overweight step: floor(excess/(base*0.5))
DEATH_MISTAKES = ((20, 0.0015), (15, 3.75e-4), (10, 7.5e-5), (5, 1.5e-5))
DEATH_SICK_P = 7.5e-5
DEATH_AGE = ((25, 3.75e-4), (20, 1.5e-4), (15, 3.75e-5))
CALL_MINUTES = 20              # a ringing call becomes a mistake after this
REPLAY_CAP_MIN = 4320          # offline catch-up horizon: 3 days
DAY_MINUTES = 1440

# evolution gates: stage -> minutes in stage before the branch check opens
EVO_TIME = {"Baby I": 10, "Baby II": 360, "Child": 600, "Adult": 720,
            "Perfect": 840, "Ultimate-Super Ultimate": 1440}

# sleep windows by stage: (sleep hour, wake hour), wall clock
SLEEP_CLOCK = {"Baby I": (20, 9), "Baby II": (20, 9), "Child": (21, 8),
               "Adult": (22, 8), "Perfect": (22, 8),
               "Ultimate-Super Ultimate": (22, 8), "Special": (22, 8),
               "Armor-Hybrid": (22, 8)}

POOP_MAX_PILES = 2             # on-screen filth cap
OVEREAT_LIMIT = 4              # a full belly reads stuffed (arena's slow bob)

BATTLE_ENERGY_COST = 5
BATTLE_WEIGHT_COST = 4
TRAIN_ENERGY_COST = 2
PILL_ENERGY_GAIN = 7
PILL_WEIGHT_GAIN = 5


def _in_window(hour, win):
    s, w = win
    return (hour >= s or hour < w) if s > w else (s <= hour < w)


def _weekend_mult(now=None):
    wd = time.localtime(now if now is not None else time.time()).tm_wday
    return 1.5 if wd >= 5 else 1.0


def weekend_bonus(now=None):
    """Online battle bits pay x1.5 on weekends."""
    return _weekend_mult(now)


ONLINE_BITS = {"win": 200, "draw": 150, "loss": 100}


def online_reward(won, draw=False, now=None):
    """The online purse: win 200 / draw 150 / loss 100, weekend x1.5."""
    base = ONLINE_BITS["draw" if draw else ("win" if won else "loss")]
    return int(base * weekend_bonus(now))


@dataclass
class Pet:
    num: int                          # roster num (-1 = egg)
    name: str = ""
    stage: str = ""
    attribute: str = ""
    egg_type: int = 0
    generation: int = 1

    # ---- the real-time clock ----
    wall_time: float = 0.0            # epoch seconds of the last applied minute
    total_minutes: int = 0            # totalTimeAlive (minutes)
    stage_minutes: int = 0            # timeInCurrentStage
    _min_acc: float = 0.0             # sub-minute wall seconds, accrued by tick()

    # ---- meters ----
    hunger: int = 4
    strength: int = 4
    energy: int = 10
    energy_bonus: int = 0             # banked at evolution: += trainings//5
    weight: int = 10
    poop: int = 0
    poop_sizes: list = _dcf(default_factory=list)
    sick: bool = False
    asleep: bool = False
    lights: bool = True
    dead: bool = False
    death_cause: str = ""

    # ---- care ledger ----
    care_mistakes: int = 0
    call_on: bool = False             # a meter call is ringing
    call_minutes: int = 0
    call_ignored: bool = False        # latched: this call already cost its mistake
    call_latched: list = _dcf(default_factory=list)  # WHICH meters latched: a
    #                                 hunger latch must not silence a strength
    #                                 call an hour later (audit 2026-07-15)
    wake_until: float = 0.0           # disturbed/alarmed awake until (epoch s):
    #                                 disturb 5-30min, alarm 1-2h (source rule)
    sleep_call_minutes: int = 0       # lights-on-at-bedtime counter
    sleep_mistake_done: bool = False  # once per night
    full_until: float = 0.0           # premium meat satiety (epoch seconds)
    auto_clean_until: float = 0.0     # smart potty (epoch seconds)
    forced_sleep: bool = False        # sleeping pill: sleep through the window
    evo_blocked: bool = False         # anti-evo chip

    # ---- counters ----
    trainings_cur_stage: int = 0
    total_trainings: int = 0
    saved_hit_type: str = "normal"    # the trained battle form (mega/normal/miss)
    battles: int = 0                  # lifetime battles (the branch gates read this)
    wins: int = 0
    hatching: bool = False
    hatch_t: float = 0.0

    # ---- possessions ----
    bits: int = 0
    inventory: dict = _dcf(default_factory=dict)
    bg_current: str = "greenhills"
    bg_owned: list = _dcf(default_factory=list)
    album: list = _dcf(default_factory=list)      # species nums raised (dex)
    revived: int = 0

    # ---- transient ----
    last_msg: str = ""

    def __post_init__(self):
        if not self.wall_time:
            self.wall_time = time.time()

    # ================= lifecycle =================

    @classmethod
    def new_egg(cls, generation=1, egg_type=None):
        from . import egg as egg_mod
        if egg_type is None:
            egg_type = random.randrange(egg_mod.count())
        # the egg STARTS on its assigned scene -- the same hue-picked bucket
        # the carousel previews it on (all bucket scenes are free catalog
        # picks); scene_for only ever reached the preview before (Joel
        # 2026-07-15: "eggs arent starting on their assigned backgrounds")
        return cls(num=-1, name="", stage="Egg", attribute="Free",
                   egg_type=egg_type, generation=generation,
                   bg_current=egg_mod.scene_for(egg_type),
                   wall_time=time.time())

    def advance_hatch(self, dt):
        """The incubating egg: dt real seconds toward the crack (~30 s)."""
        if self.stage != "Egg":
            return False
        self.hatch_t += dt
        if self.hatch_t >= 30 and not self.hatching:
            self.hatching = True
        return self.hatching

    def _hatch_into_fresh(self):
        """Crack the shell: become the egg's Baby I."""
        from . import egg as egg_mod
        target = egg_mod.hatch_target(self.egg_type)
        if target is None:
            return
        self._become(target)
        self.hatching = False
        self.hatch_t = 0.0
        self.total_minutes = 0
        self.stage_minutes = 0
        self.care_mistakes = 0
        self.energy = 10                       # newborn energy
        self.hunger = self.strength = 4
        self.weight = self._base_weight()
        # a newborn's clock starts NOW: an egg saved days ago otherwise
        # inherits its stale wall_time and the next tick() replays the whole
        # gap -- Baby I to Perfect in one frame (audit 2026-07-15)
        self.wall_time = time.time()
        self._min_acc = 0.0

    def _become(self, num):
        rec = data.record_for(num)
        self.num = num
        self.name = rec.get("name", self.name)
        self.stage = rec.get("stage", self.stage)
        self.attribute = rec.get("attribute", self.attribute)
        if num not in self.album:
            self.album.append(num)

    @classmethod
    def from_num(cls, num):
        p = cls(num=num)
        rec = data.record_for(num)
        p.name = rec.get("name", "")
        p.stage = rec.get("stage", "")
        p.attribute = rec.get("attribute", "")
        p.weight = rec.get("weight", 10)
        p.energy = rec.get("energy_max", 10)
        return p

    def _die(self, cause=""):
        self.dead = True
        self.death_cause = cause
        self.sick = False
        self.poop = 0
        self.poop_sizes = []
        self.call_on = False

    def revive(self):
        """revive_floppy: back from the dead, shaken but alive."""
        self.dead = False
        self.death_cause = ""
        self.revived += 1
        self.care_mistakes = 0
        self.hunger = self.strength = 1
        # life resumes NOW: the clock froze at death, and replaying the dead
        # days made a fresh revival sick+starving and often dead AGAIN on
        # its first tick (audit 2026-07-15)
        self.wall_time = time.time()
        self._min_acc = 0.0
        self.sick = False
        self.call_on = False
        self.call_minutes = 0
        self.call_latched.clear()
        self.call_ignored = False

    # ================= species record =================

    @property
    def species(self):
        return data.record_for(self.num) if self.num >= 0 else None

    @property
    def species_path(self):
        rec = self.species
        return rec.get("path") if rec else None

    @property
    def max_energy(self):
        rec = self.species
        base = rec.get("energy_max", 10) if rec else 10
        return min(999, base + self.energy_bonus)

    @property
    def hunger_max(self):
        rec = self.species
        return rec.get("hunger_max", 4) if rec else 4

    @property
    def strength_max(self):
        rec = self.species
        return rec.get("strength_max", 4) if rec else 4

    def _base_weight(self):
        rec = self.species
        return rec.get("weight", 10) if rec else 10

    @property
    def age_days(self):
        return self.total_minutes // DAY_MINUTES

    @property
    def win_rate(self):
        return self.wins / self.battles if self.battles else 0.5

    # ================= the clock =================

    def tick(self, dt):
        """dt REAL seconds -> whole sim minutes.  The app's frame loop and
        the lobby's live tick both land here."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return
        self._min_acc += dt
        while self._min_acc >= 60.0:
            self._min_acc -= 60.0
            self.wall_time += 60.0
            self._sim_minute()
            if self.dead:
                return
        # drift guard: never let the sim clock lag the wall by minutes
        now = time.time()
        if now - self.wall_time > 120.0:
            self.catch_up(now)

    def catch_up(self, now=None):
        """Replay offline minutes (cap 3 days) -- the load-time catch-up."""
        now = now or time.time()
        gap = int((now - self.wall_time) // 60)
        if gap <= 0 or self.dead or self.stage == "Egg" or self.num < 0:
            self.wall_time = max(self.wall_time, now)
            return 0
        n = min(gap, REPLAY_CAP_MIN)
        # minutes beyond the horizon pass unsimulated (the cap)
        self.wall_time = now - n * 60.0
        for _ in range(n):
            self.wall_time += 60.0
            self._sim_minute()
            if self.dead:
                break
        return n

    def _hour(self):
        return time.localtime(self.wall_time).tm_hour

    # ================= the per-minute sim =================

    def _sim_minute(self):
        self._anim_override = None       # transient poses die with the minute
        self.stage_minutes += 1
        self.total_minutes += 1

        win = SLEEP_CLOCK.get(self.stage, (22, 8))
        in_window = _in_window(self._hour(), win)
        if in_window and self.forced_sleep:
            self.forced_sleep = False
        # a disturbed/alarmed pet stays up past its bedtime for the wake
        # delay, then dozes back off (source rule: disturb 5-30min, alarm 1-2h)
        sleeping = ((in_window or self.forced_sleep)
                    and not self.wall_time < self.wake_until)

        if sleeping and not self.asleep:
            self.asleep = True
            self.sleep_call_minutes = 0
            self.sleep_mistake_done = False
        elif not sleeping and self.asleep:
            # morning: wake with a FULL tank
            self.asleep = False
            self.energy = self.max_energy
            self.lights = True
            self.call_on = False
            self.call_ignored = False
            self.call_latched.clear()
            self.sleep_call_minutes = 0
            self.sleep_mistake_done = False

        fed = bool(self.full_until) and self.wall_time < self.full_until

        # hourly meter decay (awake only; premium-meat satiety blocks it)
        if self.stage_minutes % 60 == 0 and not sleeping and not fed:
            if self.hunger > 0:
                self.hunger -= 1
            if self.strength > 0:
                self.strength -= 1

        if sleeping:
            # lights left on at bedtime: one call, one mistake per night
            if self.lights and not self.sleep_mistake_done:
                self.call_on = True
                self.sleep_call_minutes += 1
                if self.sleep_call_minutes >= CALL_MINUTES:
                    self.care_mistakes += 1
                    self.sleep_mistake_done = True
                    self.call_on = False
            self.call_minutes = 0
            return

        # empty-meter call (hunger or strength at zero) -- latched PER METER:
        # one shared latch let a strength meter empty an hour after a latched
        # hunger call and never ring or cost a mistake at all (audit 2026-07-15)
        zero = [m for m in ("hunger", "strength") if getattr(self, m) == 0]
        for m in list(self.call_latched):
            if m not in zero:                  # a refilled meter re-arms its call
                self.call_latched.remove(m)
        fresh = [m for m in zero if m not in self.call_latched]
        if fresh:
            self.call_on = True
            self.call_minutes += 1
            if self.call_minutes >= CALL_MINUTES:
                self.care_mistakes += 1        # one mistake per ignored ring
                self.call_latched.extend(fresh)
                self.call_on = False
                self.call_minutes = 0
        else:
            self.call_on = False
            self.call_minutes = 0
        self.call_ignored = bool(self.call_latched)   # the HUD-facing mirror

        # bowels
        if self.poop < 2 and random.random() < POOP_P:
            if self.auto_clean_until and self.wall_time < self.auto_clean_until:
                self.poop = 0
                self.poop_sizes = []
            else:
                self.poop += 1
                self.poop_sizes.append(random.randint(1, 4))
            if self.hunger > 0 and not fed:
                self.hunger -= 1
            if self.weight > self._base_weight():
                self.weight -= 1

        # sickness
        p = 0.0
        if self.poop > 0:
            p += SICK_POOP_P
        base_w = self._base_weight()
        if base_w > 0 and self.weight > base_w:
            steps = int((self.weight - base_w) // (base_w * 0.5))
            p += steps * SICK_OVERWEIGHT_P
        if not self.sick and p > 0 and random.random() < p:
            self.sick = True

        # mortality
        d = 0.0
        for thresh, rate in DEATH_MISTAKES:
            if self.care_mistakes >= thresh:
                d += rate
                break
        if self.sick:
            d += DEATH_SICK_P
        for thresh, rate in DEATH_AGE:
            if self.age_days >= thresh:
                d += rate
                break
        if d > 0 and random.random() < d:
            self._die("old age" if self.age_days >= 15 else "neglect")
            return

        # growth check runs every minute
        self._maybe_evolve()

    # ================= evolution =================

    def _branch(self):
        """best/middle/worst by the stage's branch rule."""
        cm = self.care_mistakes
        if self.stage in ("Baby I", "Baby II"):
            return "best" if cm < 3 else "middle" if cm <= 5 else "worst"
        if self.stage == "Child":
            return ("worst" if cm >= 4
                    else "best" if self.trainings_cur_stage > 24 else "middle")
        if self.stage == "Adult":
            return ("worst" if cm >= 4
                    else "best" if self.battles > 39 else "middle")
        if self.stage == "Perfect":
            return ("worst" if cm >= 3
                    else "best" if self.battles > 79 else "middle")
        return ("worst" if cm >= 3
                else "best" if self.battles > 99 else "middle")

    def evolution_progress(self):
        """(minutes in stage, minutes needed) -- the status card's meter."""
        need = EVO_TIME.get(self.stage)
        if not need:
            return (100, 100)
        return (min(self.stage_minutes, need), need)

    def _maybe_evolve(self):
        if self.evo_blocked or self.dead:
            return None
        need = EVO_TIME.get(self.stage)
        if not need or self.stage_minutes < need:
            return None
        chart = data.load_evo_branches().get(self.species_path)
        if not chart:
            return None
        b = self._branch()
        order = {"best": ("best", "middle", "worst"),
                 "middle": ("middle", "best", "worst"),
                 "worst": ("worst", "middle", "best")}[b]
        nxt = next((chart[k] for k in order if chart.get(k)), None)
        if not nxt:
            return None
        return self._evolve_to_path(nxt)

    def _evolve_to_path(self, path):
        num = data.num_by_path().get(path)
        if num is None:
            return None
        # bank the sweat, wipe the slate
        self.energy_bonus = min(999, self.energy_bonus
                                + self.trainings_cur_stage // 5)
        self.stage_minutes = 0
        self.trainings_cur_stage = 0
        self.care_mistakes = 0
        self.call_on = False
        self.call_ignored = False
        self.poop = 0
        self.poop_sizes = []
        old = data.record_for(self.num)["name"] if self.num >= 0 else "?"
        self._become(num)
        self.last_msg = f"{old} evolved!"
        return num

    def item_evolve(self, item_id):
        """A crest egg: Child -> its Armor form, if this species has one.
        Life-state guarded (audit 2026-07-15: a crest egg EVOLVED A CORPSE,
        which then kept replaying its death)."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return None
        for e in data.load_armor_evos().get(self.species_path or "", []):
            if e.get("itemId") == item_id:
                self.disturb_sleep()           # a crest egg on a sleeper wakes it
                return self._evolve_to_path(e["result"])
        return None

    def jogress_with(self, other_path):
        """Fusion: my path + the partner's path -> the pair table's result."""
        mine = self.species_path
        if not mine or not other_path:
            return None
        key = f"{min(mine, other_path)}|{max(mine, other_path)}"
        result = data.load_jogress_pairs().get(key)
        return self._evolve_to_path(result) if result else None

    # ================= actions =================

    def _guard(self, asleep_blocks=True):
        """Actions bounce off a dead / egg / sleeping pet."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return False
        if asleep_blocks and self.asleep:
            return False
        return True

    def feed_meat(self):
        """Meat: hunger +1, weight +1.  Refused at a full belly.  Feeding a
        sleeper DISTURBS it first (source rule L93; audit 2026-07-15)."""
        if not self._guard(asleep_blocks=False):
            return None
        if self.hunger >= self.hunger_max:
            return "refuse"
        self.disturb_sleep()
        self.hunger += 1
        self.weight = _clamp(self.weight + 1, 1, 999)
        return "ate"

    def feed_pill(self):
        """The pill: cures sickness, strength +1, energy +7, weight +5.
        Healing a sleeper DISTURBS it first (source rule L93)."""
        if not self._guard(asleep_blocks=False):
            return None
        if not self.sick and self.strength >= self.strength_max \
                and self.energy >= self.max_energy:
            return "refuse"
        self.disturb_sleep()
        self.sick = False
        self.strength = _clamp(self.strength + 1, 0, self.strength_max)
        self.energy = _clamp(self.energy + PILL_ENERGY_GAIN, 0, self.max_energy)
        self.weight = _clamp(self.weight + PILL_WEIGHT_GAIN, 1, 999)
        return "healed"

    def heal(self):
        return self.feed_pill()

    def clean(self):
        """Flush the filth."""
        if self.dead or self.num < 0:
            return False
        had = self.poop > 0
        self.poop = 0
        self.poop_sizes = []
        return had

    def toggle_lights(self):
        self.lights = not self.lights
        if not self.lights and self.asleep:
            # tucking it in silences the bedtime call
            self.call_on = False
        return self.lights

    def disturb_sleep(self):
        """Feeding/training/item-ing a sleeper: +1 care mistake and it's
        yanked awake for 5-30 minutes before dozing back off (source rule
        L93: 'disturbing sleep -> +1 each + 5-30min wake delay').  Wired at
        every waking action since audit 2026-07-15 -- it had ZERO callers."""
        if not self.asleep:
            return False
        self.care_mistakes += 1
        self.asleep = False
        self.forced_sleep = False
        self.wake_until = self.wall_time + random.randint(5, 30) * 60
        self.lights = True
        self.call_on = False
        return True

    def train_result(self, success):
        """One training round: energy -2, the counters that feed evolution."""
        if not self._guard():
            return False
        self.energy = max(0, self.energy - TRAIN_ENERGY_COST)
        self.trainings_cur_stage += 1
        self.total_trainings += 1
        if success:
            self.weight = max(self._base_weight(), self.weight - 1)
        return True

    def record_battle(self, won, online=False):
        """One battle: counters + costs (+bits handled by the caller online)."""
        self.battles += 1
        if won:
            self.wins += 1
        self.energy = max(0, self.energy - BATTLE_ENERGY_COST)
        self.weight = max(1, self.weight - BATTLE_WEIGHT_COST)
        if not online:
            # a local bout trains: +2 toward the branch gates
            self.trainings_cur_stage += 2
            self.total_trainings += 2

    # ================= possessions =================

    def add_bits(self, n):
        self.bits = _clamp(self.bits + int(n), 0, 99_999_999)

    def spend_bits(self, n):
        if self.bits < n:
            return False
        self.bits -= n
        return True

    def add_item(self, key, n=1):
        self.inventory[key] = self.inventory.get(key, 0) + n

    def take_item(self, key, n=1):
        have = self.inventory.get(key, 0)
        if have < n:
            return False
        if have == n:
            self.inventory.pop(key, None)
        else:
            self.inventory[key] = have - n
        return True

    def use_item(self, key):
        """Consume one inventory item -> a short result message ('' = the
        item does nothing here, None = don't have it).  A _Refused message
        keeps the item: 'consume on refusal' burned Rev.Floppies on live
        pets and fruit at a full belly (audit 2026-07-15)."""
        if key not in self.inventory:
            return None
        fx = {
            "energy_drink": lambda: self._gain_energy(self.max_energy),
            "best_fruit": lambda: self._fruit(+2),
            "normal_fruit": lambda: self._fruit(+1),
            "worst_fruit": lambda: self._fruit(0),
            "deadly_fruit": self._deadly,
            "junk_food": self._junk,
            "premium_meat": self._premium_meat,
            "poop_clean_pill": self._smart_potty,
            "care_mistake_eraser": self._erase_mistake,
            "sleeping_pill": self._sleep_pill,
            "alarm_clock": self._alarm,
            "time_gear": self._time_gear,
            "anti_evo_chip": self._anti_evo,
            "x_antibody": self._x_antibody,
            "training_pack": self._training_pack,
            "revive_floppy": self._revive_item,
            "super_carrot": self._super_carrot,
        }.get(key)
        if fx is None:
            return ""
        # life-state guard (audit 2026-07-15): only the Rev.Floppy works on
        # the dead, and NOTHING works on an egg -- a training_pack used to
        # pre-clear the Child best-branch gate before the shell even cracked
        if self.dead and key != "revive_floppy":
            return _Refused("")
        if self.stage == "Egg" or self.num < 0:
            return _Refused("")
        # item on a sleeper: the alarm wakes mistake-FREE (its whole point),
        # the sleeping pill is pointless, anything else is a DISTURB --
        # +1 mistake, 5-30min awake -- and then applies (source rule L93)
        if self.asleep and key not in ("alarm_clock", "sleeping_pill"):
            self.disturb_sleep()
        out = fx()
        if not isinstance(out, _Refused) and out is not None:
            self.take_item(key)
        return out

    def _gain_energy(self, n):
        self.energy = _clamp(self.energy + n, 0, self.max_energy)
        return "Energy restored!"

    def _fruit(self, quality):
        if self.hunger >= self.hunger_max and quality >= 0:
            return _Refused("Refused - belly's full.")
        self.hunger = _clamp(self.hunger + 1, 0, self.hunger_max)
        if quality > 0:
            self.strength = _clamp(self.strength + quality - 1, 0,
                                   self.strength_max)
        elif quality == 0:
            self.weight = _clamp(self.weight + 3, 1, 999)
        return "Munch."

    def _deadly(self):
        self._die("a deadly fruit")
        return "...that fruit was DEADLY."

    def _junk(self):
        self.hunger = self.hunger_max
        self.weight = _clamp(self.weight + 4, 1, 999)
        self.care_mistakes += 1
        return "Delicious. Regrettable."

    def _premium_meat(self):
        self.hunger = self.hunger_max
        self.full_until = self.wall_time + 12 * 3600
        return "Satiated for 12 hours."

    def _smart_potty(self):
        self.clean()
        self.auto_clean_until = self.wall_time + 24 * 3600
        return "Auto-clean for 24 hours."

    def _erase_mistake(self):
        if self.care_mistakes <= 0:
            return _Refused("No mistakes to erase.")
        self.care_mistakes -= 1
        return "One mistake, forgotten."

    def _sleep_pill(self):
        if self.asleep:
            return _Refused("It's already asleep.")   # source: pill refunded
        self.forced_sleep = True
        self.asleep = True
        self.wake_until = 0.0
        return "Zzz..."

    def _alarm(self):
        """Wake Up Without Mistake (the source's own label): a 1-2h wake with
        no disturb penalty.  The old version refilled energy for free (a
        cheap energy_drink) and re-slept the NEXT MINUTE into a second
        bedtime mistake (audit 2026-07-15)."""
        if not self.asleep:
            return _Refused("It's already awake.")
        self.asleep = False
        self.forced_sleep = False
        self.wake_until = self.wall_time + random.randint(60, 120) * 60
        self.lights = True
        self.call_on = False
        return "Rise and shine!"

    def _time_gear(self):
        self.stage_minutes += 120
        return "Time lurches forward."

    def _anti_evo(self):
        self.evo_blocked = not self.evo_blocked
        return "Evolution " + ("BLOCKED." if self.evo_blocked else "unblocked.")

    def _x_antibody(self):
        # the X path: this species' X variant if the atlas has one
        rec = self.species
        if not rec:
            return _Refused("")
        want = rec["name"] + "_X"
        for path, num in data.num_by_path().items():
            base = path.rsplit("/", 1)[-1][:-5]
            if base == want:
                self._evolve_to_path(path)
                return "The X-Antibody takes hold!"
        return _Refused("Nothing stirs.")

    def _training_pack(self):
        self.trainings_cur_stage += 5
        self.total_trainings += 5
        return "Training +5."

    def _revive_item(self):
        if not self.dead:
            return _Refused("No one needs reviving.")
        self.revive()
        return "It LIVES."

    def _super_carrot(self):
        """Spr.Carrot: weight -10 (source label 'Reduce Weight by 10') --
        one of the audit's inert buyables, now wired."""
        if self.weight <= 1:
            return _Refused("Nothing left to trim.")
        self.weight = max(1, self.weight - 10)
        return "Feather-light!"

    # ================= backgrounds (unchanged lane) =================

    def background(self, file=None):
        from . import backgrounds as bgs
        key = file if file is not None else (self.bg_current or bgs.DEFAULT)
        sheet = data.load_backgrounds().get(key)
        return sheet[0] if sheet else None

    def owns_background(self, key):
        from . import backgrounds as bgs
        return key in self.bg_owned or bgs.price(key) == 0

    def buy_background(self, key):
        from . import backgrounds as bgs
        price = bgs.price(key)
        if key in self.bg_owned:
            return self.pick_background(key)
        if not self.spend_bits(price):
            return f"Need {price}b for {bgs.name(key)}."
        self.bg_owned.append(key)
        return self.pick_background(key)

    def pick_background(self, key):
        from . import backgrounds as bgs
        self.bg_current = key
        return f"{bgs.name(key)} it is."

    # ================= HUD readings =================

    def needs_care(self):
        return (self.call_on or self.sick or self.poop > 0
                or (self.asleep and self.lights))

    def needs_attention(self):
        return self.needs_care()

    def status_word(self):
        if self.dead:
            return "gone"
        if self.stage == "Egg":
            return "egg"
        if self.asleep:
            return "asleep"
        if self.sick:
            return "sick"
        if self.hunger == 0:
            return "starving"
        if self.strength == 0:
            return "weak"
        if self.poop > 0:
            return "messy"
        return "fine"

    def condition(self):
        return self.status_word()

    def current_mood(self):
        # no mood meter in this world: the HUD keys off condition
        w = self.status_word()
        return "Unhappy" if w in ("sick", "starving", "weak", "messy") \
            else "Neutral"

    def energy_pct(self):
        m = self.max_energy
        return self.energy / m if m else 0.0

    @property
    def anim(self):
        """The home scene's pose key, derived (the old sim stored it).
        Settable: screens/fx may pin a transient pose; the next sim minute
        clears it."""
        ov = getattr(self, "_anim_override", None)
        if ov:
            return ov
        if self.dead:
            return "exhausted"
        if self.asleep:
            return "sleep"
        return "idle"

    @anim.setter
    def anim(self, value):
        self._anim_override = None if value in ("idle", "walk") else value

    def _restless(self):
        return 0

    def _set_energy(self, v):
        """Compat setter (adventure travel drain, town rest)."""
        self.energy = _clamp(int(v), 0, self.max_energy)

    def near_bedtime(self):
        win = SLEEP_CLOCK.get(self.stage, (22, 8))
        return not self.asleep and (self._hour() + 1) % 24 == win[0]

    # ---- legacy pins some surviving screens still poke ----
    def is_fatigued(self):
        return False

    def is_injured(self):
        return False

    def is_freezing(self):
        return False

    def is_overheating(self):
        return False

    def is_geriatric(self):
        return self.age_days >= 15

    def can_feed(self):
        """'' when a meal may start, else the reason (the HUD flashes it)."""
        if self.dead:
            return "It rests now."
        if self.stage == "Egg" or self.num < 0:
            return "The egg eats nothing yet."
        # a sleeper does NOT block the meal: feeding it is a DISTURB -- +1
        # mistake and a grumpy wake (source rule L93; audit 2026-07-15)
        return ""
