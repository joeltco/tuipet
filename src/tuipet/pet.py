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
# in total; reaching higher stages extends it; neglect (sickness/starvation/
# fatigue) burns it down faster. The final stretch is the geriatric "old age".
LIFE_START = 259200.0          # 3 days (egg/baby base lifespan)
STAGE_LIFE = {"Child": 345600.0, "Adult": 388800.0, "Perfect": 432000.0,
              "Ultimate": 432000.0, "Super Ultimate": 432000.0}  # 4-5 days
GERIATRIC_REMAIN = 21600.0   # last N seconds of life = elderly

# NOTE: DM20 tracks NO mood/happiness meter (manual: "does not track happiness, mood,
# emotion ... unlike traditional Tamagotchi devices").  The whole DVPet signed-mood model
# was stripped 2026-07-01.  The pet still emotes, but reactively from live care state
# (needs_care / hunger / sickness / energy), never a stored value.

# DM20 feeding (manual): two foods only. Meat fills a hunger heart; Protein fills a
# strength heart, adds weight and restores a little DP. No taste/favourites, no
# multi-nutrient system, no enthusiasm/obedience side effects (all DVPet — stripped).
PROTEIN_DP_RESTORE = 1                  # DM20 protein restores DP (manual: +0.25/feed, scaled)

# DVPet poop / filth (config.csv, PhysicalState.poop).  A bowel movement sheds a little
# weight and drops a pile of a size set by the Digimon's base weight (capped).
POOP_WEIGHT_DEC_COEF = 0.1             # PoopWeightDecCoefficient
POOP_WEIGHT_LIMIT = 4                   # PoopWeightLimit (max weight lost per poop)
POOP_INC_WEIGHT_FACTOR = 40            # PoopIncWeightFactor -> size 3 at/above
POOP_INC_WEIGHT_FACTOR_SMALL = 15      # PoopIncWeightFactorSmall -> size 1 at/below
POOP_MAX_PILES = 4                      # classic Digimon V-Pet max poops (DVPet's _filth[] is 6; Joel set 4 to match the real toy)

# DVPet calorie buffer (config.csv, PhysicalState.calorieChange / setCalories): a
# -CalorieLimit..+CalorieLimit "fullness within the current hunger heart".  Each lapse
# the buffer drains (faster when geriatric); when it empties the hunger heart drops a
# level (or, at zero, logs a care mistake).  Eating refills it; overfilling speeds the
# next poop.  DVPet's two coupled timers collapse here to one buffer whose drain rate is
# tuned to preserve tuipet's ~1800s-per-heart hunger pace (col-1 calorie mods are 0).
CALORIE_LIMIT = 4                       # CalorieLimit (buffer half-range)
CALORIE_LAPSE_CHANGE = -1               # CalorieLapseChange (drain per lapse)
CALORIE_LAPSE_GERIATRIC_EXTRA = -3      # CalorieLapseChangeGeriatric (added when elderly)
CALORIE_DECAY_SEC = 1800 / (2 * CALORIE_LIMIT)   # keep ~1800s per hunger heart
# DVPet per-species physiology (calcNeedDecay: higher coefficient = SLOWER decay). ~85% of
# species share the modal values below, so only outliers diverge from tuipet's tuned pace.
REF_HUNGER_COEF = 60          # modal HungerDecayCoefficient
REF_STRENGTH_COEF = 50        # modal StrengthDecayCoefficient
REF_POOP_RATIO = 64           # modal PoopLimit / PoopLapseInc
POOP_INTERVAL_BASE = 2700     # tuipet's tuned poop interval at the modal ratio
STRENGTH_DECAY_BASE = 3000    # gentle effort decay at the modal coefficient (~50 min/heart)

# DVPet fatigue (config.csv, PhysicalState.fatigue / checkFatigueLapse): training to
# exhaustion can leave the pet fatigued for FatigueMin..FatigueMax game-minutes -- a
# one-time energy hit, and it cannot act until it has rested off the clock.
# isFatigued() == fatigue_length > 0; the length counts down in game-minutes (1 game-min
# ~= 1s under tuipet's clock).  The lifespan hit is omitted (documented); deltas verbatim.
FATIGUE_MIN = 5                          # FatigueMin
FATIGUE_MAX = 60                         # FatigueMax
FATIGUE_ENERGY_DEC = 1                   # FatigueEnergyDec
TRAIN_POWER_PER_HIT = 2     # attribute power per drill-hit (compression-scaled from DVPet's flat +1)
FATIGUE_CHANCE = 60                      # FatigueChance (% on an exhausting drill)

# DVPet sickness & injury durations (config.csv, PhysicalState.sicken / injure): an
# illness or injury lasts Min..MaxLength recovery lapses (SickLapseMin/InjLapseMin game-min
# each) and then clears on its own.  Cured early by medicine as before.
MIN_SICK_LENGTH, MAX_SICK_LENGTH = 1, 10     # Min/MaxSickLength (recovery lapses)
MIN_INJ_LENGTH, MAX_INJ_LENGTH = 1, 12       # Min/MaxInjLength
SICK_LAPSE_MIN = 29                      # SickLapseMin (game-min per recovery lapse)
INJ_LAPSE_MIN = 29                       # InjLapseMin

# DVPet injury worsening + vitamins (config.csv, calcWorse{Exercise,Battle}Inj /
# worsenedInjury / feedVitamin): pushing an injured pet (training/battling) can worsen the
# injury -- extending it and costing energy -- at a chance set by weight and whether a
# vitamin is active.  Chances are factor/WorseInjuryChance.  No shipped item is flagged
# Vitamin in items.csv, so has_vitamin() defaults false (the no-vitamin rates apply); the
# grant path (feed_vitamin / a "vitamin" consumable flag) is wired and ready.  Values
# verbatim from config.csv column 1; WorseInjuryLifeDec lifespan hit omitted.
WORSE_INJ_CHANCE = 100                   # WorseInjuryChance / WorseBattleInjuryChance (bound)
WORSE_INJ_EXERCISE = {"bad_nv": 10, "good_nv": 1, "good_v": 0, "bad_v": 5}   # WorseInjury*
WORSE_INJ_BATTLE = {"bad_nv": 15, "good_nv": 5, "good_v": 0, "bad_v": 5}     # WorseBattleInjury*
WORSE_INJ_ENERGY_DEC = 1                 # WorseInjuryEnergyDec
VITAMIN_HOURS = 60                       # VitaminHours (game-min of injury-worsening protection)
MEDICINE_HOURS = 60                      # MedicineHours (game-min the medicine indicator lingers, config.csv)
BANDAGE_HOURS = 60                       # BandageHours (game-min the bandage indicator lingers, config.csv)

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
    calories: int = 4               # DVPet calorie buffer, -CALORIE_LIMIT..+CALORIE_LIMIT
    strength: int = 2               # effort hearts 0..4; FullStrength=4
    energy: int = 24                # DVPet energy, -max_energy..+max_energy (full at max_energy)
    max_energy: int = 24            # per-Digimon (digimon.csv MaxEnergy)
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
    fatigue_length: float = 0.0     # DVPet _fatigueLength (game-min remaining; >0 == fatigued)
    sick_length: float = 0.0        # DVPet _sickLength (game-min until natural recovery)
    inj_length: float = 0.0         # DVPet _injLength (game-min until the injury heals)
    vitamin_lapse: float = 0.0      # DVPet _vitaminLapse (game-min of injury-worsening protection)
    med_lapse: float = 0.0          # DVPet _medLapse: medicine indicator after curing sickness (getMed)
    bandage_lapse: float = 0.0      # DVPet _bandageLapse: bandage indicator after mending an injury (getBandage)
    battles: int = 0
    egg_type: int = 0
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    world_seconds: float = 0.0
    field: str = ""
    element: str = ""
    # transient animation request, consumed by the UI
    anim: str = "idle"
    anim_ttl: float = 0.0

    def __post_init__(self):
        if self.num is not None and self.num >= 0:
            _, by_num = data.load_sprites()
            rec = by_num.get(self.num)
            if rec and not self.field:
                self.field = rec.get("field", "")
                self.element = rec.get("element", "")
            req = data.load_requirements().get(self.num, {})
            self.max_energy = req.get("max_energy", 24)        # per-Digimon maxEnergy
            self._sleep_energy_gain = req.get("sleep_energy_gain", 3)
            if self.energy > self.max_energy:
                self.energy = self.max_energy

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
                  field=r.get("field", ""), element=r.get("element", ""))
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
            _rec = dt                                         # sickness/injury/fatigue recover in real time
            if self.fatigue_length > 0:                       # checkFatigueLapse: rest it off (even asleep)
                self.fatigue_length = max(0.0, self.fatigue_length - _rec)
            if self.sick_length > 0:                          # sickLapse: illness recovers in time
                self.sick_length = max(0.0, self.sick_length - _rec)
                if self.sick_length == 0:
                    self.sick = False
            if self.inj_length > 0:                           # injLapse: the injury heals over time
                self.inj_length = max(0.0, self.inj_length - _rec)
            if self.vitamin_lapse > 0:                        # vitaminLapse: protection wears off
                self.vitamin_lapse = max(0.0, self.vitamin_lapse - dt)
            if self.med_lapse > 0:                            # medLapse: medicine wears off (getMed icon)
                self.med_lapse = max(0.0, self.med_lapse - dt)
            if self.bandage_lapse > 0:                        # bandageLapse: bandage wears off (getBandage icon)
                self.bandage_lapse = max(0.0, self.bandage_lapse - dt)
        if self.asleep:
            # DVPet sleep recovery: +SleepEnergyGain every SleepMinutesToEnergyGain.
            self._sleep_e_t = getattr(self, "_sleep_e_t", 0.0) + dt
            if self._sleep_e_t >= 60:                # SleepMinutesToEnergyGain (game-min)
                self._sleep_e_t = 0.0
                self._set_energy(self.energy + getattr(self, "_sleep_energy_gain", 3))
            # sleep through the night; wake in the morning once fully rested
            if self.day_phase != "night" and self.energy >= self.max_energy:
                self.asleep = False
                self._set_anim("wake", 1.6)  # morning stretch (DVPet wakeUp())
            return

        night = self.day_phase == "night"
        # DVPet has NO passive energy decay -- energy only drops from activity
        # (exercise/battle/travel) and refills during sleep.  (No mood lapse: DM20 has
        # no mood meter -- see the module note; distress is read live from care state.)
        # hunger: the DVPet calorie buffer drains each lapse; emptying it drops a hunger
        # heart (or logs a care mistake at zero), then refills for the next heart.
        self._cal_t = getattr(self, "_cal_t", 0.0) + dt
        if self._cal_t >= self._hunger_interval:
            self._cal_t = 0.0
            self.calories += CALORIE_LAPSE_CHANGE + (CALORIE_LAPSE_GERIATRIC_EXTRA if self.is_geriatric else 0)
            if self.calories <= -CALORIE_LIMIT:
                if self.hunger > 0:
                    self.hunger -= 1
                else:
                    self.care_mistakes += 1      # DM20: starving with the call unanswered
                self.calories = CALORIE_LIMIT
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
        # bedtime: sleep through the night, or pass out if run to exhaustion by
        # day; a grace window after a manual wake lets you interact at night
        self._wake_grace = max(0.0, getattr(self, "_wake_grace", 0.0) - dt)
        if not self.asleep and self._wake_grace <= 0 and (night or self.energy <= 0):
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
        return CALORIE_DECAY_SEC * (self._phys().get("hunger_decay", 60) / REF_HUNGER_COEF)

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
        self.element = r.get("element", self.element)
        _req = data.load_requirements().get(num, {})
        self.max_energy = _req.get("max_energy", self.max_energy)
        self._sleep_energy_gain = _req.get("sleep_energy_gain", 3)
        self.energy = min(self.energy, self.max_energy)   # DVPet clamps to new max (no auto-refill)
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.trainings = 0
        self.injuries = self.sick_count = 0
        self.sick = False
        self.sick_length = self.inj_length = self.fatigue_length = 0.0
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
        return (self.hunger >= 3 and self.energy > self.max_energy // 2 and self.poop == 0
                and not self.sick and not self.is_injured() and not self.is_fatigued())

    def _set_energy(self, value):
        """DVPet setEnergy: clamp to [-max_energy, +max_energy]."""
        self.energy = _clamp(int(round(value)), -self.max_energy, self.max_energy)

    def energy_pct(self):
        return max(0, self.energy) * 100 // self.max_energy if self.max_energy else 0

    @property
    def dp(self):
        """DM20 battle power (DP): the pet's total attribute power (vaccine+data+virus)."""
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

    def _add_dp(self, amount):
        """Route DP gain into the pet's own attribute pool (DM20 protein DP restore)."""
        attr = self.attribute if self.attribute in ("Vaccine", "Data", "Virus") else "Vaccine"
        if attr == "Vaccine":
            self.vaccine += amount
        elif attr == "Data":
            self.data_power += amount
        else:
            self.virus += amount

    def feed(self, food=None):
        """DM20 feeding: two foods only. Meat fills a hunger heart; Protein fills a
        strength heart, adds weight and restores a little DP (manual). No taste,
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
            self._add_dp(PROTEIN_DP_RESTORE)                # DM20: protein restores DP
            self._set_anim("eat", 1.4)
            return f"Fed {food['name']}."
        if self.hunger >= 4:                                 # Meat, already full -> overfeed
            self.weight += 1
            self.overeat += 1
            self.calories = CALORIE_LIMIT
            self._poop_t = min(self._poop_interval, getattr(self, "_poop_t", 0) + 900)   # overeat -> sooner poop
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + max(1, food["hunger"]), 0, 4)
        self.calories = CALORIE_LIMIT                       # a meal refills the calorie buffer
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
        if self.is_fatigued():
            self._set_anim("exhausted", 1.2)
            return "Too fatigued — let it rest."
        if self.energy <= 0:                            # MinEnergyForActivity
            self._set_anim("refuse", 1.0)
            return "Too tired to train."
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
        self._set_energy(self.energy - 1)               # ExerciseEnergyDec
        if self.energy <= 0 and random.randint(0, 99) < FATIGUE_CHANCE:   # trained to exhaustion
            self._fatigue()
        # training while overweight risks an injury
        if evolution.weight_category(self.weight, self._base_weight()) == "Over" and random.random() < 0.5:
            self._injure()
        self._check_worse_injury(in_battle=False)        # drilling an injured pet can worsen it
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
        if self.is_fatigued():
            self._set_anim("exhausted", 1.2)
            return "Too fatigued — let it rest."
        if self.energy <= 0:                            # MinEnergyForActivity
            self._set_anim("refuse", 1.0)
            return "Too tired to battle."
        return None

    def record_battle(self, won, enemy=None):
        """Resolve a finished battle: update battles/wins and rewards."""
        self.battles += 1
        self._set_energy(self.energy - 1)               # battle energy (BattleWon/LostEnergyDec)
        self._check_worse_injury(in_battle=True)         # battling injured can worsen it
        if won:
            self.wins += 1
            self._set_anim("happy", 2.0)                  # reactive cheer (no mood meter)
            return "Victory!"
        if random.random() < 0.3:
            self._injure()
        self._set_anim("sad", 2.0)                        # reactive dejection
        return "Defeat..."

    def is_fatigued(self):
        """PhysicalState.isFatigued: worn out until the fatigue length counts down."""
        return self.fatigue_length > 0

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

    def has_vitamin(self):
        """PhysicalState.hasVitamin: a vitamin is active, guarding against worse injuries."""
        return self.vitamin_lapse > 0

    def has_medicine(self):
        """PhysicalState.getMed: medicine is still active (the medicine state icon shows)."""
        return self.med_lapse > 0

    def has_bandage(self):
        """PhysicalState.getBandage: a bandage is still on (the bandage state icon shows)."""
        return self.bandage_lapse > 0

    def feed_vitamin(self):
        """PhysicalState.feedVitamin: top up injury-worsening protection."""
        self.vitamin_lapse = VITAMIN_HOURS

    def _worsen_injury(self):
        """PhysicalState.worsenedInjury: the injury gets worse -- extended, with an energy
        cost (the WorseInjuryLifeDec lifespan hit is omitted)."""
        self.inj_length += random.randint(MIN_INJ_LENGTH, MAX_INJ_LENGTH) * INJ_LAPSE_MIN
        self._set_energy(self.energy - WORSE_INJ_ENERGY_DEC)

    def _check_worse_injury(self, in_battle):
        """calcWorse{Exercise,Battle}Inj: pushing an already-injured pet can worsen the
        injury, at a chance set by weight and whether a vitamin is active."""
        if not self.is_injured():
            return
        table = WORSE_INJ_BATTLE if in_battle else WORSE_INJ_EXERCISE
        good_weight = evolution.weight_category(self.weight, self._base_weight()) == "Healthy"
        if good_weight:
            factor = table["good_v"] if self.has_vitamin() else table["good_nv"]
        else:
            factor = table["bad_v"] if self.has_vitamin() else table["bad_nv"]
        if random.randint(0, WORSE_INJ_CHANCE - 1) < factor:
            self._worsen_injury()

    def _fatigue(self):
        """PhysicalState.fatigue: the pet collapses from over-exertion — an energy hit,
        then it must rest the fatigue length off (FatigueMin..FatigueMax game-min)."""
        self.fatigue_length = max(FATIGUE_MIN, random.randint(FATIGUE_MIN, FATIGUE_MAX))
        self._set_energy(self.energy - FATIGUE_ENERGY_DEC)
        self._set_anim("exhausted", 2.0)

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
        if self.is_fatigued():
            return "fatigued"
        if self.is_injured():
            return "injured"
        if self.hunger == 0:
            return "starving"
        if self.poop >= 3:
            return "needs cleaning"
        if self.day_phase == "night" and not self.asleep and self.energy < self.max_energy // 2:
            return "sleepy"
        if self._well_cared():
            return "happy"
        return "ok"
