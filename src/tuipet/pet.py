"""DVPet game model: a single virtual pet, its stats, and care logic."""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field as _dcf
from . import data
from . import shop
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
# DEFERRED awake enthusiasmLapse constants (see tick's measured rationale --
# ported faithfully it collapses mood within ~15 real-min on the compressed clock)
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
# checkRefused branch mods (config.csv col 1)
REFUSE_MED_FACTOR = -20.0           # RefuseMedFactor (medicine tastes awful)
REFUSE_DISLIKED_FOOD = -25.0        # RefuseDislikedFoodCoefficient (x hunger/stomach)
REFUSE_FAV_STOMACH = 10.0           # RefuseFavModStomachCoefficient (x room left)
REFUSE_HUNGER_MOD = -25.0           # RefuseHungerModCoefficient (x hunger/stomach)
REFUSE_GLUTTON_HUNGER = -15.0       # RefuseGluttonHungerModCoefficient
REFUSE_NOT_GLUTTON_HUNGER = -30.0   # RefuseNotGluttonHungerModCoefficient
REFUSE_PERSONALITY_MATCH = 10.0     # RefuseFavMod*MatchFactor (food suits its temperament)
REFUSE_PERSONALITY_UNMATCH = -10.0  # RefuseFavMod*UnmatchFactor
EXERCISE_REFUSE_LOW_ENTH = 20.0     # ExerciseRefuseLowEnthusiasmFactor (fav attr, dispirited)
BATTLE_DISPO_COEF = 10.0            # HighDispositionBattleObedienceDispositionCoefficient
BATTLE_LOW_DISPO_FACTOR = 50.0      # LowDispositionBattleObedienceFactor (docile pets fight when told)
# checkStopTravel (config.csv col 1).  MinEnergyForActivity is -127 in classic --
# the energy floor never gates, so it is not ported.
REFUSE_TRAVEL_COEFF = 3000.0        # RefuseTravelCoefficient (roll range 100..300100)
REFUSE_TRAVEL_WALK = 5.0            # RefuseTravelModWalkFactor (run=20; tuipet has no run mode)
REFUSE_TRAVEL_DISPO = 35.0          # RefuseTravelDispositionCoefficient
# gift call (config.csv col 1): a HAPPY pet may find you a present
GIFT_CHANCE_MIN = 57.0              # GiftChanceMin: game-min between rolls
GIFT_CHANCE_FACTOR = 70             # GiftChanceFactor
GIFT_CHANCE_MOOD_COEFF = 0.5        # GiftChanceMoodCoefficient
# trained battle HP (config.csv col 1): the HP drill GROWS fullHealthPoints
STARTING_HEALTH_POINTS = 5          # StartingHealthPoints (resetToEgg)
PERFECT_WINS_LIMIT = 5              # PerfectWinsLimit: every 5 wins -> +1 HP
PERFECT_WINS_HEALTH_INC = 1         # PerfectWinsHealthInc
# getMaxHealth: the HP CAP rises with lapsed life (real-seconds -> game-days here:
# 86400s real = 1 day = 1 tuipet DAY_LENGTH); classic MaxHealth* ladder
HEALTH_CAP_LADDER = ((13, 30), (10, 25), (7, 20), (4, 15), (1, 10))  # (days, cap)
MAX_HEALTH_DEFAULT_CAP = 10         # MaxHealthDefault (under a day old)
# exercise() nuances
EXERCISE_WORSE_SICK_CHANCE = 1      # ExerciseWorseSickChance %
OBEDIENCE_CHANGE_SICK_FORCED = -5   # ObedienceChangeSickForced (forced a sick pet; it got worse)
EXERCISE_CALORIE_DEC = 1            # ExerciseCalorieDec
FAV_EXERCISE_TIME_MOOD = 10         # FavExerciseTimeMoodInc
FAV_EXERCISE_TIME_ENTH = 1          # FavExerciseTimeEnthusiasmChange
NOTFAV_EXERCISE_TIME_MOOD = 2       # NotFavExerciseTimeMoodDec
DISLIKED_TIME_EXERCISE_ENTH = -1    # DislikedTimeExerciseEnthusiasmChange
MODE_CHANGE_ENERGY = -1             # ModeChangeEnergyChange
# toy engagement (applyItemNoObedience): a bored pet gets less from its toys
MAX_ITEM_INTEREST = 5               # MaxItemInterest
ITEM_INTEREST_TIMER = 60            # ItemInterestTimer (game-min per -1 decay; 40 sunny / 80 sour)
ITEM_INTEREST_LOW_TIMER = 40        # ItemInterestLowTimer (disposition +1)
ITEM_INTEREST_HIGH_TIMER = 80       # ItemInterestHighTimer (disposition -1)
PERSONALITY_MOOD_MATCH = 10         # ConsumablePersonalityMatchMoodChange
PERSONALITY_MOOD_UNMATCH = -10      # ConsumablePersonalityUnmatchMoodChange
EGG_MOOD = 100                      # EggMood: a new egg starts warm (Evolution.egg)
# the missed-day / birthday system (setTimeToAge): each game day of AGE the pet
# has a birthday judged by the day's MAJOR mood and its missed-day tally
MOOD_RECORD_MIN = 5                 # MoodRecordMin: sample the mood tier every 5 game-min
MAX_MISTAKE_DAY_BONUS = 0           # MaxMissedDayForBonusInc: a good day allows ZERO slips
MIN_MISTAKE_DAY_DEC = 1             # MinMissedDayForBonusDec
BONUS_LIFE_INC = 360.0              # BonusLifeInc 21600 real-sec -> game-min scale (+6 game-hours)
BONUS_LIFE_DEC = 360.0              # BonusLifeDec
BONUS_EVOLUTION_LIFE = 60.0         # BonusEvolutionLife 3600 -> game-min scale, x bonus per evolution
GOOD_BIRTHDAY_FOOD = 55             # Cupcake
BAD_BIRTHDAY_FOOD = 7               # Candy
NORMAL_BIRTHDAY_FOOD = 54           # Cookie
WIN_RATE_BONUS_COEF = 0.1           # winRateRookieBonusIncCoefficient (champion: 0.1*winRate - 5)
# saveFromDeath: frantic taps during the dying beat can pull the pet back
HITS_TO_SAVE = 30                   # HitsToSave 175 mouse-clicks over DVPet's ~7s jingle,
                                    #   scaled to a ~6/s keyboard mash over tuipet's 5s beat
REVIVAL_LIFE = 750.0                # RevivalLifeInc 45000 real-sec -> game-min scale (~12.5 game-h left)
HUNGER_AFTER_SAVED = 0              # HungerAfterSavedFromDeath (alive, but starving)
BONUS_AFTER_SAVED = -1              # BonusChangeAfterSavedFromDeath
# battle style (Battle_Style menu): Free = the pet fights its own way (+1 all
# powers, never refuses an order it never got); Orders = you call each attack
# (it may refuse mid-fight, but discipline pays obedience and prouder wins)
BATTLE_FREE_OBED_INC = 1            # BattleFreeObedienceInc (fighting under orders)
ORDERS_WON_MOOD_INC = 10            # OrdersWonMoodInc
BATTLE_DISPO_MOOD_FACTOR = -5       # BattleDispositionMoodFactor (x -disposition)
OBED_HEALTH_COEF = 5                # ObedienceChanceHealthCoefficient (hp >= full/5 = "healthy")
HI_DISPO_OBED_HIGH_HP = 0           # HighDispositionObedienceChanceHighHealthFactor
HI_DISPO_OBED_LOW_HP = -10          # ...LowHealthFactor (a hurt pet obeys less)
HI_DISPO_REFUSE_COEF = 10           # HighDispositionRefuseChanceDispositionCoefficient
LO_DISPO_OBED_HIGH_HP = 10          # LowDispositionObedienceChanceHighHealthFactor
LO_DISPO_OBED_LOW_HP = -10
LO_DISPO_REFUSE_LOW_ENEMY = 0       # LowDispositionRefuseChanceLowEnemyHealthFactor
LO_DISPO_REFUSE_HIGH_ENEMY = 10     # ...HighEnemyHealthFactor (a docile pet balks when losing)
# perfect-conditions energy save (checkEnergyIncFromPerfectConditions):
# an energy DROP during the pet's favourite time may bounce back +1 --
# roll nextInt(base + mods) == 1, so perfect conditions shrink the range
ENERGY_BONUS_BASE = 10              # BonusEnergyIncChance
ENERGY_BONUS_WEATHER = -2           # EnergyBonusChanceGoodWeather
ENERGY_BONUS_MOOD = -1              # EnergyBonusChanceGoodMood
ENERGY_BONUS_TEMP = -1              # EnergyBonusChanceGoodTemp
ENERGY_BONUS_NUTRITION = -2         # EnergyBonusChanceGoodNutrition
ENERGY_BONUS_COMPAT_F = -1          # Compatible/IncompatibleField/Element*Change
ENERGY_BONUS_COMPAT_E = -1
ENERGY_BONUS_INCOMPAT_F = 2
ENERGY_BONUS_INCOMPAT_E = 1
GOOD_NUTRITION_FATIGUE_CHANCE = 40  # GoodNutritionFatigueChance (else FatigueChance 60)
FATIGUE_COMPAT_CHANGE = 5           # Compatible/Incompatible{Field,Element}FatigueChanceChange
# the sleep cycle (config.csv col 1): a free-running ~24h pressure rhythm --
# sleepLapse accrues awake (species SleepLapseInc/min) until sleepLimit, the
# pet sleeps long enough to refill its energy, and the cycle re-anchors
DAY_MINUTES = 1440                  # HoursDay * MinutesHour
MIN_AWAKE_LIMIT = 360.0             # MinAwakeLimit (shortest sleep: 6 game-hours)
MAX_AWAKE_LIMIT = 900.0             # MaxAwakeLimit (longest: 15)
MORE_SLEEP_CHANCE = 9               # MoreSleepChance (the per-minute sleep jitter roll)
AWAKE_RESTLESS_COEF = 1             # AwakeLapseRestlessCoefficient
BONUS_SLEEP_ENERGY = 2              # BonusSleepEnergy (a restless skip still rests)
NAP_ENERGY_MIN = 1                  # NapEnergyMin
SLEEP_NOT_NAP_MIN = 90              # SleepNotNapMinutes (- restless*60): lights-out near
SLEEP_NOT_NAP_RESTLESS = 60         #   bedtime starts REAL sleep instead of a nap
ON_NAP_MOOD_INC = 10                # OnNapMoodInc
DISTURB_POSTPONE = (10, 60)         # DisturbPostponeMin/Max (game-min until it re-sleeps)
FULL_AWAKE_DISTURB = 480.0          # MaxMinutesToFullAwakeDisturb (- restless*60)
FULL_AWAKE_DISTURB_RESTLESS = 60.0
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
# hunger / stomach (DVPet FullHunger / StomachCapacity / OvereatLimit)
FULL_HUNGER = 4                         # FullHunger: a satisfied stomach (4 hearts)
STOMACH_CAPACITY = 4                    # StomachCapacity: the applyFood fullness-modifier divisor
OVEREAT_LIMIT = 5                       # OvereatLimit: a glutton may fill one heart past full
CALORIE_LIMIT = 4                       # CalorieLimit (buffer half-range)
LESS_HUNGER_CHANCE = 9                  # LessHungerChance: the glutton decay-jitter odds
# sleep (DVPet setAsleep / lightsCall / the morning wake roll)
LIGHTS_MISTAKE_SEC = 60.0               # MinutesToMistakeLights(60) as ~12% of the sleep,
#                                         scaled to tuipet's ~6-min night -- one mistake/night
MORNING_MOOD_CHANCE = 5                 # MorningMoodChance: 1/5 bad, 1/5 terrible-if-happy, 1/5 good
BAD_MORNING_MOOD = {"Happy": -150, "Neutral": -100, "Unhappy": -10, "Depressed": -10}
GOOD_MORNING_MOOD = {"Happy": 50, "Neutral": 100, "Unhappy": 150, "Depressed": 150}
WORST_MORNING_MOOD = -10                # WorstMorningMood (TerribleMorning sets mood TO this)
STARVE_WEIGHT_DEC = 1                   # ActivityWeightChange: starving sheds weight per lapse
HUNGER_MISTAKE_LIFE_DEC = 3600.0        # MistakeHungerLifeDec 21600s of a ~500h DVPet life,
#                                         scaled to tuipet's ~84h: ~1.2% of life x total mistakes
HUNGER_MISTAKE_OBEDIENCE = 1            # HungerMistakeObedienceChange
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
CURED_MOOD_BONUS = 75                    # CuredMoodBonus (divided by Max{Sick,Inj}Length per treatment)
CURED_OBED_BONUS = 25                    # CuredObedienceBonus
BAD_MED_LIFE_DEC = 3600.0                # BadMedLifeDec: a double dose is poison
BAD_MED_BM_INC = 6                       # BadMedBMInc (bowel gauge lurch)
BAD_VITAMIN_MOOD_DEC = 8                 # BadVitaminMoodDec
BAD_VITAMIN_LIFE_DEC = 7200.0            # BadVitaminLifeDec
BAD_VITAMIN_BM_INC = 2                   # BadVitaminBMInc
VITAMIN_WORSE_SICK_CHANCE = 1            # VitaminWorseSickChance %
VITAMIN_OVERFED_SICK_CHANCE = 50         # VitaminOverfedSickChance (RefuseChance-bounded roll)
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



@dataclass
class Pet:
    num: int
    name: str = ""
    stage: str = ""
    attribute: str = ""
    age_seconds: float = 0.0
    stage_seconds: float = 0.0      # time spent in the current stage
    hunger: int = 4                 # hearts 0..4 (4 = full); FullHunger=4
    calories: int = 0               # DVPet calorie buffer; resetToEgg StartingCalories=0
    strength: int = 4               # effort hearts 0..4; resetToEgg sets FullStrength(4)
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
    compliance: bool = False        # DVPet _compliance (resetToEgg starts false; a fair scold earns it)
    refused: bool = False           # DVPet _refused: the last command was blown off (one-shot)
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
    # ---- home shop (PhysicalState _homeFoodShop/_homeItemShop/_restock) ----
    shop_food: list = _dcf(default_factory=list)    # rolled food slots {key, stock, sale}
    shop_item: list = _dcf(default_factory=list)    # rolled item slots
    shop_day: int = -1                              # game day of the current roster (dailyChange)
    shop_restock: int = 0                           # banked restock credits (max RestockMax)
    shop_restock_t: float = 0.0                     # seconds toward the next credit roll
    # sleep cycle (PhysicalState _sleepLapse/_sleepLimit/_awakeLapse/_awakeLimit/_nap)
    sleep_lapse: float = 0.0        # pressure toward the next sleep (accrues awake)
    sleep_limit: float = DAY_MINUTES - MIN_AWAKE_LIMIT   # pressure cap for this cycle
    awake_lapse: float = 0.0        # minutes slept so far
    awake_limit: float = MIN_AWAKE_LIMIT                 # minutes of sleep owed
    nap: bool = False               # a lights-out nap (shallow; lights-on wakes it)
    item_interest: int = 0          # _itemInterest: toy boredom 0..5 (decays over time)
    # missed-day / birthday (PhysicalState _mistakeDay / _dailyMoodRecord / _bonus)
    mistake_day: int = 0            # today's care slips (resets each birthday)
    daily_mood: dict = _dcf(default_factory=lambda: {"Happy": 0, "Neutral": 0, "Unhappy": 0, "Depressed": 0})
    last_birthday: int = 0          # last celebrated age-day
    evol_bonus: int = 0             # _bonus: birthday/win-rate credit fed into evolution odds
    birthday_note: str = ""         # transient: the HUD's birthday announcement
    saved_from_death: int = 0       # _savedFromDeath: each rescue raises the next bar
    # long-horizon clocks (persisted: losing these on reload forgave starvation,
    # wiped the bowel gauge and re-armed once-per-night mistakes -- audit 2026-07)
    _starve_t: float = 0.0          # the 12h starvation death clock
    _poop_t: float = 0.0            # the bowel gauge (written as durable state by meals)
    _filth_t: float = 0.0           # filth-mistake grace / post-mistake postpone
    _lights_t: float = 0.0          # lights-on sleep mistake (float(-inf) = once/night latch)
    _cal_t: float = 0.0             # calorie/hunger lapse accumulator
    _str_t: float = 0.0             # effort-decay accumulator
    _exercise_day: int = -1         # daily exercise counter's day stamp
    _weather_day: int = -1          # daily temperature roll's day stamp
    free_style: bool = False        # _isFree: Battle Style toggle (Free vs Orders)
    gift: str = ""                  # pending gift-call present (consumable key; "" = none)
    gift_t: float = 0.0             # seconds toward the next GiftChanceMin roll
    # ---- home tournament (PhysicalState _trophySchedule/_foughtTrophiesToday) ----
    tourney_schedule: list = _dcf(default_factory=list)   # 24 hourly trophy ids (dailyChange re-roll)
    tourney_day: int = -1                                  # game day of the schedule
    fought_today: list = _dcf(default_factory=list)        # trophy ids fought today (SameDayRetry exempt)
    tourney_alarm: int = -1         # _tourneyAlarm: trophy id to be called for (-1 = unset)
    tourney_alert: bool = False     # TournamentAlert: the call is ringing (this hour only)
    full_health: int = STARTING_HEALTH_POINTS   # _fullHealthPoints: TRAINED battle HP
    perfect_wins: int = 0           # _perfectWins: HP-drill wins toward the next +1 HP
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
    def new_egg(cls, generation=1, egg_type=None):
        if egg_type is None:
            egg_type = random.randrange(egg_mod.count())
        pet = cls(num=-1, name="Digitama", stage="Egg",
                  egg_type=egg_type, generation=generation)
        pet.mood = EGG_MOOD                     # Evolution.egg: setMood(EggMood 100)
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
        """One game-minute of life.  Decomposed into ordered phases (audit
        2026-07); each phase's body is verbatim from the old monolith, and the
        early-return structure (egg / asleep / death) is explicit here."""
        self._tick_clock(dt)
        if self.dead:
            return
        self._tick_growth(dt)
        if self.stage == "Egg":
            self._tick_egg()
            return
        self._tick_recovery(dt)
        self._tick_effect(dt)
        if self.asleep:
            self._tick_asleep(dt)
            return
        self._tick_mood_discipline(dt)
        self._tick_hunger(dt)
        self._tick_body(dt)
        self._tick_sleep_pressure(dt)
        if self._tick_mortality(dt):
            return
        if (self.anim in ("idle", "walk") and self.anim_ttl <= 0 and not self.poop
                and not self.sick and random.random() < 0.03 * dt):
            self._special_idle()
        self._maybe_evolve()

    def _tick_clock(self, dt):
        """The world clock: hour rollover (tournament alarm) + weather -- these
        run even over the grave."""
        hr0 = int((self.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)
        self.world_seconds += dt
        hr1 = int((self.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)
        if hr1 != hr0 and not self.dead:
            self.tourney_alert = False    # a ring only lasts its cup's hour
            if self.tourney_alarm >= 0:
                from . import tournament as _tourney
                _tourney.schedule(self)   # a day rollover re-rolls (and clears the alarm)
            if self.tourney_alarm >= 0 and self.tourney_alarm in (self.tourney_schedule or []) \
                    and (self.tourney_schedule.index(self.tourney_alarm) == hr1):
                # CurrentTime.setSeconds: on the hour of the alarmed cup's slot,
                # clear the alarm and raise TournamentAlert (the attention call)
                self.tourney_alarm = -1
                self.tourney_alert = True
        self._update_weather(dt)

    def _tick_growth(self, dt):
        """Aging + the ambient systems: X-decay, shop restock, toy interest,
        the gift call, the mood record / birthday, the anim clock."""
        if self.x_antibody == "Temporary":          # a protoform fades if unused
            self.x_count -= dt
            if self.x_count <= 0:
                self.x_antibody, self.x_count = "None", 0.0
        self.age_seconds += dt
        self.stage_seconds += dt
        shop.check_restock_tick(self, dt)           # checkRestock: bank shop restock credits
        # setItemInterestLapse: toy boredom fades -1 per timer -- a sunny pet
        # (disposition +1) re-engages in 40 game-min, a sour one takes 80
        if self.item_interest > 0:
            self._interest_t = getattr(self, "_interest_t", 0.0) + dt
            timer = (ITEM_INTEREST_LOW_TIMER if self.disposition > 0
                     else ITEM_INTEREST_HIGH_TIMER if self.disposition < 0 else ITEM_INTEREST_TIMER)
            if self._interest_t >= timer:
                self._interest_t = 0.0
                self.item_interest -= 1
        self._check_gift_call(dt)                   # checkGiftCall: a happy pet may find a present
        # checkMoodRecord: sample the mood tier every MoodRecordMin game-min
        if self.stage != "Egg":
            self._mood_rec_t = getattr(self, "_mood_rec_t", 0.0) + dt
            if self._mood_rec_t >= MOOD_RECORD_MIN:
                self._mood_rec_t = 0.0
                m = self.current_mood()
                self.daily_mood[m] = self.daily_mood.get(m, 0) + 1
            # setTimeToAge: every AgeUp (one game day of age) is a BIRTHDAY,
            # judged by the day's MAJOR mood and the missed-day tally
            day = int(self.age_seconds // DAY_LENGTH)
            if day > self.last_birthday:
                self.last_birthday = day
                self._birthday()
        if self.anim_ttl > 0:
            self.anim_ttl -= dt
            if self.anim_ttl <= 0:
                self.anim = "sleep" if self.asleep else "idle"

    def _tick_egg(self):
        """Egg stage: only the hatch trigger (the 3s crack runs at frame cadence
        via advance_hatch; a 1 Hz countdown here would skip the crack frames)."""
        if not self.hatching and self.stage_seconds >= self.EGG_DURATION:
            self.hatching = True
            self._hatch_t = 3.0
            self._set_anim("hatch", 3.0)

    def _tick_recovery(self, dt):
        """Environment + the recovery lapses (they run asleep or awake)."""
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

    def _tick_asleep(self, dt):
        """The sleep branch: lights neglect, deep-sleep regen, the awakeLapse
        clock with the restless jitter, asleep death checks, desperate poop."""
        # lightsCall (DVPet): sleeping with the room light ON is neglect --
        # one care mistake per sleep once the counter crosses the threshold.
        if self.lights:
            self._lights_t = getattr(self, "_lights_t", 0.0) + dt
            if 0 <= self._lights_t >= LIGHTS_MISTAKE_SEC:
                self._lights_t = float("-inf")       # AfterMistakeMinutesPostponed: once/night
                self.care_mistakes += 1
                self.mistake_day += 1  # MistakeIncMissedDayChange
        # DVPet sleep recovery: +SleepEnergyGain every SleepMinutesToEnergyGain
        # (deep sleep only -- a nap restores just the jitter's scraps)
        if self.nap:
            self._sleep_e_t = 0.0                    # a nap earns only the jitter scraps
        self._sleep_e_t = getattr(self, "_sleep_e_t", 0.0) + dt
        if self._sleep_e_t >= 60 and not self.nap:   # SleepMinutesToEnergyGain
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
        # setAwakeLapse: +1/min with the restless jitter -- a restless
        # sleeper skips ahead (with a scrap of bonus rest), a mellow one
        # lies in; at the limit it's morning (the morning roll lives in _wake)
        step = dt
        r = random.randrange(MORE_SLEEP_CHANCE) + self.restless * AWAKE_RESTLESS_COEF
        if r < 0:
            step = 0.0
        elif r > MORE_SLEEP_CHANCE - 1:
            step += dt
            self._set_energy(self.energy + (NAP_ENERGY_MIN if self.nap else BONUS_SLEEP_ENERGY))
        if self.nap:
            self.sleep_lapse += dt * self._sleep_inc()   # a nap only BORROWS the cycle
        self.awake_lapse += step
        if self.awake_lapse >= self.awake_limit:
            self._wake(morning=not self.nap)
        # death does not wait for morning: the mistake cap and old age
        # apply asleep too (only the starvation clock freezes; audit 2026-07)
        if self.care_mistakes >= 20 or self.injuries >= 20:
            self._die(); return
        if self.age_seconds >= self.lifespan:
            self._die(); return
        # startPoop: even asleep, a truly DESPERATE gauge (>= 2x max) goes --
        # this must live in the sleep branch (the awake poop block below is
        # unreachable while asleep; latent until the canon day bands landed)
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        if self._poop_t >= self._poop_interval * 2:
            self._poop_t = 0                 # gauge zeroed (DVPet poop())
            self._do_poop(backlog=True)
            self._set_anim("poop", 2.2)

    def _tick_mood_discipline(self, dt):
        """The mood lapse + the discipline windows.  (DVPet has NO passive
        energy decay -- energy only moves via activity and sleep.)"""
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
                    self.mistake_day += 1        # DisciplineCallFailMissedDayChange
            self._check_discipline_call()                # the pet may spontaneously act up
            # awake enthusiasmLapse (mood -= |enth*EnthusiasmMoodDecCoefficient|, then an energetic
            # pet's spirit climbs HighEnergyEnthusiasmChange) stays DEFERRED -- and this was measured,
            # not assumed: ported faithfully it collapses mood to Unhappy/Depressed within ~15 real-min
            # whatever the play style, because the only awake spirit-restoring force is +1/lapse while
            # activities cost -3..-6, so under tuipet's ~60x clock |enthusiasm| pins at 10 and the drain
            # sticks at -20/lapse (active play is WORSE, driving enth to -10). It needs the real-time
            # clock to balance; DVPet numbers are NOT softened. Asleep decay (below) IS ported.

    def _tick_hunger(self, dt):
        """hunger: the DVPet calorie buffer drains each lapse; emptying it drops
        a hunger heart (or logs a care mistake at zero), then refills."""
        self._cal_t = getattr(self, "_cal_t", 0.0) + dt
        if self._cal_t >= self._hunger_interval:
            self._cal_t = 0.0
            self.calories += CALORIE_LAPSE_CHANGE + (CALORIE_LAPSE_GERIATRIC_EXTRA if self.is_geriatric else 0)
            if self.calories <= -CALORIE_LIMIT:
                if self.hunger > 0:
                    self.hunger -= 1
                elif not self.asleep:
                    # DVPet hungerCall() requires !asleep: a sleeping pet never racks
                    # hunger mistakes overnight.  The mistake carries its canon teeth
                    # (hungerMistakePenalty): lifespan -(dec x total mistakes) +
                    # obedience change, and the pet acts up.
                    self.care_mistakes += 1
                    self.mistake_day += 1  # MistakeIncMissedDayChange
                    self.lifespan = max(0.0, self.lifespan
                                        - HUNGER_MISTAKE_LIFE_DEC * max(1, self.care_mistakes))
                    self.obedience += HUNGER_MISTAKE_OBEDIENCE
                    self.mistake_day += 1        # HungerDecAtZeroMissedDayChange
                    self._open_scold()           # neglect: the pet acts up
                if self.hunger == 0:
                    # starvation (setHunger below zero): the calorie crash sheds weight
                    # every further lapse (StarvationCalorieChange -> ActivityWeightChange)
                    self.weight = max(1, self.weight - STARVE_WEIGHT_DEC)
                self.calories = CALORIE_LIMIT

    def _tick_body(self, dt):
        """The body's slow clocks: pooping, effort decay, nutrition decay, the
        filth care-mistake, and filth/starvation sickness."""
        # pooping (DVPet poop(): relief mood bump, sheds weight, drops a sized pile)
        self._poop_t = getattr(self, "_poop_t", 0) + dt
        # (a sleeping pet held it above -- only the desperate 2x gauge goes at night)
        if self._poop_t >= self._poop_interval:
            self._poop_t -= self._poop_interval  # gauge -= bmMax (the remainder carries)
            backlog = self._poop_t >= self._poop_interval / 2
            if backlog:                          # big backlog: bigger pile + extra shed,
                self._poop_t = 0                 # gauge zeroed (DVPet poop())
            self._do_poop(backlog=backlog)
            self._set_anim("poop", 2.2)          # squat-and-go (DVPet poop())
        # effort decays per species (DVPet calcStrengthDecayLapse): keep training or it slips
        self._str_t = getattr(self, "_str_t", 0.0) + dt
        if not self.asleep and self.strength > 0 and self._str_t >= self._strength_interval:
            self._str_t = 0.0
            self.strength -= 1
            if self.strength == 0:
                self.mistake_day += 1            # StrengthDecAtZeroMissedDayChange
        # strengthCall (canon gap closed, audit 2026-07): an EMPTY effort gauge
        # left unattended 10 game-min is a care mistake + obedience -5
        # (strengthMistakePenalty), postponed after one like the other calls
        if self.strength == 0 and not self.asleep:
            self._str_call_t = getattr(self, "_str_call_t", 0.0) + dt
            if self._str_call_t >= 600.0:                    # MinutesToMistakeStrength 10
                self._str_call_t = -3600.0                   # AfterMistakeMinutesPostponed
                self.care_mistakes += 1
                self.mistake_day += 1
                self.obedience -= 5                          # MistakeStrengthObedienceDec
                self._open_scold()
        else:
            self._str_call_t = 0.0
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
                    self.mistake_day += 1  # MistakeIncMissedDayChange
                    self._open_scold()       # left in filth: the pet acts up
        else:
            self._filth_t = 0                # cleaned / under the limit resets the call timer
        # sickness from filth / starvation
        if (self.poop >= 3 or self.hunger == 0) and not self.sick \
                and random.random() < 0.02 / self._phys().get("poop_sick_mult", 1.0) * dt \
                        * (GOOD_NUTR_SICK_MULT if self.good_nutrition() else 1.0):
            self._sicken()

    def _tick_sleep_pressure(self, dt):
        """bedtime is a PRESSURE clock, not the sun (setSleepLapse): SleepLapseInc
        per game-min while awake; at the limit the pet drops off by itself --
        babies (inc 9) nap constantly, adults run a free ~24h rhythm.
        checkNap: LIGHTS OUT while awake starts a shallow nap right away
        (real sleep instead when the pressure is nearly full -- sleepNotNap)."""
        if not self.asleep:
            self.sleep_lapse += dt * self._sleep_inc()
            if self.sleep_lapse >= self.sleep_limit:
                self._fall_asleep()
            elif not self.lights:
                edge = SLEEP_NOT_NAP_MIN - self.restless * SLEEP_NOT_NAP_RESTLESS
                if self.sleep_lapse >= self.sleep_limit - edge:
                    self._fall_asleep()                     # close enough to bedtime
                else:
                    # checkNap: a shallow doze that BORROWS the current cycle --
                    # pressure keeps accruing, so real bedtime still arrives on time
                    self._set_mood(self.mood + ON_NAP_MOOD_INC)
                    self.asleep, self.nap = True, True
                    self._lights_t = 0.0
                    self.awake_lapse = max(0.0, self.awake_limit - self.sleep_lapse)
                    self._set_anim("yawn", 1.8)

    def _tick_mortality(self, dt):
        """DVPet discrete neglect-death triggers (config.csv): real abandonment
        is fatal, not merely a faster lifespan burn.  Care mistakes + injuries
        are per-form (reset on evolution); the starvation timer persists across
        evolutions.  Returns True when the pet died this tick."""
        if self.care_mistakes >= 20 or self.injuries >= 20:   # MaxCareMistakes / MaxInjuries
            self._die(); return True
        if self.hunger == 0 and not self.asleep:              # awake-only, like hungerCall()
            self._starve_t = getattr(self, "_starve_t", 0.0) + dt
            if self._starve_t >= 12 * 3600:                   # empty hunger 12h -> death
                self._die(); return True
        elif self.hunger > 0:
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
            return True
        return False


    @property
    def is_geriatric(self):
        return (not self.dead
                and self.stage in ("Rookie", "Champion", "Ultimate", "Mega")
                and (self.lifespan - self.age_seconds) < GERIATRIC_REMAIN)

    @property
    def day_phase(self):
        # PhysicalState.checkTime: the day's bands come from the HOME's
        # per-season daylight triple [morningStart, noonStart, nightStart]
        # (Winter reads the FALL triple -- a DVPet quirk kept as canon); the
        # last Noon hour is the sunset (isSunset) -> tuipet's dusk.
        hour = (self.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24
        season = "Fall" if self.season == "Winter" else self.season
        tri = self.habitat_obj().get("times", {}).get(season, (6, 14, 19))
        m, n, night = tri
        if m <= hour < n:
            return "dawn"
        if n <= hour < night:
            return "dusk" if hour >= night - 1 else "day"
        return "night"

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
        # bad-temperature sickness is DISABLED in classic mode (SickChanceBadTemp=0),
        # and so is the incompatible-habitat sick check (checkIncompatibleHabitat:
        # Incompatible{Field,Element}SickChance are BOTH 0 in the classic column) --
        # an unfit home hurts through longer sick/injury/fatigue spells, the missed
        # energy saves and the fatigue odds, never through direct illness.

    def save_from_death(self):
        """PhysicalState.saveFromDeath: yanked back from the brink -- starving,
        a bonus point poorer, RevivalLifeInc of life restored -- and the DEATH
        EVOLUTION fires if a Death-special form will take the body (Devimon /
        Bakemon / Ponchomon / Dexmon...).  With none valid it lives on as-is.
        Returns the old num when a death evolution fired, else None."""
        self.dead = False
        self.saved_from_death += 1
        self.hunger = HUNGER_AFTER_SAVED
        self._starve_t = 0.0                          # the 12h clock restarts
        self.evol_bonus += BONUS_AFTER_SAVED
        self.age_seconds = max(0.0, self.lifespan - REVIVAL_LIFE)   # lapsed = total - revival
        old = self.num
        targets = evolution.death_targets(self)
        if targets:
            self.evolve_to(targets[0])               # evol(dying=true): the dark rebirth
        else:
            # no Death form takes it: it lives on -- the continuous death checks
            # need the fatal counters off the trigger line (a mechanical floor;
            # DVPet's checks are edge events so canon never faces this)
            self.care_mistakes = min(self.care_mistakes, 19)
            self.injuries = min(self.injuries, 19)
        self._set_anim("happy", 2.0)                  # the rescue ends in a cheer
        return old if targets else None

    def _guard(self, asleep_blocks=True):
        """The shared action gate: dead / still-an-egg / asleep (a sleeping pet
        is DISTURBED, not served).  Returns the refusal string or None."""
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage == "Egg":
            return "It is still an egg."
        if asleep_blocks and self.asleep:
            return self._disturbed()
        return None

    def _start_poop(self):
        """DVPet startPoop: drop a sized pile (capped at the classic 4)."""
        if self.poop < POOP_MAX_PILES:
            self.poop += 1
            self.poop_sizes.append(self._poop_size())

    def _advance_bm(self, bm):
        """applyFood/bad-med/bad-vitamin: the bowel gauge lurches BM units,
        proportional to the species' own gauge size."""
        self._poop_t = getattr(self, "_poop_t", 0) \
            + self._poop_interval * bm / max(1, self._phys().get("poop_limit", 64))

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
    def highest_dna(self):
        """DNA.getHighestDNA: the CHARGED field with the strict maximum -- a tie
        (or nothing charged) yields none (the caller falls back to the field)."""
        best, best_f = 0, ""
        for f in data.DNA_FIELDS:
            v = self.dna_applied.get(f, 0)
            if v > best:
                best, best_f = v, f
        if best and sum(1 for f in data.DNA_FIELDS
                        if self.dna_applied.get(f, 0) == best) == 1:
            return best_f
        return ""

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
        # applyDNA strength: overflowing the Effort gauge lands at limit-1, NOT
        # the cap (setExercise(getExerciseLimit() - 1)) -- DNA can't top you off
        gain = DNA_STRENGTH_CHANGE * amount
        if self.strength + gain < 4:
            self.strength = max(0, self.strength + gain)
        else:
            self.strength = 3
        same = field == self.field
        self._set_mood(self.mood + (DNA_SAME_FIELD_MOOD if same else DNA_DIFF_FIELD_MOOD) * amount)
        self._set_enthusiasm(self.enthusiasm
                             - (DNA_SAME_FIELD_ENTH_DEC if same else DNA_DIFF_FIELD_ENTH_DEC) * amount)
        # DVPet applyDNA calls checkWorseSick(...) THEN checkSick(...): these are
        # mutually exclusive on sick-state (worsen an existing illness vs. roll a brand
        # new one), so EXACTLY ONE roll ever takes effect -- not two independent
        # new-sickness chances (the old range(2) ~doubled the real sicken rate). The
        # Same/DiffField Sick and WorseSick chances are equal in config (1 / 2), so one
        # `chance` value covers both branches; both bounds are 100 (= DNA_SICK_BOUND).
        chance = (DNA_SAME_FIELD_SICK if same else DNA_DIFF_FIELD_SICK) * amount
        if random.random() < chance / DNA_SICK_BOUND:
            if self.sick:
                self._worsen_sick()                         # checkWorseSick: aggravate it
            else:
                self._sicken()                              # checkSick: a brand-new illness
        return True

    def reset_dna(self):
        """DNA.resetDNA (via resetEvolVar): charged DNA clears on evolution; owned inventory persists."""
        self.dna_applied = {f: 0 for f in data.DNA_FIELDS}

    # ---- per-species physiology (DVPet calcNeedDecay coefficients) -------
    def _phys(self):
        return data.load_requirements().get(self.num, {})

    @property
    def _hunger_interval(self):
        # checkNeedDecay's glutton jitter: each lapse has a 1-in-LessHungerChance(9)
        # roll shifted by glutton -- in expectation a glutton drains ~11% faster,
        # a picky eater ~11% slower.  Applied as a steady coefficient.
        glut = 1.0 - (self.glutton * (1.0 / LESS_HUNGER_CHANCE))
        return CALORIE_DECAY_SEC * (self._phys().get("hunger_decay", 60) / REF_HUNGER_COEF) * glut

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

    def _apply_nutrition(self, food, modifier=1.0):
        """PhysicalState.applyNutrition: a meal adds ceil(macro * modifier) (clamped 0..MaxMacro)."""
        def m(v):
            return math.ceil(int(v) * modifier)
        self.nutr_protein = _clamp(self.nutr_protein + m(food.get("protein", 0)), 0, MAX_MACRO)
        self.nutr_mineral = _clamp(self.nutr_mineral + m(food.get("mineral", 0)), 0, MAX_MACRO)
        self.nutr_vitamin = _clamp(self.nutr_vitamin + m(food.get("vitamin_n", 0)), 0, MAX_MACRO)

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

    def _become(self, num):
        """The species-swap prologue shared by evolution and mode change:
        identity, habitat, energy ceiling, X-antibody lock-in.  Returns the new
        form's requirements record."""
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
        if _req.get("xantibody", "None") in ("Induced", "Natural"):
            self._set_xantibody("Permanent")          # the X-Antibody locks in
        return _req

    def evolve_to(self, num):
        _req = self._become(num)
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
        if self.stage == "Champion" and self.battles:
            # Evolution.champion: the Rookie career's win rate adjusts the bonus
            # (0.1 x winRate - 5: below 50% costs credit, above earns it)
            wr = self.wins / self.battles * 100.0
            self.evol_bonus += int(WIN_RATE_BONUS_COEF * wr - 5)
        self.lifespan += BONUS_EVOLUTION_LIFE * self.evol_bonus   # bonusLifespan
        if _req.get("give_item", -1) >= 0:        # GiveItem: grant a consumable (dormant in data)
            self.add_item(f"i:{_req['give_item']}")
        self._set_anim("happy", 2.5)

    def _swap_form(self, num, subtract_current=False):
        """The Mode/revert half of Evolution.digivolve: swap the SPECIES ONLY.
        No growth-clock reset, no care-record/DNA/taste reset, no lifespan
        extension -- the transform shares the life (digivolve skips all of it
        when SpecialEvol is Mode or reverting)."""
        cur = data.load_requirements().get(self.num, {})
        _req = self._become(num)
        self.weight = self._base_weight()
        if subtract_current:            # revert: un-apply the Mode form's changes
            self.vaccine -= cur.get("vaccine_change", 0)
            self.data_power -= cur.get("data_change", 0)
            self.virus -= cur.get("virus_change", 0)
        else:                           # entering the Mode: its changes apply
            self.vaccine = max(0, self.vaccine + _req.get("vaccine_change", 0))
            self.data_power = max(0, self.data_power + _req.get("data_change", 0))
            self.virus = max(0, self.virus + _req.get("virus_change", 0))

    def mode_change(self):
        """PhysicalState.modeChange: a Mode form reverts to its first
        pre-evolution (only if its power changes can be un-applied); anything
        else evolves along a valid Mode target.  The activity refusal rolls
        with the energy pre-check, compliance is spent, success costs
        ModeChangeEnergyChange and plays State.Evolving.
        Returns (old_num_or_None, message)."""
        if self.dead:
            return None, "It rests now — press N for a new egg."
        if self.asleep:
            return None, self._disturbed()
        refused = self.check_refused(energy_change=MODE_CHANGE_ENERGY)
        self.check_compliant()
        if refused:
            return None, f"{self.name} refuses to change!"
        old = self.num
        if evolution.is_mode_form(self.num):
            prev = evolution.pre_evolution(self.num)
            cur = data.load_requirements().get(self.num, {})
            if (prev is None
                    or self.vaccine - cur.get("vaccine_change", 0) < 0
                    or self.data_power - cur.get("data_change", 0) < 0
                    or self.virus - cur.get("virus_change", 0) < 0):
                self._set_anim("refuse", 1.0)             # Jeering
                return None, "The mode holds — it can't revert."
            self._swap_form(prev, subtract_current=True)
        else:
            targets = evolution.mode_targets(self)
            if not targets:
                self._set_anim("refuse", 1.0)             # Jeering
                return None, "The mode is out of reach."
            self._swap_form(targets[0])
        self._set_energy(self.energy + MODE_CHANGE_ENERGY)
        self._set_anim("happy", 2.5)                      # State.Evolving
        return old, f"MODE CHANGE — {self.name}!"

    def can_mode_change(self):
        return (self.num != -1 and not self.dead
                and self.stage not in ("Egg", "Fresh")
                and evolution.can_mode_change(self))

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
        if value < self.energy:
            value = self._energy_bonus_save(value)   # checkEnergyIncFromPerfectConditions
        if value < 0 and value < self.energy:
            self._set_mood(self.mood - 10)       # NegativeEnergyMoodDec (per step into the red)
        self.energy = value

    def _nice_weather(self):
        """checkNiceWeather: DeepSaver/Water pets love the rain, cold-blooded
        (freezing ideal) or Ice pets love the snow."""
        import tuipet.weather as wx_
        if self.weather in wx_.RAIN:
            return self.field == "DeepSaver" or self.element == "Water"
        if self.weather in wx_.SNOW:
            return self.ideal_temp[0] <= wx.FREEZING_TEMP or self.element == "Ice"
        return False

    def _energy_bonus_save(self, new):
        """An energy drop during the pet's FAVOURITE time can bounce back +1
        when conditions are perfect: good weather / mood / temp / nutrition and
        a compatible home each shrink the roll range (best case ~1 in 2)."""
        if self.favorite_time() != self.day_phase:
            return new
        h = self.habitat_obj()
        rng = ENERGY_BONUS_BASE
        rng += ENERGY_BONUS_COMPAT_F if self.field in h["compat_fields"] else 0
        rng += ENERGY_BONUS_COMPAT_E if self.element in h["compat_elements"] else 0
        rng += ENERGY_BONUS_INCOMPAT_F if self.field in h["incompat_fields"] else 0
        rng += ENERGY_BONUS_INCOMPAT_E if self.element in h["incompat_elements"] else 0
        if self.weather in ("Clear", "Cloudy") or self._nice_weather():
            rng += ENERGY_BONUS_WEATHER
        if self.current_mood() == "Happy":
            rng += ENERGY_BONUS_MOOD
        lo, hi = self.ideal_temp
        if lo <= self.temp <= hi:
            rng += ENERGY_BONUS_TEMP
        if self.good_nutrition():
            rng += ENERGY_BONUS_NUTRITION
        if rng > 1 and random.randrange(rng) == 1:
            new += 1
        return new

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

    def _do_poop(self, backlog=False):
        """PhysicalState.poop: relief mood bump, weight shed, and a new sized pile
        added to the filth (capped at the _filth array length).  A big BACKLOG
        (gauge still >= bmMax/2 after the poop) makes the pile one size bigger --
        the only source of size-4 piles -- and sheds an extra half weight."""
        self._set_mood(self.mood + POOP_MOOD_INC)                 # PoopMoodInc
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self.weight = max(1, self.weight - wdec)
        size = self._poop_size()
        if backlog:
            size = min(4, size + 1)
            self.weight = max(1, self.weight - math.ceil(wdec / 2))
        if self.poop < POOP_MAX_PILES:                            # addFilth: first free slot (capped)
            self.poop += 1                                        # poop == countFilth()
            self.poop_sizes.append(size)

    def _sleep_inc(self):
        """Species sleep-pressure rate (SleepLapseInc: 1 adult / 2 / 9 baby)."""
        return data.load_requirements().get(self.num, {}).get("sleep_lapse_inc", 1)

    def _fall_asleep(self):
        """PhysicalState.sleep(): the pressure clock rolls over -- sleep long
        enough to refill the energy bar (clamped 6..15 game-hours), and the
        next awake stretch is whatever remains of the 24."""
        self.sleep_lapse = 0.0
        self.asleep = True
        self.nap = False
        self._lights_t = 0.0                        # setAsleep resets _callMinutesLights
        gain = max(1, getattr(self, "_sleep_energy_gain", 3))
        need = math.ceil(max(0, self.max_energy - self.energy) / gain) * 60.0
        self.awake_limit = _clamp(need, MIN_AWAKE_LIMIT, MAX_AWAKE_LIMIT)
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        self._set_anim("yawn", 1.8)

    def _wake(self, morning=True):
        """setAsleep(false): up for the day (the morning roll skips for naps)."""
        self.asleep = False
        self.nap = False
        self.awake_lapse = 0.0
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        if not self.lights:
            self.lights = True                      # wake: setLights(true)
        if morning:
            r = random.randrange(MORNING_MOOD_CHANCE)
            m = self.current_mood()
            if r == 0:
                self._set_mood(self.mood + BAD_MORNING_MOOD.get(m, -10))
            elif r == 1 and m == "Happy":
                self._set_mood(WORST_MORNING_MOOD)
            elif r == 2:
                self._set_mood(self.mood + GOOD_MORNING_MOOD.get(m, 100))
        self._set_anim("wake", 1.6)

    def _disturbed(self):
        """PhysicalState.disturb(): bothering REAL sleep wakes the pet grumpy --
        nearly-rested (or full energy) it just gets up; otherwise the sleep is
        POSTPONED: it will drop back off in DisturbPostpone game-minutes, still
        owing the missed rest.  Naps aren't disturbable (lights wake them)."""
        if not self.asleep or self.nap:
            return "zzz..."
        self.disturb += 1
        self.mistake_day += 1                       # DisturbanceMissedDayChange
        self._set_mood(self.mood - 10)              # DisturbMoodDec
        enth = {1: -1, 0: -2, -1: -3}.get(self.restless, -2)   # DisturbEnthusiasmDec*
        self._set_enthusiasm(self.enthusiasm + enth)
        rested = (self.awake_lapse >= FULL_AWAKE_DISTURB - self.restless * FULL_AWAKE_DISTURB_RESTLESS
                  or self.energy >= self.max_energy)
        if rested:
            self.sleep_lapse = 0.0
            self._wake(morning=False)
            return "It grumbles awake."
        postpone = random.randint(*DISTURB_POSTPONE)
        self.sleep_lapse = max(0.0, self.sleep_limit - postpone / max(1, self._sleep_inc()))
        # (the missed rest is repaid naturally: _fall_asleep re-sizes the next
        # sleep from the CURRENT energy debt, so nothing is carried by hand)
        self._wake(morning=False)
        self._set_anim("angry", 1.8)                # Sad_Jeering: woken too soon
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

    def check_refused(self, food=None, attr=None, energy_change=0.0):
        """PhysicalState.checkRefused: the obedience refusal roll.  Only a
        NON-COMPLIANT pet (uncorrected misbehavior -- a fair scold restores
        compliance) ever refuses: roll r in [0, RefuseChance) against
        adjustedObedience + the branch's obey mods; past the line, the pet blows
        you off (Refusing anim + the scold window opens)."""
        self.refused = False
        if self.dead or self.compliance:
            return False
        r = random.randrange(REFUSE_CHANCE)
        base, mood_factor, obey_all = self._obedience_factors()
        obed = self._adjusted_obedience()
        refused = False
        if energy_change and self.energy + math.ceil(energy_change * self.max_energy) < 0:
            refused = True                       # can't afford the energy -> auto-refuse
        elif food is not None:
            cats = [c for c in (food.get("category") or "").split(";") if c]
            fav = bool(self.favorite_food) and self.favorite_food in cats
            if fav and self.hunger <= FULL_HUNGER:
                return False                     # favourite food when hungry: never refused
            obey = 0.0
            if "Med" in cats:
                obey += REFUSE_MED_FACTOR * (1 - base)
            if self.disliked_food and self.disliked_food in cats:
                obey += self.hunger / STOMACH_CAPACITY * REFUSE_DISLIKED_FOOD
            elif fav:
                obey += (1 - self.hunger / STOMACH_CAPACITY) * REFUSE_FAV_STOMACH
            for trait, key in ((self.disposition, "t_disposition"),
                               (self.restless, "t_restless"), (self.glutton, "t_glutton")):
                fv = int(food.get(key, 0) or 0)
                if fv != 0:
                    obey += REFUSE_PERSONALITY_MATCH if fv == trait else REFUSE_PERSONALITY_UNMATCH
            obey += (REFUSE_UNWELL_SICK if self.sick else 0.0) * (1 - base)
            hcoef = (REFUSE_GLUTTON_HUNGER if self.glutton > 0
                     else REFUSE_NOT_GLUTTON_HUNGER if self.glutton < 0 else REFUSE_HUNGER_MOD)
            obey += self.hunger / STOMACH_CAPACITY * hcoef + mood_factor
            refused = r >= obed + obey
        elif attr is not None:
            # training: the species' own attribute obeys while spirited; dispirited,
            # even the favourite gets a +20 grace line (ExerciseRefuseLowEnthusiasm)
            if attr == self.attribute:
                if self.enthusiasm > 0:
                    return False
                refused = r >= obed + EXERCISE_REFUSE_LOW_ENTH + obey_all
            else:
                refused = r >= obed + obey_all
        else:
            # activity (battle/jogress): temperament shapes the temper -- a feisty
            # (+1) pet refuses more, a docile (-1) one fights when told (+50 grace)
            if self.disposition >= 0:
                refused = r + self.disposition * BATTLE_DISPO_COEF >= obed + obey_all
            else:
                refused = r >= obed + BATTLE_LOW_DISPO_FACTOR + obey_all
        if refused:
            self.refused = True
            self.scold_flag, self.scold_window = True, 0     # _scold = true: correct it!
            self._set_anim("refuse", 1.5)
        return refused

    def refuse_attack(self, my_hp, enemy_hp):
        """PhysicalState.refuseAttack (Orders style only): mid-fight, an ORDERED
        attack may be refused -- a hurt pet obeys less; a feisty (+1) pet
        refuses more on principle, a docile (-1) one balks when it's losing.
        On refusal the pet attacks its own way and the scold window opens."""
        if self.free_style or self.dead:
            return False
        r = random.randrange(REFUSE_CHANCE)
        obey = self._obedience_factors()[2]
        obed = self._adjusted_obedience()
        healthy = my_hp >= self.full_health / OBED_HEALTH_COEF
        if self.disposition >= 0:
            obed_chance = obed + obey + (HI_DISPO_OBED_HIGH_HP if healthy else HI_DISPO_OBED_LOW_HP)
            refuse_chance = r + self.disposition * HI_DISPO_REFUSE_COEF
        else:
            obed_chance = obed + obey + (LO_DISPO_OBED_HIGH_HP if healthy else LO_DISPO_OBED_LOW_HP)
            refuse_chance = r + (LO_DISPO_REFUSE_LOW_ENEMY if my_hp >= enemy_hp
                                 else LO_DISPO_REFUSE_HIGH_ENEMY)
        if refuse_chance >= obed_chance:
            self.scold_flag, self.scold_window = True, 0    # setScold(true) mid-fight
            return True
        return False

    def stop_travel_prob(self):
        """PhysicalState.checkStopTravel as a per-fire PROBABILITY (the caller
        composes it over a full stride).  One draw per controller fire,
        r in [cap, cap + chance*3000); the energy fraction scales the draw
        DOWN, so a rested pet essentially never stops but a drained one plants
        its feet: refuse when r*(energy+1)/max - dispo*35 + obey - 5
        <= cap - obedience."""
        if self.dead or self.compliance:
            return 0.0
        obey = self._obedience_factors()[2]
        energy_mod = 1.0 - (self.max_energy - (self.energy + 1)) / max(1, self.max_energy)
        if energy_mod <= 0:
            return 1.0
        # refuse iff r <= T / energy_mod, r uniform over [cap, cap + span)
        span = REFUSE_CHANCE * REFUSE_TRAVEL_COEFF
        t = (OBEDIENCE_REFUSAL_CAP - self.obedience
             + self.disposition * REFUSE_TRAVEL_DISPO - obey + REFUSE_TRAVEL_WALK)
        return min(1.0, max(0.0, (t / energy_mod - OBEDIENCE_REFUSAL_CAP) / span))

    def stop_travel_effects(self):
        """The refusal's side effects (split from the roll so it can compose)."""
        self.refused = True
        self.scold_flag, self.scold_window = True, 0         # _scold = true
        self._set_anim("refuse", 1.5)

    def check_stop_travel(self):
        """One canonical per-fire draw (kept for tests/direct callers)."""
        if random.random() < self.stop_travel_prob():
            self.stop_travel_effects()
            return True
        return False

    def check_compliant(self):
        """PhysicalState.checkCompliant: obeying while compliant CONSUMES the
        compliance (it covers one feed/jogress, not a lifetime pass) -- and losing
        it fairly opens the praise window (setCompliance true->false sets _praise:
        the pet did as it was told; reward it)."""
        complied = self.compliance
        if complied:
            self._open_praise()
        self.compliance = False
        return complied

    def can_feed(self):
        """Guard for opening the feed menu (mirrors feed()'s own gates)."""
        if (_g := self._guard()) is not None:
            return _g
        return None

    def feed(self, food=None):
        """PhysicalState.feed -> applyFood: apply a food's FULL effect set, each
        scaled by DVPet's fullness modifier.  A hunger-food (Meat) refuses a full
        stomach; a strength-food (Protein/Vitamin, hunger 0) never fills, so it
        builds strength/DP even on a full pet -- the classic Meat/Protein split."""
        if (_g := self._guard()) is not None:
            return _g
        foods = data.load_foods()
        food = food or (foods[0] if foods else {"name": "Meat", "hunger": 1, "weight": 4, "mood": 5})
        self._last_meal_starving = self.hunger == 0          # eat(): wolfed down (decided PRE-meal)
        refused = self.check_refused(food=food)              # applyFood: checkRefused ...
        self.check_compliant()                               # ... then the compliance is spent
        if refused:
            return f"{self.name} refuses to eat!"
        fills = int(food.get("hunger", 0)) > 0
        # a hunger-food on a full stomach -> too full (a glutton eats past FULL_HUNGER)
        if fills and self.hunger >= FULL_HUNGER and self.glutton <= 0:
            self.weight += 1
            self.overeat += 1
            self.mistake_day += 1                # OverStomachCapcityMissedDayChange
            self.calories = CALORIE_LIMIT
            self._poop_t = min(self._poop_interval, getattr(self, "_poop_t", 0) + 900)   # overeat -> sooner poop
            self._last_meal_disliked = False
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        # DVPet applyFood modifier: a near-full stomach diminishes a hunger-food's
        # effects (1 - overfull/stomach); a strength-food (hunger 0) is always full-value.
        over = self.hunger - FULL_HUNGER
        modifier = 1.0 if (over <= 0 or not fills) else max(0.0, 1.0 - over / STOMACH_CAPACITY)

        def scaled(key):
            return math.ceil(food.get(key, 0) * modifier) if food.get(key, 0) > 0 else int(round(food.get(key, 0) * modifier))

        cap = OVEREAT_LIMIT if self.glutton > 0 else FULL_HUNGER
        self.hunger = _clamp(self.hunger + scaled("hunger"), 0, cap)
        self.strength = _clamp(self.strength + scaled("strength"), 0, 4)   # Protein builds Effort/DP
        self._set_energy(self.energy + scaled("energy"))
        self._set_mood(self.mood + scaled("mood")           # foods.csv intrinsic mood (Cake +60, Veg -10)
                       + int(math.ceil(self._personality_mood(food) * modifier)))
        self.obedience += scaled("obedience")
        self._set_enthusiasm(self.enthusiasm + scaled("enthusiasm"))
        if food.get("health"):                              # HP Chip: permanent trained-HP gain
            self.full_health = min(self.max_health(),
                                   self.full_health + math.ceil(food["health"] * modifier))
        self.calories = CALORIE_LIMIT                       # a meal refills the calorie buffer
        self.weight += int(food.get("weight", 1))
        # every meal advances the bowel gauge (applyFood: bmGauge += food.BMGauge):
        # eating more means pooping sooner, proportional to the species bmMax
        bm = int(food.get("bm", 0))
        if bm > 0:
            self._poop_t = getattr(self, "_poop_t", 0) \
                + self._poop_interval * bm / max(1, self._phys().get("poop_limit", 64))
        tier = self._eat_food(food.get("category", ""))     # DVPet taste: fav/disliked/neutral
        self._last_meal_disliked = (tier == "disliked")      # eat(): disliked -> +9 grimace bite
        self._apply_nutrition(food, modifier)                # GoodNutrition macros (scaled)
        self._set_anim("eat", 1.4)
        tag = {"favorite": "  It loves it!", "disliked": "  It dislikes that."}.get(tier, "")
        return f"Fed {food['name']}.{tag}"

    def can_train(self):
        if (_g := self._guard()) is not None:
            return _g
        if self.is_fatigued():
            self._set_anim("exhausted", 1.2)
            return "Too fatigued — let it rest."
        if self.energy <= 0:                            # MinEnergyForActivity
            self._set_anim("refuse", 1.0)
            return "Too tired to train."
        return None

    def max_health(self):
        """PhysicalState.getMaxHealth: the trained-HP CAP rises with lapsed life."""
        days = self.age_seconds / DAY_LENGTH
        for d, cap in HEALTH_CAP_LADDER:
            if days >= d:
                return cap
        return MAX_HEALTH_DEFAULT_CAP

    def _check_perfect_wins(self):
        """checkAndIncPerfectWins(PracticeAlwaysIncPerfectWins=TRUE): every HP-drill
        success counts; each PerfectWinsLimit-th grows fullHealthPoints toward the
        age cap (HealthInc when it actually lands)."""
        self.perfect_wins += 1
        if self.perfect_wins % PERFECT_WINS_LIMIT == 0:
            before = self.full_health
            self.full_health = min(self.max_health(), self.full_health + PERFECT_WINS_HEALTH_INC)
            if self.full_health > before:
                return " HP +1!"                     # State.HealthInc
        return ""

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
        complied = self.check_compliant()                 # onExerciseFinish: checkCompliant
        strength0 = self.strength
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
        # checkExerciseTime: drilling at the pet's favourite time of day lifts it,
        # at the disliked time it drags; any other hour still costs a little mood
        now = self.day_phase
        if self.favorite_time() == now:
            self._set_mood(self.mood + FAV_EXERCISE_TIME_MOOD)
            self._set_enthusiasm(self.enthusiasm + FAV_EXERCISE_TIME_ENTH)
        elif self.disliked_time() == now:
            self._set_mood(self.mood - NOTFAV_EXERCISE_TIME_MOOD)
            self._set_enthusiasm(self.enthusiasm + DISLIKED_TIME_EXERCISE_ENTH)
        else:
            self._set_mood(self.mood - NOTFAV_EXERCISE_TIME_MOOD)
        self._set_mood(self.mood + self.enthusiasm)       # exercise(): mood rides the spirit
        # checkWorseSick(ExerciseWorseSickChance): drilling a SICK pet can worsen it --
        # and if it only trained because you spent its compliance, it resents you
        if self.sick and random.randrange(100) < EXERCISE_WORSE_SICK_CHANCE:
            self._worsen_sick()
            if complied:
                self.obedience += OBEDIENCE_CHANGE_SICK_FORCED
        self.weight = max(1, self.weight - 2)
        self.calories = max(-CALORIE_LIMIT, self.calories - EXERCISE_CALORIE_DEC)  # ExerciseCalorieDec
        self._set_energy(self.energy - 1)               # ExerciseEnergyDec
        # setExercise: driving the Effort gauge past its LIMIT risks fatigue --
        # good nutrition softens the odds, the home's compatibility bends them
        if success and strength0 >= 4:
            h = self.habitat_obj()
            chance = GOOD_NUTRITION_FATIGUE_CHANCE if self.good_nutrition() else FATIGUE_CHANCE
            chance += FATIGUE_COMPAT_CHANGE * ((self.field in h["incompat_fields"])
                                               + (self.element in h["incompat_elements"])
                                               - (self.field in h["compat_fields"])
                                               - (self.element in h["compat_elements"]))
            if random.randrange(100) < chance:
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
            hp_note = self._check_perfect_wins() if success else ""
            return f"{rank} {'Effort up!' if hits >= 2 else 'no gain'}{hp_note}"
        return f"{rank} +{gain} {attr}"

    def can_battle(self):
        if self.dead:
            return "It rests now — press N for a new egg."
        if self.stage in ("Egg", "Fresh"):
            return "Too young to battle."
        if self.asleep:
            return self._disturbed()
        if self.check_refused():                             # canBattle -> checkRefused
            return f"{self.name} refuses to fight!"
        if self.is_fatigued():
            self._set_anim("exhausted", 1.2)
            return "Too fatigued — let it rest."
        if self.energy <= 0:                            # MinEnergyForActivity
            self._set_anim("refuse", 1.0)
            return "Too tired to battle."
        return None

    def record_battle(self, won, enemy=None, free_style=None):
        """Resolve a finished battle: update battles/wins and rewards.  The
        battle passes its BAKED style so a mid-fight toggle can't split the
        bonus from the rewards."""
        style_free = self.free_style if free_style is None else free_style
        self.battles += 1
        if not style_free:
            self.obedience += BATTLE_FREE_OBED_INC       # fighting under orders builds discipline
        self._set_energy(self.energy - 1)               # battle energy (BattleWon/LostEnergyDec)
        self._check_worse_injury(in_battle=True)         # battling injured can worsen it
        if won:
            self.wins += 1
            if enemy:
                self.levels_fought.append(_enemy_level(enemy))
            self._open_praise()                          # a win is praiseworthy (setPraise)
            self._set_mood(self.mood + 10)               # BattleWonMoodInc
            # over/underpowered adjustments (battleEnd compareStage + HP gates):
            # squashing a hollow higher-stage foe is a JOYLESS win (-20); toppling a
            # tougher lower-stage bruiser is a proud one (+10)
            grew = ""
            if enemy:
                cap = self.full_health or 1     # DVPet's HP gates compare vs fullHealthPoints
                ehp = enemy.get("hp", cap)
                mine = data.stage_rank(self.stage)
                theirs = data.stage_rank(enemy.get("stage", self.stage))
                # (tuipet pet full-HP == its stage cap, so DVPet's two HP gates collapse)
                if mine < theirs and ehp < cap:
                    self._set_mood(self.mood - 20)       # OverpoweredBattleWonMoodDec
                elif mine > theirs and ehp > cap:
                    self._set_mood(self.mood + 10)       # UnderpoweredBattleWonMoodInc
                # incStats: the win GROWS the pet's power in the enemy's dominant
                # attribute -- classic getExtraStats = min(ceil(opp/1), 1) = +1
                counts = {"Vaccine": enemy.get("vaccine", 0), "Data": enemy.get("data_power", 0),
                          "Virus": enemy.get("virus", 0)}
                dom = max(counts, key=counts.get)
                if dom == "Vaccine":
                    self.vaccine += 1
                elif dom == "Data":
                    self.data_power += 1
                else:
                    self.virus += 1
                grew = f"  +1 {dom}"
            self._set_enthusiasm(self.enthusiasm - 3)    # BattleWonEnthusiasmDec
            if not style_free:                           # battleEnd: a win UNDER ORDERS is prouder
                self._set_mood(self.mood + ORDERS_WON_MOOD_INC
                               + BATTLE_DISPO_MOOD_FACTOR * -self.disposition)
            lo, hi = (enemy or {}).get("bits", (1, 5))
            gained = random.randint(lo, hi)
            self.bits += gained
            self._set_anim("happy", 2.0)
            return f"Victory! +{gained} bits{grew}"
        self._set_mood(self.mood - 20)               # BattleLostMoodDec
        self._set_enthusiasm(self.enthusiasm - 6)    # BattleLostEnthusiasmDec
        self.obedience -= 1                          # BattlesObedienceDec (a loss saps trust)
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

    # -- the pet-initiated surrender request (ClockTic onRoundEnd ->
    # checkSurrender; wired into battlescreen 2026-07-04) --
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

    def is_freezing(self):
        """Too cold: temperature at or below the freezing threshold."""
        return self.temp <= wx.FREEZING_TEMP

    def is_overheating(self):
        """Too hot: temperature above the ideal band's upper bound."""
        return self.temp >= self.ideal_temp[1] + wx.UPPER_IDEAL

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

    def _worsen_sick(self):
        """PhysicalState.checkWorseSick (effect body): an already-sick pet gets worse --
        the illness drags on one lapse longer, with mood/obedience/spirit costs and a
        fresh mess. (The WorseSickLifeDec lifespan hit is omitted, as in _worsen_injury.)"""
        self.obedience += WORSE_MALADY_OBED_DEC
        self._set_mood(self.mood + WORSE_MALADY_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + SICK_ENTH_CHANGE)  # WorseSickEnthusiasmChange == -1
        self.sick_length += SICK_LAPSE_MIN                        # setSickLength(_sickLength + 1) = +1 lapse
        self._start_poop()

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
        """PhysicalState.feedVitamin: top up injury-worsening protection.  A dose
        while the last one still runs is a BAD VITAMIN: sick risks, a bowel
        lurch, mood and lifespan costs, and it comes right up."""
        if self.vitamin_lapse > 0:
            self.mistake_day += 1                            # BadVitaminMissedDayChange
            if self.sick and random.randrange(100) < VITAMIN_WORSE_SICK_CHANCE:
                self._worsen_sick()
            self._advance_bm(BAD_VITAMIN_BM_INC)
            self._set_mood(self.mood - BAD_VITAMIN_MOOD_DEC)
            self.lifespan = max(0.0, self.lifespan - BAD_VITAMIN_LIFE_DEC)
            if not self.sick and random.randrange(REFUSE_CHANCE) < VITAMIN_OVERFED_SICK_CHANCE:
                self._sicken()                               # vitaminOverfedSickChance
            self._start_poop()
            self._set_anim("refuse", 1.5)                    # Bad_Health_Jeering
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
        self.mistake_day += 1                    # FatigueMissedDay
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
        if (_g := self._guard()) is not None:
            return _g
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
        if (_g := self._guard()) is not None:
            return _g
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
            self.refused = False                              # setRefused(false): back in line
            self._set_anim("angry", 1.8)
            return f"{self.name} takes the lesson to heart."
        self._set_enthusiasm(self.enthusiasm + SCOLD_ENTH)
        self._set_anim("angry", 1.6)
        return f"You scold {self.name}."

    def clean(self):
        if (_g := self._guard()) is not None:
            return _g
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.poop_sizes = []                        # clearFilth()
        self._set_mood(self.mood + 6)               # CleanMoodInc
        self._set_anim("wash", 1.2)
        return f"Cleaned {n} poop."

    def heal(self):
        """The First Aid button (Medical menu): a SICK pet takes the Med staple
        (feedMed), an injured one gets the Bandage (applyBandage).  Treatment is
        INCREMENTAL -- each dose shortens the spell by its CureLapse/HealLapse
        (-2 lapses); the instant cure is the shop's Elixir (Cured=TRUE, 2000b)."""
        if (_g := self._guard()) is not None:
            return _g
        if self.sick:
            return self._feed_med()
        if self.is_injured():
            return self._apply_bandage()
        return "It's not sick or injured."

    def _feed_med(self):
        """PhysicalState.feedMed: the Med staple (f:4, infinite, CureLapse -2).
        Dosing AGAIN while the medicine indicator still runs is a BAD MED --
        poison: lifespan -BadMedLifeDec, the bowels lurch, and it jeers."""
        med = data.consumable_by_key("f:4") or {"mood": -10, "cure_lapse": -2}
        refused = self.check_refused(food=med)               # feed(): the Med -20 obey mod
        self.check_compliant()
        if refused:
            return f"{self.name} spits out the medicine!"
        if self.med_lapse > 0:                               # getMed(): double dose
            self.mistake_day += 1                            # BadMedMissedDayChange
            self.lifespan = max(0.0, self.lifespan - BAD_MED_LIFE_DEC)
            self._advance_bm(BAD_MED_BM_INC)
            self._start_poop()
            self._set_anim("refuse", 1.5)                    # Bad_Health_Jeering
            return "A double dose — that was poison!"
        self._set_mood(self.mood + int(med.get("mood", -10)))          # it tastes awful
        self.sick_length = max(0.0, self.sick_length
                               + med.get("cure_lapse", -2) * SICK_LAPSE_MIN)
        if self.sick_length == 0:
            self.sick = False                                # the dose finished it off
        self._set_mood(self.mood + CURED_MOOD_BONUS // MAX_SICK_LENGTH)
        self.obedience += CURED_OBED_BONUS // MAX_SICK_LENGTH
        self.med_lapse = MEDICINE_HOURS                      # the indicator runs as it wears off
        self._set_anim("heal", 1.5)
        return ("The medicine worked!" if not self.sick
                else f"{self.name} keeps the medicine down... it helps.")

    def _apply_bandage(self):
        """PhysicalState.applyBandage: the Bandage item (i:80, HealLapse -2);
        an already-bandaged pet jeers the second wrap off."""
        if self.bandage_lapse > 0:                           # getBandage(): one wrap at a time
            self._set_anim("refuse", 1.0)                    # Jeering
            return "It's already bandaged up."
        bandage = data.consumable_by_key("i:80") or {"heal_lapse": -2}
        refused = self.check_refused(food=bandage)           # useItem's refusal roll
        self.check_compliant()
        if refused:
            return f"{self.name} squirms away from the bandage!"
        self.inj_length = max(0.0, self.inj_length
                              + bandage.get("heal_lapse", -2) * INJ_LAPSE_MIN)
        if self.inj_length == 0:
            self.injuries = max(0, self.injuries - 1)        # mended
        self._set_mood(self.mood + CURED_MOOD_BONUS // MAX_INJ_LENGTH)
        self.obedience += CURED_OBED_BONUS // MAX_INJ_LENGTH
        self.bandage_lapse = BANDAGE_HOURS
        self._set_anim("heal", 1.5)
        return ("All patched up!" if self.inj_length == 0
                else f"{self.name} is bandaged — it needs rest now.")

    def toggle_lights(self):
        """The lights button (DVPet setLights): toggles the room light ONLY. The pet
        sleeps and wakes on its own schedule -- this does not force sleep or wake."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        self.lights = not self.lights
        if self.lights and self.asleep and self.nap:
            # lightSwitch: lights ON rouses a NAPPING pet (deep sleep ignores it;
            # sick or injured, the lost doze pushes bedtime a minute closer)
            if self.sick or self.is_injured():
                self.sleep_lapse += 1
            self._wake(morning=False)
            return "Lights on — up from its nap."
        return "Lights off." if not self.lights else "Lights on."

    def play(self):
        if (_g := self._guard()) is not None:
            return _g
        # tuipet's Play button maps onto PhysicalState.spoil(): setMood(+SpoilMoodInc)
        # AND setObedience(-SpoilObedienceDec) -- a real tradeoff (happier now, but the
        # pet gets cheekier).  The animation is DVPet's jumping()/playing(): the pet
        # bounces on poses 1<->5 (ROLES["play"]), rendered as the "play" hop fx.
        self._set_mood(self.mood + SPOIL_MOOD_INC)
        self.obedience = max(0, self.obedience - SPOIL_OBEDIENCE_DEC)   # DVPet setObedience floors at 0
        self._set_anim("play", 1.5)
        return "Played together -- happy, but a bit spoiled."

    # ---- shop / items --------------------------------------------------------
    def buy_slot(self, slot):
        """Buy one from a rolled shop slot: pay the sale-aware purchase price,
        decrement the slot's stock (decStock) and bag it."""
        entry = data.consumable_by_key(slot["key"])
        if not entry:
            return "?"
        if slot.get("stock", 0) <= 0:
            return "Sold out."
        price = shop.purchase_price(slot)
        if self.bits < price:
            return "Not enough bits."
        key = entry["key"]
        cap = entry.get("max_uses") or 99
        if self.inventory.get(key, 0) >= cap:
            return f"Can't carry more {entry['name']} (max {cap})."
        self.bits -= price
        slot["stock"] -= 1
        self.inventory[key] = self.inventory.get(key, 0) + 1
        return f"Bought {entry['name']}."

    def sell(self, entry):
        """Resell one from the bag at price/DefaultResellFactor (unsellable at 0)."""
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

    def _birthday(self):
        """setTimeToAge's age-up: a mostly-Happy, zero-slip day earns a GOOD
        birthday (+bonus, +lifespan, a Cupcake); a mostly-Unhappy day with slips
        is a BAD one (-bonus, -lifespan, a consolation Candy); anything else is
        normal (a Cookie).  getMajority: a TIE yields no major mood -> normal.
        The slate (missed-days + the mood record) wipes for the new day."""
        counts = self.daily_mood
        best = max(counts.values()) if counts else 0
        tops = [k for k, v in counts.items() if v == best and best > 0]
        major = tops[0] if len(tops) == 1 else None
        if major == "Happy" and self.mistake_day <= MAX_MISTAKE_DAY_BONUS:
            self.lifespan += BONUS_LIFE_INC
            self.evol_bonus += 1
            self.add_item(f"f:{GOOD_BIRTHDAY_FOOD}")
            self._set_anim("happy", 2.0)                     # Birthday_Good
            self.birthday_note = f"A wonderful day! {self.name} earned a Cupcake!"
        elif major == "Unhappy" and self.mistake_day >= MIN_MISTAKE_DAY_DEC:
            self.lifespan = max(0.0, self.lifespan - BONUS_LIFE_DEC)
            if self.evol_bonus > 0:
                self.evol_bonus -= 1
            self.add_item(f"f:{BAD_BIRTHDAY_FOOD}")
            self._set_anim("sad", 2.0)                       # Birthday_Bad
            self.birthday_note = "A rough day... just a Candy."
        else:
            self.add_item(f"f:{NORMAL_BIRTHDAY_FOOD}")
            self._set_anim("happy", 1.5)                     # Birthday_Normal
            self.birthday_note = f"{self.name} is a day older — have a Cookie."
        self.mistake_day = 0
        self.daily_mood = {k: 0 for k in self.daily_mood}

    def _check_gift_call(self, dt):
        """PhysicalState.checkGiftCall + checkGift: every GiftChanceMin game-min,
        a grown, awake, HAPPY pet rolls nextInt(cap - obedience +
        (maxMood - mood) * 0.5 + 70) -- a 0 means it found you a present (the
        better cared-for the pet, the narrower the range).  The pet then calls
        for attention (GiftCall, poses 5/7) until the gift is claimed."""
        self.gift_t += dt
        if self.gift_t < GIFT_CHANCE_MIN:
            return
        self.gift_t = 0.0
        if (self.gift or self.asleep or self.stage in ("Egg", "Fresh", "InTraining")
                or self.current_mood() != "Happy"):
            return
        chance = int(OBEDIENCE_REFUSAL_CAP - self.obedience
                     + (MOOD_MAX - self.mood) * GIFT_CHANCE_MOOD_COEFF + GIFT_CHANCE_FACTOR)
        if chance > 0 and random.randrange(chance) == 0:
            self.gift = self._pick_gift()

    def _pick_gift(self):
        """PhysicalState.getGift: each CanInc consumable enters the pool at its
        own GiftChance/100 odds (getCanGift is a per-roll randomChance); the
        present is a uniform pick from the passers."""
        pool = [e["key"] for e in data.home_shop_pool()
                if e.get("can_inc") and e.get("gift_chance", 0) > 0
                and data.item_is_functional(e)
                and random.randrange(100) < e["gift_chance"]]
        return random.choice(pool) if pool else ""

    def claim_gift(self):
        """ClockTic.giftEnd: the present lands in the bag and the pet cheers."""
        key, self.gift = self.gift, ""
        if not key:
            return ""
        e = data.consumable_by_key(key) or {}
        self.add_item(key)
        self._set_anim("happy", 2.0)                # giftEnd -> State.Cheering
        return f"{self.name} gives you {e.get('name', 'a present')}!"

    def add_item(self, key, n=1):
        """Drop loot / grants straight into the bag."""
        self.inventory[key] = self.inventory.get(key, 0) + n

    def _personality_mood(self, e):
        """consumablePersonalityMoodChange: +-10 per personality tag the
        consumable shares/clashes with the pet (disposition/restless/glutton)."""
        total = 0
        for trait, key in ((self.disposition, "t_disposition"),
                           (self.restless, "t_restless"), (self.glutton, "t_glutton")):
            fv = int(e.get(key, 0) or 0)
            if fv != 0:
                total += PERSONALITY_MOOD_MATCH if fv == trait else PERSONALITY_MOOD_UNMATCH
        return total

    def use_item(self, key):
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        e = data.consumable_by_key(key)
        if not e:
            return "?"
        if not data.item_is_functional(e):
            return f"{e['name']} has no use yet."   # action-item whose system is unbuilt
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        refused = self.check_refused(food=e)         # useItem: checkRefused (audit: canon gap)
        self.check_compliant()                       # ...; checkCompliant
        if refused:
            return f"{self.name} wants nothing to do with it!"
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
        # applyItemNoObedience: a DiminishingReturns toy scales by 1 - interest/5
        # (canon quirk: at FULL boredom the scale is skipped and the toy lands at
        # full strength again); every item use bores the pet a step further
        mod = 1.0
        if not is_food:
            if e.get("diminishing"):
                m = 1.0 - self.item_interest / MAX_ITEM_INTEREST
                if 0.0 < m < mod:
                    mod = m
            self.item_interest = _clamp(self.item_interest + e.get("interest_change", 0),
                                        0, MAX_ITEM_INTEREST)

        def _sc(v):
            return math.ceil(v * mod) if v > 0 else int(round(v * mod))
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + _sc(e["hunger"]), 0, 4)
            self.calories = CALORIE_LIMIT               # food refills the calorie buffer
        # applyConsumable: the consumable's mood is shaped by personality tags
        self._set_mood(self.mood + _sc(e["mood"]) + _sc(self._personality_mood(e)))
        self._set_enthusiasm(self.enthusiasm + _sc(e.get("enthusiasm", 0)))
        self.weight = max(1, self.weight + e["weight"])
        if e["energy"]:
            self._set_energy(self.energy + _sc(e["energy"]))
        if e["strength"]:
            self.strength = _clamp(self.strength + _sc(e["strength"]), 0, 4)
        self.obedience += e["obedience"]                 # canon: obedience is UNscaled
        self.vaccine = max(0, self.vaccine + _sc(e["vaccine"]))
        self.data_power = max(0, self.data_power + _sc(e["data"]))
        self.virus = max(0, self.virus + _sc(e["virus"]))
        if e.get("vitamin"):
            self.feed_vitamin()                          # guards against injury worsening
        if e["unfatigue"]:
            self.fatigue_length = 0.0                    # DVPet Fatigued flag only clears
            # fatigue-length; energy stays driven by the item's Energy column, not a full refill
        if e["undepressed"]:
            self._set_mood(max(self.mood, NEW_UNDEPRESSED_MOOD))  # leave depression
        if self.sick and e.get("cure_lapse"):
            self.sick_length = max(0.0, self.sick_length + e["cure_lapse"] * SICK_LAPSE_MIN)
            self.sick = self.sick_length > 0             # applyConsumable CureLapseChange
        if self.is_injured() and e.get("heal_lapse"):
            self.inj_length = max(0.0, self.inj_length + e["heal_lapse"] * INJ_LAPSE_MIN)
        if self.is_fatigued() and e.get("fatigue_lapse_change"):
            self.fatigue_length = max(0.0, self.fatigue_length + e["fatigue_lapse_change"] * 60.0)
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
            self._fall_asleep()                          # DVPet item Sleep flag: a REAL sleep
                                                         # (limits sized, lights latch reset)
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
        if self.is_freezing():
            return "freezing"
        if self.is_overheating():
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
