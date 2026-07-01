"""DVPet game model: a single virtual pet, its stats, and care logic."""
from __future__ import annotations
import random
from dataclasses import dataclass, field as _dcf
from . import data
from . import egg as egg_mod
from . import evolution
from . import species as sp


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# Lifespan (seconds), scaled from DVPet's real-time model. A pet lives this long
# in total; reaching higher stages extends it; neglect (sickness/starvation)
# burns it down faster. The final stretch is the geriatric "old age".
LIFE_START = 259200.0          # 3 days (egg/baby base lifespan)
STAGE_LIFE = {"Child": 345600.0, "Adult": 388800.0, "Perfect": 432000.0,
              "Ultimate": 432000.0, "Super Ultimate": 432000.0}  # 4-5 days
GERIATRIC_REMAIN = 21600.0   # last N seconds of life = elderly

# NOTE: DM20 tracks NO mood/happiness meter (manual: "does not track happiness, mood,
# emotion ... unlike traditional Tamagotchi devices").  The whole DVPet signed-mood model
# was stripped 2026-07-01.  The pet still emotes, but reactively from live care state
# (needs_care / hunger / sickness), never a stored value.

# DM20 feeding (manual): two foods only. Meat fills a hunger heart; Protein fills a
# strength heart, adds weight and restores DP (stamina). No taste/favourites, no
# multi-nutrient system, no enthusiasm/obedience side effects (all DVPet — stripped).
# (PROTEIN_DP_RESTORE / BATTLE_DP_COST / SLEEP_DP_GAIN live in the DP block below.)

# DVPet poop / filth (config.csv, PhysicalState.poop).  A bowel movement sheds a little
# weight and drops a pile of a size set by the Digimon's base weight (capped).
POOP_WEIGHT_DEC_COEF = 0.1             # PoopWeightDecCoefficient
POOP_WEIGHT_LIMIT = 4                   # PoopWeightLimit (max weight lost per poop)
POOP_INC_WEIGHT_FACTOR = 40            # PoopIncWeightFactor -> size 3 at/above
POOP_INC_WEIGHT_FACTOR_SMALL = 15      # PoopIncWeightFactorSmall -> size 1 at/below
POOP_MAX_PILES = 4                      # classic Digimon V-Pet max poops (DVPet's _filth[] is 6; Joel set 4 to match the real toy)

# DM20 hunger: whole hearts only (manual -- "hunger depletes in whole hearts only").  The
# DVPet sub-heart calorie/fullness buffer was stripped 2026-07-01.  A heart drops every
# HUNGER_HEART_SEC (scaled per species); at zero with the call unanswered it logs a care
# mistake.  The elderly get hungry faster.
HUNGER_HEART_SEC = 1800                 # seconds per hunger heart at the modal decay
GERIATRIC_HUNGER_FACTOR = 4             # the elderly get hungry ~4x faster
# DVPet per-species physiology (calcNeedDecay: higher coefficient = SLOWER decay). ~85% of
# species share the modal values below, so only outliers diverge from tuipet's tuned pace.
REF_HUNGER_COEF = 60          # modal HungerDecayCoefficient
REF_STRENGTH_COEF = 50        # modal StrengthDecayCoefficient
REF_POOP_RATIO = 64           # modal PoopLimit / PoopLapseInc
POOP_INTERVAL_BASE = 2700     # tuipet's tuned poop interval at the modal ratio
STRENGTH_DECAY_BASE = 3000    # gentle effort decay at the modal coefficient (~50 min/heart)

TRAIN_POWER_PER_HIT = 2     # attribute power per drill-hit (compression-scaled from DVPet's flat +1)
# (No fatigue: DM20 has no over-training exhaustion state -- manual "no such system".)

# DVPet sickness & injury durations (config.csv, PhysicalState.sicken / injure): an
# illness or injury lasts Min..MaxLength recovery lapses (SickLapseMin/InjLapseMin game-min
# each) and then clears on its own.  Cured early by medicine as before.  (No vitamins /
# injury-worsening: those were DVPet -- manual "no vitamins".)
MIN_SICK_LENGTH, MAX_SICK_LENGTH = 1, 10     # Min/MaxSickLength (recovery lapses)
MIN_INJ_LENGTH, MAX_INJ_LENGTH = 1, 12       # Min/MaxInjLength
SICK_LAPSE_MIN = 29                      # SickLapseMin (game-min per recovery lapse)
INJ_LAPSE_MIN = 29                       # InjLapseMin
MEDICINE_HOURS = 60                      # MedicineHours (game-min the medicine indicator lingers, config.csv)
BANDAGE_HOURS = 60                       # BandageHours (game-min the bandage indicator lingers, config.csv)

# DM20 DP (battle stamina): restored by protein feeding + sleeping >=3h; consumed by battle.
PROTEIN_DP_RESTORE = 6                   # DP a protein feed restores (also +1 strength)
BATTLE_DP_COST = 4                       # DP spent per battle
SLEEP_DP_GAIN = 3                        # DP recovered per sleep lapse (SleepMinutesToGain)

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
    hunger: int = 4                 # hearts 0..4 (4 = full); FullHunger=4
    strength: int = 2               # effort hearts 0..4; FullStrength=4
    dp: int = 24                    # DM20 battle stamina, 0..dp_max (restored by sleep >=3h + protein)
    dp_max: int = 24                # per-Digimon DP capacity
    weight: int = 20
    poop: int = 0                   # pile count == DVPet countFilth()
    poop_sizes: list = _dcf(default_factory=list)   # per-pile size 1..4 (DVPet _filth bytes)
    sick: bool = False
    asleep: bool = False
    lights: bool = True             # DVPet _lights: room-light toggle, SEPARATE from sleep
    care_mistakes: int = 0
    trainings: int = 0              # successful training sessions this stage (gates DM20 evolution)
    wins: int = 0
    hatching: bool = False
    vaccine: int = 0
    data_power: int = 0
    virus: int = 0
    # care-quality counters that drive DM20 evolution
    overeat: int = 0
    sick_count: int = 0
    injuries: int = 0
    exercise_today: int = 0         # DM20 _exercise: drills done today (resets daily)
    sick_length: float = 0.0        # DVPet _sickLength (game-min until natural recovery)
    inj_length: float = 0.0         # DVPet _injLength (game-min until the injury heals)
    med_lapse: float = 0.0          # DVPet _medLapse: medicine indicator after curing sickness (getMed)
    bandage_lapse: float = 0.0      # DVPet _bandageLapse: bandage indicator after mending an injury (getBandage)
    battles: int = 0
    egg_type: int = 0
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    world_seconds: float = 0.0
    field: str = ""
    # transient animation request, consumed by the UI
    anim: str = "idle"
    anim_ttl: float = 0.0

    def __post_init__(self):
        if self.num is not None and self.num >= 0:
            _, by_num = data.load_sprites()
            rec = by_num.get(self.num)
            if rec and not self.field:
                self.field = rec.get("field", "")
            req = data.load_requirements().get(self.num, {})
            self.dp_max = req.get("dp_max", 24)                # per-Digimon DP capacity
            if self.dp > self.dp_max:
                self.dp = self.dp_max

    # seconds in each stage before it is eligible to evolve (accelerated time)
    EGG_DURATION = 180     # seconds an egg incubates before hatching (~3 min)

    # Authentic DM20 real-time stage timers (seconds): Baby I 10min .. Perfect 48h.
    # Ultimate/Super Ultimate have no further timer -> terminal (9e9) barring jogress.
    STAGE_DURATION = {st: (sp.stage_time(st) or 9e9) for st in sp.STAGE_ORDER}

    @classmethod
    def hatch(cls, num=None):
        _, by_num = data.load_sprites()
        if num is None:
            babies = [n for n, r in by_num.items() if r["stage"] == "Baby I" and not data.is_placeholder(n)]
            num = random.choice(babies)
        return cls.from_num(num)

    @classmethod
    def new_egg(cls, generation=1, egg_type=None):
        if egg_type is None:
            egg_type = random.randrange(egg_mod.count())
        pet = cls(num=-1, name="Digitama", stage="Egg",
                  egg_type=egg_type, generation=generation)
        return pet

    def _hatch_into_fresh(self):
        _, by_num = data.load_sprites()
        target = egg_mod.hatch_target(self.egg_type)
        if target is None or target not in by_num or data.is_placeholder(target):
            babies = [n for n, r in by_num.items() if r["stage"] == "Baby I" and not data.is_placeholder(n)]
            target = random.choice(babies)
        self.evolve_to(target)
        self.hatching = False

    def advance_hatch(self, dt):
        """Advance the 3s hatch animation at frame cadence (10 Hz) so every DVPet
        crack interval renders (rock 4-15, drawNum(1)@16, drawNum(2)@19, hatch@29).
        Returns True on the frame the egg actually hatches into a Fresh."""
        if not self.hatching:
            return False
        self._hatch_t = getattr(self, "_hatch_t", 3.0) - dt
        if self._hatch_t <= 0:
            self._hatch_into_fresh()
            return True
        return False

    @classmethod
    def from_num(cls, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        pet = cls(num=num, name=r["name"], stage=r["stage"], attribute=r["attribute"],
                  field=r.get("field", ""))
        return pet

    # ---- per-tick simulation -------------------------------------------------
    def tick(self, dt):
        self.world_seconds += dt          # the day/night clock runs even past death
        if self.dead:
            return
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
            # the 3s hatch is advanced at frame cadence (10 Hz) via advance_hatch();
            # a 1 Hz countdown here would skip the crack frames (only 3 coarse steps).
            return

        if self.stage != "Egg":
            day = int(self.world_seconds // DAY_LENGTH)
            if getattr(self, "_exercise_day", -1) != day:    # DM20 checkExerciseTime: daily reset
                self._exercise_day = day
                self.exercise_today = 0
            _rec = dt                                         # sickness/injury recover in real time
            if self.sick_length > 0:                          # sickLapse: illness recovers in time
                self.sick_length = max(0.0, self.sick_length - _rec)
                if self.sick_length == 0:
                    self.sick = False
            if self.inj_length > 0:                           # injLapse: the injury heals over time
                self.inj_length = max(0.0, self.inj_length - _rec)
            if self.med_lapse > 0:                            # medLapse: medicine wears off (getMed icon)
                self.med_lapse = max(0.0, self.med_lapse - dt)
            if self.bandage_lapse > 0:                        # bandageLapse: bandage wears off (getBandage icon)
                self.bandage_lapse = max(0.0, self.bandage_lapse - dt)
        if self.asleep:
            # DM20: sleeping >=3h restores DP (stamina); recover it gradually while asleep.
            self._sleep_dp_t = getattr(self, "_sleep_dp_t", 0.0) + dt
            if self._sleep_dp_t >= 60:               # SleepMinutesToGain (game-min)
                self._sleep_dp_t = 0.0
                self._set_dp(self.dp + SLEEP_DP_GAIN)
            if self.day_phase != "night":            # wake in the morning
                self.asleep = False
                self._set_anim("wake", 1.6)  # morning stretch (DVPet wakeUp())
            return

        night = self.day_phase == "night"
        # DM20 has no passive DP decay (DP only drops from battling) and no mood lapse;
        # only hunger drains here: a whole heart every _hunger_interval, and at zero the
        # unanswered call logs a care mistake.
        self._hunger_t = getattr(self, "_hunger_t", 0.0) + dt
        if self._hunger_t >= self._hunger_interval:
            self._hunger_t = 0.0
            if self.hunger > 0:
                self.hunger -= 1
            else:
                self.care_mistakes += 1      # DM20: starving with the call unanswered
        # pooping (DVPet poop(): sheds a little weight, drops a sized pile)
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        if self._poop_t >= self._poop_interval:
            self._poop_t = 0
            self._do_poop()
            self._set_anim("poop", 2.2)          # squat-and-go (DVPet poop())
        # effort decays per species (DVPet calcStrengthDecayLapse): keep training or it slips
        self._str_t = getattr(self, "_str_t", 0.0) + dt
        if not self.asleep and self.strength > 0 and self._str_t >= self._strength_interval:
            self._str_t = 0.0
            self.strength -= 1
        # Filth care-mistake (DVPet poopCall/incCallMinutes): a mistake is only logged
        # once the mess reaches the filth limit AND the awake pet leaves it uncleaned for
        # a grace period; after one, the timer is postponed (AfterMistakeMinutesPostponed)
        # so they do not stack instantly. DVPet MistakeFilthLimit=7 filth items; tuipet's
        # coarse `poop` count maps the visible "needs cleaning" level (>=3) to that gate.
        FILTH_LIMIT = 3                      # MistakeFilthLimit (mapped to tuipet poop scale)
        if self.poop >= FILTH_LIMIT:
            if not self.asleep:              # DVPet poopCall() only ticks while awake;
                self._filth_t = getattr(self, "_filth_t", 0) + dt   # sleep pauses, not resets
                if self._filth_t >= 1800:    # uncleaned grace before it counts
                    self._filth_t = -3600    # AfterMistakeMinutesPostponed grace after one
                    self.care_mistakes += 1  # DM20: left in filth with the call unanswered
        else:
            self._filth_t = 0                # cleaned / under the limit resets the call timer
        # sickness from filth / starvation
        if (self.poop >= 3 or self.hunger == 0) and not self.sick \
                and random.random() < 0.02 / self._phys().get("poop_sick_mult", 1.0) * dt:
            self._sicken()
        # bedtime: sleep through the night (DM20 sleeps on the clock, not from exhaustion);
        # a grace window after a manual wake lets you interact at night
        self._wake_grace = max(0.0, getattr(self, "_wake_grace", 0.0) - dt)
        if not self.asleep and self._wake_grace <= 0 and night:
            self.asleep = True
            self._set_anim("yawn", 1.8)   # yawn, then settle into sleep

        # DVPet discrete neglect-death triggers (config.csv): real abandonment is fatal,
        # not merely a faster lifespan burn. Care mistakes + injuries are per-form (they
        # reset on evolution); the starvation timer persists across evolutions.
        if self.care_mistakes >= 20 or self.injuries >= 20:   # MaxCareMistakes / MaxInjuries
            self._die(); return
        if self.hunger == 0:
            self._starve_t = getattr(self, "_starve_t", 0.0) + dt
            if self._starve_t >= 12 * 3600:                   # empty hunger 12h -> death
                self._die(); return
        else:
            self._starve_t = 0.0
        # lifespan: neglect burns life down faster than the natural clock
        extra = 0.0
        if self.sick:
            extra += 0.8
        if self.hunger == 0:
            extra += 0.4
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
                and self.stage in ("Child", "Adult", "Perfect", "Ultimate", "Super Ultimate")
                and (self.lifespan - self.age_seconds) < GERIATRIC_REMAIN)

    @property
    def day_phase(self):
        return _phase_of((self.world_seconds % DAY_LENGTH) / DAY_LENGTH)

    @property
    def is_daytime(self):
        return self.day_phase in ("dawn", "day")

    def background(self):
        """The backdrop for the current device/field + time of day (or None). It's fixed
        per device (DM20 = Plains), not a switchable habitat — see species.background_key."""
        frames = data.load_backgrounds().get(sp.background_key(getattr(self, "field", None)))
        if not frames:
            return None
        idx = {"dawn": 0, "day": 1, "dusk": 2, "night": 3}.get(self.day_phase, 1)
        return frames[min(idx, len(frames) - 1)]

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

    # ---- per-species physiology (DVPet calcNeedDecay coefficients) -------
    def _phys(self):
        return data.load_requirements().get(self.num, {})

    @property
    def _hunger_interval(self):
        base = HUNGER_HEART_SEC * (self._phys().get("hunger_decay", 60) / REF_HUNGER_COEF)
        return base / (GERIATRIC_HUNGER_FACTOR if self.is_geriatric else 1)

    @property
    def _poop_interval(self):
        r = self._phys()
        return POOP_INTERVAL_BASE * (r.get("poop_limit", 64) / max(1, r.get("poop_lapse", 1))) / REF_POOP_RATIO

    @property
    def _strength_interval(self):
        return STRENGTH_DECAY_BASE * (self._phys().get("strength_decay", 50) / REF_STRENGTH_COEF)

    def evolve_to(self, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        self.num, self.name = num, r["name"]
        self.stage, self.attribute = r["stage"], r["attribute"]
        self.field = r.get("field", self.field)
        _req = data.load_requirements().get(num, {})
        self.dp_max = _req.get("dp_max", self.dp_max)
        self.dp = min(self.dp, self.dp_max)               # clamp to the new capacity (no auto-refill)
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.trainings = 0
        self.injuries = self.sick_count = 0
        self.sick = False
        self.sick_length = self.inj_length = 0.0
        self.weight = self._base_weight()
        # DVPet attributeEvolChange: a form raises/lowers the carried attribute powers
        self.vaccine = max(0, self.vaccine + _req.get("vaccine_change", 0))
        self.data_power = max(0, self.data_power + _req.get("data_change", 0))
        self.virus = max(0, self.virus + _req.get("virus_change", 0))
        # reaching a higher stage extends lifespan toward the stage floor; LifespanMod adjusts
        # it per form (real-time scale). GrowthPeriodMod is omitted -- DVPet's growth period is
        # in real days while tuipet's evolve timer is compressed, so the scales don't align.
        self.lifespan = max(self.lifespan,
                            STAGE_LIFE.get(self.stage, self.lifespan) + _req.get("lifespan_mod", 0))
        self._set_anim("happy", 2.5)

    # ---- care actions --------------------------------------------------------
    def _set_anim(self, name, ttl):
        self.anim, self.anim_ttl = name, ttl

    def needs_care(self):
        """Any unmet care need (DM20 reads live state, not a mood meter): hungry, sick,
        injured, or a big mess.  Drives the pet's distress emoting + status word."""
        return (self.hunger == 0 or self.sick or self.is_injured() or self.poop >= 3)

    def _well_cared(self):
        """Every need comfortably met -- the pet reads as content (happy idle hop)."""
        return (self.hunger >= 3 and self.poop == 0
                and not self.sick and not self.is_injured())

    def _set_dp(self, value):
        """DM20 DP (battle stamina): clamp to [0, dp_max]."""
        self.dp = _clamp(int(round(value)), 0, self.dp_max)

    def dp_pct(self):
        return max(0, self.dp) * 100 // self.dp_max if self.dp_max else 0

    @property
    def power(self):
        """DM20 Power: the pet's total attribute power (vaccine+data+virus), from training."""
        return self.vaccine + self.data_power + self.virus

    def _poop_size(self):
        """DVPet poop(): pile size from base weight (heavier mons drop bigger)."""
        bw = self._base_weight()
        if bw >= POOP_INC_WEIGHT_FACTOR:
            return 3
        if bw <= POOP_INC_WEIGHT_FACTOR_SMALL:
            return 1
        return 2

    def _do_poop(self):
        """PhysicalState.poop: weight shed and a new sized pile added to the filth
        (capped at the _filth array length).  The bmGauge timer that schedules this is
        replaced by tuipet's poop interval."""
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self.weight = max(1, self.weight - wdec)
        if self.poop < POOP_MAX_PILES:                            # addFilth: first free slot (capped)
            self.poop += 1                                        # poop == countFilth()
            self.poop_sizes.append(self._poop_size())

    def _disturbed(self):
        """It's asleep — the DM20 Ver.20th no longer penalises waking, so this is just
        a gentle 'leave it be' nudge (no stat change)."""
        return "zzz... mind its sleep!"

    def _special_idle(self):
        """An occasional idle quirk that reads the pet's live care state (no mood meter):
        a happy hop when well cared for, a grumpy fuss when it needs care."""
        if self._well_cared():
            self._set_anim(random.choice(("play", "surprise")), 2.0)
        elif self.needs_care():
            self._set_anim(random.choice(("angry", "tantrum")), 2.0)
        elif random.random() < 0.5:
            self._set_anim("surprise", 1.6)

    def feed(self, food=None):
        """DM20 feeding: two foods only. Meat fills a hunger heart; Protein fills a
        strength heart, adds weight and restores DP stamina (manual). No taste,
        favourites, or nutrition macros (all DVPet — stripped)."""
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        foods = data.load_foods()
        food = food or (foods[0] if foods else {"name": "Meat", "hunger": 1, "weight": 1})
        if food.get("strength", 0) > 0 and food.get("hunger", 0) <= 0:   # Protein
            if self.strength >= 4:
                self.weight += 1
                self.overeat += 1
                self._set_anim("refuse", 1.0)
                return f"{self.name} is already strong!"
            self.strength = _clamp(self.strength + max(1, food["strength"]), 0, 4)
            self.weight += food.get("weight", 2)
            self._set_dp(self.dp + PROTEIN_DP_RESTORE)      # DM20: protein restores DP stamina
            self._set_anim("eat", 1.4)
            return f"Fed {food['name']}."
        if self.hunger >= 4:                                 # Meat, already full -> overfeed
            self.weight += 1
            self.overeat += 1
            self._poop_t = min(self._poop_interval, getattr(self, "_poop_t", 0) + 900)   # overeat -> sooner poop
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + max(1, food["hunger"]), 0, 4)
        self._hunger_t = 0.0                                # a meal resets the hunger timer
        self.weight += food.get("weight", 1)
        self._set_anim("eat", 1.4)
        return f"Fed {food['name']}."

    def can_train(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        return None

    def apply_training(self, hits, power, attribute=None, game="hp"):
        """Apply a training-minigame result (hits 0..3, power 0..100).

        game in {hp, vaccine, data, virus}: the HP (wall) drill builds Effort
        (strength); an attribute drill builds that attribute's power (DP), which
        accumulates for the whole life (NOT reset on evolution).
        """
        self.exercise_today += 1                          # DM20 _exercise (incExerciseTime)
        if hits >= 2:
            self.strength = _clamp(self.strength + 1, 0, 4)
        success = hits >= 2
        if success:
            self.trainings += 1                           # DM20 onExerciseFinish: +1 Training (gates evolution)
        # A flat +1/drill can't reach the attribute-power thresholds in tuipet's
        # compressed stage, so scale the gain by drill QUALITY (3 hits = +6, 2 = +4).
        gain = hits * TRAIN_POWER_PER_HIT if success else 0
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
        self.weight = max(1, self.weight - 2)
        # training while overweight risks an injury (DM20 has no over-training fatigue)
        if evolution.weight_category(self.weight, self._base_weight()) == "Over" and random.random() < 0.5:
            self._injure()
        # DVPet HP_Training_AttackSuccess = hit pose (frame 6); AttackFail = dejected pose
        # (frame 9). A failed drill shows the dejected reaction (which surfaces the "unhappy"
        # discourage emote), not an attack pose.
        self._set_anim("happy" if hits >= 2 else "sad", 1.8)
        rank = "Perfect!" if hits == 3 else ("Good!" if hits == 2 else ("Meh." if hits == 1 else "Whiff."))
        if game == "hp":
            return f"{rank} {'Effort up!' if hits >= 2 else 'no gain'}"
        return f"{rank} +{gain} {attr}"

    def can_battle(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage in ("Egg", "Baby I"):
            return "Too young to battle."
        if self.asleep:
            return self._disturbed()
        if self.dp <= 0:                                # DM20: DP is the stamina battling needs
            self._set_anim("refuse", 1.0)
            return "No DP — feed protein or let it sleep."
        return None

    def record_battle(self, won, enemy=None):
        """Resolve a finished battle: update battles/wins and rewards."""
        self.battles += 1
        self._set_dp(self.dp - BATTLE_DP_COST)           # DM20: battling spends DP stamina
        if won:
            self.wins += 1
            self._set_anim("happy", 2.0)                  # reactive cheer (no mood meter)
            return "Victory!"
        if random.random() < 0.3:
            self._injure()
        self._set_anim("sad", 2.0)                        # reactive dejection
        return "Defeat..."

    def is_injured(self):
        """PhysicalState.isInj: currently nursing an injury (the count persists for evolution)."""
        return self.inj_length > 0

    def _sicken(self):
        """PhysicalState.sicken: fall ill for MinSickLength..MaxSickLength recovery lapses;
        it clears on its own once that runs out (or earlier with medicine)."""
        if self.sick:
            return
        self.sick = True
        self.sick_count += 1
        self.sick_length = random.randint(MIN_SICK_LENGTH, MAX_SICK_LENGTH) * SICK_LAPSE_MIN

    def _injure(self):
        """PhysicalState.injure: take an injury for MinInjLength..MaxInjLength recovery
        lapses; the cumulative injury count (used by evolution) also ticks up."""
        self.injuries += 1
        rolled = random.randint(MIN_INJ_LENGTH, MAX_INJ_LENGTH) * INJ_LAPSE_MIN
        self.inj_length = max(self.inj_length, rolled)

    def has_medicine(self):
        """PhysicalState.getMed: medicine is still active (the medicine state icon shows)."""
        return self.med_lapse > 0

    def has_bandage(self):
        """PhysicalState.getBandage: a bandage is still on (the bandage state icon shows)."""
        return self.bandage_lapse > 0

    def clean(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.poop_sizes = []                        # clearFilth()
        self._set_anim("wash", 1.2)
        return f"Cleaned {n} poop."

    def heal(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        if not self.sick and not self.is_injured():
            return "It's not sick or injured."
        sick0, inj0 = self.sick, self.is_injured()
        if self.sick:
            self.sick = False
            self.sick_length = 0.0                  # medicine cures the illness outright
            self.med_lapse = MEDICINE_HOURS         # DVPet feedMed: medicine indicator runs as it wears off
        if self.is_injured():
            self.inj_length = 0.0                   # first aid mends the active injury (DVPet bath/recovery)
            self.bandage_lapse = BANDAGE_HOURS      # DVPet applyBandage: the bandage shows during recovery
        self._set_anim("heal", 1.5)
        what = "illness and injury" if (sick0 and inj0) else ("injury" if inj0 else "illness")
        return f"Treated {self.name}'s {what}."

    def toggle_lights(self):
        """The lights button (DVPet setLights): toggles the room light ONLY. The pet
        sleeps and wakes on its own schedule -- this does not force sleep or wake."""
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        self.lights = not self.lights
        return "Lights off." if not self.lights else "Lights on."

    def status_word(self):
        if self.dead:
            return "passed away"
        if self.is_geriatric:
            return "elderly"
        if self.asleep:
            return "asleep"
        if self.sick:
            return "sick"
        if self.is_injured():
            return "injured"
        if self.hunger == 0:
            return "starving"
        if self.poop >= 3:
            return "needs cleaning"
        if self.day_phase == "night" and not self.asleep:
            return "sleepy"
        if self._well_cared():
            return "happy"
        return "ok"
