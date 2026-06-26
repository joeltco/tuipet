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

# DVPet mood model (config.csv): a signed score mapped to a Mood enum.
MOOD_MIN, MOOD_MAX = -300, 300        # MinMood / MaxMood
MIN_HAPPY_MOOD = 150                  # MinHappyMood
MIN_UNHAPPY_MOOD = -1                 # MinUnhappyMood
TO_DEPRESSED_MOOD = -250              # ToDepressedMoodMin
NEW_UNDEPRESSED_MOOD = -50            # NewUndepressedMood
MIN_ENTHUSIASM, MAX_ENTHUSIASM = -10, 10   # MinEnthusiasm / MaxEnthusiasm
MAX_ENTHUSIASM_MOOD_PENALTY = 10           # MaxEnthusiasmMoodPenalty
# enthusiasmLapse (every EnthusiasmLapseMin=59 game-min == tuipet's mood lapse): awake, an
# unspent spirit sours the mood (mood -= |enth*EnthusiasmMoodDecCoefficient|) and an energetic
# pet's spirit climbs; asleep it decays toward 0.  Spending spirit on activities keeps the
# drain small -- a "stay engaged" mechanic.
ENTHUSIASM_MOOD_DEC_COEF = 2               # EnthusiasmMoodDecCoefficient
ENTHUSIASM_CHANGE_ENERGY_COEF = 24         # EnthusiasmChangeEnergyCoefficient
HIGH_ENERGY_ENTH_CHANGE = 1                # HighEnergyEnthusiasmChange (energetic -> spirit up)
LOW_ENERGY_ENTH_CHANGE = 0                 # LowEnergyEnthusiasmChange
ENTHUSIASM_LAPSE_DEC = 1                   # EnthusiasmLapseDec (asleep, +enth -> 0)
ENTHUSIASM_LAPSE_INC = 2                   # EnthusiasmLapseInc (asleep, -enth -> 0)

# DVPet obedience + battle-surrender morale (config.csv column 1, where CanRefuse=TRUE;
# Config.loadConfig strips the name column and PhysicalState loads column 0 => the first
# value column).  Drives PhysicalState.getObedienceFactors / getAdjustedObedience /
# checkSurrender — the pet may give up or beg to flee a battle based on disposition,
# obedience, health and win-rate.  Every number is verbatim from the binary.
CAN_REFUSE = True
REFUSE_CHANCE = 100                 # RefuseRate -> Random.nextInt(REFUSE_CHANCE)
OBEDIENCE_REFUSAL_CAP = 100         # ObedienceRefusalCap
OBEDIENCE_MOOD_MOD = 15.0           # ObedienceMoodModCoefficient
OBEDIENCE_TIME_MOD = 10.0           # ObedienceTimeModCoefficient
# PhysicalState.spoil (config SpoilMoodInc / SpoilObedienceDec): a mood lift paired
# with an obedience cost. tuipet's Play button maps onto this DVPet mechanic.
SPOIL_MOOD_INC = 10                 # SpoilMoodInc
SPOIL_OBEDIENCE_DEC = 10            # SpoilObedienceDec
OBEDIENCE_ENTH_MOD = 6.0            # ObedienceEnthusiasmModCoefficient
REFUSE_UNWELL_SICK = -10.0          # RefuseUnwellModSickFactor
DEPRESSED_OBEDIENCE = 50.0          # DepressedObedience
SURR_HEALTH_COEF = 5.0              # SurrenderChanceHealthCoefficient
SURR_DISP_COEF = 5.0                # HighDispositionSurrenderChanceDispositionCoefficient
HD_CONT_HI_HP, HD_CONT_LO_HP = 30.0, -10.0    # HighDispositionContinueChance*HealthFactor
HD_CONT_HI_EHP, HD_CONT_LO_EHP = -10.0, 25.0  # HighDispositionContinueChance*EnemyHealthFactor
HD_SURR_HI_HP, HD_SURR_LO_HP = -10.0, 10.0     # HighDispositionSurrenderChance*HealthFactor
LD_CONT_HI_HP, LD_CONT_LO_HP = 60.0, 0.0       # LowDispositionContinueChance*HealthFactor
LD_SURR_HI_EHP, LD_SURR_LO_EHP = 5.0, -60.0    # LowDispositionSurrenderChance*EnemyHealthFactor
SURR_HI_EHP, SURR_LO_EHP = 10.0, 30.0          # SurrenderChance*EnemyHealthFactor
SURR_HI_FACTOR, SURR_LO_FACTOR = 3.0, 0.75     # SurrenderChanceHigh/LowFactor
SURR_HI_WINRATE_MIN = 0.4                       # SurrenderChanceHighFactorWinRateMin
# aftermath (ClockTic.surrenderEffect / surrender-reject / Battle.surrender)
SURR_EFFECT_MOOD_INC = 10               # SurrenderEffectMoodInc
SURR_EFFECT_LOWDISP_MOOD_DEC = 20       # SurrenderEffectLowDispositionMoodDec
SURR_EFFECT_REQ_OBED_DEC = 10           # SurrenderEffectRequestObedienceDec
SURR_EFFECT_OBED_DEC = 1                # SurrenderEffectObedienceDec
SURR_EFFECT_REQ_LOWHP_OBED = 15         # SurrenderEffectRequestLowHealthObedienceInc (setObedience)
SURR_REJECT_MOOD_DEC = 10               # SurrenderRejectMoodDec
SURR_REJECT_OBED_INC = 1                # SurrenderRejectObedienceInc
SURR_ENTH_DEC = 3                       # SurrenderEnthusiasmDec
# --- DNA system (DVPet DNA.class + PhysicalState.applyDNA + config.csv) ---
MAX_DNA_INVENTORY = 99                  # config MaxDNAInventory
DNA_STRENGTH_CHANGE = 1                 # config DNAStrengthChange
DNA_SAME_FIELD_MOOD, DNA_DIFF_FIELD_MOOD = 1, -1
DNA_SAME_FIELD_ENTH_DEC, DNA_DIFF_FIELD_ENTH_DEC = 3, 6
DNA_SAME_FIELD_SICK, DNA_DIFF_FIELD_SICK = 1, 2     # checkSick target out of SICK_BOUND
DNA_SICK_BOUND = 100                    # config SickChance / WorseSickChance bound
DNA_FULFILLED_RATE = 2                  # config DNAFulfilledRate (priority weight per met field)

# DVPet ClockTic.getDNARate: the DNA-generate mini-game maps your mash-rate (which,
# at the 10s mark, equals your total presses) onto one of these 8-wide Field bands
# (config _<field>RateMaxMiniGame). Too slow (<=8) or over-mashed (>80) -> None = a
# wasted wager. Faster mashing reaches the rarer late fields (DarkArea needs 73-80).
DNA_RATE_BANDS = (
    (8, "None"), (16, "DeepSaver"), (24, "JungleTrooper"), (32, "NatureSpirit"),
    (40, "WindGuardian"), (48, "DragonsRoar"), (56, "MetalEmpire"),
    (64, "NightmareSoldier"), (72, "VirusBuster"), (80, "DarkArea"),
)


def dna_field_for_rate(rate):
    """DVPet getDNARate: the Field a mini-game rate yields (None if over/under-mashed)."""
    for hi, field in DNA_RATE_BANDS:
        if rate <= hi:
            return field
    return "None"
# --- food taste (DVPet Taste<Food> + Rank + config.csv) ---
RANK_LIMIT, RANK_MIN = 200, -200       # config RankLimit / RankMinimum
RANK_CHANGE_FOOD = 1                    # config RankChangeFood (per meal)
RANK_PREF_INC = 2                       # config RankChangeSpeciesPreferenceInc (species like/dislike bias)
RANK_DISLIKED = -2                      # config RankChangeDisliked
RANK_AFTER_FAV = 20                     # config RankChangeAfterFav (decay other ranks toward 0)
FAV_FOOD_MOOD = 10                      # config FavFoodMoodInc
FOOD_MOOD = 2                           # config FoodMoodInc (neutral food)
FAV_FOOD_ENTH = 1                       # config FavFoodEnthusiasmInc
DISLIKED_FOOD_OBEDIENCE = -1            # config DislikedFoodObedienceChange
INTOL_FOOD_SICK_CHANCE = 50            # config IntolerantFoodSickChance (per roll, x2 rolls)

# DVPet poop / filth (config.csv, PhysicalState.poop / poopWaitMoodCheck).  A bowel
# movement bumps mood, sheds a little weight and drops a pile of a size set by the
# Digimon's base weight; an uncleaned mess then nags the mood until it is cleaned.
POOP_MOOD_INC = 10                      # PoopMoodInc (relief)
POOP_WEIGHT_DEC_COEF = 0.1             # PoopWeightDecCoefficient
POOP_WEIGHT_LIMIT = 4                   # PoopWeightLimit (max weight lost per poop)
POOP_INC_WEIGHT_FACTOR = 40            # PoopIncWeightFactor -> size 3 at/above
POOP_INC_WEIGHT_FACTOR_SMALL = 15      # PoopIncWeightFactorSmall -> size 1 at/below
POOP_WAIT_MOOD = -1                     # PoopWaitMoodChange (mess nags)
LARGE_POOP_WAIT_MOOD = -2              # LargePoopWaitMoodChange (a big mess nags more)
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

# DVPet discipline (config.csv, PhysicalState.praise / scold / checkPraiseScoldWindow).
# The pet flags a praise window after a good deed and a scold window after a bad one;
# praising/scolding while the matching window is open trains obedience, the mistimed
# response penalizes it.  Deltas verbatim; windows age on the mood-lapse cadence.
PRAISE_HIGH_DISP_MOOD_INC = 10          # PraiseHighDispositionMoodInc
PRAISE_LOW_DISP_MOOD_INC = 6            # PraiseLowDispositionMoodInc
PRAISE_NONCOMPLIANT_OBED_DEC = 2        # PraiseNoncompliantObedienceDec
CORRECT_PRAISE_OBED = {0: 3, 1: 5, -1: 1}   # CorrectPraiseObedienceInc[/High/Low]
PRAISE_SCOLD_MOOD_INC = 10              # PraiseScoldMoodInc (mis-praise during scold window)
PRAISE_SCOLD_ENTH = 5                   # PraiseScoldEnthusiasmChange (setEnthusiasm)
PRAISE_SCOLD_OBED_DEC = 8               # PraiseScoldObedienceDec
SCOLD_OBED_INC = 1                      # ScoldObedienceInc
SCOLD_HIGH_OBED_MOOD = 75               # ScoldHighObedienceMood threshold
SCOLD_HIGH_OBED_MOOD_DEC = 5            # ScoldHighObedienceMoodDec
SCOLD_LOW_OBED_MOOD_DEC = 15            # ScoldLowObedienceMoodDec
CORRECT_SCOLD_OBED = {0: 0, 1: 2, -1: 0}    # CorrectScoldObedienceInc[/High/Low]
CORRECT_SCOLD_ENTH = -1                 # CorrectScoldEnthusiasmChange
SCOLD_ENTH = -3                         # ScoldEnthusiasmChange (scold outside any window)
SCOLD_PRAISE_MOOD_DEC = 10              # ScoldPraiseMoodDec (mis-scold during praise window)
SCOLD_PRAISE_ENTH_DEC = 6              # ScoldPraiseEnthusiasmDec
SCOLD_PRAISE_OBED = {0: 1, 1: 3, -1: 0}     # ScoldPraiseObedienceInc[/High/Low]
DISCIPLINE_SCOLD_OBED_INC = 2           # DisciplineCallScoldObedienceInc (a fair scold)
PRAISE_WINDOW_MAX = 2                    # PraiseWindowMax (lapses the window stays open)
SCOLD_WINDOW_MAX = 2                     # ScoldWindowMax
# auto disciplineCall (checkDisciplineCall): the pet spontaneously acts up on the
# DisciplineCallMin cadence -- chance = randomChance(TargetChance+careAdjust,
# DisciplineCallChance-(ObedienceRefusalCap-obedience)); well-behaved grown pets are
# exempt.  DisciplineCallMin=59 game-min maps onto tuipet's ~59s mood-lapse (Joel's
# cadence-scaling choice), numbers verbatim.
DISCIPLINE_TARGET_CHANCE = 16            # DisciplineCallTargetChance
DISCIPLINE_CALL_CHANCE = 150             # DisciplineCallChance (randomChance bound base)
DISCIPLINE_TARGET_GLUTTON = 3            # DisciplineCallTargetGluttonChange
DISCIPLINE_TARGET_RESTLESS_HI = 3        # restless & under-exercised acts up more
DISCIPLINE_TARGET_RESTLESS_LO = -1
DISCIPLINE_OBEDIENCE_MAX = 50            # DisciplineCallObedienceMax (grown + obedient => exempt)

# DVPet fatigue (config.csv, PhysicalState.fatigue / checkFatigueLapse): training to
# exhaustion can leave the pet fatigued for FatigueMin..FatigueMax game-minutes -- a big
# one-time mood/energy/spirit hit, and it cannot act until it has rested off the clock.
# isFatigued() == fatigue_length > 0; the length counts down in game-minutes (1 game-min
# ~= 1s under tuipet's clock).  Habitat-compatibility length mods and the lifespan hit
# are omitted (documented); deltas verbatim.
FATIGUE_MIN = 5                          # FatigueMin
FATIGUE_MAX = 60                         # FatigueMax
FATIGUE_MOOD_DEC = 50                    # FatigueMoodDec (the exhaustion hit)
FATIGUE_ENERGY_DEC = 1                   # FatigueEnergyDec
FATIGUE_ENTH_CHANGE = -1                 # FatigueEnthusiasmChange
ALREADY_FATIGUED_MOOD_DEC = 35           # alreadyFatiguedMoodDec (re-fatigued while down)
TRAIN_POWER_PER_HIT = 2     # attribute power per drill-hit (compression-scaled from DVPet's flat +1)
FATIGUE_CHANCE = 60                      # FatigueChance (% on an exhausting drill)

# DVPet sickness & injury durations (config.csv, PhysicalState.sicken / injure): an
# illness or injury lasts Min..MaxLength recovery lapses (SickLapseMin/InjLapseMin game-min
# each) and then clears on its own; onset costs mood/spirit.  Habitat-compat length mods
# omitted (documented); deltas verbatim.  Cured early by medicine as before.
SICK_MOOD_DEC = 50                       # SickMoodDec
INJ_MOOD_DEC = 50                        # InjuryMoodDec
SICK_ENTH_CHANGE = -1                    # SickEnthusiasmChange
INJ_ENTH_CHANGE = -1                     # InjuryEnthusiasmChange
MIN_SICK_LENGTH, MAX_SICK_LENGTH = 1, 10     # Min/MaxSickLength (recovery lapses)
MIN_INJ_LENGTH, MAX_INJ_LENGTH = 1, 12       # Min/MaxInjLength
SICK_LAPSE_MIN = 29                      # SickLapseMin (game-min per recovery lapse)
# DVPet GoodNutrition (config.csv): 3 macros accumulate from food and decay each lapse; all
# >= GoodNutritionMinimum gives a "well-fed" buff. Foods are specialised (Meat=protein,
# Fruit=vitamin, Veg=mineral), so good nutrition rewards a VARIED diet.
GOOD_NUTRITION_MIN = 16        # GoodNutritionMinimum
MAX_MACRO = 24                 # MaxProtein / MaxVitamin / MaxMineral
NUTRITION_LAPSE_CHANGE = -3    # NutritionLapseChange (decay per lapse)
NUTRITION_LAPSE_SEC = 600.0    # tuipet cadence for macro decay (real-time adaptation)
GOOD_NUTR_RECOVERY_MULT = 2.0  # GoodNutrition{Sick,Inj,Fatigue}LapseChange=-1 -> ~2x recovery
GOOD_NUTR_LIFESPAN_COEF = 0.5  # GoodNutritionLifespanDecCoefficient (slower lifespan loss)
GOOD_NUTR_SICK_MULT = 40 / 60  # GoodNutritionFatigueChance(40) / FatigueChance(60)
INJ_LAPSE_MIN = 29                       # InjLapseMin

# DVPet injury worsening + vitamins (config.csv, calcWorse{Exercise,Battle}Inj /
# worsenedInjury / feedVitamin): pushing an injured pet (training/battling) can worsen the
# injury -- extending it and costing mood/obedience/energy/spirit -- at a chance set by
# weight and whether a vitamin is active.  Chances are factor/WorseInjuryChance.  No shipped
# item is flagged Vitamin in items.csv, so has_vitamin() defaults false (the no-vitamin
# rates apply); the grant path (feed_vitamin / a "vitamin" consumable flag) is wired and
# ready.  Values verbatim from config.csv column 1; WorseInjuryLifeDec lifespan hit omitted.
WORSE_INJ_CHANCE = 100                   # WorseInjuryChance / WorseBattleInjuryChance (bound)
WORSE_INJ_EXERCISE = {"bad_nv": 10, "good_nv": 1, "good_v": 0, "bad_v": 5}   # WorseInjury*
WORSE_INJ_BATTLE = {"bad_nv": 15, "good_nv": 5, "good_v": 0, "bad_v": 5}     # WorseBattleInjury*
WORSE_MALADY_MOOD_DEC = -35              # worseMaladyMoodDec
WORSE_MALADY_OBED_DEC = -10              # worseMaladyObedienceDec
WORSE_INJ_ENERGY_DEC = 1                 # WorseInjuryEnergyDec
WORSE_INJ_ENTH_CHANGE = -1               # WorseInjuryEnthusiasmChange
VITAMIN_HOURS = 60                       # VitaminHours (game-min of injury-worsening protection)
MEDICINE_HOURS = 60                      # MedicineHours (game-min the medicine indicator lingers, config.csv)
BANDAGE_HOURS = 60                       # BandageHours (game-min the bandage indicator lingers, config.csv)

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
    hunger: int = 4                 # hearts 0..4 (4 = full); FullHunger=4
    calories: int = 4               # DVPet calorie buffer, -CALORIE_LIMIT..+CALORIE_LIMIT
    strength: int = 2               # effort hearts 0..4; FullStrength=4
    energy: int = 24                # DVPet energy, -max_energy..+max_energy (full at max_energy)
    max_energy: int = 24            # per-Digimon (digimon.csv MaxEnergy)
    mood: int = 0                   # DVPet signed mood (MinMood..MaxMood); Neutral at 0
    enthusiasm: int = 0             # DVPet spirit, MinEnthusiasm..MaxEnthusiasm (separate from mood)
    weight: int = 20
    poop: int = 0                   # pile count == DVPet countFilth()
    poop_sizes: list = _dcf(default_factory=list)   # per-pile size 1..4 (DVPet _filth bytes)
    sick: bool = False
    asleep: bool = False
    lights: bool = True             # DVPet _lights: room-light toggle, SEPARATE from sleep
    care_mistakes: int = 0
    dna_owned: dict = _dcf(default_factory=lambda: {f: 0 for f in data.DNA_FIELDS})    # banked
    dna_applied: dict = _dcf(default_factory=lambda: {f: 0 for f in data.DNA_FIELDS})  # charged
    food_ranks: dict = _dcf(default_factory=lambda: {c: 0 for c in data.FOOD_CATEGORIES})
    food_eaten: dict = _dcf(default_factory=lambda: {c: 0 for c in data.FOOD_CATEGORIES})
    favorite_food: str = ""             # emerges at rank +RankLimit
    disliked_food: str = ""             # emerges at rank -RankLimit
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
    # personality traits: fixed at hatch (DVPet randPersonalityTraits), each in {-1,0,+1}.
    # Distinct from the overeat/disturb care counters, which drive evolution.
    disposition: int = 0
    glutton: int = 0
    restless: int = 0
    exercise_today: int = 0         # DVPet _exercise: drills done today (resets daily)
    # discipline windows (DVPet _praise/_scold + their aging windows)
    praise_flag: bool = False       # a good deed is awaiting praise
    scold_flag: bool = False        # a bad deed is awaiting a scolding
    praise_window: int = 0          # lapses since the praise flag opened
    scold_window: int = 0
    compliance: bool = True         # DVPet _compliance (a fair scold restores it)
    fatigue_length: float = 0.0     # DVPet _fatigueLength (game-min remaining; >0 == fatigued)
    sick_length: float = 0.0        # DVPet _sickLength (game-min until natural recovery)
    inj_length: float = 0.0         # DVPet _injLength (game-min until the injury heals)
    vitamin_lapse: float = 0.0      # DVPet _vitaminLapse (game-min of injury-worsening protection)
    med_lapse: float = 0.0          # DVPet _medLapse: medicine indicator after curing sickness (getMed)
    bandage_lapse: float = 0.0      # DVPet _bandageLapse: bandage indicator after mending an injury (getBandage)
    nutr_protein: int = 0           # DVPet _protein (0..MaxProtein), from a meaty diet
    nutr_mineral: int = 0           # DVPet _mineral, from vegetables
    nutr_vitamin: int = 0           # DVPet _vitamin, from fruit
    battles: int = 0
    levels_fought: list = _dcf(default_factory=list)  # opponent levels beaten this stage (DVPet _levelsFought)
    bits: int = 0
    trophies: int = 0
    trophies_won: dict = _dcf(default_factory=dict)   # trophy id -> season won (per-season earned)
    adv_map: int = 0
    adv_zone: int = 0
    adv_seek: bool = False    # Disaster Transport: next adventure leg forces an encounter
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
    habitat_record: dict = _dcf(default_factory=dict)   # time-in-each-habitat -> getMajorHabitat
    time_pref: dict = _dcf(default_factory=lambda: {"dawn": 0, "day": 0, "dusk": 0, "night": 0})
    x_antibody: str = "None"
    effect_id: int = -1            # active care effect (careEffect.csv id; -1 = none)
    effect_t: float = 0.0          # remaining duration of the active care effect
    x_count: float = 0.0
    train_time: str = ""            # time of day of the last training (gates some evolutions)
    inventory: dict = _dcf(default_factory=dict)
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
        self._rand_personality_traits()               # fix disposition/glutton/restless for life
        if self.x_antibody == "None" and random.randint(0, X_BIRTH_BOUND - 1) < X_BIRTH_TARGET:
            self._set_xantibody("Permanent")          # born a natural X-Antibody carrier

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

    def _rand_personality_traits(self):
        """PhysicalState.randPersonalityTraits: each trait rolls Random.nextInt(3) ->
        {0:-1, 1:0, 2:+1} and is fixed for life (only assigned while still neutral)."""
        def roll(cur):
            if cur != 0:
                return cur
            r = random.randint(0, 2)
            return -1 if r < 1 else (1 if r > 1 else 0)
        self.restless = roll(self.restless)
        self.glutton = roll(self.glutton)
        self.disposition = roll(self.disposition)

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
            # the 3s hatch is advanced at frame cadence (10 Hz) via advance_hatch();
            # a 1 Hz countdown here would skip the crack frames (only 3 coarse steps).
            return

        if self.stage != "Egg":
            self._temperature_effects(dt)
            self._track_time_pref(dt)
            day = int(self.world_seconds // DAY_LENGTH)
            if getattr(self, "_exercise_day", -1) != day:    # DVPet checkExerciseTime: daily reset
                self._exercise_day = day
                self.exercise_today = 0
            _rec = dt * (GOOD_NUTR_RECOVERY_MULT if self.good_nutrition() else 1.0)  # well-fed heals faster
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
        self._tick_effect(dt)
        if self.asleep:
            # DVPet sleep recovery: +SleepEnergyGain every SleepMinutesToEnergyGain.
            self._sleep_e_t = getattr(self, "_sleep_e_t", 0.0) + dt
            if self._sleep_e_t >= 60:                # SleepMinutesToEnergyGain (game-min)
                self._sleep_e_t = 0.0
                self._set_energy(self.energy + getattr(self, "_sleep_energy_gain", 3))
            # asleep enthusiasmLapse: spirit settles toward 0 while resting
            self._enth_lapse_t = getattr(self, "_enth_lapse_t", 0.0) + dt
            if self._enth_lapse_t >= 59:
                self._enth_lapse_t = 0.0
                if self.enthusiasm > 0:
                    self._set_enthusiasm(self.enthusiasm - ENTHUSIASM_LAPSE_DEC)
                elif self.enthusiasm < 0:
                    self._set_enthusiasm(self.enthusiasm + ENTHUSIASM_LAPSE_INC)
            # sleep through the night; wake in the morning once fully rested
            if self.day_phase != "night" and self.energy >= self.max_energy:
                self.asleep = False
                self._set_anim("wake", 1.6)  # morning stretch (DVPet wakeUp())
            return

        night = self.day_phase == "night"
        # DVPet has NO passive energy decay -- energy only drops from activity
        # (exercise/battle/travel) and refills during sleep.
        # DVPet mood lapse (~MoodLapseMin game-min): Happy drains, Unhappy recovers,
        # Neutral settles toward 0 (config *MoodLapse* values).
        self._mood_lapse_t = getattr(self, "_mood_lapse_t", 0.0) + dt
        if self._mood_lapse_t >= 59:
            self._mood_lapse_t = 0.0
            m = self.current_mood()
            if m == "Happy":
                self._set_mood(self.mood - 10)           # HappyMoodLapseDec
            elif m == "Depressed":
                self._set_mood(self.mood + 10)           # VeryUnhappyMoodLapseInc (climb out)
            elif m == "Unhappy":
                self._set_mood(self.mood + 5)            # UnhappyMoodLapseInc
            elif self.mood > 0:
                self._set_mood(self.mood - 1)            # NeutralMoodLapseDec toward 0
            elif self.mood < 0:
                self._set_mood(self.mood + 1)
            if self.poop > 0 and self._phys().get("filth_mood", -1):   # some species are unbothered by filth
                self._set_mood(self.mood + (LARGE_POOP_WAIT_MOOD if self.poop >= 3 else POOP_WAIT_MOOD))
            # discipline windows age (checkPraiseScoldWindow); a missed window closes
            if self.praise_flag:
                self.praise_window += 1
                if self.praise_window > PRAISE_WINDOW_MAX:
                    self.praise_flag, self.praise_window = False, 0
            if self.scold_flag:
                self.scold_window += 1
                if self.scold_window > SCOLD_WINDOW_MAX:
                    self.scold_flag, self.scold_window = False, 0
            self._check_discipline_call()                # the pet may spontaneously act up
            # awake enthusiasmLapse (mood -= |enth*EnthusiasmMoodDecCoefficient|, then an energetic
            # pet's spirit climbs HighEnergyEnthusiasmChange) stays DEFERRED -- and this was measured,
            # not assumed: ported faithfully it collapses mood to Unhappy/Depressed within ~15 real-min
            # whatever the play style, because the only awake spirit-restoring force is +1/lapse while
            # activities cost -3..-6, so under tuipet's ~60x clock |enthusiasm| pins at 10 and the drain
            # sticks at -20/lapse (active play is WORSE, driving enth to -10). It needs the real-time
            # clock to balance; DVPet numbers are NOT softened. Asleep decay (below) IS ported.
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
                    self.care_mistakes += 1
                    self._open_scold()           # neglect: the pet acts up
                self.calories = CALORIE_LIMIT
        # pooping (DVPet poop(): relief mood bump, sheds weight, drops a sized pile)
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
        # nutrition macros decay each lapse (NutritionLapseChange) -- keep a varied diet up
        self._nutr_t = getattr(self, "_nutr_t", 0.0) + dt
        if self._nutr_t >= NUTRITION_LAPSE_SEC:
            self._nutr_t = 0.0
            self.nutr_protein = max(0, self.nutr_protein + NUTRITION_LAPSE_CHANGE)
            self.nutr_mineral = max(0, self.nutr_mineral + NUTRITION_LAPSE_CHANGE)
            self.nutr_vitamin = max(0, self.nutr_vitamin + NUTRITION_LAPSE_CHANGE)
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
                    self.care_mistakes += 1
                    self._open_scold()       # left in filth: the pet acts up
        else:
            self._filth_t = 0                # cleaned / under the limit resets the call timer
        # sickness from filth / starvation
        if (self.poop >= 3 or self.hunger == 0) and not self.sick \
                and random.random() < 0.02 / self._phys().get("poop_sick_mult", 1.0) * dt \
                        * (GOOD_NUTR_SICK_MULT if self.good_nutrition() else 1.0):
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
        self.habitat_record[self.habitat] = self.habitat_record.get(self.habitat, 0) + dt
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
        self.lifespan -= extra * dt * (GOOD_NUTR_LIFESPAN_COEF if self.good_nutrition() else 1.0)
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
        if self.weather in _PRECIP and len(frames) > 4:
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

    def major_habitat(self):
        """DVPet getMajorHabitat: the habitat lived in the MOST (evolution gates on this,
        not the current home). Falls back to the current habitat early on / on ties."""
        rec = self.habitat_record
        if not rec:
            return self.habitat
        return max(rec, key=lambda hid: (rec[hid], hid == self.habitat))

    def _track_time_pref(self, dt):
        # the pet warms to the times of day it spends happy in, and sours on the
        # rest -- DVPet's timeRanks favorite/disliked, kept lightweight
        d = 1 if self.mood >= MIN_HAPPY_MOOD else (-1 if self.mood <= MIN_UNHAPPY_MOOD else 0)
        if d:
            ph = self.day_phase
            self.time_pref[ph] = _clamp(self.time_pref.get(ph, 0) + d, -90, 90)

    def _disposition(self):
        return self.disposition          # DVPet _disposition: fixed personality trait

    def _glutton(self):
        return self.glutton

    def _restless(self):
        return self.restless

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
        self.habitat = hid                 # buying a new home moves you in (moving is free anyway)
        self._weather_day = -1             # fresh climate roll on arrival, like move_to
        return f"Bought {h['name']} — moved in!"

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

    def _tick_effect(self, dt):
        """Advance the active care effect (Futon): rate gains; end on sleep change / expiry."""
        if self.effect_id < 0:
            return
        eff = data.load_care_effects().get(self.effect_id)
        if not eff:
            self.effect_id, self.effect_t = -1, 0.0
            return
        if eff["end_on_sleep"] and getattr(self, "_eff_asleep", self.asleep) != self.asleep:
            self.effect_id, self.effect_t = -1, 0.0          # dozing off / waking ends it
            return
        self._eff_asleep = self.asleep
        self.effect_t -= dt
        if self.effect_t <= 0:
            self.effect_id, self.effect_t = -1, 0.0
            return
        self._eff_acc = getattr(self, "_eff_acc", 0.0) + dt
        while self._eff_acc >= 60:                            # uniform 60-tick cadence (the one defined effect)
            self._eff_acc -= 60
            if eff["mood"][0]:
                self._set_mood(self.mood + eff["mood"][0])
            if eff["energy"][0]:
                self._set_energy(self.energy + eff["energy"][0])
            if eff["hunger"][0]:
                self.hunger = _clamp(self.hunger + eff["hunger"][0], 0, 4)
            if eff["strength"][0]:
                self.strength = _clamp(self.strength + eff["strength"][0], 0, 4)

    def effect_name(self):
        eff = data.load_care_effects().get(self.effect_id) if self.effect_id >= 0 else None
        return eff["name"] if eff else ""

    def call_paused(self):
        """True if the active care effect suppresses the care-need call (Futon PauseCall)."""
        if self.effect_id < 0:
            return False
        eff = data.load_care_effects().get(self.effect_id)
        return bool(eff and eff["pause_call"])

    def _temperature_effects(self, dt):
        if self.effect_id >= 0:
            eff = data.load_care_effects().get(self.effect_id)
            if eff and eff["pause_temp"]:
                return                                       # Futon: temperature paused
        lo, hi = self.ideal_temp
        aff = self._affinity()                # compatible home helps, incompatible hurts
        too_hot = self.temp >= hi + wx.UPPER_IDEAL
        too_cold = self.temp <= lo - wx.LOWER_IDEAL
        self._comfort_t = getattr(self, "_comfort_t", 0.0) + dt
        if self._comfort_t >= wx.IDEAL_TEMP_MOOD_SEC:
            self._comfort_t = 0.0
            if lo <= self.temp <= hi:
                self._set_mood(self.mood + wx.IDEAL_TEMP_INC + aff)
            elif too_hot or too_cold:
                self._set_mood(self.mood - wx.IDEAL_TEMP_DEC + aff)
        # bad-temperature sickness is DISABLED in classic mode (config SickChanceBadTemp=0;
        # only hardcore enables it) -- temperature drives mood, not illness. An incompatible
        # habitat is still unhealthy (DVPet incompatibleField/ElementSickChanceChange).
        self._btemp_t = getattr(self, "_btemp_t", 0.0) + dt
        if self._btemp_t >= wx.BAD_TEMP_SICK_SEC:
            self._btemp_t = 0.0
            if not self.sick and aff < 0 and random.random() < 0.004 * (-aff):
                self._sicken()

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

    # ---- DNA (DVPet DNA.class) -------------------------------------------
    def dna_total(self):
        return sum(self.dna_applied.get(f, 0) for f in data.DNA_FIELDS)

    def dna_percent(self, field):
        """DNA.getPercent: this field's share of all charged DNA (the evolution gate)."""
        t = self.dna_total()
        return int(100 * self.dna_applied.get(field, 0) / t) if t else 0

    def can_charge_dna(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "An egg has no DNA yet."
        if self.asleep:
            return self._disturbed()
        return None

    def generate_dna(self, field, amount):
        """DNA_GenerateValidate: spend `amount` bits 1:1 -> owned[field]; cap 99 (overflow refunds)."""
        if field not in self.dna_owned or amount <= 0 or self.bits < amount:
            return False
        self.bits -= amount
        total = self.dna_owned.get(field, 0) + amount
        if total > MAX_DNA_INVENTORY:
            self.bits += total - MAX_DNA_INVENTORY          # refund the overflow as bits
            total = MAX_DNA_INVENTORY
        self.dna_owned[field] = total
        return True

    def dna_bet(self, amount):
        """DVPet DNA_GenerateValidate (onEnter): pay the wager up front, before the mash
        mini-game runs. Returns False (and jeers) if the pet can't afford it."""
        if amount <= 0 or self.bits < amount:
            self._set_anim("refuse", 1.0)                   # Jeering: can't afford the wager
            return False
        self.bits -= amount
        return True

    def dna_minigame_award(self, amount, rate):
        """DVPet onDNAGenerate: the mash `rate` picks the Field; bank `amount` DNA of it
        (the wager was already spent in dna_bet). Overflow past the 99 cap refunds as
        bits, exactly like the device. Returns the Field won ("None" = wasted)."""
        field = dna_field_for_rate(rate)
        total = self.dna_owned.get(field, 0) + amount
        if total > MAX_DNA_INVENTORY:
            self.bits += total - MAX_DNA_INVENTORY          # refund the overflow as bits
            total = MAX_DNA_INVENTORY
        self.dna_owned[field] = total
        return field

    def apply_dna(self, field, amount):
        """PhysicalState.applyDNA: owned -> charged, at a cost (disturb/strength/mood/spirit/sick)."""
        owned = self.dna_owned.get(field, 0)
        if amount <= 0 or owned < amount:
            self._set_anim("refuse", 1.0)                   # Jeering: not enough DNA
            return False
        self.dna_owned[field] = owned - amount
        self.dna_applied[field] = self.dna_applied.get(field, 0) + amount
        self.disturb += 1                                   # DVPet disturb()
        self.strength = _clamp(self.strength + DNA_STRENGTH_CHANGE * amount, 0, 4)
        same = field == self.field
        self._set_mood(self.mood + (DNA_SAME_FIELD_MOOD if same else DNA_DIFF_FIELD_MOOD) * amount)
        self._set_enthusiasm(self.enthusiasm
                             - (DNA_SAME_FIELD_ENTH_DEC if same else DNA_DIFF_FIELD_ENTH_DEC) * amount)
        chance = (DNA_SAME_FIELD_SICK if same else DNA_DIFF_FIELD_SICK) * amount
        for _ in range(2):                                  # checkWorseSick + checkSick (2 rolls)
            if random.random() < chance / DNA_SICK_BOUND:
                self._sicken()
                break
        return True

    def reset_dna(self):
        """DNA.resetDNA (via resetEvolVar): charged DNA clears on evolution; owned inventory persists."""
        self.dna_applied = {f: 0 for f in data.DNA_FIELDS}

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

    # ---- nutrition (DVPet GoodNutrition: protein/mineral/vitamin macros) --
    def good_nutrition(self):
        return (self.nutr_protein >= GOOD_NUTRITION_MIN and self.nutr_mineral >= GOOD_NUTRITION_MIN
                and self.nutr_vitamin >= GOOD_NUTRITION_MIN)

    def _apply_nutrition(self, food):
        """PhysicalState.applyNutrition: a meal adds its macros (clamped 0..MaxMacro)."""
        self.nutr_protein = _clamp(self.nutr_protein + int(food.get("protein", 0)), 0, MAX_MACRO)
        self.nutr_mineral = _clamp(self.nutr_mineral + int(food.get("mineral", 0)), 0, MAX_MACRO)
        self.nutr_vitamin = _clamp(self.nutr_vitamin + int(food.get("vitamin_n", 0)), 0, MAX_MACRO)

    # ---- food taste (DVPet Taste<Food>) ----------------------------------
    def _species_food(self):
        r = data.load_requirements().get(self.num, {})
        return (r.get("food_pref", "None"), r.get("food_aversion", "None"),
                r.get("food_intol", []))

    def major_food(self):
        """PhysicalState.getMajorFood: the strictly most-eaten category, else None."""
        best = max(self.food_eaten.values(), default=0)
        if best <= 0:
            return None
        top = [c for c in data.FOOD_CATEGORIES if self.food_eaten.get(c, 0) == best]
        return top[0] if len(top) == 1 else None

    def _change_rank(self, cat):
        """Taste.changeRank: bump the eaten category's rank (+/- species pref bias); eating
        your current favourite/disliked pulls the OTHER ranks back toward 0; clamp to
        +/-RankLimit; a rank that reaches the cap becomes the new favourite/disliked."""
        pref, aver, _ = self._species_food()
        delta = RANK_CHANGE_FOOD
        if cat == pref:
            delta += RANK_PREF_INC
        elif cat == aver:
            delta -= RANK_PREF_INC
        if cat == self.disliked_food:
            delta += RANK_DISLIKED
            for c in data.FOOD_CATEGORIES:                 # incRankExcept toward 0
                if c != cat and self.food_ranks[c] < 0:
                    self.food_ranks[c] = min(0, self.food_ranks[c] + RANK_AFTER_FAV)
        if cat == self.favorite_food:
            for c in data.FOOD_CATEGORIES:                 # decRankExcept toward 0
                if c != cat and self.food_ranks[c] > 0:
                    self.food_ranks[c] = max(0, self.food_ranks[c] - RANK_AFTER_FAV)
        self.food_ranks[cat] = _clamp(self.food_ranks[cat] + delta, RANK_MIN, RANK_LIMIT)
        for c in data.FOOD_CATEGORIES:
            if self.food_ranks[c] >= RANK_LIMIT:
                self.favorite_food = c
            elif self.food_ranks[c] <= RANK_MIN:
                self.disliked_food = c

    def _eat_food(self, category):
        """DVPet feed taste. A food's Type is a ";"-list of categories (foodType.getType()):
        the tier comes from whether any category is the CURRENT disliked (first) or favourite,
        then each category's rank/eaten is bumped (incFoodRankAndEaten) and intolerance rolled."""
        cats = [c for c in (category or "").split(";") if c in data.FOOD_CATEGORIES]
        if not cats:
            return "neutral"
        if self.disliked_food and self.disliked_food in cats:
            tier = "disliked"
            self._set_mood(self.mood - FAV_FOOD_MOOD)
            self.obedience += DISLIKED_FOOD_OBEDIENCE
        elif self.favorite_food and self.favorite_food in cats:
            tier = "favorite"
            self._set_mood(self.mood + FAV_FOOD_MOOD)
            self._set_enthusiasm(self.enthusiasm + FAV_FOOD_ENTH)
        else:
            tier = "neutral"
            self._set_mood(self.mood + FOOD_MOOD)
        for c in cats:                                     # incFoodRankAndEaten: per category
            self.food_eaten[c] = self.food_eaten.get(c, 0) + 1
            self._change_rank(c)
        _, _, intol = self._species_food()
        if any(c in intol for c in cats):                  # checkIntolerantFoodSick (x2 rolls)
            for _ in range(2):
                if random.random() < INTOL_FOOD_SICK_CHANCE / 100:
                    self._sicken()
                    break
        return tier

    def evolve_to(self, num):
        _, by_num = data.load_sprites()
        r = by_num[num]
        self.num, self.name = num, r["name"]
        self.stage, self.attribute = r["stage"], r["attribute"]
        self.field = r.get("field", self.field)
        self.element = r.get("element", self.element)
        self._apply_natural_habitat()
        _req = data.load_requirements().get(num, {})
        self.max_energy = _req.get("max_energy", self.max_energy)
        self._sleep_energy_gain = _req.get("sleep_energy_gain", 3)
        self.energy = min(self.energy, self.max_energy)   # DVPet clamps to new max (no auto-refill)
        if data.load_requirements().get(num, {}).get("xantibody", "None") in ("Induced", "Natural"):
            self._set_xantibody("Permanent")          # the X-Antibody locks in
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.disturb = 0
        self.injuries = self.sick_count = 0
        self.sick = False
        self.sick_length = self.inj_length = self.fatigue_length = 0.0
        self.levels_fought = []
        self.reset_dna()                # DNA.resetDNA: charged DNA clears each evolution
        self.food_eaten = {c: 0 for c in data.FOOD_CATEGORIES}   # MajorFood resets per stage
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
        if _req.get("give_item", -1) >= 0:        # GiveItem: grant a consumable (dormant in data)
            self.add_item(f"i:{_req['give_item']}")
        self._set_anim("happy", 2.5)

    # ---- care actions --------------------------------------------------------
    def _set_anim(self, name, ttl):
        self.anim, self.anim_ttl = name, ttl

    def _set_mood(self, value):
        """PhysicalState.setMood: nudge once by disposition (MoodChangeDispositionCoefficient=1),
        then clamp to [MinMood, MaxMood]."""
        value = int(round(value))
        if value != self.mood:
            value += self._disposition()      # MoodChangeDispositionCoefficient = 1
        self.mood = _clamp(value, MOOD_MIN, MOOD_MAX)

    def mood_pct(self):
        """Mood as 0..100 for the status bar."""
        return (self.mood - MOOD_MIN) * 100 // (MOOD_MAX - MOOD_MIN)

    def current_mood(self):
        """PhysicalState.setCurrentMood -> Mood enum word."""
        if self.mood <= TO_DEPRESSED_MOOD:
            return "Depressed"
        if self.mood >= MIN_HAPPY_MOOD:
            return "Happy"
        if self.mood <= MIN_UNHAPPY_MOOD:
            return "Unhappy"
        return "Neutral"

    def _set_enthusiasm(self, value):
        """PhysicalState.setEnthusiasm: clamp to [MinEnthusiasm, MaxEnthusiasm];
        hitting a boundary costs mood (MaxEnthusiasmMoodPenalty)."""
        value = _clamp(int(round(value)), MIN_ENTHUSIASM, MAX_ENTHUSIASM)
        if value != self.enthusiasm and value in (MIN_ENTHUSIASM, MAX_ENTHUSIASM):
            self._set_mood(self.mood - MAX_ENTHUSIASM_MOOD_PENALTY)
        self.enthusiasm = value

    def _set_energy(self, value):
        """DVPet setEnergy: clamp to [-max_energy, +max_energy]; dropping into the
        red saps mood (NegativeEnergyMoodDec)."""
        value = _clamp(int(round(value)), -self.max_energy, self.max_energy)
        if value < 0 and value < self.energy:
            self._set_mood(self.mood - 10)       # NegativeEnergyMoodDec (per step into the red)
        self.energy = value

    def energy_pct(self):
        return max(0, self.energy) * 100 // self.max_energy if self.max_energy else 0

    def _poop_size(self):
        """DVPet poop(): pile size from base weight (heavier mons drop bigger)."""
        bw = self._base_weight()
        if bw >= POOP_INC_WEIGHT_FACTOR:
            return 3
        if bw <= POOP_INC_WEIGHT_FACTOR_SMALL:
            return 1
        return 2

    def _do_poop(self):
        """PhysicalState.poop: relief mood bump, weight shed, and a new sized pile
        added to the filth (capped at the _filth array length).  The bmGauge timer
        that schedules this is replaced by tuipet's poop interval."""
        self._set_mood(self.mood + POOP_MOOD_INC)                 # PoopMoodInc
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self.weight = max(1, self.weight - wdec)
        if self.poop < POOP_MAX_PILES:                            # addFilth: first free slot (capped)
            self.poop += 1                                        # poop == countFilth()
            self.poop_sizes.append(self._poop_size())

    def _disturbed(self):
        """Bothering the pet mid-sleep: counts toward restlessness AND costs mood
        now (DVPet DisturbMoodDec)."""
        self.disturb += 1
        self._set_mood(self.mood - 10)              # DisturbMoodDec
        self._set_enthusiasm(self.enthusiasm - 2)   # DisturbEnthusiasmDec
        return "zzz... mind its sleep!"

    def _special_idle(self):
        """An occasional idle quirk reflecting weather + mood (DVPet
        weathering()/personalityMood*): huddle in bad weather, a happy hop
        when content, a grumpy tantrum when unhappy."""
        if self.weather in _RAIN:
            self._set_anim("shield", 2.0)
        elif self.weather in _SNOW:
            self._set_anim("huddle", 2.0)
        elif self.mood >= MIN_HAPPY_MOOD:
            self._set_anim(random.choice(("play", "surprise")), 2.0)
        elif self.mood <= MIN_UNHAPPY_MOOD:
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
            self.calories = CALORIE_LIMIT
            self._poop_t = min(self._poop_interval, getattr(self, "_poop_t", 0) + 900)   # overeat -> sooner poop
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + max(1, food["hunger"]), 0, 4)
        self.calories = CALORIE_LIMIT                       # a meal refills the calorie buffer
        self.weight += food.get("weight", 1)
        self._set_mood(self.mood + food.get("mood", 0))     # foods.csv intrinsic mood
        tier = self._eat_food(food.get("category", ""))     # DVPet taste: fav/disliked/neutral
        self._last_meal_disliked = (tier == "disliked")      # eat(): disliked -> +9 grimace bite
        self._apply_nutrition(food)                          # GoodNutrition macros
        self._set_anim("eat", 1.4)
        tag = {"favorite": "  It loves it!", "disliked": "  It dislikes that."}.get(tier, "")
        return f"Fed {food['name']}.{tag}"

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

        game in {hp, vaccine, data, virus}: the HP drill builds Effort
        (strength); the attribute drills build that attribute's power, which
        accumulates for the whole life (NOT reset on evolution), exactly like
        DVPet. Training a non-favored attribute costs a little mood
        (DVPet NoneTrainingAttributeMoodRankChange).
        """
        self.train_time = _dvpet_time(self.day_phase)
        self.exercise_today += 1                          # DVPet _exercise (incExerciseTime)
        if hits >= 2:
            self.strength = _clamp(self.strength + 1, 0, 4)
            self.obedience += 1
        success = hits >= 2
        # DVPet onExerciseFinish adds +1 per drill, but the real device's stages last
        # real-DAYS (hundreds of trainings) while tuipet compresses them to ~2h. A flat
        # +1 can't reach the real-data attribute-power thresholds (digimon.csv median 50)
        # in a compressed stage, so good forms become unreachable. Scale the gain by drill
        # QUALITY to compensate for the clock -- same approach as the deferred enthusiasm
        # lapse. A perfect drill (3 hits) = +6, a solid one (2) = +4.
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
            if attr != self.attribute:                       # disliked-attribute cost
                self._set_mood(self.mood - 1)            # NoneTrainingAttributeMoodRankChange
                self._set_enthusiasm(self.enthusiasm - 3)  # ExerciseDislikedAttributeEnthusiasmChange
            else:
                self._set_enthusiasm(self.enthusiasm - 1)  # ExerciseFavAttributeEnthusiasmDec
        self.weight = max(1, self.weight - 2)
        self._set_energy(self.energy - 1)               # ExerciseEnergyDec
        if self.energy <= 0 and random.randint(0, 99) < FATIGUE_CHANCE:   # trained to exhaustion
            self._fatigue()
        if not success:                                  # DVPet exercise-fail penalties
            self._set_mood(self.mood - 10)               # ExerciseFailMoodDec
            self.obedience -= 1                          # ExerciseFailObedienceDec
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
        if self.stage in ("Egg", "Fresh"):
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
            if enemy:
                self.levels_fought.append(_enemy_level(enemy))
            self._open_praise()                          # a win is praiseworthy
            self._set_mood(self.mood + 10)               # BattleWonMoodInc
            self._set_enthusiasm(self.enthusiasm - 3)    # BattleWonEnthusiasmDec
            lo, hi = (enemy or {}).get("bits", (1, 5))
            gained = random.randint(lo, hi)
            self.bits += gained
            self._set_anim("happy", 2.0)
            return f"Victory! +{gained} bits"
        self._set_mood(self.mood - 20)               # BattleLostMoodDec
        self._set_enthusiasm(self.enthusiasm - 6)    # BattleLostEnthusiasmDec
        if random.random() < 0.3:
            self._injure()
        self._set_anim("sad", 2.0)
        return "Defeat..."

    # ---- battle morale: obedience & surrender (PhysicalState) ----------------
    def _adjusted_obedience(self):
        """PhysicalState.getAdjustedObedience: the obedience score, capped down to
        DepressedObedience while the mood is Depressed."""
        ao = float(self.obedience)
        if self.current_mood() == "Depressed" and DEPRESSED_OBEDIENCE < ao:
            ao = DEPRESSED_OBEDIENCE
        return ao

    def _obedience_factors(self):
        """PhysicalState.getObedienceFactors -> (base, moodFactor, total).  Verbatim
        port; the time term uses tuipet's day-phase time ranks for the clock-hour
        favorite/disliked check, and 'fatigued' maps to spent energy (tuipet has no
        separate fatigue flag)."""
        depressed = self.current_mood() == "Depressed"
        obed = DEPRESSED_OBEDIENCE if depressed else float(self.obedience)
        base = obed / OBEDIENCE_REFUSAL_CAP
        if OBEDIENCE_MOOD_MOD == 0:
            mood_factor = 0.0
        else:
            mood_factor = (self.mood / OBEDIENCE_MOOD_MOD) * ((1 - base) if self.mood < 0 else base)
        energy_ratio = (self.energy / self.max_energy if self.max_energy else 0.0) * 24.0
        now = self.day_phase
        if self.favorite_time() == now:
            time_factor = OBEDIENCE_TIME_MOD
        elif self.disliked_time() == now:
            time_factor = -OBEDIENCE_TIME_MOD
        else:
            time_factor = 0.0
        time_factor *= base
        unwell = self.sick or self.is_injured() or self.is_fatigued()   # isSick||isInj||isFatigued
        unwell_factor = (REFUSE_UNWELL_SICK if unwell else 0.0) * (1 - base)
        ex = self.exercise_today or 1                                  # _exercise!=0 ? _exercise : 1
        if self.energy >= 0:
            exercise_factor = base * (energy_ratio / ex)
        else:
            exercise_factor = base * (energy_ratio * ex)
        enth_factor = (self.enthusiasm * OBEDIENCE_ENTH_MOD) * (1 - base)
        total = exercise_factor + time_factor + mood_factor + unwell_factor + enth_factor
        return (base, mood_factor, total)

    def check_surrender(self, health, enemy_health, enemy_max_health, full_hp):
        """PhysicalState.checkSurrender (verbatim two-pass formula).  Returns
        0 = fight on, 2 = the pet REQUESTS to give up (the trainer decides), or
        1 = it surrenders/flees outright.  Disposition 0/+1 = the steady 'high'
        branch; -1 = the grumpy 'low' branch that quits more readily."""
        if not CAN_REFUSE:
            return 0
        adj_factor = self._obedience_factors()[2]
        adj_obed = self._adjusted_obedience()
        disp = self._disposition()
        health_thresh = full_hp / SURR_HEALTH_COEF
        r1 = random.randint(0, REFUSE_CHANCE - 1)
        if disp == 0 or disp == 1:                                    # HIGH disposition
            cont = adj_obed + adj_factor
            cont += HD_CONT_HI_HP if health >= health_thresh else HD_CONT_LO_HP
            if health < enemy_health and enemy_health >= enemy_max_health / SURR_HEALTH_COEF:
                cont += HD_CONT_HI_EHP
            else:
                cont += HD_CONT_LO_EHP
            surr = r1 + disp * SURR_DISP_COEF
            surr += HD_SURR_HI_HP if (health >= health_thresh and health >= enemy_health) else HD_SURR_LO_HP
        else:                                                         # LOW disposition (-1)
            cont = adj_obed + adj_factor
            cont += LD_CONT_HI_HP if health >= health_thresh else LD_CONT_LO_HP
            surr = float(r1)
            surr += LD_SURR_LO_EHP if (health >= health_thresh and health >= enemy_health) else LD_SURR_HI_EHP
        if surr < cont:
            return 0
        # provisional surrender request; the second pass decides whether it escalates to a flat refusal
        high_hp = health >= health_thresh
        ratio_ok = bool(full_hp and enemy_max_health and
                        health / full_hp >= enemy_health / enemy_max_health)
        if high_hp and (health >= enemy_health or ratio_ok):
            factor = SURR_HI_FACTOR
        elif self.battles > 0 and self.wins / self.battles >= SURR_HI_WINRATE_MIN:
            factor = SURR_HI_FACTOR
        else:
            factor = SURR_LO_FACTOR
        r2 = random.randint(0, REFUSE_CHANCE - 1)
        surr2 = r2 + disp * SURR_DISP_COEF
        if health < enemy_health and enemy_health >= enemy_max_health / SURR_HEALTH_COEF:
            surr2 -= SURR_HI_EHP
        else:
            surr2 -= SURR_LO_EHP
        surr2 = surr2 / factor
        return 1 if surr2 >= cont else 2

    def surrender_effect(self, surrender_val, health, enemy_health):
        """ClockTic.surrenderEffect: the morale aftermath when the pet gives up (1) or
        its surrender request is accepted (2)."""
        self._set_mood(self.mood + SURR_EFFECT_MOOD_INC)
        if surrender_val == 1 and self._disposition() < 0 and health >= enemy_health:
            self._set_mood(self.mood - SURR_EFFECT_LOWDISP_MOOD_DEC)
        if health >= enemy_health:
            self.obedience -= SURR_EFFECT_REQ_OBED_DEC if surrender_val == 2 else SURR_EFFECT_OBED_DEC
        if surrender_val == 2 and health < enemy_health:
            self.obedience = SURR_EFFECT_REQ_LOWHP_OBED          # setObedience(15), verbatim (a SET, not +=)

    def surrender_reject(self):
        """ClockTic: the trainer refuses the pet's surrender request (surrender==2) and
        sends it back in — it sulks but obeys a touch more."""
        self._set_mood(self.mood - SURR_REJECT_MOOD_DEC)
        self.obedience += SURR_REJECT_OBED_INC

    # ---- discipline: praise / scold (PhysicalState) --------------------------
    def _open_praise(self):
        """A good deed opens a praise window (DVPet setPraise)."""
        if self.num != -1 and self.stage != "Egg":
            self.praise_flag, self.praise_window = True, 0

    def _open_scold(self):
        """A bad deed makes the pet act up: opens a scold window and marks it
        noncompliant.  DVPet raises this on its periodic disciplineCall timer (deferred
        here — at tuipet's ~60x clock it would fire far too often) and on battle misdeeds;
        tuipet opens it on the care-mistake event instead, keeping the deltas faithful."""
        if self.num != -1 and self.stage != "Egg":
            self.scold_flag, self.scold_window, self.compliance = True, 0, False

    def _check_discipline_call(self):
        """checkDisciplineCall: on the DisciplineCallMin cadence, a chance for the pet to
        act up on its own (opening a scold window) — likelier when its needs go unmet,
        rarer the more obedient it is.  Obedient grown pets are exempt.  (Sleep-approach
        gating from DVPet is approximated by running this only while awake.)"""
        if self.scold_flag or self.praise_flag:          # checkCall(): already mid-discipline
            return
        if self.obedience >= DISCIPLINE_OBEDIENCE_MAX and self.stage not in ("Fresh", "InTraining"):
            return
        adjust = 0
        if self.hunger < 4 and self.glutton > 0:          # hungry glutton frets
            adjust = DISCIPLINE_TARGET_GLUTTON
        if self.exercise_today < 4 and self.restless > 0:  # under-exercised & restless (overrides)
            adjust = DISCIPLINE_TARGET_RESTLESS_HI
        elif self.exercise_today < 4 and self.restless < 0:
            adjust = DISCIPLINE_TARGET_RESTLESS_LO
        target = DISCIPLINE_TARGET_CHANCE + adjust
        bound = max(1, DISCIPLINE_CALL_CHANCE - (OBEDIENCE_REFUSAL_CAP - self.obedience))
        if random.randint(0, bound - 1) < target:
            self._open_scold()

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
        self.sick_length = max(SICK_LAPSE_MIN, self.sick_length - self._affinity() * SICK_LAPSE_MIN)
        self._set_mood(self.mood - SICK_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + SICK_ENTH_CHANGE)

    def _injure(self):
        """PhysicalState.injure: take an injury for MinInjLength..MaxInjLength recovery
        lapses; the cumulative injury count (used by evolution) also ticks up."""
        self.injuries += 1
        rolled = random.randint(MIN_INJ_LENGTH, MAX_INJ_LENGTH) * INJ_LAPSE_MIN
        rolled = max(INJ_LAPSE_MIN, rolled - self._affinity() * INJ_LAPSE_MIN)   # habitat-compat length mod
        self.inj_length = max(self.inj_length, rolled)
        self._set_mood(self.mood - INJ_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + INJ_ENTH_CHANGE)

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
        """PhysicalState.worsenedInjury: the injury gets worse -- extended, with mood/
        obedience/energy/spirit costs (the WorseInjuryLifeDec lifespan hit is omitted)."""
        self.obedience += WORSE_MALADY_OBED_DEC
        self._set_mood(self.mood + WORSE_MALADY_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + WORSE_INJ_ENTH_CHANGE)
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
        """PhysicalState.fatigue: the pet collapses from over-exertion — a heavy one-time
        mood/energy/spirit hit (worse if it was already fatigued), then it must rest the
        fatigue length off (FatigueMin..FatigueMax game-min)."""
        already = self.is_fatigued()
        self.fatigue_length = max(FATIGUE_MIN, random.randint(FATIGUE_MIN, FATIGUE_MAX) - self._affinity())   # habitat-compat length mod
        self._set_energy(self.energy - FATIGUE_ENERGY_DEC)
        self._set_enthusiasm(self.enthusiasm + FATIGUE_ENTH_CHANGE)
        self._set_mood(self.mood - FATIGUE_MOOD_DEC)
        if already:
            self._set_mood(self.mood - ALREADY_FATIGUED_MOOD_DEC)
        self._set_anim("exhausted", 2.0)

    def praise(self):
        """PhysicalState.praise: cheering the pet always lifts its mood; doing so inside
        an open praise window trains obedience, but praising while it is misbehaving (a
        scold window is open) spoils it instead."""
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            self._disturbed()
        self._set_mood(self.mood + (PRAISE_LOW_DISP_MOOD_INC if self._disposition() < 0
                                    else PRAISE_HIGH_DISP_MOOD_INC))
        if not self.compliance:
            self.obedience -= PRAISE_NONCOMPLIANT_OBED_DEC
        if self.scold_flag and not self.praise_flag:          # mis-praised a misbehaving pet
            self._set_mood(self.mood + PRAISE_SCOLD_MOOD_INC)
            self._set_enthusiasm(PRAISE_SCOLD_ENTH)
            self.obedience -= PRAISE_SCOLD_OBED_DEC
            self.scold_flag, self.scold_window = False, 0
            self._set_anim("surprise", 1.6)
            return "It was misbehaving — the praise only spoiled it."
        if self.praise_flag:                                  # well-timed praise
            self.obedience += CORRECT_PRAISE_OBED[self._disposition()]
            self.praise_flag, self.praise_window = False, 0
            self._set_anim("happy", 2.0)
            return f"{self.name} beams with pride!"
        self._set_anim("happy", 1.6)
        return f"You praise {self.name}."

    def scold(self):
        """PhysicalState.scold: a scolding nudges obedience up and mood down (more so for
        a low-obedience pet); a well-timed scold (an open scold window) corrects it, while
        scolding a pet that did nothing wrong (an open praise window) is unfair."""
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            self._disturbed()
        self.obedience += SCOLD_OBED_INC
        self._set_mood(self.mood - (SCOLD_LOW_OBED_MOOD_DEC if self.obedience < SCOLD_HIGH_OBED_MOOD
                                    else SCOLD_HIGH_OBED_MOOD_DEC))
        if self.praise_flag and not self.scold_flag:          # mis-scolded a good pet
            self._set_mood(self.mood - SCOLD_PRAISE_MOOD_DEC)
            self._set_enthusiasm(self.enthusiasm - SCOLD_PRAISE_ENTH_DEC)
            self.obedience += SCOLD_PRAISE_OBED[self._disposition()]
            self.praise_flag, self.praise_window = False, 0
            self._set_anim("sad", 1.8)
            return "It did nothing wrong — that scolding was unfair."
        if self.scold_flag:                                   # well-timed scold
            self._set_enthusiasm(self.enthusiasm + CORRECT_SCOLD_ENTH)
            self.obedience += CORRECT_SCOLD_OBED[self._disposition()]
            self.scold_flag, self.scold_window, self.compliance = False, 0, True
            self._set_anim("angry", 1.8)
            return f"{self.name} takes the lesson to heart."
        self._set_enthusiasm(self.enthusiasm + SCOLD_ENTH)
        self._set_anim("angry", 1.6)
        return f"You scold {self.name}."

    def clean(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.poop_sizes = []                        # clearFilth()
        self._set_mood(self.mood + 6)               # CleanMoodInc
        self._set_anim("wash", 1.2)
        return f"Cleaned {n} poop."

    def heal(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
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
        self._set_mood(self.mood + 75)              # curedMoodBonus
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

    def play(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if self.asleep:
            return self._disturbed()
        # DVPet has no dedicated 'play' care action; tuipet's Play button maps onto
        # PhysicalState.spoil(): setMood(+SpoilMoodInc) AND setObedience(-SpoilObedienceDec).
        # A real tradeoff -- happier now, but the pet gets cheekier (more disobedient).
        self._set_mood(self.mood + SPOIL_MOOD_INC)
        self.obedience = max(0, self.obedience - SPOIL_OBEDIENCE_DEC)   # DVPet setObedience floors at 0
        self._set_anim("play", 1.5)
        return "Played together -- happy, but a bit spoiled."

    # ---- shop / items --------------------------------------------------------
    def buy(self, entry):
        """Purchase one consumable at its list price, capped at the item's bag stack."""
        from . import shop
        price = shop.purchase_price(entry)
        if self.bits < price:
            return "Not enough bits."
        key = entry["key"]
        cap = entry.get("max_uses") or 99
        if self.inventory.get(key, 0) >= cap:
            return f"Can't carry more {entry['name']} (max {cap})."
        self.bits -= price
        self.inventory[key] = self.inventory.get(key, 0) + 1
        return f"Bought {entry['name']}."

    def sell(self, entry):
        """Resell one from the bag for a fraction of its price (shop.resell_price)."""
        from . import shop
        key = entry["key"]
        if self.inventory.get(key, 0) <= 0:
            return "None to sell."
        val = shop.resell_price(entry)
        if val <= 0:
            return f"{entry['name']} can't be resold."
        self.inventory[key] -= 1
        if self.inventory[key] <= 0:
            self.inventory.pop(key, None)
        self.bits += val
        return f"Sold {entry['name']} for {val}b."

    def add_item(self, key, n=1):
        """Drop loot / grants straight into the bag."""
        self.inventory[key] = self.inventory.get(key, 0) + n

    def use_item(self, key):
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        e = data.consumable_by_key(key)
        if not e:
            return "?"
        if not data.item_is_functional(e):
            return f"{e['name']} has no use yet."   # action-item whose system is unbuilt
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
        if e.get("effect_id", -1) >= 0:                 # Futon: lay out a temporary care buff
            eff = data.load_care_effects().get(e["effect_id"])
            if eff:
                self.effect_id = e["effect_id"]
                self.effect_t = float(eff["duration"])
                self._eff_acc = 0.0
                self._eff_asleep = self.asleep
                self._set_anim("happy", 1.4)
                return f"{self.name} settles onto the {e['name']}."
        # crafter (DVPet FoodID/ItemID unlock list): yields a random treat from its list --
        # the Toy Oven bakes a random food, the Chocolate Egg pops a random capsule.
        targets = [f"f:{n}" for n in e.get("unlocks_food", [])] + \
                  [f"i:{n}" for n in e.get("unlocks_item", [])]
        if targets:
            got = random.choice(targets)
            self.add_item(got)
            self._set_anim("happy", 1.4)
            made = (data.consumable_by_key(got) or {}).get("name", got)
            return f"{self.name} got a {made}!"
        if e.get("action") == "ItemEvol":           # item-triggered evolution (Digimental/etc.)
            target = evolution.item_select(self, e["id"])
            if target is None and e.get("dexnum", -1) >= 0:
                target = evolution.item_direct(self, e["dexnum"])
            if target is None:
                self.inventory[key] = self.inventory.get(key, 0) + 1   # refund: not usable now
                self._set_anim("refuse", 1.0)
                return f"{self.name} can't use that yet."
            self.evolve_to(target)
            self._set_anim("happy", 1.4)
            return f"{self.name} evolved!"
        is_food = key.startswith("f:")
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + e["hunger"], 0, 4)
            self.calories = CALORIE_LIMIT               # food refills the calorie buffer
        self._set_mood(self.mood + e["mood"])
        self._set_enthusiasm(self.enthusiasm + e.get("enthusiasm", 0))
        self.weight = max(1, self.weight + e["weight"])
        if e["energy"]:
            self._set_energy(self.energy + e["energy"])
        if e["strength"]:
            self.strength = _clamp(self.strength + e["strength"], 0, 4)
        self.obedience += e["obedience"]
        self.vaccine = max(0, self.vaccine + e["vaccine"])
        self.data_power = max(0, self.data_power + e["data"])
        self.virus = max(0, self.virus + e["virus"])
        if e.get("vitamin"):
            self.feed_vitamin()                          # guards against injury worsening
        if e["unfatigue"]:
            self.fatigue_length = 0.0                    # DVPet Fatigued flag only clears
            # fatigue-length; energy stays driven by the item's Energy column, not a full refill
        if e["undepressed"]:
            self._set_mood(max(self.mood, NEW_UNDEPRESSED_MOOD))  # leave depression
        if e["cured"]:
            self.sick = False
            self.sick_length = 0.0
            self.med_lapse = MEDICINE_HOURS              # medicine item -> getMed indicator
        if e["healed"]:
            self.injuries = max(0, self.injuries - 1)
            self.inj_length = 0.0
            self.bandage_lapse = BANDAGE_HOURS           # recovery item -> getBandage indicator
        if e.get("seconds"):
            self.lifespan += e["seconds"]                # DVPet setTotalLifespan: +/- lifespan
        if e.get("temp"):
            new_temp = self.temp + e["temp"]             # DVPet applies only if it stays in range
            if 0 <= new_temp <= wx.MAX_TEMP:             # config MaxTemp=100, floor 0
                self.temp = new_temp
        if e.get("sleep") and not self.asleep:
            self.asleep = True                           # DVPet item Sleep flag forces sleep
        if is_food:
            self._eat_food(e.get("category", ""))           # bag food -> same taste system
            self._apply_nutrition(e)
        if not e.get("sleep"):                           # a sleep item leaves the pet dozing,
            self._set_anim("eat" if is_food else "happy", 1.4)   # not in the happy/eat pose
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
        if self.is_fatigued():
            return "fatigued"
        if self.is_injured():
            return "injured"
        if self.temp <= wx.FREEZING_TEMP:
            return "freezing"
        lo, hi = self.ideal_temp
        if self.temp >= hi + wx.UPPER_IDEAL:
            return "overheating"
        if self.hunger == 0:
            return "starving"
        if self.poop >= 3:
            return "needs cleaning"
        if self.day_phase == "night" and not self.asleep and self.energy < self.max_energy // 2:
            return "sleepy"
        if self.scold_flag:
            return "misbehaving"
        if self.praise_flag:
            return "did great!"
        if self.mood <= MIN_UNHAPPY_MOOD:
            return "unhappy"
        if self.mood >= MIN_HAPPY_MOOD:
            return "happy"
        return "ok"
