"""DVPet game model: a single virtual pet, its stats, and care logic."""
from __future__ import annotations
import random
from dataclasses import dataclass, field as _dcf
from . import data
from . import egg as egg_mod
from . import evolution
from . import weather as wx
from . import theme


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _enemy_level(enemy):
    """DVPet getLevel: (vaccine+data+virus + (health-5)*10) / 100, min 1."""
    v = enemy.get("vaccine", 0)
    d = enemy.get("data_power", 0)
    vir = enemy.get("virus", 0)
    h = enemy.get("hp", 5)
    return max(1, int((v + d + vir + (h - 5) * 10) / 100))


_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}
_PRECIP = _RAIN | _SNOW


def _dvpet_time(phase):
    """Map tuipet's day phase to DVPet's training Time (Morning/Noon/Night)."""
    return {"dawn": "Morning", "day": "Noon", "dusk": "Noon", "night": "Night"}.get(phase, "Noon")


# Lifespan (seconds), scaled from DVPet's real-time model. A pet lives this long
# in total; reaching higher stages extends it; neglect (sickness/starvation/
# fatigue) burns it down faster. The final stretch is the geriatric "old age".
LIFE_START = 259200.0          # 3 days (egg/baby base lifespan)
STAGE_LIFE = {"Rookie": 345600.0, "Champion": 388800.0, "Ultimate": 432000.0, "Mega": 432000.0}  # 4-5 days
GERIATRIC_REMAIN = 21600.0   # last N seconds of life = elderly

# X-Antibody: a special state that unlocks evolution into the "X" Digimon forms.
# None -> Temporary (decays) -> Permanent -> XProgram.  Acquired by a rare natural
# birth roll or the X-Antibody / X-Program items.  (DVPet birth is 1/1000; bumped
# for tuipet so it is an occasional surprise rather than never seen.)
X_COUNT_MAX = 3600.0
X_BIRTH_TARGET, X_BIRTH_BOUND = 1, 50
_XA_ORDER = {"None": 0, "Temporary": 1, "Permanent": 2, "XProgram": 3}

# Personality: DVPet's 3x3x3 table over (disposition, glutton, restless), each in
# {-1 low, 0 neutral, +1 high}.  Ported verbatim from PhysicalState.checkPersonality.
_PERSONALITY = {
    (0, 0): ("Docile", "Restless", "Calm"),
    (0, 1): ("Gluttonous", "Hasty", "Lazy"),
    (0, -1): ("Content", "Fidgety", "Stoic"),
    (1, 0): ("Cheerful", "Hyper", "Carefree"),
    (1, 1): ("Eager", "Playful", "Loafing"),
    (1, -1): ("Generous", "Antsy", "Mellow"),
    (-1, 0): ("Serious", "Anxious", "Apathetic"),
    (-1, 1): ("Selfish", "Impish", "Lethargic"),
    (-1, -1): ("Tolerant", "Unruly", "Callous"),
}

# Day/night: the world runs on an accelerated clock. One full DAY_LENGTH-second
# cycle runs dawn -> day -> dusk -> night. Night makes the pet sleepy: kept awake
# it tires and sulks faster, while rest is deepest then.
DAY_LENGTH = 1440.0           # 24 min per day/night cycle


def _phase_of(p):
    if p < 0.08:
        return "dawn"
    if p < 0.55:
        return "day"
    if p < 0.70:
        return "dusk"
    return "night"


@dataclass
class Pet:
    num: int
    name: str = ""
    stage: str = ""
    attribute: str = ""
    age_seconds: float = 0.0
    stage_seconds: float = 0.0      # time spent in the current stage
    hunger: int = 4                 # hearts 0..4 (4 = full)
    strength: int = 2               # effort hearts 0..4
    energy: int = 100               # 0..100
    mood: int = 80                  # 0..100
    weight: int = 20
    poop: int = 0
    sick: bool = False
    asleep: bool = False
    care_mistakes: int = 0
    wins: int = 0
    hatching: bool = False
    vaccine: int = 0
    data_power: int = 0
    virus: int = 0
    # care-quality counters that drive evolution (mirror DVPet's tracked stats)
    overeat: int = 0
    sick_count: int = 0
    injuries: int = 0
    disturb: int = 0
    obedience: int = 0
    battles: int = 0
    levels_fought: list = _dcf(default_factory=list)  # opponent levels beaten this stage (DVPet _levelsFought)
    bits: int = 0
    trophies: int = 0
    adv_map: int = 0
    adv_zone: int = 0
    egg_type: int = 0
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    world_seconds: float = 0.0
    temp: float = 50.0
    day_temp: float = 50.0
    weather: str = "Clear"
    field: str = ""
    element: str = ""
    habitat: int = 2                # current home (2 = Plains, a temperate default)
    habitats: list = _dcf(default_factory=lambda: [0, 2])
    time_pref: dict = _dcf(default_factory=lambda: {"dawn": 0, "day": 0, "dusk": 0, "night": 0})
    x_antibody: str = "None"
    x_count: float = 0.0
    train_time: str = ""            # time of day of the last training (gates some evolutions)
    inventory: dict = _dcf(default_factory=dict)
    # transient animation request, consumed by the UI
    anim: str = "idle"
    anim_ttl: float = 0.0

    def __post_init__(self):
        if self.num is not None and self.num >= 0 and not self.field:
            _, by_num = data.load_sprites()
            rec = by_num.get(self.num)
            if rec:
                self.field = rec.get("field", "")
                self.element = rec.get("element", "")

    # seconds in each stage before it is eligible to evolve (accelerated time)
    EGG_DURATION = 180     # seconds an egg incubates before hatching (~3 min)

    STAGE_DURATION = {                       # seconds in a stage before it may evolve
        "Fresh": 1800, "InTraining": 2400, "Rookie": 3000,
        "Champion": 3600, "Ultimate": 3600, "Mega": 9e9,
    }

    @classmethod
    def hatch(cls, num=None):
        _, by_num = data.load_sprites()
        if num is None:
            fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh" and not data.is_placeholder(n)]
            num = random.choice(fresh)
        return cls.from_num(num)

    @classmethod
    def new_egg(cls, generation=1, egg_type=None):
        if egg_type is None:
            egg_type = random.randrange(egg_mod.count())
        pet = cls(num=-1, name="Digitama", stage="Egg",
                  egg_type=egg_type, generation=generation)
        pet._apply_egg_habitat()
        return pet

    def _hatch_into_fresh(self):
        _, by_num = data.load_sprites()
        target = egg_mod.hatch_target(self.egg_type)
        if target is None or target not in by_num or data.is_placeholder(target):
            fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh" and not data.is_placeholder(n)]
            target = random.choice(fresh)
        self.evolve_to(target)
        self.hatching = False
        if self.x_antibody == "None" and random.randint(0, X_BIRTH_BOUND - 1) < X_BIRTH_TARGET:
            self._set_xantibody("Permanent")          # born a natural X-Antibody carrier

    @classmethod
    def from_num(cls, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        pet = cls(num=num, name=r["name"], stage=r["stage"], attribute=r["attribute"],
                  field=r.get("field", ""), element=r.get("element", ""))
        pet._apply_natural_habitat()
        return pet

    # ---- per-tick simulation -------------------------------------------------
    def tick(self, dt):
        self.world_seconds += dt          # the day/night clock runs even past death
        self._update_weather(dt)          # ...and so does the weather, over the grave
        if self.dead:
            return
        if self.x_antibody == "Temporary":          # a protoform fades if unused
            self.x_count -= dt
            if self.x_count <= 0:
                self.x_antibody, self.x_count = "None", 0.0
        self.age_seconds += dt
        self.stage_seconds += dt
        if self.anim_ttl > 0:
            self.anim_ttl -= dt
            if self.anim_ttl <= 0:
                self.anim = "sleep" if self.asleep else "idle"

        if self.stage == "Egg":
            if not self.hatching and self.stage_seconds >= self.EGG_DURATION:
                self.hatching = True
                self._hatch_t = 3.0
                self._set_anim("hatch", 3.0)
            if self.hatching:
                self._hatch_t = getattr(self, "_hatch_t", 3.0) - dt
                if self._hatch_t <= 0:
                    self._hatch_into_fresh()
            return

        if self.stage != "Egg":
            self._temperature_effects(dt)
            self._track_time_pref(dt)
        if self.asleep:
            rate = 0.35 if self.day_phase == "night" else 0.28   # rest is deepest at night
            self.energy = _clamp(self.energy + rate * dt, 0, 100)
            # sleep through the night; wake in the morning once decently rested
            if self.day_phase != "night" and self.energy >= 60:
                self.asleep = False
                self._set_anim("wake", 1.6)  # morning stretch (DVPet wakeUp())
            return

        night = self.day_phase == "night"
        # at night an awake pet tires and grows cranky about twice as fast
        drain = 0.05 if night else 0.03
        lo, hi = self.ideal_temp
        if self.weather in ("Clear", "Cloudy") and lo <= self.temp <= hi:
            drain *= 0.6                  # fair weather + ideal temp eases fatigue
        drain *= max(0.5, min(1.6, 1 - 0.12 * self._affinity()))
        self.energy = _clamp(self.energy - drain * dt, 0, 100)
        self.mood = _clamp(self.mood - (0.009 if night else 0.005) * dt, 0, 100)
        # hunger ticks down on a slow clock
        self._hunger_t = getattr(self, "_hunger_t", 0) + dt
        if self._hunger_t >= 1800:
            self._hunger_t = 0
            if self.hunger > 0:
                self.hunger -= 1
            else:
                self.care_mistakes += 1
        # pooping
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        if self._poop_t >= 2700:
            self._poop_t = 0
            self.poop += 1
            self._set_anim("poop", 2.2)          # squat-and-go (DVPet poop())
        # filth care-mistake: filth left uncleaned too long (DVPet MinutesToMistakePoop).
        # Cleaning resets the timer; otherwise neglect counts toward the evolution gate.
        if self.poop > 0:
            self._filth_t = getattr(self, "_filth_t", 0) + dt
            if self._filth_t >= 1800:
                self._filth_t = 0
                self.care_mistakes += 1
        else:
            self._filth_t = 0
        # sickness from filth / starvation
        if (self.poop >= 3 or self.hunger == 0) and not self.sick and random.random() < 0.02 * dt:
            self.sick = True
            self.sick_count += 1
        # bedtime: sleep through the night, or pass out if run to exhaustion by
        # day; a grace window after a manual wake lets you interact at night
        self._wake_grace = max(0.0, getattr(self, "_wake_grace", 0.0) - dt)
        if not self.asleep and self._wake_grace <= 0 and ((night and self.energy < 85) or self.energy <= 0):
            self.asleep = True
            self._set_anim("yawn", 1.8)   # yawn, then settle into sleep

        # lifespan: neglect burns life down faster than the natural clock
        extra = 0.0
        if self.sick:
            extra += 0.8
        if self.hunger == 0:
            extra += 0.4
        if self.energy <= 0:
            extra += 0.2
        if self.is_geriatric:
            extra += 0.2
        self.lifespan -= extra * dt
        if self.age_seconds >= self.lifespan:
            self._die()
            return

        if (self.anim in ("idle", "walk") and self.anim_ttl <= 0 and not self.poop
                and not self.sick and random.random() < 0.03 * dt):
            self._special_idle()

        self._maybe_evolve()

    @property
    def is_geriatric(self):
        return (not self.dead
                and self.stage in ("Rookie", "Champion", "Ultimate", "Mega")
                and (self.lifespan - self.age_seconds) < GERIATRIC_REMAIN)

    @property
    def day_phase(self):
        return _phase_of((self.world_seconds % DAY_LENGTH) / DAY_LENGTH)

    @property
    def is_daytime(self):
        return self.day_phase in ("dawn", "day")

    @property
    def season(self):
        return wx.season_for_day(int(self.world_seconds // DAY_LENGTH))

    @property
    def ideal_temp(self):
        return data.load_requirements().get(self.num, {}).get("ideal_temp", (40, 60))

    def habitat_obj(self):
        habs = data.load_habitats()
        return habs.get(self.habitat) or habs.get(0) or next(iter(habs.values()))

    def background(self):
        """The habitat background frame for the current weather/time (or None)."""
        frames = data.load_backgrounds().get(self.habitat_obj().get("bg", ""))
        if not frames:
            return None
        if self.asleep and len(frames) > 3:
            idx = 3                                          # lights off: the dark habitat
        elif self.weather in _PRECIP and len(frames) > 4:
            idx = 4
        else:
            idx = {"dawn": 0, "day": 1, "dusk": 2, "night": 3}.get(self.day_phase, 1)
        return theme.weather_tint(frames[min(idx, len(frames) - 1)], self.weather)

    def _affinity(self):
        """Net Field/Element fit with the current home: +compatible, -incompatible."""
        h = self.habitat_obj()
        f, e = self.field, self.element
        compat = (f in h["compat_fields"]) + (e in h["compat_elements"])
        incompat = (f in h["incompat_fields"]) + (e in h["incompat_elements"])
        return compat - incompat

    def _track_time_pref(self, dt):
        # the pet warms to the times of day it spends happy in, and sours on the
        # rest -- DVPet's timeRanks favorite/disliked, kept lightweight
        d = 1 if self.mood >= 60 else (-1 if self.mood <= 25 else 0)
        if d:
            ph = self.day_phase
            self.time_pref[ph] = _clamp(self.time_pref.get(ph, 0) + d, -90, 90)

    def _disposition(self):
        return 1 if self.mood >= 70 else (-1 if self.mood <= 30 else 0)

    def _glutton(self):
        return 1 if self.overeat >= 4 else (-1 if self.overeat == 0 else 0)

    def _restless(self):
        return 1 if self.disturb >= 3 else (-1 if self.disturb == 0 else 0)

    def personality(self):
        if self.num == -1 or self.stage == "Egg":
            return "Unhatched"
        trio = _PERSONALITY[(self._disposition(), self._glutton())]
        rst = self._restless()
        return trio[0 if rst == 0 else (1 if rst == 1 else 2)]

    def favorite_time(self):
        return max(self.time_pref, key=self.time_pref.get) if any(self.time_pref.values()) else None

    def disliked_time(self):
        return min(self.time_pref, key=self.time_pref.get) if any(v < 0 for v in self.time_pref.values()) else None

    def _update_weather(self, dt):
        hab = self.habitat_obj()
        lo_i, hi_i = self.ideal_temp
        if hab["weather_chance"] <= 0:        # climate-controlled home (Hard Disk)
            self.weather = "Clear"
            target = self.day_temp = (lo_i + hi_i) / 2
        else:
            day = int(self.world_seconds // DAY_LENGTH)
            if getattr(self, "_weather_day", -1) != day:
                self._weather_day = day
                lo, hi = hab["temps"][self.season]
                self.day_temp = random.randint(min(lo, hi), max(lo, hi))
            self._weather_t = getattr(self, "_weather_t", 0.0) + dt
            if self._weather_t >= wx.WEATHER_CHECK_SEC:
                self._weather_t = 0.0
                self.weather = wx.next_weather(self.weather, self.season, self.day_temp, hab)
            target = wx.adjusted_day_temp(self.day_temp, self.weather, self.day_phase, hab)
        if self.temp < target:
            self.temp = min(target, self.temp + wx.TEMP_RATE * dt)
        elif self.temp > target:
            self.temp = max(target, self.temp - wx.TEMP_RATE * dt)

    def _set_xantibody(self, state):
        """Raise the X-Antibody state (never downgrades except by expiry)."""
        if _XA_ORDER[state] > _XA_ORDER.get(self.x_antibody, 0):
            self.x_antibody = state
        self.x_count = X_COUNT_MAX if self.x_antibody == "Temporary" else 0.0

    def buy_habitat(self, hid):
        habs = data.load_habitats()
        h = habs.get(hid)
        if not h:
            return "?"
        if hid in self.habitats:
            return f"You already own {h['name']}."
        if self.bits < h["price"]:
            return "Not enough bits."
        self.bits -= h["price"]
        self.habitats = sorted(set(self.habitats) | {hid})
        return f"Bought {h['name']}!"

    def move_to(self, hid):
        habs = data.load_habitats()
        h = habs.get(hid)
        if not h:
            return "?"
        if hid not in self.habitats:
            return "You don't own that habitat."
        self.habitat = hid
        self._weather_day = -1            # force a fresh climate roll on arrival
        return f"Moved to {h['name']}."

    def _temperature_effects(self, dt):
        lo, hi = self.ideal_temp
        aff = self._affinity()                # compatible home helps, incompatible hurts
        too_hot = self.temp >= hi + wx.UPPER_IDEAL
        too_cold = self.temp <= lo - wx.LOWER_IDEAL
        self._comfort_t = getattr(self, "_comfort_t", 0.0) + dt
        if self._comfort_t >= wx.IDEAL_TEMP_MOOD_SEC:
            self._comfort_t = 0.0
            if lo <= self.temp <= hi:
                self.mood = _clamp(self.mood + wx.IDEAL_TEMP_INC + aff, 0, 100)
            elif too_hot or too_cold:
                self.mood = _clamp(self.mood - wx.IDEAL_TEMP_DEC + aff, 0, 100)
        self._btemp_t = getattr(self, "_btemp_t", 0.0) + dt
        if self._btemp_t >= wx.BAD_TEMP_SICK_SEC:
            self._btemp_t = 0.0
            if not self.sick:
                chance = wx.BAD_TEMP_SICK_CHANCE * (1 - 0.25 * aff) if (too_hot or too_cold) else 0.0
                if aff < 0:                   # an incompatible home is just unhealthy
                    chance += 0.004 * (-aff)
                if chance > 0 and random.random() < chance:
                    self.sick = True
                    self.sick_count += 1

    def _die(self):
        self.dead = True
        self.asleep = False
        self.hatching = False
        self._set_anim("idle", 0)

    def _base_weight(self):
        return data.load_requirements().get(self.num, {}).get("base_weight", 20)

    def _maybe_evolve(self):
        if self.sick or self.asleep or self.is_geriatric:
            return
        if self.stage_seconds < self.STAGE_DURATION.get(self.stage, 9e9):
            return
        target = evolution.select(self)
        if target is not None:
            self.evolve_to(target)

    def _apply_egg_habitat(self):
        """Show the destined habitat as soon as the egg is chosen (DVPet)."""
        for t in egg_mod.hatch_targets(self.egg_type):
            h = data.natural_habitat(t)
            if h >= 0:
                self.habitat = h
                if h not in self.habitats:
                    self.habitats = sorted(set(self.habitats) | {h})
                return

    def _apply_natural_habitat(self):
        """Move to this species' natural habitat (digimon.csv Habitat) so each
        Digimon shows its own background. -1 = no preference -> keep current."""
        hr = data.natural_habitat(self.num)
        if hr is not None and hr >= 0:
            self.habitat = hr
            if hr not in self.habitats:
                self.habitats = sorted(set(self.habitats) | {hr})

    def evolve_to(self, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        self.num, self.name = num, r["name"]
        self.stage, self.attribute = r["stage"], r["attribute"]
        self.field = r.get("field", self.field)
        self.element = r.get("element", self.element)
        self._apply_natural_habitat()
        if data.load_requirements().get(num, {}).get("xantibody", "None") in ("Induced", "Natural"):
            self._set_xantibody("Permanent")          # the X-Antibody locks in
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.disturb = 0
        self.injuries = self.sick_count = 0
        self.levels_fought = []
        self.weight = self._base_weight()
        # reaching a higher stage extends the total lifespan toward that stage's floor
        self.lifespan = max(self.lifespan, STAGE_LIFE.get(self.stage, self.lifespan))
        self._set_anim("happy", 2.5)

    # ---- care actions --------------------------------------------------------
    def _set_anim(self, name, ttl):
        self.anim, self.anim_ttl = name, ttl

    def _disturbed(self):
        """Bothering the pet mid-sleep: counts toward restlessness AND costs mood
        now (DVPet DisturbMoodDec)."""
        self.disturb += 1
        self.mood = _clamp(self.mood - 10, 0, 100)
        return "zzz... mind its sleep!"

    def _special_idle(self):
        """An occasional idle quirk reflecting weather + mood (DVPet
        weathering()/personalityMood*): huddle in bad weather, a happy hop
        when content, a grumpy tantrum when unhappy."""
        if self.weather in _RAIN:
            self._set_anim("shield", 2.0)
        elif self.weather in _SNOW:
            self._set_anim("huddle", 2.0)
        elif self.mood >= 70:
            self._set_anim(random.choice(("play", "surprise")), 2.0)
        elif self.mood <= 30:
            self._set_anim(random.choice(("angry", "tantrum")), 2.0)
        elif random.random() < 0.5:
            self._set_anim("surprise", 1.6)

    def feed(self, food=None):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        foods = data.load_foods()
        food = food or (foods[0] if foods else {"name": "Meat", "hunger": 1, "weight": 4, "mood": 5})
        if self.hunger >= 4:
            self.weight += 1
            self.overeat += 1
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + max(1, food["hunger"]), 0, 4)
        self.weight += food.get("weight", 1)
        self.mood = _clamp(self.mood + food.get("mood", 0), 0, 100)
        self._set_anim("eat", 1.4)
        return f"Fed {food['name']}."

    def can_train(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        if self.energy < 12:
            self._set_anim("refuse", 1.0)
            return "Too tired to train."
        return None

    def apply_training(self, hits, power, attribute=None, game="hp"):
        """Apply a training-minigame result (hits 0..3, power 0..100).

        game in {hp, vaccine, data, virus}: the HP drill builds Effort
        (strength); the attribute drills build that attribute's power, which
        accumulates for the whole life (NOT reset on evolution), exactly like
        DVPet. Training a non-favored attribute costs a little mood
        (DVPet NoneTrainingAttributeMoodRankChange).
        """
        self.train_time = _dvpet_time(self.day_phase)
        if hits >= 2:
            self.strength = _clamp(self.strength + 1, 0, 4)
            self.obedience += 1
        gain = max(0, power)
        if game == "hp":
            attr = "Effort"
        else:
            attr = attribute or (self.attribute if self.attribute in ("Vaccine", "Data", "Virus") else "Vaccine")
            if attr == "Vaccine":
                self.vaccine += gain
            elif attr == "Data":
                self.data_power += gain
            elif attr == "Virus":
                self.virus += gain
            if attr != self.attribute:                       # disliked-attribute cost
                self.mood = _clamp(self.mood - 1, 0, 100)
        self.weight = max(1, self.weight - 2)
        self.energy = _clamp(self.energy - 15, 0, 100)
        self.mood = _clamp(self.mood + hits * 3, 0, 100)
        # training while overweight risks an injury
        if evolution.weight_category(self.weight, self._base_weight()) == "Over" and random.random() < 0.5:
            self.injuries += 1
        self._set_anim("happy" if hits >= 2 else "attack", 1.8)
        rank = "Perfect!" if hits == 3 else ("Good!" if hits == 2 else ("Meh." if hits == 1 else "Whiff."))
        if game == "hp":
            return f"{rank} {'Effort up!' if hits >= 2 else 'no gain'}"
        return f"{rank} +{gain} {attr}"

    def can_battle(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage in ("Egg", "Fresh"):
            return "Too young to battle."
        if self.asleep:
            return self._disturbed()
        if self.energy < 10:
            self._set_anim("refuse", 1.0)
            return "Too tired to battle."
        return None

    def record_battle(self, won, enemy=None):
        """Resolve a finished battle: update battles/wins and rewards."""
        self.battles += 1
        self.energy = _clamp(self.energy - 10, 0, 100)
        if won:
            self.wins += 1
            if enemy:
                self.levels_fought.append(_enemy_level(enemy))
            self.mood = _clamp(self.mood + 8, 0, 100)
            lo, hi = (enemy or {}).get("bits", (1, 5))
            gained = random.randint(lo, hi)
            self.bits += gained
            self._set_anim("happy", 2.0)
            return f"Victory! +{gained} bits"
        self.mood = _clamp(self.mood - 10, 0, 100)
        if random.random() < 0.3:
            self.injuries += 1
        self._set_anim("sad", 2.0)
        return "Defeat..."

    def clean(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.mood = _clamp(self.mood + 3, 0, 100)
        self._set_anim("wash", 1.2)
        return f"Cleaned {n} poop."

    def heal(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if not self.sick:
            return "Not sick."
        self.sick = False
        self.mood = _clamp(self.mood + 5, 0, 100)
        self._set_anim("heal", 1.5)
        return f"{self.name} feels better!"

    def toggle_sleep(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        self.asleep = not self.asleep
        if not self.asleep:
            self._wake_grace = 180.0          # stay up after a manual wake
        self._set_anim("sleep" if self.asleep else "idle", 0)
        return "Lights off. Zzz." if self.asleep else "Lights on."

    def play(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        self.mood = _clamp(self.mood + 8, 0, 100)
        self.energy = _clamp(self.energy - 4, 0, 100)
        self._set_anim("play", 1.5)
        return "Played together!"

    # ---- shop / items --------------------------------------------------------
    def buy(self, entry):
        if self.bits < entry["price"]:
            return "Not enough bits."
        self.bits -= entry["price"]
        self.inventory[entry["key"]] = self.inventory.get(entry["key"], 0) + 1
        return f"Bought {entry['name']}."

    def add_item(self, key, n=1):
        """Drop loot / grants straight into the bag."""
        self.inventory[key] = self.inventory.get(key, 0) + n

    def use_item(self, key):
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        e = data.consumable_by_key(key)
        if not e:
            return "?"
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        self.inventory[key] -= 1
        if self.inventory[key] <= 0:
            del self.inventory[key]
        if e.get("special") == "xantibody":
            self._set_anim("happy", 1.5)
            if key == "i:14":
                self._set_xantibody("Permanent")
                return "X-Program complete! The X-Antibody is permanent."
            self._set_xantibody("Temporary")
            return "X-Antibody induced! Evolve soon to make it stick."
        is_food = key.startswith("f:")
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + e["hunger"], 0, 4)
        self.mood = _clamp(self.mood + e["mood"], 0, 100)
        self.weight = max(1, self.weight + e["weight"])
        if e["energy"]:
            self.energy = _clamp(self.energy + e["energy"], 0, 100)
        if e["strength"]:
            self.strength = _clamp(self.strength + e["strength"], 0, 4)
        self.obedience += e["obedience"]
        self.vaccine = max(0, self.vaccine + e["vaccine"])
        self.data_power = max(0, self.data_power + e["data"])
        self.virus = max(0, self.virus + e["virus"])
        if e["unfatigue"]:
            self.energy = 100
        if e["undepressed"]:
            self.mood = _clamp(self.mood + 50, 0, 100)
        if e["cured"]:
            self.sick = False
        if e["healed"]:
            self.injuries = max(0, self.injuries - 1)
        self._set_anim("eat" if is_food else "happy", 1.4)
        return f"Used {e['name']}."

    # ---- presentation helpers -----------------------------------------------
    def status_word(self):
        if self.dead:
            return "passed away"
        if self.is_geriatric:
            return "elderly"
        if self.asleep:
            return "asleep"
        if self.sick:
            return "sick"
        if self.temp <= wx.FREEZING_TEMP:
            return "freezing"
        lo, hi = self.ideal_temp
        if self.temp >= hi + wx.UPPER_IDEAL:
            return "overheating"
        if self.hunger == 0:
            return "starving"
        if self.poop >= 3:
            return "needs cleaning"
        if self.day_phase == "night" and not self.asleep and self.energy < 45:
            return "sleepy"
        if self.mood < 25:
            return "unhappy"
        if self.mood > 75:
            return "happy"
        return "ok"
