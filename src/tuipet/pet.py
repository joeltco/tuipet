"""DVPet game model: a single virtual pet, its stats, and care logic."""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field as _dcf
from . import data
from . import shop
from . import egg as egg_mod
from . import evolution
from . import lines as lines_mod
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
OBEDIENCE_REFUSAL_CAP = 100         # ObedienceRefusalCap (the refusal-ROLL bound only)
OBEDIENCE_MOOD_MOD = 15.0           # ObedienceMoodModCoefficient
OBEDIENCE_TIME_MOD = 10.0           # ObedienceTimeModCoefficient
# setObedience (obedience audit 2026-07-06): the stat itself caps at MaxObedience
# 150, and EVERY change is nudged once AGAINST the disposition (value -=
# disposition x 1: a sunny pet takes each change a point lower, a sour one a
# point higher) -- the mirror image of setMood's nudge
MAX_OBEDIENCE = 150                 # MaxObedience
OBEDIENCE_DISPO_COEF = 1            # ObedienceChangeDispositionCoefficient (SUBTRACTED)
# obedienceLapse: discipline FADES while awake -- dec 2 on a disposition-shaded
# cadence (sunny 180 / neutral 120 / sour 60 game-min), and each dec event also
# bills the mess (ObedienceChangeFilthScale x piles).  MinObedienceAsleep 150
# == MaxObedience: the lapse can never run asleep (shipped-config quirk).
OBEDIENCE_LAPSE_MIN = {0: 120.0, 1: 180.0, -1: 60.0}   # ObedienceLapseMin[/High/Low]
OBEDIENCE_LAPSE_DEC = 2             # ObedienceLapseDec (same for all dispositions)
OBEDIENCE_FILTH_SCALE = -1          # ObedienceChangeFilthScale
# checkRefusedOff: an UNSCOLDED refusal expires on its own -- the pet got away
# with it (mood up) and hardens a little less (obedience down)
REFUSED_OFF_MIN = 10.0              # RefusedOffMin (game-min on tuipet's cadence scale)
REFUSED_OFF_MOOD_INC = 1            # RefusedOffMoodInc
REFUSED_OFF_OBED_DEC = 1            # RefusedOffObedienceDec
OBEDIENCE_CHANGE_INTOL_FORCED = -3  # ObedienceChangeIntolerantForced (complied + intolerant meal)
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
REFUSE_INTEREST_MOD = -15.0         # RefuseInterestModCoefficient (a bored pet refuses toys)
WEAK_CONSUMABLE_COEF = 0.1          # WeakConsumableCoefficient: a COMPLIANT pet takes items
#                                     grudgingly (Inherit/Recover exempt, like applyItem)
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
PERFECT_WINS_LIMIT = 1              # PerfectWinsLimit is 5 in canon -- scaled x5 for the
#                                     compressed clock EXACTLY like TRAIN_POWER_PER_HIT:
#                                     a real device stage lasts DAYS; 50 drill wins to
#                                     reach Champion-foe HP parity (foes 15-25 vs the
#                                     starting 5) was unreachable in a ~2h tuipet stage,
#                                     so pets fought at 5 HP forever, lost constantly,
#                                     and the losses fed the misbehaving spiral
#                                     (audit 2026-07-05).  Every HP-drill win = +1 HP,
#                                     still capped by the age ladder (max_health()).
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
# DVPet DigiMemory / inheritance (PhysicalState.setNewDigimemory / getDigimemory,
# item 32 anim Inherit; config.csv DigimemoryAttributeCoefficient / LifeInc).  The
# departed etches its attack powers -- scaled by the care bonus it died holding --
# into the Digimemory; the HEIR uses the item to add Va/D/Vi and lifespan.
DIGIMEMORY_ATTR_COEF = 0.01         # DigimemoryAttributeCoefficient
DIGIMEMORY_LIFE_INC = 60.0          # DigimemoryLifeIncCoefficient 3600 real-sec (1h) -> the
#                                     game-min scale, exactly like BonusEvolutionLife above
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
LIGHTS_ON_AWAKE_STALL = 50          # LightsOnAwakeLapseUnchangedChance: lit rest is poor rest
CHANGE_NAP_TO_SLEEP = 240           # ChangeNapToSleepMinutes: a held nap becomes the night
NAP_TO_SLEEP_RESTLESS = 10          # ChangeNapToSleepMinutesRestlessCoefficient
NAP_ENERGY_INC = 30                 # NapEnergyInc (checkNapEnergy's accumulator threshold)
NEGATIVE_ENERGY_GAIN = 6            # NegativeEnergyGain: a DRAINED pet recovers faster
SLEEP_MIN_HUNGER_DECAY = 3          # SleepMinHungerDecay: asleep the stomach floors here
SLEEP_MIN_TO_GAIN = 60.0            # SleepMinutesToEnergyGain (uniform across the corpus)
SICK_TEMP_DEC_CHANCE = 100          # SickTempDecChance (the fever/chills roll bound)
SICK_TEMP_SWING = 30                # SickTempInc / SickTempDec
AWAKE_RESTLESS_COEF = 1             # AwakeLapseRestlessCoefficient
BONUS_SLEEP_ENERGY = 2              # BonusSleepEnergy (a restless skip still rests)
NAP_ENERGY_MIN = 1                  # NapEnergyMin
SLEEP_NOT_NAP_MIN = 90              # SleepNotNapMinutes (- restless*60): lights-out near
SLEEP_NOT_NAP_RESTLESS = 60         #   bedtime starts REAL sleep instead of a nap
ON_NAP_MOOD_INC = 10                # OnNapMoodInc
# toNapSleepLapse -> calcToSleepNapLapse (sleep audit 2026-07-06): the pet sits
# in the DARK a while before nodding off -- energetic ~40 game-min, drained 20,
# +-restless, and a well-drilled pet (obedience >= 75) drops the extra +1.
# This delay is canon's real anti-farm for the +10 nap mood.
TO_NAP_HIGH_ENERGY = 40             # ToNapHighEnergyFactor (energy > max/2)
TO_NAP_LOW_ENERGY = 20              # ToNapLowEnergyFactor
TO_NAP_OBEDIENCE_FACTOR = 75        # ToNapObedienceFactor
TO_SLEEP_NAP_RESTLESS = 1           # ToSleepNapLapseRestlessCoefficient
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
# battleEnd's tail (battle-math audit 2026-07-06)
BATTLE_WON_WORSE_SICK = 10              # BattleWonWorseSickChance (winning hurt still costs)
BATTLE_LOST_WORSE_SICK = 20             # BattleLostWorseSickChance
BATTLE_LOW_HEALTH_COEF = 2              # BattleLowHealthCoefficient (limping = at/below half HP)
BATTLE_HIGH_HP_ENERGY = 1               # BattleHighHealthEnergyDec
BATTLE_LOW_HP_ENERGY = 2                # BattleLowHealthEnergyDec (a hard fight drains double)
BATTLE_CAL_HIGH = 1                     # BattleCalorieDecHighHealth
BATTLE_CAL_LOW = 2                      # BattleCalorieDecLowHealth
BATTLE_LOST_MISSED_DAY = 1              # BattleLostMissedDayChange
SURR_DECLINED_LOST_OBED = 10            # SurrenderRequestDeclinedLostBattleObedienceDec --
#                                         it BEGGED to quit, you refused, it lost: obedience
#                                         is SET to 10 (absolute), not decremented
ENEMY_SICK_CHANCE = 50                  # EnemySickChance: fighting a SICK opponent (PvP
#                                         contagion -- the partner's real state ships) risks
#                                         catching it at battle's end, win or lose
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
RANK_CHANGE_SICK = 5                    # RankChangeSick: a bad dose sours the taste...
RANK_CHANGE_SICK_FORCED = 5             # RankChangeSickForced: ...more so when force-fed
RANK_PREF_INC = 2                       # config RankChangeSpeciesPreferenceInc (species like/dislike bias)
RANK_DISLIKED = -2                      # config RankChangeDisliked
RANK_AFTER_FAV = 20                     # config RankChangeAfterFav (decay other ranks toward 0)
# the ATTRIBUTE taste ledger + the rank-event deltas (taste/rank audit
# 2026-07-06 -- the standing "rank system unported" deferral closed).  Young
# pets form tastes faster: the per-event base is stage-scaled.
RANK_CHANGE_ATTR = 1                    # RankChangeAttribute (per drill)
RANK_STAGE_INC = {"Fresh": 3, "InTraining": 2, "Rookie": 1}   # RankChangeStage{1,2,3}Inc
RANK_TRAIN_FORCED = 2                   # RankChangeTrainForced (forced training sours it)
RANK_INJ_BATTLE_WON = 1                 # RankChangeInjuryBattleWon (hurt by that attribute...)
RANK_INJ_BATTLE_LOST = 5                # RankChangeInjuryBattleLost (...and beaten by it)
RANK_BAD_FOOD_FORCED = 3                # RankChangeBadFoodForced (forced the disliked meal)
RANK_FOOD_FORCED = 1                    # RankChangeFoodForced (any forced meal grates)
RANK_INTOL_FORCED = 5                   # RankChangeIntolerantForced
RANK_SICK_FORCED = 5                    # RankChangeSickForced (a forced meal that sickened)
RANK_TIME_SICK = 5                      # RankChangeSick/Injury: misery sours the HOUR too
NONE_TRAIN_MOOD_RANK = -1               # NoneTrainingAttributeMoodRankChange (the HP drill)
# the personality TRACKER (randPersonalityTraits seeds / personalityTracker /
# randOnChampion): childhood care -- energy kept high, weight kept healthy,
# mood kept happy -- is tallied through Fresh/InTraining/Rookie and RE-ROLLS
# the temperament at the Champion evolution (threshold +-42)
PCHAMP_RANK = 42                        # PersonalityChampRandom{High,Low}*Rank
PCHAMP_HI_ENERGY = 0.75                 # PersonalityChampRandomHighEnergyCoefficient
PCHAMP_LO_ENERGY = 0.25                 # PersonalityChampRandomLowEnergyCoefficient
EXERCISE_DISLIKED_ATTR_ENTH = -3        # ExerciseDislikedAttributeEnthusiasmChange
ENTH_DISLIKE_FORCED = -1                # EnthusiasmChangeDislikeForced
FAV_FOOD_MOOD = 10                      # config FavFoodMoodInc
FOOD_MOOD = 2                           # config FoodMoodInc (neutral food)
FAV_FOOD_ENTH = 1                       # config FavFoodEnthusiasmInc
DISLIKED_FOOD_OBEDIENCE = -1            # config DislikedFoodObedienceChange
INTOL_FOOD_SICK_CHANCE = 50            # config IntolerantFoodSickChance (per roll, x2 rolls)

# DVPet poop / filth (config.csv, PhysicalState.poop / poopWaitMoodCheck).  A bowel
# movement bumps mood, sheds a little weight and drops a pile of a size set by the
# Digimon's base weight; an uncleaned mess then nags the mood until it is cleaned.
POOP_MOOD_INC = 10                      # PoopMoodInc (relief)
CLEAN_MOOD_INC = 6                      # CleanMoodInc
CLEAN_OBED_INC = {0: 1, 1: 2, -1: 0}    # CleanObedienceInc / HighDisposition / LowDisposition
POOP_WEIGHT_DEC_COEF = 0.1             # PoopWeightDecCoefficient
POOP_WEIGHT_LIMIT = 4                   # PoopWeightLimit (max weight lost per poop)
# setWeight (weight audit 2026-07-06): the body clamps HARD at baseWeight +-
# round(baseWeight x WeightLimitMultiple) -- wider than the +-0.5 Over/Under
# tier band -- and hitting either wall stings (weightLimitPenalty: mood -10,
# obedience -0 at difficulty 0, spirit -1)
WEIGHT_LIMIT_MULTIPLE = 0.75            # WeightLimitMultiple
WEIGHT_LIMIT_MOOD_PENALTY = 10          # WeightLimitMoodPenalty
WEIGHT_LIMIT_OBED_PENALTY = 0           # WeightLimitObediencePenalty (difficulty 0: no-op)
WEIGHT_LIMIT_ENTH_PENALTY = 1           # WeightLimitEnthusiasmPenalty
ABOVE_MAX_CAL_BM = 1                    # AboveMaxCaloriesBMGaugeChange: calorie overflow
#                                         while rising hastens the poop (setCalories)
# DVPet toilet training (config col 0): ONE toilet use while InTraining teaches
# it; from Rookie on (obedience >= 50) the pet takes ITSELF to a stocked toilet
# at poop time -- no filth, ever (doPoop's SelfToilet branch).
MIN_TOILET_USES_TO_TRAIN = 1            # MinToiletUsesToTrain
TOILET_TRAINED_OBED_MIN = 50            # ToiletTrainedObedienceMin
STAGE_CAN_TOILET_TRAIN = ("InTraining",)                            # StageCanToiletTrain
STAGE_CAN_AUTO_TOILET = ("Rookie", "Champion", "Ultimate", "Mega")  # StageCanAutoToilet
TOILET_URGENT_FRAC = 0.8                # tuipet: the manual-use / poop-dance urgency window
#                                         (canon gates on a FULL gauge; tuipet's gauge fires
#                                         the poop the moment it fills, so the window leads)
POOP_INC_WEIGHT_FACTOR = 40            # PoopIncWeightFactor -> size 3 at/above
POOP_INC_WEIGHT_FACTOR_SMALL = 15      # PoopIncWeightFactorSmall -> size 1 at/below
POOP_WAIT_MOOD = -1                     # PoopWaitMoodChange (the HELD gauge nags)
LARGE_POOP_WAIT_MOOD = -2               # LargePoopWaitMoodChange (a desperate gauge nags more)
FILTH_MOOD_DEC_MIN = 300.0              # FilthMoodDecMin 5 game-min: species filth_mood x piles
FILTH_SICK_BOUND = 200                  # FilthSickChanceBound 12000 real-min -> /60 game scale
FILTH_SICK_CHANCE = 1                   # FilthSickChance (x piles, per game-min)
FILTH_WORSE_CHANCE = 20                 # FilthWorseSickChance (x piles, already sick)
BAD_WEIGHT_MOOD_DEC = 2                 # BadWeightMoodLapseDec (per lapse off Healthy)
VERY_NEUTRAL_MOOD_DEC = 5               # VeryNeutralMoodLapseDec (neutral [5,150) drains faster)
DEPRESSED_LAPSE_MIN = 59.0              # DepressedLapseMin
DEPRESSED_CHANCE = 1000                 # DepressedChance (the roll bound)
DEPRESSED_EXIT_NEG = 100                # DepressedToUnhappyNegativeMoodChance
DEPRESSED_EXIT_POS = 500                # DepressedToUnhappyPositiveMoodChance
UNDEPRESSED_OBED_INC = 33               # UndepressedObedienceIncPositiveMood
DEPRESSED_MOOD_CHANGE = 50              # DepressedMoodChange (each interval while depressed)
DEPRESSED_OBED_CHANGE = -5              # DepressedObedienceChange (each interval)
DEPRESSED_ENTH_CHANGE = -1              # DepressedEnthusiasmChange
TO_DEPRESSED_ROLL_NEG = 10              # negativeMoodDepressedChance (mood <= -250)
TO_DEPRESSED_ROLL_NORM = 1              # normalMoodDepressedChance
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
DISPOSE_LEFTOVERS_MIN = 0.5             # DisposeLeftoversMinModifier: at/below, Munching drops the rest
OVEREAT_LIMIT = 5                       # OvereatLimit: a glutton may fill one heart past full
CALORIE_LIMIT = 4                       # CalorieLimit (buffer half-range)
DP_MAX = 4                              # Pen20 DP meter: full (4) required to jogress;
DP_SLEEP_MIN = 45.0                     # +1 per 45 game-min asleep (3h sleep = a full refill)
FOOD_WEIGHT_CHANGE = 1                  # FoodWeightChange: calories rising while positive fattens
DIRTY_EATING_MOOD_DEC = 10              # DirtyEatingMoodDec (a meal amid the filth)
DIRTY_EATING_WORSE_CHANCE = 16          # DirtyEatingWorseSickChance (% per pile)
DIRTY_EATING_SICK_CHANCE = 8            # DirtyEatingSickChance (% per pile)
LESS_HUNGER_CHANCE = 9                  # LessHungerChance: the glutton decay-jitter odds
# sleep (DVPet setAsleep / lightsCall / the morning wake roll)
# careBonusOnReset (config col 0): the departed's whole-life REPORT CARD --
# graded at the next generation's start; the result SEEDS the new egg's bonus.
# (The Digimemory etch runs FIRST and spends the bonus, so an etched life
# grades from zero + the card; an unetched one keeps its leftover credit.)
BONUS_INC_OBEDIENCE = 75                # BonusIncObedience
BONUS_DEC_OBEDIENCE = 50                # BonusDecObedience
BONUS_INC_WIN_RATE = 90                 # BonusIncWinRate (lifetime %)
BONUS_STAGE = {                         # stage base / attribute bar / battles bar
    "Champion": (0, 175, 30),           # (+1 extra when NOT a Failed form)
    "Ultimate": (2, 225, 50),
    "Mega": (3, 300, 75)}
MISTAKE_HAPPY_MOOD = 100                # MistakeHappyMoodChange: a Happy pet DROPS TO 100
MISTAKE_MOOD_DEC = 50                   # MistakeMoodDec: everyone else loses 50
LIGHTS_MISTAKE_POSTPONE = -60.0         # AfterMistakeMinutesPostponed: the NEXT lit mistake
#                                         lands 120 lit-minutes on (it REPEATS, not once/night)
LIGHTS_MISTAKE_OBED = -1                # LightsOnMistakeObedienceChange (once per night)
HUNGER_MISTAKE_OBED = 1                 # HungerMistakeObedienceChange (canon: +1!)
HUNGER_MISTAKE_OBED_GLUTTON = -1        # ...ChangeGlutton
LIGHTS_MISTAKE_SEC = 60.0               # MinutesToMistakeLights(60) as ~12% of the sleep,
#                                         scaled to tuipet's ~6-min night -- one mistake/night
MORNING_MOOD_CHANCE = 5                 # MorningMoodChance: 1/5 bad, 1/5 terrible-if-happy, 1/5 good
BAD_MORNING_MOOD = {"Happy": -150, "Neutral": -100, "Unhappy": -10, "Depressed": -10}
GOOD_MORNING_MOOD = {"Happy": 50, "Neutral": 100, "Unhappy": 150, "Depressed": 150}
WORST_MORNING_MOOD = -10                # WorstMorningMood (TerribleMorning sets mood TO this)
NAP_WAKE_MOOD_DEC = 20                  # NapWakeMoodDec: a NAP wake swings +-20 on 2 of the 5 rolls
# disturb (setAsleep(false) runs the wake roll after these; canon disturb())
DISTURB_MOOD_DEC = {1: 0, 0: 10, -1: 20}     # DisturbMoodDec{Restless,,NotRestless}: a restless
#                                              pet WANTED up (0); a mellow one hates it (20)
DISTURB_WORSE_SICK_CHANCE = 50          # DisturbWorseSickChance % (an already-sick sleeper worsens)
DISTURB_SICK_CHANCE = 25                # DisturbSickChance % (vs SickChance bound 100)
DISTURB_LIMIT_CHECK_SICK = 5            # DisturbLimitCheckSick: the sick risk from the 5th disturb on
STARVE_WEIGHT_DEC = 1                   # ActivityWeightChange: starving sheds weight per lapse
HUNGER_MISTAKE_LIFE_DEC = 360.0         # MistakeHungerLifeDec 21600 real-sec on the /60 game
#                                         scale (x TOTAL mistakes per event; the old 3600 was a
#                                         bespoke rescale -- the BadMed audit's bug class)
SICK_LIFE_DEC = 180.0                   # SickLifeDec 10800: every illness costs 3 real-hours
INJURY_LIFE_DEC = 180.0                 # InjuryLifeDec 10800
WORSE_MALADY_LIFE_DEC = 180.0           # WorseSick/WorseInjuryLifeDec 10800 (each worsening)
FATIGUE_LIFE_DEC = 360.0                # FatigueLifeDec 21600
GERIATRIC_FATIGUE_LIFE_DEC = 60.0       # GeriatricFatigueLifeDec 3600 (an old body pays extra)
X_LIFE_DEC = 1440.0                     # XAntibodyLifeDec 86400: the X-Program's price in LIFE
X_LIFE_DEC_BOUND = 7                    # XAntibodyLifeDecModifierBound (86400/nextInt(7); 0 = free)
# xProgramSurvivalChance 1/1000 (death/rebirth audit 2026-07-06): the sample
# is RUSSIAN ROULETTE for an UNMARKED pet -- 999 in 1000 it dies outright,
# and that death cannot be mash-revived (savedFromDeath = 127, verbatim).
# A pet already carrying any antibody state is safe.
X_SURVIVAL_TARGET = 1                   # XProgramSurvivalChanceTarget
X_SURVIVAL_BOUND = 1000                 # XProgramSurvivalChanceBound
X_SAVE_BLOCK = 127                      # the canon revive-block sentinel
INSTANT_DEATH_GRACE = 60.0              # InstantDeathGracePeriod 3600: a burn cannot kill in
#                                         under the grace -- setTotalLifespan's clamp, verbatim
MIN_ENERGY_LIFE_PENALTY = 60.0          # MinEnergyLifePenalty 3600: bottoming out at the
#                                         -maxEnergy floor burns life (setEnergy, per hit)
#                                         scaled to tuipet's ~84h: ~1.2% of life x total mistakes
# setEnergy: a drop INTO the red bills mood/obedience scaled by the depth
# (dec - newEnergy, i.e. 10 + |new| / 1 + |new|) and fatigues an uninjured pet
NEGATIVE_ENERGY_MOOD_DEC = 10           # NegativeEnergyMoodDec (base; depth added)
NEGATIVE_ENERGY_OBEDIENCE_DEC = 1       # NegativeEnergyObedienceDec (base; depth added)
BONUS_ATTRIBUTE_POWER = 1               # BonusAttributePower: a Happy pet's standard gain in its
#                                         favoured attribute lands doubled (set*Power; the bonus
#                                         rides only the battle incStats + training award paths --
#                                         the only canon callers of the bonus-carrying setters)
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
PRAISE_FAIL_MOOD_PENALTY = 10            # PraiseFailMoodPenalty (a good deed unpraised)
PRAISE_FAIL_OBED_INC = 3                 # PraiseFailObedienceInc...
PRAISE_FAIL_OBED_DISPO_COEF = 1          # ...IncDispositionCoefficient (shaded by temperament)
SCOLD_FAIL_MOOD_INC = 10                 # ScoldFailMoodInc (it got away with it)
SCOLD_FAIL_OBED_PENALTY = 10             # ScoldFailObediencePenalty
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
# the CALL itself (mood re-audit 2026-07-06): the tantrum is a care light with
# three exits -- the scold it demands (+2 obedience), any OTHER care placates it
# (obedience -10, a smug mood +5: it got its way), or it times out ignored
# (mood -25 and a missed day)
DISCIPLINE_CALL_SCOLD_OBED_INC = 2       # DisciplineCallScoldObedienceInc (the right answer)
DISCIPLINE_CALL_OBED_DEC = 10            # DisciplineCallObedienceDec (placated unscolded)
DISCIPLINE_CALL_MOOD_INC = 5             # DisciplineCallMoodInc (placated: it won)
DISCIPLINE_CALL_MOOD_PENALTY = 25        # DisciplineCallMoodPenalty (ignored)
DISCIPLINE_CALL_FAIL_MISSED_DAY = 1      # DisciplineCallFailMissedDayChange
MINUTES_TO_DISCIPLINE_PENALTY = 180.0    # _minutesToDisciplinePenalty 3 game-min

# DVPet AI Assistant (config.csv AutoCare*, PhysicalState.setAutoCare / doAutoCare /
# checkAutoCare / processAutoCarePrice).  A hired helper keeps house while you're
# away: awake it cleans filth, then feeds a starving pet (food 44), then a drained
# one (food 43); asleep it cleans, then dims a lit room (unless the Futon already
# holds the night).  Every visit bills the stage price AND costs bond -- mood -10,
# obedience -1, enthusiasm -1: hired care is not YOUR care.  An hourly retainer
# (or a visit) it cannot cover puts the assistant off duty.
AUTO_CARE_VISIT_PRICE = {"Egg": 50, "Fresh": 50, "InTraining": 100, "Rookie": 200,
                         "Champion": 400, "Ultimate": 800, "Mega": 1600}   # AutoCareStage*Price
AUTO_CARE_HOUR_PRICE = {"Egg": 0, "Fresh": 0, "InTraining": 0, "Rookie": 100,
                        "Champion": 100, "Ultimate": 100, "Mega": 100}     # AutoCareStage*HourPrice
AUTO_CARE_HUNGER_FOOD = 44               # AutoCareHungerFoodID (the AI Food Pill)
AUTO_CARE_STRENGTH_FOOD = 43             # AutoCareStrengthFoodID (the AI Supplement)
AUTO_CARE_MOOD = -10                     # _autoCareMoodChange
AUTO_CARE_OBEDIENCE = -1                 # _autoCareObedienceChange
AUTO_CARE_ENTHUSIASM = -1                # _autoCareEnthusiasmChange
AUTO_CARE_PAYMENT_MIN = 60               # _autoCarePaymentMin: the retainer bills hourly
AUTO_CARE_VISIT_SPACING = 3              # game-min between visits (DVPet spaces them via the
#                                          ASSISTANT_ANIM guard -- one helper on screen at a time)

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
# the WEAK tables (taste/rank audit 2026-07-06): drilling the species'
# ATTRIBUTE AVERSION (a fixed seed -- the aversion never drifts) hurts more
INJ_WEAK_EXERCISE = {"bad_nv": 20, "good_nv": 5, "good_v": 1, "bad_v": 10}   # WeakInjury*
WORSE_INJ_WEAK = {"bad_nv": 15, "good_nv": 5, "good_v": 1, "bad_v": 5}       # WorseWeakInjury*
# FRESH injuries (sickness/injury audit 2026-07-06): the same weight x vitamin
# matrix vs a 1000 bound, plus a shared additive term -- geriatric/bad-age,
# fatigue x coefficient, negative energy x coefficient, habitat compatibility
# (+-1/axis) -- and battles pad +50 on a LOSS.  The old ports ("overweight ->
# 50%", "loss -> 30%") were paraphrases; canon's baseline is ~0.1-1%.
INJ_CHANCE = 1000                        # InjuryChance (exercise bound)
INJ_EXERCISE = {"bad_nv": 10, "good_nv": 1, "good_v": 0, "bad_v": 5}   # Injury*
INJ_GERIATRIC = 10                       # InjuryGeriatricFactor
INJ_FATIGUE_COEF = 10                    # InjuryFatigueCoefficient (x FatigueMod)
INJ_NEG_ENERGY_COEF = 0.5                # InjuryNegativeEnergyCoefficient
BATTLE_INJ_CHANCE = 1000                 # BattleInjuryChance
INJ_BATTLE = {"bad_nv": 100, "good_nv": 3, "good_v": 0, "bad_v": 25}   # BattleInjury*
BATTLE_INJ_BAD_AGE = 10                  # BattleInjuryBadAgeFactor (elder OR baby)
BATTLE_INJ_LOSS = 50                     # BattleInjuryWonFactor (added on a LOSS)
BATTLE_INJ_FATIGUE_COEF = 10             # BattleInjuryFatigueCoefficient
BATTLE_INJ_NEG_ENERGY_COEF = 1.0         # BattleInjuryNegativeEnergyCoefficient
FATIGUE_MOD = 10                         # FatigueMod
WORSE_INJ_GERIATRIC = 10                 # WorseInjuryGeriatricFactor
WORSE_BATTLE_INJ_BAD_AGE = 10            # WorseBattleInjuryBadAgeFactor
WORSE_BATTLE_INJ_LOSS = 5                # WorseBattleInjuryWonFactor (on a LOSS)
WORSE_INJ_NEG_ENERGY_COEF = 1.0          # WorseInjuryNegativeEnergyCoefficient (battle same)
INJURY_ENERGY_DEC = 1                    # InjuryEnergyDec (a fresh injury saps a bar)
OBED_INJ_FORCED = -5                     # ObedienceChangeInjuryForced (complied + hurt)
OBED_INJ_BATTLE_WON = -2                 # ObedienceChangeInjuryBattleWonForced
OBED_INJ_BATTLE_LOST = -5                # ObedienceChangeInjuryBattleLostForced
# checkSick/checkWorseSick BOUNDS: the home's compatibility shifts the sick
# bound (+-5/axis; a compatible home = safer), old age thins both by 25, and
# fatigue pads a worse-sick TARGET by FatigueMod
SICK_CHANCE_BOUND = 100                  # SickChance
SICK_COMPAT_CHANGE = 5                   # Compatible*SickChanceChange
SICK_GERIATRIC_FACTOR = 25               # SickGeriatricFactor
WORSE_SICK_BOUND = 100                   # WorseSickChance
WORSE_SICK_GERIATRIC = 25                # WorseSickGeriatricFactor
INTOL_WORSE_SICK_CHANCE = 50             # IntolerantFoodWorseSickChance
# incMistake's sickness risks (flagged in the mood arc, closed here): filth
# rolls per pile with a misery pad (|mood| x 0.1 when Unhappy/Depressed), and
# ANY mistake while fatigued adds a 1/1 whisper.  The 50/50 MistakeFilth*
# pair keys on poopCall -- PROVABLY DEAD in the shipped config (the filth
# array holds 6, MistakeFilthLimit is 7) -- kept as documentation only.
MISTAKE_FILTH_WORSE = 50                 # MistakeFilthWorseSickChance (dead: poopCall)
MISTAKE_FILTH_SICK = 50                  # MistakeFilthSickChance (dead: poopCall)
MISTAKE_LOW_FILTH_WORSE = 5              # MistakeLowFilthWorseSickChance (x piles)
MISTAKE_LOW_FILTH_SICK = 1               # MistakeLowFilthSickChance (x piles)
MISTAKE_FILTH_MOOD_COEF = 0.1            # MistakeFilthSickChanceMoodCoefficient
ANY_MISTAKE_FATIGUED = 1                 # AnyMistakeWhileFatigued{,Worse}SickChance
SICK_LAPSE_PENALTY_BM = 48               # SickLapsePenaltyBM: an awake sick pet's gauge races
SICK_NUTRITION_CHANGE = -1               # SickNutritionChange (per awake sick lapse)
WORSE_MALADY_MOOD_DEC = -35              # worseMaladyMoodDec
WORSE_MALADY_OBED_DEC = -10              # worseMaladyObedienceDec
WORSE_INJ_ENERGY_DEC = 1                 # WorseInjuryEnergyDec
WORSE_INJ_ENTH_CHANGE = -1               # WorseInjuryEnthusiasmChange
VITAMIN_HOURS = 60                       # VitaminHours (game-min of injury-worsening protection)
CURED_MOOD_BONUS = 75                    # CuredMoodBonus (divided by Max{Sick,Inj}Length per treatment)
CURED_OBED_BONUS = 25                    # CuredObedienceBonus
BAD_MED_LIFE_DEC = 60.0                  # BadMedLifeDec 3600 real-sec (1h) -> the game-min
#                                          scale, like BonusEvolutionLife/DigimemoryLifeInc
#                                          (the old 3600 game-sec was 60x too harsh)
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
    depressed: bool = False         # DVPet _currentMood==Depressed: a sticky STATE entered and
    #                                 left by checkDepressed's rolls, not a mood threshold
    auto_care: bool = False         # DVPet _autoCare: the hired AI Assistant is on duty
    assistant_num: int = -1         # DVPet _assistantID: WHICH Digimon answered the contract
    care_mistakes: int = 0
    dna_owned: dict = _dcf(default_factory=lambda: {f: 0 for f in data.DNA_FIELDS})    # banked
    dna_applied: dict = _dcf(default_factory=lambda: {f: 0 for f in data.DNA_FIELDS})  # charged
    food_ranks: dict = _dcf(default_factory=lambda: {c: 0 for c in data.FOOD_CATEGORIES})
    # the ATTRIBUTE taste ledger (taste/rank audit 2026-07-06): drills warm the
    # pet to an attribute, injuries and forced training sour it; a rank at
    # +-RankLimit becomes the emergent favourite/disliked ("" = none yet)
    attr_ranks: dict = _dcf(default_factory=lambda: {"Vaccine": 0, "Data": 0, "Virus": 0})
    favorite_attr: str = ""
    disliked_attr: str = ""
    # the personality tracker (childhood care -> the Champion temperament)
    energy_rank: int = 0
    weight_rank: int = 0
    mood_rank: int = 0
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
    discipline_call: bool = False   # DVPet _disciplineCall: a tantrum begging to be disciplined
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
    # ---- evolution lines (LINES_SPEC.md): the legible bracket engine ----
    line_id: str = ""               # hatched-from line; "" = corpus fuzzy engine
    stage_trainings: int = 0        # drills attempted this stage (every attempt counts; Pen20)
    stage_battles: int = 0          # battles fought this stage
    battle_log: list = _dcf(default_factory=list)   # last-15 results 1/0 (persists across evolution; Pen20)
    mega_kills: int = 0             # lifetime Ultimate/Mega-class foes beaten (DMX KO6 gate)
    dp: int = 0                     # Pen20 DP meter 0..4: full to jogress; protein +1, 3h sleep refills
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
    digimemory: dict = _dcf(default_factory=dict)   # held inheritance data (item 32 payload)
    birthday_note: str = ""         # transient: the HUD's birthday announcement
    saved_from_death: int = 0       # _savedFromDeath: each rescue raises the next bar
    # long-horizon clocks (persisted: losing these on reload forgave starvation,
    # wiped the bowel gauge and re-armed once-per-night mistakes -- audit 2026-07)
    _starve_t: float = 0.0          # the 12h starvation death clock
    _poop_t: float = 0.0            # the bowel gauge (written as durable state by meals)
    toilet_trained: int = 0         # _toiletTrained: InTraining-stage toilet uses (1 trains)
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
    adv_loc: int = 0          # transport ARRIVAL step (canon warps land AT a place: the
    #                           zone's first town / the next boss, not step 0) -- the next
    #                           Adventure starts here, then it clears (audit 2026-07-04)
    egg_type: int = 0
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    death_cause: str = ""           # what took it (memorial epitaph, audit 2026-07-05)
    world_seconds: float = 0.0
    temp: float = 50.0
    day_temp: float = 50.0
    weather: str = "Clear"
    field: str = ""
    element: str = ""
    habitat: int = 2                # the CURRENT habitat (canon _currentHabitat --
    #                                 it follows the zone background on the road)
    home_habitat: int = -1          # canon _homeHabitat: the OWNED home the pet
    #                                 returns to after an adventure (-1 = backfill
    #                                 from `habitat` on first use; habitat audit
    #                                 2026-07-06)
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

    # seconds in each stage before it is eligible to evolve (accelerated time).
    # LINES_SPEC §5: the canon curve — babies fly, adults stretch (DM20 timing
    # mapped to game-hours: 6h baby, Child = one full 24h day, 36h, 48h).
    EGG_DURATION = 60      # seconds an egg incubates before hatching (~1 game-hour)

    STAGE_DURATION = {                       # seconds in a stage before it may evolve
        "Fresh": 180, "InTraining": 360, "Rookie": 1440,
        "Champion": 2160, "Ultimate": 2880, "Mega": 9e9,
    }
    LATE_STAGE_WINDOW = 2880.0   # Pen20: the Stage V/VI "evolution window" for the
    #                              5-mistake death rule (Ultimate's own duration)

    @classmethod
    def new_egg(cls, generation=1, egg_type=None):
        if egg_type is None:
            egg_type = random.randrange(egg_mod.count())
        pet = cls(num=-1, name="Digitama", stage="Egg",
                  egg_type=egg_type, generation=generation)
        pet.mood = EGG_MOOD                     # Evolution.egg: setMood(EggMood 100)
        if generation > 1:
            # careBonusOnReset (death/rebirth audit 2026-07-06): the BONUS
            # carries across generations, adjusted by the ended life's care --
            # canon's resetToEgg never zeroes it
            from . import persistence as _persist
            pet.evol_bonus = _persist.prev_gen_bonus()
        # a fresh game dawns at 8:00 -- world_seconds 0 is MIDNIGHT, inside every
        # bedtime window, and a hatchling born asleep is a rotten first minute
        pet.world_seconds = 8 * 60.0
        pet._apply_egg_habitat()
        if generation <= 1:
            # canon items.csv StartingUses: the device begins with a stocked
            # home Toilet (100 flushes) -- granted once, on the first generation
            pet.inventory["i:82"] = 100
        return pet

    def _hatch_into_fresh(self):
        _, by_num = data.load_sprites()
        target = egg_mod.hatch_target(self.egg_type)
        if target is None or target not in by_num or data.is_placeholder(target):
            fresh = [n for n, r in by_num.items() if r["stage"] == "Fresh" and not data.is_placeholder(n)]
            target = random.choice(fresh)
        # arc 5: every hatch canonicalizes to a line root -- duplicate twin
        # dexes (the mystery-egg pools) become the root carrying their name.
        # The fuzzy corpus engine receives no NEW pets; it remains for legacy
        # saves and for pets jogressed out of their line.
        croot, lid = lines_mod.canonical_root(target)
        if croot is not None:
            target = croot
        self.evolve_to(target)
        self.line_id = lid                    # binds the pet to its line for life
        self.hatching = False
        self._rand_personality_traits()               # fix disposition/glutton/restless for life
        # (the X-Antibody birth roll is retired -- LINES_SPEC §4: X-forms are
        # reached by hatching X eggs, not won in a lottery at birth)

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
        {0:-1, 1:0, 2:+1} (only assigned while still neutral) -- and SEEDS the
        matching tracker rank at +-42 so the Champion re-roll starts from the
        rolled temperament, not from zero (taste/rank audit 2026-07-06)."""
        def roll(cur):
            if cur != 0:
                return cur
            r = random.randint(0, 2)
            return -1 if r < 1 else (1 if r > 1 else 0)
        self.restless = roll(self.restless)
        self.glutton = roll(self.glutton)
        self.disposition = roll(self.disposition)
        self.energy_rank = self.restless * PCHAMP_RANK      # randPersonalityTraits seeds
        self.weight_rank = self.glutton * PCHAMP_RANK
        self.mood_rank = self.disposition * PCHAMP_RANK

    def _rand_on_champion(self):
        """PhysicalState.randOnChampion: at the CHAMPION evolution the
        temperament is RE-ROLLED from the tracked childhood ranks -- a pup
        kept energetic turns restless, one kept fat turns gluttonous, one
        kept happy turns sunny (threshold +-42, no randomness)."""
        self.restless = (1 if self.energy_rank >= PCHAMP_RANK
                         else -1 if self.energy_rank <= -PCHAMP_RANK else 0)
        self.glutton = (1 if self.weight_rank >= PCHAMP_RANK
                        else -1 if self.weight_rank <= -PCHAMP_RANK else 0)
        self.disposition = (1 if self.mood_rank >= PCHAMP_RANK
                            else -1 if self.mood_rank <= -PCHAMP_RANK else 0)

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
        if self.dead:                # the 6h-malady clock can end the life here
            return
        self._tick_effect(dt)
        self._tick_auto_care(dt)     # the assistant serves awake AND asleep (never an egg)
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
        # sickLapse -> sickPenalty (awake only): illness burns the macros and
        # RACES the bowels (SickLapsePenaltyBM 48 gauge-units a lapse; the
        # startPoop it forces fires naturally when the gauge crosses)
        if self.sick and not self.asleep:
            self._sick_pen_t = getattr(self, "_sick_pen_t", 0.0) + dt
            if self._sick_pen_t >= 60.0:                  # SickLapseMin
                self._sick_pen_t = 0.0
                for f in ("nutr_protein", "nutr_mineral", "nutr_vitamin"):
                    setattr(self, f, max(0, getattr(self, f) + SICK_NUTRITION_CHANGE))
                self._poop_t = (getattr(self, "_poop_t", 0.0)
                                + self._poop_interval * SICK_LAPSE_PENALTY_BM
                                / max(1, self._phys().get("poop_limit", 64)))
        if self.inj_length > 0:                           # injLapse: the injury heals over time
            self.inj_length = max(0.0, self.inj_length - _rec)
        if self.vitamin_lapse > 0:                        # vitaminLapse: protection wears off
            self.vitamin_lapse = max(0.0, self.vitamin_lapse - dt)
        if self.med_lapse > 0:                            # medLapse: medicine wears off (getMed icon)
            self.med_lapse = max(0.0, self.med_lapse - dt)
        if self.bandage_lapse > 0:                        # bandageLapse: bandage wears off (getBandage icon)
            self.bandage_lapse = max(0.0, self.bandage_lapse - dt)
        # LINES_SPEC §5 (DM20: "remaining injured for 6 hours causes death"):
        # 6 continuous game-hours sick-or-injured is fatal.  Natural spells heal
        # inside the window (sick <=290, injury <=348 game-min), so only a pet
        # left to WORSEN (filth rolls, battling hurt, double doses) crosses it.
        if self.sick or self.inj_length > 0:
            self._malady_t = getattr(self, "_malady_t", 0.0) + dt
            if self._malady_t >= 360.0 and not self.dead:
                self._die("sickness" if self.sick else "its wounds")
        else:
            self._malady_t = 0.0

    def _inc_mistake(self):
        """PhysicalState.incMistake: EVERY care mistake stings the mood first --
        a Happy pet is knocked DOWN TO 100 (MistakeHappyMoodChange, absolute),
        anyone else loses 50 -- then the counters tick (care-mistake audit
        2026-07-05: the counters ticked silently)."""
        if self.current_mood() == "Happy":
            self._set_mood(MISTAKE_HAPPY_MOOD)
        else:
            self._set_mood(self.mood - MISTAKE_MOOD_DEC)
        self.care_mistakes += 1
        self.mistake_day += 1                        # MistakeIncMissedDayChange
        # incMistake's sickness risks (sickness/injury audit 2026-07-06):
        # filth rolls per pile with a misery pad, and ANY mistake while
        # fatigued adds a 1/1 whisper.  Canon's 50/50 poopCall branch is
        # PROVABLY DEAD in the shipped config (poop/filth audit: the filth
        # array holds 6 piles, MistakeFilthLimit is 7 -- countFilth can never
        # reach it), so it is not ported.
        if self.poop > 0:
            pad = (int(abs(math.ceil(self.mood * MISTAKE_FILTH_MOOD_COEF)))
                   if self.current_mood() in ("Unhappy", "Depressed") else 0)
            self._check_worse_sick(MISTAKE_LOW_FILTH_WORSE * self.poop + pad)
            self._check_sick(MISTAKE_LOW_FILTH_SICK * self.poop + pad)
        if self.is_fatigued():
            self._check_worse_sick(ANY_MISTAKE_FATIGUED)
            self._check_sick(ANY_MISTAKE_FATIGUED)

    def _tick_asleep(self, dt):
        """The sleep branch: lights neglect, deep-sleep regen, the awakeLapse
        clock with the restless jitter, asleep death checks, desperate poop."""
        # lightsCall (DVPet): sleeping with the room light ON is neglect.
        # AfterMistakeMinutesPostponed is -60, NOT a latch: the mistake REPEATS
        # every 120 lit minutes (a fully lit night is ~4 mistakes); the
        # obedience ding lands ONCE per night (_lightsOffMistake flag).
        if self.lights:
            self._lights_t = getattr(self, "_lights_t", 0.0) + dt
            if self._lights_t >= LIGHTS_MISTAKE_SEC:
                self._lights_t = LIGHTS_MISTAKE_POSTPONE
                if not getattr(self, "_lit_obed_hit", False):
                    self._lit_obed_hit = True
                    self._set_obedience(self.obedience + LIGHTS_MISTAKE_OBED)
                self._inc_mistake()
        # Pen20 DP: sleep restores jogress power -- 3 game-hours = a full meter
        if self.dp < DP_MAX:
            self._dp_t = getattr(self, "_dp_t", 0.0) + dt
            if self._dp_t >= DP_SLEEP_MIN:
                self._dp_t -= DP_SLEEP_MIN
                self.dp += 1
        # asleep enthusiasmLapse: spirit settles toward 0 while resting
        self._enth_lapse_t = getattr(self, "_enth_lapse_t", 0.0) + dt
        if self._enth_lapse_t >= 59:
            self._enth_lapse_t = 0.0
            if self.enthusiasm > 0:
                self._set_enthusiasm(self.enthusiasm - ENTHUSIASM_LAPSE_DEC)
            elif self.enthusiasm < 0:
                self._set_enthusiasm(self.enthusiasm + ENTHUSIASM_LAPSE_INC)
        # sleepDecay/setAwakeLapse (canon re-audit 2026-07): the wake clock steps
        # by the species AwakeLapseInc; a LIT room stalls it half the time
        # (LightsOnAwakeLapseUnchangedChance -- lit rest is poor rest); the
        # MoreSleepChance jitter lets a mellow pet lie in and a restless one
        # skip ahead, its bonus routed through the ACCUMULATORS like canon
        # (the old code paid energy directly, misreading NapEnergyMin -- a
        # cadence -- as an amount).
        phys = self._phys()
        awake_inc = phys.get("awake_inc", 1)

        def _inc_sleep_minutes(gain):
            # incSleepMinutes: the meter fills by AwakeLapseInc; a crossing pays
            self._sleep_min = getattr(self, "_sleep_min", 0.0) + awake_inc * dt
            if self._sleep_min >= SLEEP_MIN_TO_GAIN:
                self._sleep_min -= SLEEP_MIN_TO_GAIN
                self._set_energy(self.energy + gain)

        def _nap_energy(mult=1):
            # checkNapEnergy: the nap's own accumulator pays NapEnergyGain (1)
            self._nap_e = getattr(self, "_nap_e", 0.0) + awake_inc * dt * mult
            if self._nap_e >= NAP_ENERGY_INC:
                self._nap_e -= NAP_ENERGY_INC
                self._set_energy(self.energy + 1)

        step = awake_inc * dt
        if self.lights and not self.call_paused() and random.randrange(100) < LIGHTS_ON_AWAKE_STALL:
            step = 0.0
        r = random.randrange(MORE_SLEEP_CHANCE) + self.restless * AWAKE_RESTLESS_COEF
        bonus = False
        if r < 0:
            step = max(0.0, step - dt)
        elif r > MORE_SLEEP_CHANCE - 1:
            step += dt
            bonus = True
        if self.nap:
            # canon: a nap PAYS DOWN bedtime pressure (sleepLapse -= inc) -- the
            # old '+=' inverted it -- and, held past ChangeNapToSleepMinutes
            # (+restless coef), the nap BECOMES the night: pressure clears, the
            # accumulator residue rolls into the sleep meter, nap=false
            self.sleep_lapse = max(0.0, self.sleep_lapse - awake_inc * dt)
            self._nap_cycle = getattr(self, "_nap_cycle", 0.0) + dt
            _nap_energy(2 if bonus else 1)
            if (self._nap_cycle >= CHANGE_NAP_TO_SLEEP + self.restless * NAP_TO_SLEEP_RESTLESS
                    and self._in_sleep_window() is not False):   # a line pet's day-doze
                #                          never becomes the night; bedtime does that
                self._sleep_min = (getattr(self, "_sleep_min", 0.0)
                                   + max(0.0, getattr(self, "_nap_e", 0.0) - 1))
                self._nap_cycle = self._nap_e = 0.0
                self.sleep_lapse = 0.0
                self.nap = False
        else:
            _inc_sleep_minutes(NEGATIVE_ENERGY_GAIN if self.energy < 0
                               else getattr(self, "_sleep_energy_gain", 3))
            if bonus:
                _inc_sleep_minutes(BONUS_SLEEP_ENERGY)
        self.awake_lapse += step
        iw = self._in_sleep_window()
        if iw is not None and not self.nap:
            if iw is False:                      # LINES_SPEC §5: 7:00 sharp, no jitter
                self._wake()
        elif self.awake_lapse >= self.awake_limit:
            self._wake()                         # nap wakes take the nap roll inside
        # hungerDecay: asleep the stomach drains only ABOVE the floor
        # (SleepMinHungerDecay=3) -- one heart overnight, then it holds
        if self.hunger > SLEEP_MIN_HUNGER_DECAY:
            self._tick_hunger(dt)
        # canon runs these in bed too: the mood lapse (MinMoodAsleep only mutes
        # a rock-bottom sleeper), depression's rolls, the filth nag+risk, and
        # poopWaitMoodCheck -- the HELD gauge (only a sleeper holds it) nags
        self._mood_lapse(dt)
        self._check_depressed(dt)
        self._filth_effects(dt)
        if self._poop_t >= self._poop_interval:
            self._poop_wait_t = getattr(self, "_poop_wait_t", 0.0) + dt
            if self._poop_wait_t >= 60.0:                # PoopWaitMin, game-min lapse
                self._poop_wait_t = 0.0
                self._set_mood(self.mood + (LARGE_POOP_WAIT_MOOD
                                            if self._poop_t >= self._poop_interval * 1.5
                                            else POOP_WAIT_MOOD))
        # death does not wait for morning: the mistake caps and old age
        # apply asleep too (only the starvation clock freezes; audit 2026-07)
        if self._check_death_caps() or self._check_old_age():
            return
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
        self._mood_lapse(dt)
        self._check_depressed(dt)
        self._filth_effects(dt)
        # obedienceLapse (obedience audit 2026-07-06): discipline FADES while
        # awake -- dec 2 on a disposition-shaded cadence (sunny 180 / neutral
        # 120 / sour 60), each dec event billing the mess too
        # (ObedienceChangeFilthScale x piles).  MinObedienceAsleep 150 ==
        # MaxObedience: canon's lapse can never run asleep, and tick() only
        # reaches here awake.
        self._obed_lapse_t = getattr(self, "_obed_lapse_t", 0.0) + dt
        if self._obed_lapse_t >= OBEDIENCE_LAPSE_MIN.get(self._disposition(), 120.0):
            self._obed_lapse_t = 0.0
            self._set_obedience(self.obedience - OBEDIENCE_LAPSE_DEC)
            if self.poop > 0:
                self._set_obedience(self.obedience + OBEDIENCE_FILTH_SCALE * self.poop)
        # checkRefusedOff: an UNSCOLDED refusal expires on its own -- the pet
        # got away with it (mood +1) and hardens a little less (obedience -1)
        if self.refused and not self.scold_flag:
            self._refused_t = getattr(self, "_refused_t", 0.0) + dt
            if self._refused_t >= REFUSED_OFF_MIN:
                self._refused_t = 0.0
                self.refused = False
                self._set_mood(self.mood + REFUSED_OFF_MOOD_INC)
                self._set_obedience(self.obedience - REFUSED_OFF_OBED_DEC)
        else:
            self._refused_t = 0.0
        # the discipline CALL ages on its own clock (canon callMinutesDiscipline):
        # ignored past _minutesToDisciplinePenalty the tantrum sours -- mood -25,
        # a missed day -- and the light goes dark
        if self.discipline_call:
            self._disc_call_t = getattr(self, "_disc_call_t", 0.0) + dt
            if self._disc_call_t >= MINUTES_TO_DISCIPLINE_PENALTY:
                self.discipline_call, self._disc_call_t = False, 0.0
                self._set_mood(self.mood - DISCIPLINE_CALL_MOOD_PENALTY)
                self.mistake_day += DISCIPLINE_CALL_FAIL_MISSED_DAY
        # discipline windows age (checkPraiseScoldWindow); a missed window closes
        self._mood_lapse_t2 = getattr(self, "_mood_lapse_t2", 0.0) + dt
        if self._mood_lapse_t2 >= 59:
            self._mood_lapse_t2 = 0.0
            if self.praise_flag:
                self.praise_window += 1
                if self.praise_window > PRAISE_WINDOW_MAX:
                    # setPraiseWindow overflow: the good deed went UNPRAISED --
                    # the pet sulks and hardens a little (disposition-shaded)
                    self._set_mood(self.mood - PRAISE_FAIL_MOOD_PENALTY)
                    self._set_obedience(self.obedience
                                        + (PRAISE_FAIL_OBED_INC if self._disposition() > 0
                                           else PRAISE_FAIL_OBED_INC
                                           + self._disposition() * PRAISE_FAIL_OBED_DISPO_COEF))
                    self.praise_flag, self.praise_window = False, 0
            if self.scold_flag:
                self.scold_window += 1
                if self.scold_window > SCOLD_WINDOW_MAX:
                    # setScoldWindow overflow: it GOT AWAY WITH IT -- happier,
                    # less obedient, and the refusal is forgiven unscolded
                    self._set_mood(self.mood + SCOLD_FAIL_MOOD_INC)
                    self._set_obedience(self.obedience - SCOLD_FAIL_OBED_PENALTY)
                    self.refused = False
                    self.scold_flag, self.scold_window = False, 0
            self._check_discipline_call()                # the pet may spontaneously act up
            # personalityTracker (taste/rank audit 2026-07-06): childhood care
            # is TALLIED through Fresh/InTraining/Rookie -- energy kept above
            # 75% of max builds restlessness, weight off Healthy builds
            # gluttony, the mood tier builds disposition; randOnChampion
            # cashes the tally in at the Champion evolution
            if self.stage in ("Fresh", "InTraining", "Rookie"):
                if self.energy >= PCHAMP_HI_ENERGY * self.max_energy:
                    self.energy_rank += 1
                elif self.energy <= PCHAMP_LO_ENERGY * self.max_energy:
                    self.energy_rank -= 1
                wc = evolution.weight_category(self.weight, self._base_weight())
                if wc == "Over":
                    self.weight_rank += 1
                elif wc == "Under":
                    self.weight_rank -= 1
                m = self.current_mood()
                if m == "Happy":
                    self.mood_rank += 1
                elif m in ("Unhappy", "Depressed"):
                    self.mood_rank -= 1
            # awake enthusiasmLapse (mood -= |enth*EnthusiasmMoodDecCoefficient|, then an energetic
            # pet's spirit climbs HighEnergyEnthusiasmChange) stays DEFERRED -- and this was measured,
            # not assumed: ported faithfully it collapses mood to Unhappy/Depressed within ~15 real-min
            # whatever the play style, because the only awake spirit-restoring force is +1/lapse while
            # activities cost -3..-6, so under tuipet's ~60x clock |enthusiasm| pins at 10 and the drain
            # sticks at -20/lapse (active play is WORSE, driving enth to -10). It needs the real-time
            # clock to balance; DVPet numbers are NOT softened. Asleep decay (below) IS ported.

    def _mood_lapse(self, dt):
        """PhysicalState.moodLapse, verbatim (canon re-audit 2026-07).  Gated off
        while sick/injured or while a care call begs (checkCall) -- misery and
        need FREEZE the drift; it runs ASLEEP too (MinMoodAsleep only mutes a
        rock-bottom sleeper).  Per lapse: the personality drifts (glutton x
        hunger band; the restless term compares the TRAIT to fullStrength/2 --
        a shipped DVPet quirk that makes it a constant drift -- kept verbatim),
        then Happy -10 / Unhappy +5 (or +10 below minMood/2) / Neutral -5 in
        [5, maxMood/2) else -1, and -2 whenever the weight is off Healthy."""
        self._mood_lapse_t = getattr(self, "_mood_lapse_t", 0.0) + dt
        if self._mood_lapse_t < 59:                       # MoodLapseMin
            return
        self._mood_lapse_t = 0.0
        if self.asleep and self.mood <= -300:             # MinMoodAsleep
            return
        if self.sick or self.is_injured() or self.needs_attention():
            return
        # the tier branch reads _currentMood as of the last setMood -- BEFORE
        # this lapse's raw drift lands (mood re-audit 2026-07-06)
        m = self.current_mood()
        # the personality nudges are RAW `_mood +=` in canon: no disposition
        # kicker, no tier recompute (setMood adds both; routing the +-1 drift
        # through it doubled or zeroed the nudge for any +-1-disposition pet)
        if self.hunger <= FULL_HUNGER // 2:
            self.mood = _clamp(self.mood + (-1 if self.glutton == 1 else 1 if self.glutton == -1 else 0),
                               MOOD_MIN, MOOD_MAX)
        elif self.hunger > FULL_HUNGER:
            self.mood = _clamp(self.mood + (1 if self.glutton == 1 else -1 if self.glutton == -1 else 0),
                               MOOD_MIN, MOOD_MAX)
        # the restless term: canon compares _restless (the trait) to fullStrength/2,
        # so the "low strength" branch ALWAYS holds -- a restless pet drifts -1 and
        # a mellow one +1 every lapse.  Shipped behavior, kept verbatim.
        self.mood = _clamp(self.mood + (-1 if self.restless == 1 else 1 if self.restless == -1 else 0),
                           MOOD_MIN, MOOD_MAX)
        if m == "Happy":
            self._set_mood(self.mood - 10)                # HappyMoodLapseDec
        elif m == "Unhappy":
            if self.mood > -150:                          # minMood/2
                self._set_mood(self.mood + 5)             # UnhappyMoodLapseInc
            elif self.mood < -150:
                self._set_mood(self.mood + 10)            # VeryUnhappyMoodLapseInc
        elif m == "Neutral":
            if VERY_NEUTRAL_MOOD_DEC <= self.mood < 150:  # [5, maxMood/2)
                self._set_mood(self.mood - VERY_NEUTRAL_MOOD_DEC)
            else:
                self._set_mood(self.mood - 1)             # NeutralMoodLapseDec
        if evolution.weight_category(self.weight, self._base_weight()) != "Healthy":
            self._set_mood(self.mood - BAD_WEIGHT_MOOD_DEC)

    def _check_depressed(self, dt):
        """PhysicalState.checkDepressed: depression is a sticky STATE with random
        entry/exit rolls -- while down, mood climbs +50 an interval but obedience
        -5 and spirit -1; the exits snap mood to NewUndepressedMood (-50), the
        positive-mood exit paying +33 obedience for weathering it."""
        self._depress_t = getattr(self, "_depress_t", 0.0) + dt
        if self._depress_t < DEPRESSED_LAPSE_MIN:
            return
        self._depress_t = 0.0
        r = random.randrange(DEPRESSED_CHANCE)
        if self.depressed:
            if r < DEPRESSED_EXIT_NEG and self.mood < 0:
                self.depressed = False
                self._set_mood(NEW_UNDEPRESSED_MOOD)
            elif r < DEPRESSED_EXIT_POS and self.mood > 0:
                self.depressed = False
                self._set_obedience(self.obedience + UNDEPRESSED_OBED_INC)
                self._set_mood(NEW_UNDEPRESSED_MOOD)
            else:
                self._set_mood(self.mood + DEPRESSED_MOOD_CHANGE)
                self._set_obedience(self.obedience + DEPRESSED_OBED_CHANGE)
                self._set_enthusiasm(self.enthusiasm + DEPRESSED_ENTH_CHANGE)
        elif (self.mood <= MIN_UNHAPPY_MOOD and not self.depressed
                and self.stage not in ("Fresh", "InTraining")):
            if self.mood <= TO_DEPRESSED_MOOD and r < TO_DEPRESSED_ROLL_NEG:
                self.depressed = True
            elif r < TO_DEPRESSED_ROLL_NORM:
                self.depressed = True

    def _filth_effects(self, dt):
        """checkFilthMoodDec + the filth sickness rolls (canon re-audit 2026-07):
        every FilthMoodDecMin the mess costs species filth_mood x piles; every
        game-min each pile is a sickness risk (chance x piles vs the bound x the
        species multiplier -- the 12000 real-min bound rides the /60 game scale,
        which lands within a hair of the old hand-rolled rate while gaining the
        per-pile scaling and the worse-sick path the flat roll lacked)."""
        if self.poop <= 0:
            return
        fm = self._phys().get("filth_mood", -1)
        if fm:
            self._filth_mood_t = getattr(self, "_filth_mood_t", 0.0) + dt
            if self._filth_mood_t >= FILTH_MOOD_DEC_MIN:
                self._filth_mood_t = 0.0
                self._set_mood(self.mood + fm * self.poop)
        bound = int(FILTH_SICK_BOUND * self._phys().get("poop_sick_mult", 1.0))
        self._filth_sick_t = getattr(self, "_filth_sick_t", 0.0) + dt
        if self._filth_sick_t >= 60.0:                    # FilthSickMin, on the game-min lapse
            self._filth_sick_t = 0.0
            if self.sick:
                if random.randrange(max(1, bound)) < FILTH_WORSE_CHANCE * self.poop:
                    self._worsen_sick()
            elif random.randrange(max(1, bound)) < FILTH_SICK_CHANCE * self.poop:
                self._sicken()

    def _tick_hunger(self, dt):
        """hunger: the DVPet calorie buffer drains each lapse; emptying it drops
        a hunger heart, then refills.  The care MISTAKE is the call light
        (LINES_SPEC §5, canon on all three devices): hunger empty and unanswered
        for 10 minutes = ONE mistake, then the call is postponed — it no longer
        repeats every calorie cycle while starving."""
        # hungerCall: a single mistake per unanswered call, mirroring strengthCall
        if self.hunger == 0 and not self.asleep:
            self._hunger_call_t = getattr(self, "_hunger_call_t", 0.0) + dt
            if self._hunger_call_t >= 600.0:                 # MinutesToMistake 10
                self._hunger_call_t = -3600.0                # AfterMistakeMinutesPostponed
                self._inc_mistake()
                self.mistake_day += 1  # + HungerDecAtZero MissedDayChange
                self._burn_life(HUNGER_MISTAKE_LIFE_DEC * max(1, self.care_mistakes))
                # hungerMistakePenalty: obedience +1 -- or -1 for a glutton
                self._set_obedience(self.obedience
                                    + (HUNGER_MISTAKE_OBED_GLUTTON if self.glutton > 0
                                       else HUNGER_MISTAKE_OBED))
                self._open_scold()           # neglect: the pet acts up
        elif self.hunger > 0:
            self._hunger_call_t = 0.0
        self._cal_t = getattr(self, "_cal_t", 0.0) + dt
        if self._cal_t >= self._hunger_interval:
            self._cal_t = 0.0
            self._set_calories(self.calories + CALORIE_LAPSE_CHANGE
                               + (CALORIE_LAPSE_GERIATRIC_EXTRA if self.is_geriatric else 0))
            if self.calories <= -CALORIE_LIMIT:
                if self.hunger > 0:
                    self.hunger -= 1
                if self.hunger == 0:
                    # starvation (setHunger below zero): the calorie crash sheds weight
                    # every further lapse (StarvationCalorieChange -> ActivityWeightChange)
                    self._set_weight(self.weight - STARVE_WEIGHT_DEC)
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
            tk = self._toilet_for_poop()         # doPoop: a trained pet goes by itself
            if tk:
                self._toilet_visit(tk, backlog=backlog)
            else:
                self._do_poop(backlog=backlog)
                self._set_anim("poop", 2.2)      # squat-and-go (DVPet poop())
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
                self._inc_mistake()
                self._set_obedience(self.obedience - 5)      # MistakeStrengthObedienceDec
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
        # Filth acting-up (LINES_SPEC §5): NO real device counts filth as a care
        # mistake (Pen20 says so explicitly — mistakes are unanswered call lights
        # only), so the DVPet poopCall mistake is retired.  Filth keeps its teeth
        # (sickness rolls + mood drain in _filth_effects); an awake pet left amid
        # the mess past the grace still ACTS UP (scold window), postponed after one.
        FILTH_LIMIT = 3                      # the visible "needs cleaning" level
        if self.poop >= FILTH_LIMIT:
            if not self.asleep:              # only ticks while awake; sleep pauses, not resets
                self._filth_t = getattr(self, "_filth_t", 0) + dt
                if self._filth_t >= 1800:    # uncleaned grace before it acts up
                    self._filth_t = -3600    # AfterMistakeMinutesPostponed grace after one
                    self._open_scold()       # left in filth: the pet acts up
        else:
            self._filth_t = 0                # cleaned / under the limit resets the call timer
        # (the filth sickness rolls moved to _filth_effects -- canon shape; the
        # old flat roll also invented a STARVATION sickness canon does not have)

    WAKE_MINUTE = 7 * 60          # LINES_SPEC §5: every line form wakes at 7:00

    def _in_sleep_window(self):
        """Line pets sleep by the CLOCK: True/False = inside/outside the form's
        fixed bedtime→7:00 window; None = not a line pet (pressure model)."""
        bt = lines_mod.bedtime_minutes(self) if lines_mod.active(self) else None
        if bt is None:
            return None
        mod = self.world_seconds % DAY_MINUTES
        if bt > self.WAKE_MINUTE:                     # the usual wrap past midnight
            return mod >= bt or mod < self.WAKE_MINUTE
        return bt <= mod < self.WAKE_MINUTE           # a midnight sleeper (24:00 -> 0)

    def _tick_bedtime(self, dt):
        """LINES_SPEC §5: the fixed per-form bedtime replaces the pressure clock.
        Inside the window the pet drops off by itself (a disturb postpones the
        re-sleep); lights-out OUTSIDE the window is a shallow nap, like checkNap.
        The nightly ritual: at bedtime the room is still lit — turning the lights
        off within the grace is the care; a lit sleeper logs the once-per-night
        lights mistake exactly as before."""
        if self.asleep:
            return
        if self._in_sleep_window():
            self._bed_postpone_t = getattr(self, "_bed_postpone_t", 0.0) - dt
            if self._bed_postpone_t > 0:
                return                                # a disturb bought some grumbling time
            self._fall_asleep()
            # the night is the window, not an energy budget: rested checks and
            # the sleep meter size off the real span (bedtime -> 7:00)
            bt = lines_mod.bedtime_minutes(self)
            self.awake_limit = (self.WAKE_MINUTE - bt) % DAY_MINUTES
            self.sleep_limit = DAY_MINUTES - self.awake_limit
        elif not self.lights:
            # the daytime doze waits out the same calcToSleepNapLapse as the
            # pressure model (sleep audit 2026-07-06)
            self._to_nap_t = getattr(self, "_to_nap_t", 0.0) + dt
            if self._to_nap_t < self._calc_to_nap():
                return
            self._to_nap_t = 0.0
            # a daytime doze: same once-per-game-hour mood bonus guard as checkNap
            if self.world_seconds - getattr(self, "_nap_bonus_t", -9e9) >= 60:
                self._nap_bonus_t = self.world_seconds
                self._set_mood(self.mood + ON_NAP_MOOD_INC)
            self.asleep, self.nap = True, True
            self._lights_t = 0.0
            self._lit_obed_hit = False
            self._set_anim("yawn", 1.8)
        else:
            self._to_nap_t = 0.0

    def _calc_to_nap(self):
        """calcToSleepNapLapse: how long the pet sits in the DARK before it
        nods off -- an energetic pet resists (~40 game-min), a drained one
        folds in 20; restless +-1; a well-drilled pet (obedience >= 75)
        drops the extra +1."""
        r = self.restless * TO_SLEEP_NAP_RESTLESS
        obed_mod = 0 if self.obedience >= TO_NAP_OBEDIENCE_FACTOR else 1
        return (TO_NAP_HIGH_ENERGY if self.energy > self.max_energy / 2
                else TO_NAP_LOW_ENERGY) + r + obed_mod

    def _tick_sleep_pressure(self, dt):
        """bedtime is a PRESSURE clock, not the sun (setSleepLapse): SleepLapseInc
        per game-min while awake; at the limit the pet drops off by itself --
        babies (inc 9) nap constantly, adults run a free ~24h rhythm.
        checkNap fires only after the DOZE-OFF WAIT (toNapSleepLapse; sleep
        audit 2026-07-06 -- the old instant nap skipped it): lights out, the
        pet sits a calcToSleepNapLapse while, THEN dozes (real sleep instead
        when the pressure is nearly full -- sleepNotNap).
        Line pets sleep by the CLOCK instead (LINES_SPEC §5)."""
        if self._in_sleep_window() is not None:
            self._tick_bedtime(dt)
            return
        if not self.asleep:
            self.sleep_lapse += dt * self._sleep_inc()
            if self.sleep_lapse >= self.sleep_limit:
                self._fall_asleep()
            elif not self.lights:
                self._to_nap_t = getattr(self, "_to_nap_t", 0.0) + dt
                if self._to_nap_t < self._calc_to_nap():
                    return                                  # still blinking in the dark
                self._to_nap_t = 0.0
                edge = SLEEP_NOT_NAP_MIN - self.restless * SLEEP_NOT_NAP_RESTLESS
                if self.sleep_lapse >= self.sleep_limit - edge:
                    self._fall_asleep()                     # close enough to bedtime
                else:
                    # checkNap: a shallow doze that BORROWS the current cycle --
                    # pressure keeps accruing, so real bedtime still arrives on
                    # time.  The +10 nap mood keeps the extra once-per-game-hour
                    # guard (belt over the doze-off wait, canon's own anti-farm)
                    if self.sleep_lapse - getattr(self, "_nap_bonus_lapse", -9e9) >= 60:
                        self._nap_bonus_lapse = self.sleep_lapse
                        self._set_mood(self.mood + ON_NAP_MOOD_INC)
                    self.asleep, self.nap = True, True
                    self._lights_t = 0.0
                    self._lit_obed_hit = False
                    # checkNap's nap length: a SICK or hurt pet takes a fixed
                    # hour (awakeLimit - minutesHour); healthy naps repay the
                    # accrued pressure.  (Canon's end-of-hour 2-hour variant is
                    # a wall-clock alignment quirk tuipet's clock doesn't have.)
                    self.awake_lapse = (max(0.0, self.awake_limit - 60.0)
                                        if (self.sick or self.is_injured())
                                        else max(0.0, self.awake_limit - self.sleep_lapse))
                    self._set_anim("yawn", 1.8)
            else:
                self._to_nap_t = 0.0                        # the light resets the wait

    def _check_death_caps(self):
        """The discrete mistake/injury caps + the Pen20 elder-frailty rule:
        ONE copy for both tick paths -- these gates were duplicated between the
        sleep tick and _tick_mortality and had to be edited in lockstep
        (refactor 2026-07-05).  True when the pet died."""
        if self.care_mistakes >= 20 or self.injuries >= 20:   # MaxCareMistakes / MaxInjuries
            self._die("neglect" if self.care_mistakes >= 20 else "its injuries")
            return True
        # Pen20 (LINES_SPEC §5): at the last stages, 5 slips once the evolution
        # window is open = death -- an elder Perfect/Ultimate demands real care
        if (self.stage in ("Ultimate", "Mega") and self.care_mistakes >= 5
                and self.stage_seconds >= self.LATE_STAGE_WINDOW):
            self._die("frailty")
            return True
        return False

    def _check_old_age(self):
        """lapsedLife >= totalLifespan -- canon's one true death trigger.
        True when the pet died."""
        if self.age_seconds >= self.lifespan:
            self._die("old age")
            return True
        return False

    def _burn_life(self, amount):
        """setTotalLifespan's penalty path (canon re-audit 2026-07): every
        neglect event BURNS lifespan, clamped so a cut can never kill inside
        InstantDeathGracePeriod of now -- death always gives you the grace."""
        self.lifespan = max(self.age_seconds + INSTANT_DEATH_GRACE, self.lifespan - amount)

    def _tick_mortality(self, dt):
        """Canon death is ONE trigger -- old age (lapsedLife >= totalLifespan)
        -- with every neglect event BURNING lifespan toward it (the Sick/Injury/
        Fatigue/Mistake/X LifeDec economy; canon re-audit 2026-07).  The discrete
        caps (20 mistakes / 20 injuries / 12h starving) are tuipet SAFETY NETS
        kept beneath the burn economy, not canon (an earlier docstring claimed
        otherwise); under correct burns they almost never fire first.  Returns
        True when the pet died this tick."""
        if self._check_death_caps():
            return True
        if self.hunger == 0 and not self.asleep:              # awake-only, like hungerCall()
            self._starve_t = getattr(self, "_starve_t", 0.0) + dt
            if self._starve_t >= 12 * 3600:                   # empty hunger 12h -> death
                self._die("starvation"); return True
        elif self.hunger > 0:
            self._starve_t = 0.0
        self.habitat_record[self.habitat] = self.habitat_record.get(self.habitat, 0) + dt
        # (the old continuous per-second "extra" drain was invented -- canon
        # burns lifespan through the EVENT penalties wired below instead)
        return self._check_old_age()


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

    def background(self, habitat_id=None):
        """The habitat background frame for the current weather/time (or None).
        habitat_id overrides the home -- adventure shows the ZONE's scenery."""
        h = (data.load_habitats().get(habitat_id) if habitat_id is not None
             else self.habitat_obj()) or {}
        frames = data.load_backgrounds().get(h.get("bg", ""))
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
        """The pet warms to the times of day it spends happy in, and sours on
        the rest (DVPet's timeRanks).  One step per GAME-MINUTE: the old
        per-SECOND drift saturated a phase to -90 within 90s of sadness and
        poisoned the whole clock -- disliked-hour drains then kept the pet
        unhappy, souring MORE hours (the misbehaving ratchet; Joel's Devimon
        hated all four phases at -60..-90, 2026-07-05).  A neutral-mood minute
        drifts the current phase back toward 0, so a scarred clock heals."""
        self._time_pref_t = getattr(self, "_time_pref_t", 0.0) + dt
        if self._time_pref_t < 60.0:
            return
        self._time_pref_t -= 60.0
        ph = self.day_phase
        cur = self.time_pref.get(ph, 0)
        if self.mood >= MIN_HAPPY_MOOD:
            d = 1
        elif self.mood <= MIN_UNHAPPY_MOOD:
            d = -1
        else:
            d = 1 if cur < 0 else (-1 if cur > 0 else 0)   # neutral: mend toward 0
        if d:
            self.time_pref[ph] = _clamp(cur + d, -90, 90)

    def _disposition(self):
        return self.disposition          # DVPet _disposition: fixed personality trait

    def _power_bonus_attr(self):
        """set{Vaccine,Data,Virus}Power's bonus gate: the attribute whose gains
        a HAPPY pet doubles -- its own attribute (any stage), or for a None/
        Free-attribute pet past InTraining its EMERGENT favourite (the ledger
        drifts now; the AttributePreference seed stands in until one forms)."""
        if self.attribute in ("Vaccine", "Data", "Virus"):
            return self.attribute
        if self.stage in ("Fresh", "InTraining"):
            return "None"
        return self.favorite_attr or self._phys().get("attr_pref", "None")

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
        # checkTemp's fever/chills (canon re-audit 2026-07): a SICK pet's
        # temperature lurches -- 1% chill (-30) / 1% fever (+30) per check
        if self.sick:
            i = random.randrange(SICK_TEMP_DEC_CHANCE)
            if i == 1:
                self.temp = max(0, self.temp - SICK_TEMP_SWING)
            elif i == 2:
                self.temp = min(wx.MAX_TEMP, self.temp + SICK_TEMP_SWING)

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
        if not self.spend_bits(h["price"]):
            return "Not enough bits."
        self.habitats = sorted(set(self.habitats) | {hid})
        self.habitat = self.home_habitat = hid   # buying a new home moves you in
        self._weather_day = -1             # fresh climate roll on arrival, like move_to
        return f"Bought {h['name']} — moved in!"

    def move_to(self, hid):
        habs = data.load_habitats()
        h = habs.get(hid)
        if not h:
            return "?"
        if hid not in self.habitats:
            return "You don't own that habitat."
        self.habitat = self.home_habitat = hid
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

    def needs_attention(self):
        """The ONE care-call predicate behind the '!' bubble AND the HUD alarm
        (they had drifted; design call, polish 2026-07): an awake, hatched pet
        that is starving, sick, filthy, exhausted or misbehaving."""
        return (not self.dead and self.stage != "Egg" and not self.asleep
                and not self.call_paused()
                and (self.hunger == 0 or self.sick or self.poop >= 3
                     or self.energy <= 0 or self.scold_flag or self.discipline_call))

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

    def _add_filth(self, size):
        """addFilth (poop/filth audit 2026-07-06): below the cap the pile takes
        the next slot; a FULL room UPGRADES the first pile smaller than the new
        mess instead of dropping it (canon's overflow rule -- the old cap
        silently discarded it).  Cap stays Joel's 4 (real-toy match; canon's
        array is 6 -- with its poopCall threshold at 7, provably dead)."""
        if self.poop < POOP_MAX_PILES:
            self.poop += 1
            self.poop_sizes.append(size)
            return
        for i, s in enumerate(self.poop_sizes):
            if s < size:
                self.poop_sizes[i] = size
                break

    def _start_poop(self):
        """DVPet startPoop: drop a sized pile."""
        self._add_filth(self._poop_size())

    def _advance_bm(self, bm):
        """applyFood/bad-med/bad-vitamin: the bowel gauge lurches BM units,
        proportional to the species' own gauge size."""
        self._poop_t = getattr(self, "_poop_t", 0) \
            + self._poop_interval * bm / max(1, self._phys().get("poop_limit", 64))

    def _die(self, cause=""):
        self.dead = True
        self.death_cause = cause or self.death_cause   # first cause wins
        self.asleep = False
        self.hatching = False
        self._set_anim("idle", 0)

    def _base_weight(self):
        return data.load_requirements().get(self.num, {}).get("base_weight", 20)

    def _maybe_evolve(self):
        if self.sick or self.asleep or self.is_geriatric:
            return
        if getattr(self, "fx_hold", False):
            return          # an animation owns the screen; evolve on a quiet tick
        if self.stage_seconds < self.STAGE_DURATION.get(self.stage, 9e9):
            return
        if lines_mod.active(self):
            # line pets evolve by their line's first-match bracket table ONLY.
            # No match = stay and keep re-checking: counters can still earn a
            # row later (the DM20 Perfect battle gate works exactly so).
            target = lines_mod.select_line(self)
            if target is not None:
                self.evolve_to(target)
            return
        target = evolution.select(self)
        if target is not None:
            self.evolve_to(target)

    def _apply_egg_habitat(self):
        """Show the destined habitat as soon as the egg is chosen (DVPet)."""
        for t in egg_mod.hatch_targets(self.egg_type):
            h = data.natural_habitat(t)
            if h >= 0:
                self.habitat = self.home_habitat = h
                if h not in self.habitats:
                    self.habitats = sorted(set(self.habitats) | {h})
                return

    def _apply_natural_habitat(self):
        """Move HOME to this species' natural habitat (digimon.csv Habitat) so
        each Digimon shows its own background. -1 = no preference -> keep
        current.  (tuipet design: evolution grants the natural home free --
        canon's habitat SHOP is provably dead, so tuipet's buy/move economy
        plus this grant IS the habitat system's agency.)"""
        hr = data.natural_habitat(self.num)
        if hr is not None and hr >= 0:
            self.habitat = self.home_habitat = hr
            if hr not in self.habitats:
                self.habitats = sorted(set(self.habitats) | {hr})

    def go_home_habitat(self):
        """setCurrentHabitat(home): back from the road -- the CURRENT habitat
        returns to the owned home (habitat audit 2026-07-06)."""
        if self.home_habitat >= 0 and self.habitat != self.home_habitat:
            self.habitat = self.home_habitat
            self._weather_day = -1                 # fresh sky back home

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
        if amount <= 0 or not self.spend_bits(amount):
            self._set_anim("refuse", 1.0)                   # Jeering: can't afford the wager
            return False
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

    _ATTR3 = ("Vaccine", "Data", "Virus")

    def _rank_stage_inc(self):
        """RankChangeStage*Inc: young pets form tastes faster (+3/+2/+1)."""
        return RANK_STAGE_INC.get(self.stage, 0)

    def _promote_attr_ranks(self):
        """A rank at +-RankLimit becomes the emergent favourite/disliked
        (simplified from Taste.setNewFavDislike like the food port: no
        repeat-collision reroll -- all three attributes are valid both ways)."""
        for a in self._ATTR3:
            if self.attr_ranks[a] >= RANK_LIMIT and self.favorite_attr != a:
                self.favorite_attr = a
                if self.disliked_attr == a:
                    self.disliked_attr = ""
            elif self.attr_ranks[a] <= RANK_MIN and self.disliked_attr != a:
                self.disliked_attr = a
                if self.favorite_attr == a:
                    self.favorite_attr = ""

    def _change_attr_rank(self, attr):
        """Taste.changeRank for the attribute ledger: a drill warms the pet to
        its attribute (stage-scaled base, +-2 species preference/aversion
        bias); drilling the current favourite decays the others toward 0."""
        if attr not in self._ATTR3:
            return
        req = self._phys()
        delta = RANK_CHANGE_ATTR + self._rank_stage_inc()
        if attr == req.get("attr_pref", "None"):
            delta += RANK_PREF_INC
        elif attr == req.get("attr_aversion", "None"):
            delta -= RANK_PREF_INC
        if attr == self.disliked_attr:
            delta += RANK_DISLIKED
            for a in self._ATTR3:                          # incRankExcept toward 0
                if a != attr and self.attr_ranks[a] < 0:
                    self.attr_ranks[a] = min(0, self.attr_ranks[a] + RANK_AFTER_FAV)
        if attr == self.favorite_attr:
            for a in self._ATTR3:                          # decRankExcept toward 0
                if a != attr and self.attr_ranks[a] > 0:
                    self.attr_ranks[a] = max(0, self.attr_ranks[a] - RANK_AFTER_FAV)
        self.attr_ranks[attr] = _clamp(self.attr_ranks[attr] + delta, RANK_MIN, RANK_LIMIT)
        self._promote_attr_ranks()

    def _dec_attr_rank(self, attr, change):
        """decRankAndCheckFavDislikeChange: a bad experience keyed to an
        attribute sours it (None = all three, like canon's disturb(None))."""
        for a in ([attr] if attr in self._ATTR3 else self._ATTR3):
            self.attr_ranks[a] = _clamp(self.attr_ranks[a] - change, RANK_MIN, RANK_LIMIT)
        self._promote_attr_ranks()

    def _dec_food_ranks(self, cats, change):
        """The food ledger's negative path (forced meals, forced sickness)."""
        for c in cats:
            if c in self.food_ranks:
                self.food_ranks[c] = _clamp(self.food_ranks[c] - change, RANK_MIN, RANK_LIMIT)
                if self.food_ranks[c] <= RANK_MIN:
                    self.disliked_food = c

    def _eat_food(self, category, complied=False):
        """DVPet feed taste. A food's Type is a ";"-list of categories (foodType.getType()):
        the tier comes from whether any category is the CURRENT disliked (first) or favourite,
        then each category's rank/eaten is bumped (incFoodRankAndEaten) and intolerance rolled."""
        cats = [c for c in (category or "").split(";") if c in data.FOOD_CATEGORIES]
        if not cats:
            return "neutral"
        if self.disliked_food and self.disliked_food in cats:
            tier = "disliked"
            self._set_mood(self.mood - FAV_FOOD_MOOD)
            self._set_obedience(self.obedience + DISLIKED_FOOD_OBEDIENCE)
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
            # a COMPLIANT pet forced through an intolerant meal resents you --
            # sick or not (canon ObedienceChangeIntolerantForced; obedience
            # audit 2026-07-06)
            if complied:
                self._set_obedience(self.obedience + OBEDIENCE_CHANGE_INTOL_FORCED)
            # checkIntolerantFoodSick rolls worse AND fresh once each (the old
            # x2 fresh loop misread it; sickness/injury audit 2026-07-06)
            self._check_worse_sick(INTOL_WORSE_SICK_CHANCE)
            self._check_sick(INTOL_FOOD_SICK_CHANCE)
        # the FORCED-meal taste decs (taste/rank audit 2026-07-06): a compliant
        # pet's grudging meal sours the categories -- the disliked worst
        if complied and cats:
            self._dec_food_ranks(cats, RANK_BAD_FOOD_FORCED if tier == "disliked"
                                 else RANK_INTOL_FORCED if any(c in intol for c in cats)
                                 else RANK_FOOD_FORCED)
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
        was_young = self.stage in ("Egg", "Fresh", "InTraining", "Rookie")
        _req = self._become(num)
        if was_young and self.stage == "Champion":
            # randOnChampion (taste/rank audit 2026-07-06): the childhood-care
            # tally becomes the adult temperament
            self._rand_on_champion()
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.disturb = 0
        self.stage_trainings = self.stage_battles = 0     # battle_log persists (Pen20 rolling window)
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
        if _req.get("xantibody", "None") in ("Induced", "Natural"):
            # Evolution.digivolve: becoming an X form makes the X state PERMANENT
            self._set_xantibody("Permanent")
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

    def _set_weight(self, value):
        """PhysicalState.setWeight (weight audit 2026-07-06): clamp to
        baseWeight +- round(baseWeight x WeightLimitMultiple 0.75); slamming
        into either wall fires weightLimitPenalty (mood -10, obedience -0 at
        difficulty 0, spirit -1); inside the band the floor is 1."""
        value = int(round(value))
        base = self._base_weight()
        span = round(base * WEIGHT_LIMIT_MULTIPLE)
        if value < base - span:
            self.weight = base - span
            self._weight_limit_penalty()
        elif value > base + span:
            self.weight = base + span
            self._weight_limit_penalty()
        else:
            self.weight = max(1, value)

    def _weight_limit_penalty(self):
        """PhysicalState.weightLimitPenalty: hitting the body's hard wall."""
        self._set_mood(self.mood - WEIGHT_LIMIT_MOOD_PENALTY)
        self._set_obedience(self.obedience - WEIGHT_LIMIT_OBED_PENALTY)
        self._set_enthusiasm(self.enthusiasm - WEIGHT_LIMIT_ENTH_PENALTY)

    def _set_calories(self, value):
        """DVPet setCalories: the buffer clamps at +-CalorieLimit -- and an
        OVERFLOW while rising bumps the BM gauge (AboveMaxCaloriesBMGaugeChange:
        overeating hastens the poop; proportional to the species poop_limit
        like feed's own gauge line).  Canon's falling-underflow hunger-lapse
        push is absorbed by tuipet's crash-refill restructure (the refill IS
        the delay).  The per-pet calorieMax/MinMod metabolism rolls and the
        Over/Under CalorieLimitModWeight are all 0 at difficulty 0: data-dead."""
        value = int(round(value))
        if value > CALORIE_LIMIT and value > self.calories:
            self._poop_t = (getattr(self, "_poop_t", 0.0)
                            + self._poop_interval * ABOVE_MAX_CAL_BM
                            / max(1, self._phys().get("poop_limit", 64)))
        self.calories = _clamp(value, -CALORIE_LIMIT, CALORIE_LIMIT)

    def _set_obedience(self, value):
        """PhysicalState.setObedience (obedience audit 2026-07-06): any CHANGE
        is nudged once AGAINST the disposition (value -= disposition x 1 --
        the mirror image of setMood's nudge: a sunny pet takes every change a
        point lower, a sour one a point higher), then clamped to
        [0, MaxObedience 150].  The old raw mutations had no ceiling at all."""
        value = int(round(value))
        if value != self.obedience:
            value -= self._disposition() * OBEDIENCE_DISPO_COEF
        self.obedience = _clamp(value, 0, MAX_OBEDIENCE)

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
        """PhysicalState _currentMood: Depressed is a sticky STATE (checkDepressed's
        entry/exit rolls -- canon re-audit 2026-07; a mood threshold only biases the
        entry roll), the rest are value bands."""
        if self.depressed:
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
        """DVPet setEnergy, canon order (mood re-audit 2026-07-06): a drop INTO
        the red bills mood AND obedience scaled by the depth (dec - newEnergy)
        and FATIGUES an uninjured pet -- being pushed past empty is the
        over-exertion mechanic, not a flat sting.  Then the perfect-conditions
        bounce may save the step, and the clamp runs last (BOTTOMING OUT at
        the floor burns MinEnergyLifePenalty of life per hit)."""
        raw = int(round(value))
        if raw < self.energy and raw < 0:
            self._set_mood(self.mood - (NEGATIVE_ENERGY_MOOD_DEC - raw))
            self._set_obedience(self.obedience - (NEGATIVE_ENERGY_OBEDIENCE_DEC - raw))
            if not self.is_injured():
                self._fatigue()                  # canon fatigue(false)
        if raw < self.energy:
            raw = self._energy_bonus_save(raw)   # checkEnergyIncFromPerfectConditions
        if raw < -self.max_energy:
            self._burn_life(MIN_ENERGY_LIFE_PENALTY)     # setEnergy's floor penalty
        self.energy = _clamp(raw, -self.max_energy, self.max_energy)

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

    def is_toilet_trained(self):
        """PhysicalState.isToiletTrained: enough training uses + obedience +
        a stage that can go alone."""
        return (self.toilet_trained >= MIN_TOILET_USES_TO_TRAIN
                and self.obedience >= TOILET_TRAINED_OBED_MIN
                and self.stage in STAGE_CAN_AUTO_TOILET)

    def _toilet_train(self):
        """toiletTrain(): visits count toward training only while the stage
        still learns (InTraining) and the minimum isn't met yet."""
        if (self.toilet_trained < MIN_TOILET_USES_TO_TRAIN
                and self.stage in STAGE_CAN_TOILET_TRAIN):
            self.toilet_trained += 1

    def _toilet_for_poop(self):
        """doPoop's SelfToilet branch: the home Toilet (i:82) first, then the
        Port. Potty (i:83) -- each stocked use is one flush."""
        if not self.is_toilet_trained():
            return None
        if self.inventory.get("i:82", 0) > 0:
            return "i:82"
        if self.inventory.get("i:83", 0) > 0:
            return "i:83"
        return None

    def poop_urgent(self):
        """The manual-toilet / poop-dance window: the gauge is nearly full."""
        return self._poop_t >= TOILET_URGENT_FRAC * self._poop_interval

    def _toilet_visit(self, key, backlog=False, spend_use=True):
        """poopToilet: the poop lands IN the toilet -- canon poop(true) keeps
        the relief mood and the weight shed, skips the pile (and the floor-
        obedience ding, 0 in this column anyway).  Each visit spends one flush
        and applies the toilet's own mood/obedience blessing (canon useItem
        runs on every self-visit), then counts toward training."""
        if spend_use:
            self.take_item(key)
        self._set_mood(self.mood + POOP_MOOD_INC)
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self._set_weight(self.weight - wdec)
        if backlog:
            self._set_weight(self.weight - math.ceil(wdec / 2))
        e = data.consumable_by_key(key) or {}
        self._set_mood(self.mood + int(e.get("mood", 0) or 0))
        self._set_obedience(self.obedience + int(e.get("obedience", 0) or 0))
        self._toilet_train()
        self._toilet_event = key                  # the app plays poopToilet
        self._set_anim("toilet", 3.8)

    def _do_poop(self, backlog=False):
        """PhysicalState.poop: relief mood bump, weight shed, and a new sized pile
        added to the filth (capped at the _filth array length).  A big BACKLOG
        (gauge still >= bmMax/2 after the poop) makes the pile one size bigger --
        the only source of size-4 piles -- and sheds an extra half weight."""
        self._set_mood(self.mood + POOP_MOOD_INC)                 # PoopMoodInc
        wdec = min(int(self._base_weight() * POOP_WEIGHT_DEC_COEF), POOP_WEIGHT_LIMIT)
        self._set_weight(self.weight - wdec)
        size = self._poop_size()
        if backlog:
            size = min(4, size + 1)
            self._set_weight(self.weight - math.ceil(wdec / 2))
        self._add_filth(size)                    # capped; a full room upgrades a smaller pile

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
        self._calm_discipline_call()                # bedtime placates the tantrum (canon
        #                                             sleep-onset setDisciplineCall(false))
        self._lights_t = 0.0                        # setAsleep resets _callMinutesLights
        gain = max(1, getattr(self, "_sleep_energy_gain", 3))
        need = math.ceil(max(0, self.max_energy - self.energy) / gain) * 60.0
        self.awake_limit = _clamp(need, MIN_AWAKE_LIMIT, MAX_AWAKE_LIMIT)
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        self._set_anim("yawn", 1.8)

    def _wake(self):
        """setAsleep(false): the wake roll runs on EVERY rise -- natural,
        disturbed or lights-on alike (mood re-audit 2026-07-06; canon disturb()
        funnels through setAsleep(false) unconditionally, so even a grumbled
        wake takes its chances).  A full sleep wakes into the morning tiers; a
        NAP wakes with a +-NapWakeMoodDec swing on 2 rolls of the 5."""
        was_nap = self.nap
        self.asleep = False
        self.nap = False
        self.awake_lapse = 0.0
        self.sleep_limit = DAY_MINUTES - self.awake_limit
        if not self.lights:
            self.lights = True                      # wake: setLights(true)
        wake_anim = "wake"
        r = random.randrange(MORNING_MOOD_CHANCE)
        m = self.current_mood()
        if was_nap:
            if r == 0:
                self._set_mood(self.mood - NAP_WAKE_MOOD_DEC)
                wake_anim = "sad"                    # BadMorning: wakeUp(9)
            elif r == 1:
                self._set_mood(self.mood + NAP_WAKE_MOOD_DEC)
                wake_anim = "happy"                  # GoodMorning: wakeUp(5)
        else:
            # canon wakeUp poses vary with the morning: 7 normal / 5 good /
            # 9 bad / 6 terrible (birthday audit 2026-07-05: it always woke
            # on the plain pose)
            if r == 0:
                self._set_mood(self.mood + BAD_MORNING_MOOD.get(m, -10))
                wake_anim = "sad"                    # BadMorning: wakeUp(9)
            elif r == 1 and m == "Happy":
                self._set_mood(WORST_MORNING_MOOD)
                wake_anim = "surprise"               # TerribleMorning: wakeUp(6)
            elif r == 2:
                self._set_mood(self.mood + GOOD_MORNING_MOOD.get(m, 100))
                wake_anim = "happy"                  # GoodMorning: wakeUp(5)
        self._set_anim(wake_anim, 1.6)

    def _disturbed(self):
        """PhysicalState.disturb(): bothering a sleeper wakes it grumpy.  The
        bookkeeping (count, missed day, postpone, sick risks) only bills REAL
        sleep -- but the mood/spirit dec and the wake land on a NAP too (mood
        re-audit 2026-07-06: canon keeps them outside the !nap guard).  Real
        sleep: nearly-rested (or full energy) it just gets up; otherwise the
        sleep is POSTPONED: it drops back off in DisturbPostpone game-minutes,
        still owing the missed rest."""
        if not self.asleep:
            return "zzz..."
        nap, postponed = self.nap, False
        if not nap:
            self.disturb += 1
            self.mistake_day += 1                   # DisturbanceMissedDayChange
            rested = (self.awake_lapse >= FULL_AWAKE_DISTURB - self.restless * FULL_AWAKE_DISTURB_RESTLESS
                      or self.energy >= self.max_energy)
            if rested:
                self.sleep_lapse = 0.0
            else:
                postponed = True
                postpone = random.randint(*DISTURB_POSTPONE)
                self.sleep_lapse = max(0.0, self.sleep_limit - postpone / max(1, self._sleep_inc()))
                if self._in_sleep_window() is not None:
                    self._bed_postpone_t = float(postpone)   # a line pet re-sleeps by the clock
                # (the missed rest is repaid naturally: _fall_asleep re-sizes the
                # next sleep from the CURRENT energy debt, so nothing is carried)
            # a rough waking is a health hazard: an already-sick sleeper may
            # worsen, and from the DisturbLimitCheckSick'th disturb every poke
            # risks fresh illness (canon checkWorseSick / checkSick)
            self._check_worse_sick(DISTURB_WORSE_SICK_CHANCE)
            if self.disturb >= DISTURB_LIMIT_CHECK_SICK:
                self._check_sick(DISTURB_SICK_CHANCE)
        # DisturbMoodDec{,Restless,NotRestless}: a restless pet WANTED up
        self._set_mood(self.mood - DISTURB_MOOD_DEC.get(self.restless, 10))
        enth = {1: -1, 0: -2, -1: -3}.get(self.restless, -2)   # DisturbEnthusiasmDec*
        self._set_enthusiasm(self.enthusiasm + enth)
        self._wake()                                # setAsleep(false): the wake roll
        if nap:
            return "It stirs from its doze."
        if not postponed:
            return "It grumbles awake."
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

    def check_refused(self, food=None, attr=None, energy_change=0.0, item=None):
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
        elif item is not None:
            # refused(Item): medicine by its healing flags, the personality mods,
            # sick-only unwell, and the BOREDOM term -- a bored pet refuses toys
            # (itemInterest x RefuseInterestModCoefficient when the item bores)
            obey = 0.0
            if item.get("cured") or item.get("healed") or item.get("cure_lapse") or item.get("heal_lapse"):
                obey += REFUSE_MED_FACTOR * (1 - base)
            for trait, key in ((self.disposition, "t_disposition"),
                               (self.restless, "t_restless"), (self.glutton, "t_glutton")):
                fv = int(item.get(key, 0) or 0)
                if fv != 0:
                    obey += REFUSE_PERSONALITY_MATCH if fv == trait else REFUSE_PERSONALITY_UNMATCH
            obey += (REFUSE_UNWELL_SICK if self.sick else 0.0) * (1 - base)
            if int(item.get("interest_change", 0) or 0) > 0:
                obey += self.item_interest * REFUSE_INTEREST_MOD
            obey += mood_factor
            refused = r >= obed + obey
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

    def feed(self, food=None, assisted=False):
        """PhysicalState.feed -> applyFood: apply a food's FULL effect set, each
        scaled by DVPet's fullness modifier.  A hunger-food (Meat) refuses a full
        stomach; a strength-food (Protein/Vitamin, hunger 0) never fills, so it
        builds strength/DP even on a full pet -- the classic Meat/Protein split.
        assisted = DVPet assistantFeed (canRefuse=false): the same path minus
        the refusal roll -- a pet never turns down the hired help."""
        if (_g := self._guard()) is not None:
            return _g
        foods = data.load_foods()
        food = food or (foods[0] if foods else {"name": "Meat", "hunger": 1, "weight": 4, "mood": 5})
        self._last_meal_starving = self.hunger == 0          # eat(): wolfed down (decided PRE-meal)
        refused = False if assisted else self.check_refused(food=food)   # applyFood: checkRefused ...
        complied = self.check_compliant()                    # ... then the compliance is spent
        if refused:
            return f"{self.name} refuses to eat!"
        self._calm_discipline_call()                         # a meal placates the tantrum
        fills = int(food.get("hunger", 0)) > 0
        # a hunger-food on a full stomach -> too full (a glutton eats past FULL_HUNGER)
        if fills and self.hunger >= FULL_HUNGER and self.glutton <= 0:
            self._set_weight(self.weight + 1)
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
        # applyFood: modifier <= DisposeLeftoversMinModifier -> State.Munching --
        # the stuffed pet takes two bites and DROPS the rest (the eat fx reads it)
        self._last_meal_leftover = fills and modifier <= DISPOSE_LEFTOVERS_MIN

        def scaled(key):
            return math.ceil(food.get(key, 0) * modifier) if food.get(key, 0) > 0 else int(round(food.get(key, 0) * modifier))

        cap = OVEREAT_LIMIT if self.glutton > 0 else FULL_HUNGER
        self.hunger = _clamp(self.hunger + scaled("hunger"), 0, cap)
        self.strength = _clamp(self.strength + scaled("strength"), 0, 4)   # Protein builds Effort/DP
        if food.get("strength", 0) > 0:
            self.dp = min(DP_MAX, self.dp + 1)   # Pen20: 4 protein items refill the DP meter
        self._set_energy(self.energy + scaled("energy"))
        self._set_mood(self.mood + scaled("mood")           # foods.csv intrinsic mood (Cake +60, Veg -10)
                       + int(math.ceil(self._personality_mood(food) * modifier)))
        self._set_obedience(self.obedience + scaled("obedience"))
        self._set_enthusiasm(self.enthusiasm + scaled("enthusiasm"))
        if food.get("health"):                              # HP Chip: permanent trained-HP gain
            self.full_health = min(self.max_health(),
                                   self.full_health + math.ceil(food["health"] * modifier))
        # canon re-audit 2026-07: applyConsumable's remaining food effects --
        # the old flat calorie refill ignored the per-food Calories column
        # (setCaloriesAndChangeWeight: a rich meal buffers longer, and calories
        # rising while ALREADY positive fatten by FoodWeightChange)
        cal = scaled("calories")
        if cal > 0 and self.calories > 0:
            self._set_weight(self.weight + FOOD_WEIGHT_CHANGE)
        self._set_calories(self.calories + cal)   # a rich-meal OVERFLOW hastens the poop
        self.vaccine = max(0, self.vaccine + scaled("vaccine"))       # attribute foods
        self.data_power = max(0, self.data_power + scaled("data"))
        self.virus = max(0, self.virus + scaled("virus"))
        if food.get("seconds"):                             # lifespan foods (real-sec -> game /60)
            self.lifespan = max(0.0, self.lifespan + scaled("seconds") / 60.0)
        if food.get("sleep_lapse"):                         # bedtime nudge (Hot Milk)
            self.sleep_lapse = max(0.0, self.sleep_lapse + scaled("sleep_lapse"))
        t = food.get("temp", 0)
        if t and 0 <= self.temp + t <= 100:                 # MaxTemp guard, verbatim
            self.temp += math.ceil(t * modifier) if t > 0 else t
        self._set_weight(self.weight + math.ceil(food.get("weight", 1) * modifier))   # modifier-scaled, like canon
        # every meal advances the bowel gauge (applyFood: bmGauge += food.BMGauge):
        # eating more means pooping sooner, proportional to the species bmMax
        bm = int(food.get("bm", 0))
        if bm > 0:
            self._poop_t = getattr(self, "_poop_t", 0) \
                + self._poop_interval * bm / max(1, self._phys().get("poop_limit", 64))
        # checkDirtyEating: a meal amid the filth sours it, and each pile is a
        # sickness risk (worse 16%/pile if already sick, else sick 8%/pile)
        if self.poop > 0:
            self._set_mood(self.mood - DIRTY_EATING_MOOD_DEC)
            worse = self._check_worse_sick(DIRTY_EATING_WORSE_CHANCE * self.poop)
            got_ill = self._check_sick(DIRTY_EATING_SICK_CHANCE * self.poop)
            # checkDirtyEating: a COMPLIANT pet forced to eat amid the filth
            # and sickened by it resents you (obedience audit 2026-07-06) --
            # and the meal's categories sour hard (RankChangeSickForced)
            if (worse or got_ill) and complied:
                self._set_obedience(self.obedience + OBEDIENCE_CHANGE_SICK_FORCED)
                self._dec_food_ranks([c for c in (food.get("category") or "").split(";")
                                      if c in data.FOOD_CATEGORIES], RANK_SICK_FORCED)
        tier = self._eat_food(food.get("category", ""), complied)   # DVPet taste: fav/disliked/neutral
        self._last_meal_disliked = (tier == "disliked")      # eat(): disliked -> +9 grimace bite
        self._apply_nutrition(food, modifier)                # GoodNutrition macros (scaled)
        self._set_anim("eat", 1.4)
        tag = {"favorite": "  It loves it!", "disliked": "  It dislikes that."}.get(tier, "")
        return f"Fed {food['name']}.{tag}"

    def can_train(self):
        """canExercise (energy audit 2026-07-06): NO hard fatigue/energy gate --
        MinEnergyForActivity is -127 on the classic column (vacuous), and
        fatigue/sickness only SHADE the refusal roll (unwellMod) and the injury
        odds.  The roll itself fires at drill start (training.py), like canon's
        checkRefused inside canExercise.  The old hard gates were invented."""
        if (_g := self._guard()) is not None:
            return _g
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
        self._calm_discipline_call()                      # exercise() placates the tantrum
        self.exercise_today += 1                          # DVPet _exercise (incExerciseTime)
        self.stage_trainings += 1                         # LINES_SPEC TR gate: every attempt counts (Pen20)
        complied = self.check_compliant()                 # onExerciseFinish: checkCompliant
        strength0 = self.strength
        success = hits >= 2
        # canon re-audit 2026-07: onExerciseFinish calls exercise() BEFORE checking
        # success -- the Effort gauge, spirit costs, body costs and the fatigue
        # roll all land WIN OR LOSE.  (The old success-only +1 and the invented
        # obedience+1 were not canon; success grants the praise flag + power.)
        self.strength = _clamp(self.strength + 1, 0, 4)   # setExercise(+1), unconditional
        # DVPet onExerciseFinish adds +1 per drill, but the real device's stages last
        # real-DAYS (hundreds of trainings) while tuipet compresses them to ~2h. A flat
        # +1 can't reach the real-data attribute-power thresholds (digimon.csv median 50)
        # in a compressed stage, so good forms become unreachable. Scale the gain by drill
        # QUALITY to compensate for the clock -- same approach as the deferred enthusiasm
        # lapse. A perfect drill (3 hits) = +6, a solid one (2) = +4.
        gain = hits * TRAIN_POWER_PER_HIT if success else 0
        if game == "hp":
            attr = "Effort"
            self.mood_rank += NONE_TRAIN_MOOD_RANK   # NoneTrainingAttributeMoodRankChange
            if self.disposition == -1:
                # exercise() None-branch: a SOUR pet pays the fav-dec on the HP drill
                self._set_enthusiasm(self.enthusiasm - 1)
        else:
            attr = attribute or (self.attribute if self.attribute in ("Vaccine", "Data", "Virus") else "Vaccine")
            # BonusAttributePower under the compressed scale: canon's standard
            # +1 training award lands +1 extra (doubled) for a HAPPY pet
            # drilling its favoured attribute -- ours doubles the scaled
            # standard award the same way (mood re-audit 2026-07-06)
            if gain and self.current_mood() == "Happy" and attr == self._power_bonus_attr():
                gain *= 1 + BONUS_ATTRIBUTE_POWER
            if attr == "Vaccine":
                self.vaccine += gain
            elif attr == "Data":
                self.data_power += gain
            elif attr == "Virus":
                self.virus += gain
            # the drill drives the ATTRIBUTE taste ledger (taste/rank audit
            # 2026-07-06): the trained attribute warms; a FORCED drill sours it
            self._change_attr_rank(attr)
            if complied:
                self._dec_attr_rank(attr, RANK_TRAIN_FORCED)
            # exercise()'s enthusiasm branches key on the ledger's EMERGENT
            # favourite/disliked (the species attribute / seed stands in until
            # a real taste forms); the emergent disliked drags hard (-3, and a
            # forced drill of it adds -1)
            fav = self.favorite_attr or (self.attribute if self.attribute in self._ATTR3
                                         else self._phys().get("attr_pref", "None"))
            if attr == fav:
                self._set_enthusiasm(self.enthusiasm - 1)  # ExerciseFavAttributeEnthusiasmDec
            elif attr == self.disliked_attr:
                self._set_enthusiasm(self.enthusiasm + EXERCISE_DISLIKED_ATTR_ENTH
                                     + (ENTH_DISLIKE_FORCED if complied else 0))
            else:
                self._set_enthusiasm(self.enthusiasm - 2)  # ExerciseNotFavAttributeEnthusiasmDec
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
        if self._check_worse_sick(EXERCISE_WORSE_SICK_CHANCE) and complied:
            self._set_obedience(self.obedience + OBEDIENCE_CHANGE_SICK_FORCED)
        # canon ExerciseWeightDec = 0 (classic): drills do NOT shed flat weight.
        # The body cost is CALORIC (setCaloriesAndChangeWeight): an activity
        # decrement landing while ALREADY in deficit sheds ActivityWeightChange.
        if self.calories < 0:
            self._set_weight(self.weight - 1)             # ActivityWeightChange -1
        self._set_calories(self.calories - EXERCISE_CALORIE_DEC)   # ExerciseCalorieDec
        self._set_energy(self.energy - 1)               # ExerciseEnergyDec
        # setExercise: driving the Effort gauge past its LIMIT risks fatigue --
        # good nutrition softens the odds, the home's compatibility bends them.
        # Unconditional like the +1 itself (canon rolls whenever the gauge is
        # pushed past the cap, win or lose).
        if strength0 >= 4:
            h = self.habitat_obj()
            chance = GOOD_NUTRITION_FATIGUE_CHANCE if self.good_nutrition() else FATIGUE_CHANCE
            chance += FATIGUE_COMPAT_CHANGE * ((self.field in h["incompat_fields"])
                                               + (self.element in h["incompat_elements"])
                                               - (self.field in h["compat_fields"])
                                               - (self.element in h["compat_elements"]))
            if random.randrange(100) < chance:
                self._fatigue()
        if success:
            self._open_praise()                          # onExerciseFinish: setPraise(true)
        else:                                            # DVPet exercise-fail penalties
            self._set_mood(self.mood - 10)               # ExerciseFailMoodDec
            self._set_obedience(self.obedience - 1)      # ExerciseFailObedienceDec
        # checkExerciseInj: worsening first, then the fresh matrix roll (the
        # species aversion rides the WEAK tables)
        self._check_exercise_injury(complied, attr if attr in self._ATTR3 else None)
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
        self._calm_discipline_call()                         # canBattle placates the tantrum
        # canBattle (energy audit 2026-07-06): the refusal roll is the ONLY
        # gate -- MinEnergyForActivity is -127 on the classic column (vacuous)
        # and fatigue has no hard gate anywhere in canon; it shades the roll
        # (unwellMod -10) and the battle-injury odds instead.  A worn pet
        # fights worse and refuses more, but it CAN fight.
        if self.check_refused():                             # canBattle -> checkRefused
            return f"{self.name} refuses to fight!"
        return None

    def record_battle(self, won, enemy=None, free_style=None, low_health=False):
        """Resolve a finished battle (canon battleEnd; battle-math audit
        2026-07-06): compliance is SPENT here, the end cost is banded by the
        finishing HP (limping at/below half = double energy + calories), a
        SICK opponent is contagious, and the disposition factor shades every
        win/loss mood.  The battle passes its BAKED style so a mid-fight
        toggle can't split the bonus from the rewards."""
        style_free = self.free_style if free_style is None else free_style
        complied = self.check_compliant()                # battleEnd: checkCompliant
        surr_declined = getattr(self, "_surr_declined", False)   # one bout only
        self._surr_declined = False
        self.exercise_today += 1                         # incExerciseTime (the +1 effort
        #                                                  bump is 0 at difficulty 0)
        self.battles += 1
        self.stage_battles += 1                          # LINES_SPEC BTL gate (per-stage)
        self.battle_log = (self.battle_log + [1 if won else 0])[-15:]   # Pen20 rolling window
        if not style_free:
            self._set_obedience(self.obedience + BATTLE_FREE_OBED_INC)   # fighting under orders builds discipline
        # the end cost is banded by the FINISHING health: above half HP the
        # fight cost energy -1 / calories -1; limping out costs double
        if low_health:
            self._set_energy(self.energy - BATTLE_LOW_HP_ENERGY)
            self._set_calories(self.calories - BATTLE_CAL_LOW)
        else:
            self._set_energy(self.energy - BATTLE_HIGH_HP_ENERGY)
            self._set_calories(self.calories - BATTLE_CAL_HIGH)
        # checkBattleInj: worsening, then a fresh roll WIN OR LOSE (a loss
        # pads +50/1000); a fresh battle injury sours the opponent's attribute
        self._check_battle_injury(won, complied=complied,
                                  opp_attr=(enemy or {}).get("attribute"))
        # checkSick: a SICK opponent is contagious at the bout's end (PvP
        # ships the partner's real state), win or lose
        if (enemy or {}).get("sick"):
            self._check_sick(ENEMY_SICK_CHANCE)
        if won:
            self.wins += 1
            # lifetime wins (cross-generation, gates the mystery eggs) -- counted
            # HERE so every flow that resolves a battle counts: home key, adventure
            # encounters, tournaments, town cups, lobby.  Late import: persistence
            # imports pet at module top.
            from . import persistence as _persist
            total = _persist.wins_add(1)
            if total in egg_mod.win_eggs().values():     # a gate just crossed
                self.egg_unlock_note = "A mysterious egg appeared in the nursery!"
            if enemy:
                self.levels_fought.append(_enemy_level(enemy))
                if enemy.get("stage") in ("Ultimate", "Mega"):
                    self.mega_kills += 1                 # LINES_SPEC KO6 gate (DMX Stage-VI kills)
                    _persist.mega_kills_add(1)           # ...and the lifetime X-egg progress
            self._open_praise()                          # a win is praiseworthy (setPraise)
            # BattleWonMoodInc + BattleDispositionMoodFactor x disposition:
            # the -5 x dispo shade rides EVERY win/loss, not just orders-won
            self._set_mood(self.mood + 10 + BATTLE_DISPO_MOOD_FACTOR * self.disposition)
            if self._check_worse_sick(BATTLE_WON_WORSE_SICK) and complied:
                self._set_obedience(self.obedience + OBEDIENCE_CHANGE_SICK_FORCED)
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
                inc = 1
                # setPower's BonusAttributePower: a HAPPY pet's +1 in its
                # favoured attribute lands +2 (canon exact -- the win gain is
                # always the standard single point here)
                if self.current_mood() == "Happy" and dom == self._power_bonus_attr():
                    inc += BONUS_ATTRIBUTE_POWER
                if dom == "Vaccine":
                    self.vaccine += inc
                elif dom == "Data":
                    self.data_power += inc
                else:
                    self.virus += inc
                grew = f"  +{inc} {dom}"
            self._set_enthusiasm(self.enthusiasm - 3)    # BattleWonEnthusiasmDec
            if not style_free:                           # battleEnd: a win UNDER ORDERS is prouder
                self._set_mood(self.mood + ORDERS_WON_MOOD_INC
                               + BATTLE_DISPO_MOOD_FACTOR * -self.disposition)
            lo, hi = (enemy or {}).get("bits", (1, 5))
            gained = random.randint(lo, hi)
            self.bits += gained
            self._set_anim("happy", 2.0)
            return f"Victory! +{gained} bits{grew}"
        self._set_mood(self.mood - 20 + BATTLE_DISPO_MOOD_FACTOR * self.disposition)   # BattleLostMoodDec
        self._set_enthusiasm(self.enthusiasm - 6)    # BattleLostEnthusiasmDec
        self._set_obedience(self.obedience - 1)      # BattlesObedienceDec (a loss saps trust)
        self.mistake_day += BATTLE_LOST_MISSED_DAY   # BattleLostMissedDayChange
        if self._check_worse_sick(BATTLE_LOST_WORSE_SICK) and complied:
            self._set_obedience(self.obedience + OBEDIENCE_CHANGE_SICK_FORCED)
        if surr_declined:
            # it BEGGED to quit, you refused, it lost: obedience is SET to 10
            self._set_obedience(SURR_DECLINED_LOST_OBED)
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
        # canon re-audit 2026-07: DVPet's `_exercise` here is the EFFORT GAUGE
        # (strength hearts) -- the old port divided by drills-done-today
        ex = self.strength or 1                                        # _exercise!=0 ? _exercise : 1
        if self.energy >= 0:
            exercise_factor = base * (energy_ratio / ex)
        else:
            exercise_factor = base * (energy_ratio * ex)
        enth_factor = (self.enthusiasm * OBEDIENCE_ENTH_MOD) * (1 - base)
        total = exercise_factor + time_factor + mood_factor + unwell_factor + enth_factor
        return (base, mood_factor, total)

    # -- the pet-initiated surrender request (ClockTic onRoundEnd ->
    # checkSurrender; wired into battlescreen 2026-07-04) --
    def can_escape(self, enemy):
        """PhysicalState.canEscape: a power-weighted roll -- prob = nextInt(mine +
        theirs); escaped iff prob <= mine, the foe's side padded by
        BossEscapeChance 50 / RandomEscapeChance 10 (bosses hold you harder)."""
        mine = self.vaccine + self.data_power + self.virus + (self.full_health or 1)
        theirs = (enemy.get("vaccine", 0) + enemy.get("data_power", 0)
                  + enemy.get("virus", 0) + enemy.get("hp", 0)
                  + (50 if enemy.get("boss") else 10))     # Boss/RandomEscapeChance
        return random.randrange(max(1, mine + theirs)) <= mine

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
            self._set_obedience(self.obedience
                                - (SURR_EFFECT_REQ_OBED_DEC if surrender_val == 2 else SURR_EFFECT_OBED_DEC))
        if surrender_val == 2 and health < enemy_health:
            self._set_obedience(SURR_EFFECT_REQ_LOWHP_OBED)      # setObedience(15), verbatim (a SET, not +=)

    def surrender_reject(self):
        """ClockTic: the trainer refuses the pet's surrender request (surrender==2) and
        sends it back in — it sulks but obeys a touch more.  If it then LOSES,
        battleEnd SETS obedience to 10 (the declined-request grudge)."""
        self._set_mood(self.mood - SURR_REJECT_MOOD_DEC)
        self._set_obedience(self.obedience + SURR_REJECT_OBED_INC)
        self._surr_declined = True                       # consumed by record_battle

    # ---- discipline: praise / scold (PhysicalState) --------------------------
    def _open_praise(self):
        """A good deed opens a praise window (DVPet setPraise)."""
        if self.num != -1 and self.stage != "Egg":
            self.praise_flag, self.praise_window = True, 0

    def _open_scold(self):
        """A bad deed makes the pet act up: opens a scold window and marks it
        noncompliant.  Raised by the care-mistake events, battle misdeeds, and
        the periodic disciplineCall (_check_discipline_call, which also lights
        the discipline care light)."""
        if self.num != -1 and self.stage != "Egg":
            self.scold_flag, self.scold_window, self.compliance = True, 0, False

    def _calm_discipline_call(self):
        """setDisciplineCall(false) by any care that ISN'T the scold it demands
        (feed / item / praise / training / battle / bedtime): the tantrum is
        PLACATED -- obedience -10 (it learned acting up works), a smug mood +5,
        and the open scold window closes with it (mood re-audit 2026-07-06)."""
        if not self.discipline_call:
            return
        self.discipline_call, self._disc_call_t = False, 0.0
        self._set_obedience(self.obedience - DISCIPLINE_CALL_OBED_DEC)
        self._set_mood(self.mood + DISCIPLINE_CALL_MOOD_INC)
        self.scold_flag, self.scold_window = False, 0        # setScoldWindow(0)

    def _check_discipline_call(self):
        """checkDisciplineCall: on the DisciplineCallMin cadence, a chance for the pet to
        act up on its own (opening a scold window) — likelier when its needs go unmet,
        rarer the more obedient it is.  Obedient grown pets are exempt, and a pet on
        the EDGE OF SLEEP never tantrums (canon: toNapSleepLapse about to doze, or
        bedtime pressure about to tip; sleep audit 2026-07-06)."""
        if self.scold_flag or self.praise_flag:          # checkCall(): already mid-discipline
            return
        if (self.sleep_lapse + 1 >= self.sleep_limit
                or (not self.lights
                    and getattr(self, "_to_nap_t", 0.0) + 1 >= self._calc_to_nap())):
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
            self.discipline_call = True          # the care light comes on
            self._disc_call_t = 0.0

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
        self._burn_life(SICK_LIFE_DEC)          # sicken(): every illness costs life
        self.sick_length = random.randint(MIN_SICK_LENGTH, MAX_SICK_LENGTH) * SICK_LAPSE_MIN
        self.sick_length = max(SICK_LAPSE_MIN, self.sick_length - self._affinity() * SICK_LAPSE_MIN)
        self._set_mood(self.mood - SICK_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + SICK_ENTH_CHANGE)
        # canon sours the HOUR it fell ill in (timeRanks -RankChangeSick),
        # mapped onto the tuned time ledger's +-90 scale
        ph = self.day_phase
        self.time_pref[ph] = _clamp(self.time_pref.get(ph, 0) - RANK_TIME_SICK, -90, 90)

    def _worsen_sick(self):
        """PhysicalState.checkWorseSick (effect body): an already-sick pet gets worse --
        the illness drags on one lapse longer, with mood/obedience/spirit costs, a
        fresh mess -- and the WorseSickLifeDec burn (canon re-audit 2026-07: the
        old omission note is gone; every worsening costs 3 real-hours of life)."""
        self._burn_life(WORSE_MALADY_LIFE_DEC)
        self._set_obedience(self.obedience + WORSE_MALADY_OBED_DEC)
        self._set_mood(self.mood + WORSE_MALADY_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + SICK_ENTH_CHANGE)  # WorseSickEnthusiasmChange == -1
        self.sick_length += SICK_LAPSE_MIN                        # setSickLength(_sickLength + 1) = +1 lapse
        self._start_poop()

    def _injure(self):
        """PhysicalState.injure: take an injury for MinInjLength..MaxInjLength recovery
        lapses; the cumulative injury count (used by evolution) also ticks up.
        Every injury burns InjuryLifeDec of life (canon re-audit 2026-07)."""
        self.injuries += 1
        self._burn_life(INJURY_LIFE_DEC)
        rolled = random.randint(MIN_INJ_LENGTH, MAX_INJ_LENGTH) * INJ_LAPSE_MIN
        rolled = max(INJ_LAPSE_MIN, rolled - self._affinity() * INJ_LAPSE_MIN)   # habitat-compat length mod
        self.inj_length = max(self.inj_length, rolled)
        self._set_mood(self.mood - INJ_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + INJ_ENTH_CHANGE)
        # InjuryEnergyDec (sickness/injury audit 2026-07-06): a fresh injury
        # saps a bar -- inj_length is already set, so the red-energy fatigue
        # trigger's !isInj guard holds like canon's
        self._set_energy(self.energy - INJURY_ENERGY_DEC)
        ph = self.day_phase                                # timeRanks -RankChangeInjury
        self.time_pref[ph] = _clamp(self.time_pref.get(ph, 0) - RANK_TIME_SICK, -90, 90)

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
            self._check_worse_sick(VITAMIN_WORSE_SICK_CHANCE)
            self._advance_bm(BAD_VITAMIN_BM_INC)
            self._set_mood(self.mood - BAD_VITAMIN_MOOD_DEC)
            self._burn_life(BAD_VITAMIN_LIFE_DEC)
            if not self.sick and random.randrange(REFUSE_CHANCE) < VITAMIN_OVERFED_SICK_CHANCE:
                self._sicken()                               # vitaminOverfedSickChance
            self._start_poop()
            self._set_anim("refuse", 1.5)                    # Bad_Health_Jeering
        self.vitamin_lapse = VITAMIN_HOURS

    def _worsen_injury(self):
        """PhysicalState.worsenedInjury: the injury gets worse -- extended, with mood/
        obedience/energy/spirit costs and the WorseInjuryLifeDec burn."""
        self._burn_life(WORSE_MALADY_LIFE_DEC)   # WorseInjuryLifeDec (canon re-audit)
        self._set_obedience(self.obedience + WORSE_MALADY_OBED_DEC)
        self._set_mood(self.mood + WORSE_MALADY_MOOD_DEC)
        self._set_enthusiasm(self.enthusiasm + WORSE_INJ_ENTH_CHANGE)
        self.inj_length += random.randint(MIN_INJ_LENGTH, MAX_INJ_LENGTH) * INJ_LAPSE_MIN
        self._set_energy(self.energy - WORSE_INJ_ENERGY_DEC)

    def _compat_inj_change(self):
        """getCompatibilityInjChange: the home shifts injury odds +-1 per axis
        (a compatible field/element = sturdier)."""
        h = self.habitat_obj()
        return ((self.field in h["incompat_fields"])
                + (self.element in h["incompat_elements"])
                - (self.field in h["compat_fields"])
                - (self.element in h["compat_elements"]))

    def _inj_matrix_roll(self, table, bound, inj_chance):
        """The shared weight x vitamin injury matrix (checkExerciseInj /
        checkBattleInj / calcWorse*Inj all ride it): bad weight is Over OR
        Under; a vitamin blunts it (sickness/injury audit 2026-07-06)."""
        healthy = evolution.weight_category(self.weight, self._base_weight()) == "Healthy"
        key = ("good_" if healthy else "bad_") + ("v" if self.has_vitamin() else "nv")
        return random.randrange(bound) < table[key] + inj_chance

    def _neg_energy_mod(self, coef):
        """-(energy x coef) while in the red: exhaustion pads injury odds."""
        return int(-(self.energy * coef)) if self.energy < 0 else 0

    def _check_exercise_injury(self, complied=False, attr=None):
        """checkExerciseInj: EVERY drill risks worsening, then a fresh injury --
        the old 'overweight -> 50%' paraphrase is gone (canon baseline is
        1/1000 healthy, 10/1000 off-weight, vitamin-blunted, padded by age /
        fatigue / exhaustion / an incompatible home).  Drilling the species'
        ATTRIBUTE AVERSION rides the harsher WEAK tables."""
        weak = attr is not None and attr == self._phys().get("attr_aversion", "None")
        self._check_worse_injury("exercise", complied=complied, weak=weak)
        if self.is_injured():
            return
        inj = ((INJ_GERIATRIC if self.is_geriatric else 0)
               + (FATIGUE_MOD * INJ_FATIGUE_COEF if self.is_fatigued() else 0)
               + self._neg_energy_mod(INJ_NEG_ENERGY_COEF)
               + self._compat_inj_change())
        if self._inj_matrix_roll(INJ_WEAK_EXERCISE if weak else INJ_EXERCISE, INJ_CHANCE, inj):
            self._injure()
            if complied:
                self._set_obedience(self.obedience + OBED_INJ_FORCED)

    def _check_battle_injury(self, won, complied=False, opp_attr=None):
        """checkBattleInj: worsening first, then a fresh roll -- WIN OR LOSE
        (a loss pads +50/1000, being a baby or an elder +10, fatigue +100).
        The old loss-only 30% flat roll is gone.  A fresh battle injury also
        SOURS the opponent's attribute (changeBattleRanks: won -1 / lost -5)."""
        self._check_worse_injury("battle", won=won, complied=complied)
        if self.is_injured():
            return
        inj = ((BATTLE_INJ_BAD_AGE if (self.is_geriatric
                                       or self.stage in ("Fresh", "InTraining")) else 0)
               + (FATIGUE_MOD * BATTLE_INJ_FATIGUE_COEF if self.is_fatigued() else 0)
               + (0 if won else BATTLE_INJ_LOSS)
               + self._neg_energy_mod(BATTLE_INJ_NEG_ENERGY_COEF)
               + self._compat_inj_change())
        if self._inj_matrix_roll(INJ_BATTLE, BATTLE_INJ_CHANCE, inj):
            self._injure()
            self._dec_attr_rank(opp_attr, RANK_INJ_BATTLE_WON if won else RANK_INJ_BATTLE_LOST)
            if complied:
                self._set_obedience(self.obedience
                                    + (OBED_INJ_BATTLE_WON if won else OBED_INJ_BATTLE_LOST))

    def _check_worse_injury(self, kind, won=True, complied=False, weak=False):
        """calcWorse{Exercise,Battle}Inj: pushing an already-injured pet can
        worsen the injury.  kind: "exercise" / "battle" / "travel" -- canon's
        checkWorseTravelInj rides the BATTLE table with won=True (the old port
        used the exercise table for walks).  The additive term (age, fatigue,
        exhaustion, home) was missing entirely.  weak=True (drilling the
        species aversion) rides the harsher WorseWeakInjury table."""
        if not self.is_injured():
            return
        if kind == "exercise":
            table = WORSE_INJ_WEAK if weak else WORSE_INJ_EXERCISE
            inj = ((WORSE_INJ_GERIATRIC if self.is_geriatric else 0)
                   + (FATIGUE_MOD if self.is_fatigued() else 0))
        else:                                        # battle / travel share a table
            table = WORSE_INJ_BATTLE
            inj = ((WORSE_BATTLE_INJ_BAD_AGE if (self.is_geriatric
                                                 or self.stage in ("Fresh", "InTraining")) else 0)
                   + (FATIGUE_MOD if self.is_fatigued() else 0)
                   + (0 if won else WORSE_BATTLE_INJ_LOSS))
        inj += self._neg_energy_mod(WORSE_INJ_NEG_ENERGY_COEF) + self._compat_inj_change()
        if self._inj_matrix_roll(table, WORSE_INJ_CHANCE, inj):
            self._worsen_injury()
            if complied:
                self._set_obedience(self.obedience
                                    + (OBED_INJ_FORCED if kind == "exercise"
                                       else (OBED_INJ_BATTLE_WON if won else OBED_INJ_BATTLE_LOST)))

    def _check_sick(self, target):
        """checkSick(target, bound): the bound is SickChance shaped by the
        home (+-5/axis, compatible = safer) and old age (-25 = frailer)."""
        if self.sick or target <= 0:
            return False
        h = self.habitat_obj()
        bound = (SICK_CHANCE_BOUND
                 + SICK_COMPAT_CHANGE * ((self.element in h["compat_elements"])
                                         + (self.field in h["compat_fields"])
                                         - (self.field in h["incompat_fields"])
                                         - (self.element in h["incompat_elements"]))
                 - (SICK_GERIATRIC_FACTOR if self.is_geriatric else 0))
        if random.randrange(max(1, bound)) < target:
            self._sicken()
            return True
        return False

    def _check_worse_sick(self, target):
        """checkWorseSick(prob): fatigue pads the target (+FatigueMod), old
        age thins the bound (-25)."""
        if not self.sick or target <= 0:
            return False
        target += FATIGUE_MOD if self.is_fatigued() else 0
        bound = WORSE_SICK_BOUND - (WORSE_SICK_GERIATRIC if self.is_geriatric else 0)
        if random.randrange(max(1, bound)) < target:
            self._worsen_sick()
            return True
        return False

    def _fatigue(self):
        """PhysicalState.fatigue: the pet collapses from over-exertion — a heavy one-time
        mood/energy/spirit hit (worse if it was already fatigued), then it must rest the
        fatigue length off (FatigueMin..FatigueMax game-min)."""
        already = self.is_fatigued()
        self.mistake_day += 1                    # FatigueMissedDay
        # FatigueLifeDec (+ the geriatric surcharge) -- canon re-audit 2026-07:
        # the fatigue arc had documented this hit as omitted
        self._burn_life(FATIGUE_LIFE_DEC
                        + (GERIATRIC_FATIGUE_LIFE_DEC if self.is_geriatric else 0.0))
        self.fatigue_length = max(FATIGUE_MIN, random.randint(FATIGUE_MIN, FATIGUE_MAX) - self._affinity())   # habitat-compat length mod
        # canon fatigue() writes the energy dec RAW (_energy -= dec, never
        # setEnergy) -- routing it through _set_energy would recurse through
        # the fatigue trigger it now carries (mood re-audit 2026-07-06)
        self.energy = _clamp(self.energy - FATIGUE_ENERGY_DEC, -self.max_energy, self.max_energy)
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
        self._calm_discipline_call()          # canon praise() placates the tantrum first
        self._set_mood(self.mood + (PRAISE_LOW_DISP_MOOD_INC if self._disposition() < 0
                                    else PRAISE_HIGH_DISP_MOOD_INC))
        if not self.compliance:
            self._set_obedience(self.obedience - PRAISE_NONCOMPLIANT_OBED_DEC)
        if self.scold_flag and not self.praise_flag:          # mis-praised a misbehaving pet
            self._set_mood(self.mood + PRAISE_SCOLD_MOOD_INC)
            self._set_enthusiasm(PRAISE_SCOLD_ENTH)
            self._set_obedience(self.obedience - PRAISE_SCOLD_OBED_DEC)
            self.scold_flag, self.scold_window = False, 0
            self._set_anim("surprise", 1.6)
            return "It was misbehaving — the praise only spoiled it."
        if self.praise_flag:                                  # well-timed praise
            self._set_obedience(self.obedience + CORRECT_PRAISE_OBED[self._disposition()])
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
        self._set_obedience(self.obedience + SCOLD_OBED_INC)
        self._set_mood(self.mood - (SCOLD_LOW_OBED_MOOD_DEC if self.obedience < SCOLD_HIGH_OBED_MOOD
                                    else SCOLD_HIGH_OBED_MOOD_DEC))
        if self.praise_flag and not self.scold_flag:          # mis-scolded a good pet
            self._set_mood(self.mood - SCOLD_PRAISE_MOOD_DEC)
            self._set_enthusiasm(self.enthusiasm - SCOLD_PRAISE_ENTH_DEC)
            self._set_obedience(self.obedience + SCOLD_PRAISE_OBED[self._disposition()])
            self.praise_flag, self.praise_window = False, 0
            self._set_anim("sad", 1.8)
            msg = "It did nothing wrong — that scolding was unfair."
        elif self.scold_flag:                                 # well-timed scold
            self._set_enthusiasm(self.enthusiasm + CORRECT_SCOLD_ENTH)
            self._set_obedience(self.obedience + CORRECT_SCOLD_OBED[self._disposition()])
            self.scold_flag, self.scold_window, self.compliance = False, 0, True
            self.refused = False                              # setRefused(false): back in line
            self._set_anim("angry", 1.8)
            msg = f"{self.name} takes the lesson to heart."
        else:
            self._set_enthusiasm(self.enthusiasm + SCOLD_ENTH)
            self._set_anim("angry", 1.6)
            msg = f"You scold {self.name}."
        # scoldDisciplineCall, LAST like canon: answering the tantrum earns the
        # +2 -- and its compliance=false overrides the correct-scold's true
        # (the tantrum spent the goodwill even though you handled it right)
        if self.discipline_call:
            self.discipline_call, self._disc_call_t = False, 0.0
            self.compliance = False
            self._set_obedience(self.obedience + DISCIPLINE_CALL_SCOLD_OBED_INC)
        return msg

    def clean(self):
        """PhysicalState.clean: sweeping real filth lifts mood (CleanMoodInc)
        AND builds obedience, disposition-shaded (CleanObedienceInc 1 / sunny 2
        / sour 0) -- diligent housekeeping is one of the honest obedience
        earners (clean audit 2026-07-05; it was mood-only)."""
        if (_g := self._guard()) is not None:
            return _g
        if not self.poop:
            return "Nothing to clean."
        n, self.poop = self.poop, 0
        self.poop_sizes = []                        # clearFilth()
        self._set_mood(self.mood + CLEAN_MOOD_INC)
        self._set_obedience(self.obedience + CLEAN_OBED_INC[self._disposition()])
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
        complied = self.check_compliant()
        if refused:
            return f"{self.name} spits out the medicine!"
        if self.med_lapse > 0:                               # getMed(): double dose
            self.mistake_day += 1                            # BadMedMissedDayChange
            self._burn_life(BAD_MED_LIFE_DEC)
            self._advance_bm(BAD_MED_BM_INC)
            # rankChangeSick (+Forced when its compliance was spent): a
            # double-dosed pet grows to DISLIKE medicine (heal audit 2026-07-05)
            ding = RANK_CHANGE_SICK + (RANK_CHANGE_SICK_FORCED if complied else 0)
            self.food_ranks["Med"] = _clamp(self.food_ranks.get("Med", 0) - ding,
                                            RANK_MIN, RANK_LIMIT)
            if self.food_ranks["Med"] <= RANK_MIN:
                self.disliked_food = "Med"
            self._start_poop()
            self._set_anim("refuse", 1.5)                    # Bad_Health_Jeering
            return "A double dose — that was poison!"
        self._set_mood(self.mood + int(med.get("mood", -10)))          # it tastes awful
        self.sick_length = max(0.0, self.sick_length
                               + med.get("cure_lapse", -2) * SICK_LAPSE_MIN)
        if self.sick_length == 0:
            self.sick = False                                # the dose finished it off
        self._set_mood(self.mood + CURED_MOOD_BONUS // MAX_SICK_LENGTH)
        self._set_obedience(self.obedience + CURED_OBED_BONUS // MAX_SICK_LENGTH)
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
        self._set_obedience(self.obedience + CURED_OBED_BONUS // MAX_INJ_LENGTH)
        self.bandage_lapse = BANDAGE_HOURS
        self._set_anim("heal", 1.5)
        return ("All patched up!" if self.inj_length == 0
                else f"{self.name} is bandaged — it needs rest now.")

    def _growth_period(self):
        """The growth curve's total: egg + every stage through the current one
        (canon _growthPeriod; the longevity leg credits life lived past it)."""
        order = ("Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega")
        total = float(self.EGG_DURATION)
        for st in order:
            total += self.STAGE_DURATION.get(st, 0)
            if st == self.stage:
                break
        return total

    def _is_failed_form(self):
        """isFilthyEvol: the current form is a SpecialEvolution=Failed one."""
        r = data.load_requirements().get(self.num, {})
        return (r.get("special") or "None") == "Failed"

    def final_care_grade(self):
        """careBonusOnReset: grade the ending life.  Runs at death AFTER the
        Digimemory etch (which spends the bonus); the result seeds the next
        generation's evol_bonus."""
        b = self.evol_bonus
        b = b - self.care_mistakes if self.care_mistakes > 0 else b + 1
        m = self.current_mood()
        if m == "Happy":
            b += 1
        elif m != "Neutral":
            b -= 1
        if self.obedience > BONUS_INC_OBEDIENCE:
            b += 1
        elif self.obedience < BONUS_DEC_OBEDIENCE:
            b -= 1
        if self.battles and (self.wins / self.battles * 100.0) >= BONUS_INC_WIN_RATE:
            b += 1
        # longevity: whole days lived past the growth curve (negative if short)
        b += int((self.age_seconds - self._growth_period()) // DAY_MINUTES)
        st = BONUS_STAGE.get(self.stage)
        if st:
            base, attr_bar, battle_bar = st
            b += base
            if self.stage == "Champion" and not self._is_failed_form():
                b += 1
            if self.vaccine + self.data_power + self.virus >= attr_bar:
                b += 1
            if self.battles > battle_bar:
                b += 1
        return max(0, b)

    def make_digimemory(self):
        """setNewDigimemory, the dying pet's side: with a care bonus in hand, etch
        Va/D/Vi = floor(power * bonus * 0.01) and +1 bonus-hour of lifespan into
        the Digimemory payload; the bonus is spent.  Returns None with no bonus
        (DVPet onDie only enters UnlockInheritance when _bonus > 0)."""
        if self.evol_bonus <= 0:
            return None
        b = self.evol_bonus
        mem = {"name": self.name, "num": self.num,
               "vaccine": int(self.vaccine * b * DIGIMEMORY_ATTR_COEF),
               "data": int(self.data_power * b * DIGIMEMORY_ATTR_COEF),
               "virus": int(self.virus * b * DIGIMEMORY_ATTR_COEF),
               "seconds": DIGIMEMORY_LIFE_INC * b}
        self.evol_bonus = 0
        return mem

    def set_auto_care(self, on):
        """SpriteAnim's Set_AutoCare switch -> PhysicalState.setAutoCare: hiring
        the assistant also rolls WHICH Digimon answers, from the digimon.csv
        CanAssist pool (Evolution.getRandomAssistDigimon)."""
        if self.dead:
            return "It rests now — press N for a new egg."
        self.auto_care = bool(on)
        if self.auto_care:
            pool = data.assist_pool()
            self.assistant_num = random.choice(pool) if pool else -1
            _, by_num = data.load_sprites()
            name = (by_num.get(self.assistant_num) or {}).get("name", "The assistant")
            return f"{name} is on duty."
        return "The assistant was dismissed."

    def _tick_auto_care(self, dt):
        """PhysicalState.checkAutoCare, one game-min cadence.  The hourly retainer
        bills first (unpaid -> off duty); then at most one visit per spacing --
        awake: filth > hunger > strength; asleep: filth > a lit room (unless the
        Futon is active, DVPet's !isFuton()).  doAutoCare also walks off duty when
        the pet cannot afford the NEXT visit.  ADAPTATION: DVPet charges when the
        assistant animation ends; a headless tuipet pet applies state (and the
        processAutoCarePrice fee + bond costs) here in the tick, and the app-side
        assistant fx is pure presentation via the assist_event mailbox."""
        if not self.auto_care:
            return
        self._ac_pay = getattr(self, "_ac_pay", 0.0) + dt
        while self._ac_pay >= AUTO_CARE_PAYMENT_MIN:
            self._ac_pay -= AUTO_CARE_PAYMENT_MIN
            hourly = AUTO_CARE_HOUR_PRICE.get(self.stage, 0)
            if self.bits < hourly:
                self.auto_care = False
                self.assist_note = "The assistant left — the retainer went unpaid."
                return
            self.bits -= hourly
        self._ac_cool = max(0.0, getattr(self, "_ac_cool", 0.0) - dt)
        if self._ac_cool > 0:
            return
        act = None
        if not self.asleep:
            if self.poop > 0:
                act = "clean"
            elif self.hunger == 0:
                act = "feed"
            elif self.strength == 0:
                act = "strength"
        else:
            if self.poop > 0:
                act = "clean"
            elif self.lights and self.effect_id != 0:   # !isFuton(): the Futon already holds the night
                act = "lights"
        if act is None:
            return
        price = AUTO_CARE_VISIT_PRICE.get(self.stage, 0)
        if self.bits < price:                            # doAutoCare: can't cover the visit
            self.auto_care = False
            self.assist_note = "The assistant left — it couldn't cover a visit."
            return
        piles, sizes = self.poop, list(self.poop_sizes)
        if act == "clean":
            # Assistant_Clean -> onClean: the standard clean, minus YOUR wash pose
            self.poop, self.poop_sizes = 0, []
            self._set_mood(self.mood + 6)                # CleanMoodInc
            self._filth_t = 0                            # mess handled: the filth call resets
        elif act in ("feed", "strength"):
            fid = AUTO_CARE_HUNGER_FOOD if act == "feed" else AUTO_CARE_STRENGTH_FOOD
            food = data.consumable_by_key(f"f:{fid}")
            if food is None:
                return
            self.feed(food, assisted=True)               # assistantFeed: the full path, no refusal
        elif act == "lights":
            self.lights = False                          # Assistant_Lights -> onLights
        # processAutoCarePrice: the visit fee, and the bond cost of hired care
        self.bits -= price
        self._set_mood(self.mood + AUTO_CARE_MOOD)
        self._set_obedience(self.obedience + AUTO_CARE_OBEDIENCE)
        self._set_enthusiasm(self.enthusiasm + AUTO_CARE_ENTHUSIASM)
        self._ac_cool = AUTO_CARE_VISIT_SPACING
        self.assist_event = (act, piles, sizes)          # the app plays the visit

    def toggle_lights(self):
        """The lights button (DVPet setLights): toggles the room light ONLY. The pet
        sleeps and wakes on its own schedule -- this does not force sleep or wake."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        self.lights = not self.lights
        if self.lights and self.asleep and self.nap and self.effect_id != 0:
            # lightSwitch: lights ON rouses a NAPPING pet (deep sleep ignores it;
            # sick or injured, the lost doze pushes bedtime a minute closer).
            # canon !isFuton() (lights audit 2026-07-05): an active Futon
            # (effect_id 0, the same check auto-care honours) shields the nap
            if self.sick or self.is_injured():
                self.sleep_lapse += 1
            self._wake()                         # a nap wake rolls +-NapWakeMoodDec
            return "Lights on — up from its nap."
        if self.lights and self.asleep and self.nap:
            return "Lights on — the futon keeps it dozing."
        return "Lights off." if not self.lights else "Lights on."

    def play(self):
        if (_g := self._guard()) is not None:
            return _g
        # tuipet's Play button maps onto PhysicalState.spoil(): setMood(+SpoilMoodInc)
        # AND setObedience(-SpoilObedienceDec) -- a real tradeoff (happier now, but the
        # pet gets cheekier).  The animation is DVPet's jumping()/playing(): the pet
        # bounces on poses 1<->5 (ROLES["play"]), rendered as the "play" hop fx.
        self._set_mood(self.mood + SPOIL_MOOD_INC)
        self._set_obedience(self.obedience - SPOIL_OBEDIENCE_DEC)
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
        if self.bits < price:                # gate only: the cap must veto first
            return "Not enough bits."
        key = entry["key"]
        cap = entry.get("max_uses") or 99
        if self.inventory.get(key, 0) >= cap:
            return f"Can't carry more {entry['name']} (max {cap})."
        self.spend_bits(price)
        slot["stock"] -= 1
        # canon incQuantity adds UsesPerItem per purchase (a Toilet refill is
        # 100 flushes, a Potty 1), clamped at MaxUses (toilet audit 2026-07-05)
        self.inventory[key] = min(cap, self.inventory.get(key, 0)
                                  + int(entry.get("uses_per", 1) or 1))
        return f"Bought {entry['name']}."

    def sell(self, entry):
        """Resell one from the bag at price/DefaultResellFactor (unsellable at 0)."""
        key = entry["key"]
        if self.inventory.get(key, 0) <= 0:
            return "None to sell."
        val = shop.resell_price(entry)
        if val <= 0:
            return f"{entry['name']} can't be resold."
        self.take_item(key)
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
            self._burn_life(BONUS_LIFE_DEC)
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

    def take_item(self, key, n=1):
        """Spend n from the bag, dropping the key at zero -- add_item's mirror
        (this decrement lived in four hand-rolled copies; refactor 2026-07-05)."""
        left = self.inventory.get(key, 0) - n
        if left <= 0:
            self.inventory.pop(key, None)
        else:
            self.inventory[key] = left

    def spend_bits(self, price):
        """The affordability gate + deduction in ONE place (the 'Not enough
        bits.' guard lived in four copies).  True when paid."""
        if self.bits < price:
            return False
        self.bits -= price
        return True

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

    def _apply_item_stats(self, e, mod):
        """The canon applyItem stat core, shared by the generic path AND the
        special branches that used to skip it (energy audit 2026-07-06: the
        X-Program applied NONE of its hunger -10 / strength -13 / energy -0.8 /
        spirit -10 / mood -300, and the Digimentals skipped their -0.66 energy
        price).  A FRACTIONAL energy is a share of maxEnergy."""
        def _sc(v):
            return math.ceil(v * mod) if v > 0 else int(round(v * mod))
        if e["hunger"]:
            self.hunger = _clamp(self.hunger + _sc(e["hunger"]), 0, 4)
            self.calories = CALORIE_LIMIT               # food refills the calorie buffer
        # applyConsumable: the consumable's mood is shaped by personality tags
        self._set_mood(self.mood + _sc(e["mood"]) + _sc(self._personality_mood(e)))
        self._set_enthusiasm(self.enthusiasm + _sc(e.get("enthusiasm", 0)))
        # canon applyItem scales weight by the modifier like every other stat
        # (PhysicalState:3502 ceil(item.getWeight() x modifier))
        self._set_weight(self.weight + _sc(e["weight"]))
        if e["energy"]:
            ev = e["energy"]
            amt = math.ceil(ev * self.max_energy * mod) if ev != int(ev) else _sc(ev)
            self._set_energy(self.energy + amt)
        if e["strength"]:
            self.strength = _clamp(self.strength + _sc(e["strength"]), 0, 4)
        # canon scales obedience too (PhysicalState:3428) -- the old "obedience
        # is UNscaled" note misread the decompile (weight audit 2026-07-06)
        self._set_obedience(self.obedience + _sc(e["obedience"]))
        self.vaccine = max(0, self.vaccine + _sc(e["vaccine"]))
        self.data_power = max(0, self.data_power + _sc(e["data"]))
        self.virus = max(0, self.virus + _sc(e["virus"]))
        # canon applyItem: a Disposition item nudges the MOOD RANK (the
        # tracker the Champion re-roll cashes in), scaled like every stat
        self.mood_rank += _sc(int(e.get("t_disposition", 0) or 0))

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
        is_item = key.startswith("i:")
        # canon: an ItemEvol item's fractional energy price feeds the
        # AFFORDABILITY auto-refuse (a pet that can't pay the Digimental's
        # -0.66 x max refuses, exactly like jogress)
        ev = e.get("energy", 0)
        echange = ev if (e.get("action") == "ItemEvol" and ev != int(ev)) else 0.0
        refused = (self.check_refused(item=e, energy_change=echange)
                   if is_item else self.check_refused(food=e))
        # checkRefused's compliant-else: a COMPLIANT pet cannot refuse an ITEM,
        # but it cooperates grudgingly -- the item lands at WeakConsumableCoefficient
        # strength (0.1), except the Digimemory and healing items (Inherit/Recover)
        weak = (is_item and self.compliance
                and e.get("action") not in ("Inherit", "Recover")
                and not (e.get("cured") or e.get("healed") or e.get("cure_lapse") or e.get("heal_lapse")))
        self.check_compliant()                       # ...; checkCompliant
        if refused:
            return f"{self.name} wants nothing to do with it!"
        self._calm_discipline_call()                 # useItem placates the tantrum
        self.take_item(key)
        if e.get("special") == "xantibody":
            # canon runs applyItem for the X-Program too (PhysicalState:3323/
            # 3326): the sample is BRUTAL -- hunger -10, strength -13, energy
            # -0.8 x max, spirit -10, mood -300 -- on top of the life price
            self._apply_item_stats(e, WEAK_CONSUMABLE_COEF if weak else 1.0)
            self._set_anim("happy", 1.5)
            if key == "i:14":
                if self.x_antibody == "None":
                    # the SURVIVAL roll (death/rebirth audit 2026-07-06): an
                    # unmarked pet survives the sample 1 in 1000 -- otherwise
                    # it dies on the spot and the mash can't bring it back
                    # (savedFromDeath = 127; the item warns "if it survives")
                    if random.randrange(X_SURVIVAL_BOUND) >= X_SURVIVAL_TARGET:
                        self.saved_from_death = X_SAVE_BLOCK
                        self._die("the X-Program")
                        return "The X-Program was too much for it..."
                    # it SURVIVED: xEvolve charges its price in LIFE --
                    # 86400/nextInt(7) real-sec (/60 scale; a 0 draw is free),
                    # canon calcXAntibodyLifeDec verbatim
                    d = random.randrange(X_LIFE_DEC_BOUND)
                    if d:
                        self._burn_life(X_LIFE_DEC / d)
                self._set_xantibody("Permanent")
                return "X-Program complete! The X-Antibody is permanent."
            self._set_xantibody("Temporary")
            return "X-Antibody induced! Evolve soon to make it stick."
        if e.get("action") == "Inherit":                # the Digimemory (item 32)
            # DVPet useItem routes Inherit around the weak-consumable coefficient
            # and diminishing returns: applyItem(item, 1.0) -- full strength always
            mem, self.digimemory = (self.digimemory or {}), {}
            if not mem:
                return "The Digimemory is blank."
            self.vaccine = max(0, self.vaccine + int(mem.get("vaccine", 0)))
            self.data_power = max(0, self.data_power + int(mem.get("data", 0)))
            self.virus = max(0, self.virus + int(mem.get("virus", 0)))
            self.lifespan += float(mem.get("seconds", 0.0))
            self._set_anim("happy", 1.5)
            return (f"{mem.get('name', '?')}'s power lives on!  "
                    f"Va+{mem.get('vaccine', 0)} | D+{mem.get('data', 0)} | Vi+{mem.get('virus', 0)}")
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
        if e.get("action") in ("Toilet", "PortToilet"):
            # canon gates toilet items on a FULL gauge (isMaxBMGauge); tuipet's
            # urgency window leads the auto-fire.  Using it empties the gauge
            # into the toilet NOW (no pile); the generic decrement above
            # already spent the flush.
            if not self.poop_urgent():
                self.inventory[key] = self.inventory.get(key, 0) + 1   # refund
                self._set_anim("refuse", 1.0)
                return f"{self.name} doesn't need to go."
            self._poop_t = 0.0
            self._toilet_visit(key, spend_use=False)
            return f"{self.name} used the {e['name']} — no mess!"
        if e.get("action") == "ItemEvol":           # item-triggered evolution (Digimental/etc.)
            target = evolution.item_select(self, e["id"])
            if target is None and e.get("dexnum", -1) >= 0:
                target = evolution.item_direct(self, e["dexnum"])
            if target is None:
                self.inventory[key] = self.inventory.get(key, 0) + 1   # refund: not usable now
                self._set_anim("refuse", 1.0)
                return f"{self.name} can't use that yet."
            self.evolve_to(target)
            # canon digivolve-then-applyItem(item, 1.0): the Digimental's
            # -0.66 x max energy price bills the NEW form's ceiling
            self._apply_item_stats(e, 1.0)
            self._set_anim("happy", 1.4)
            return f"{self.name} evolved!"
        is_food = key.startswith("f:")
        # applyItemNoObedience: a DiminishingReturns toy scales by 1 - interest/5
        # (canon quirk: at FULL boredom the scale is skipped and the toy lands at
        # full strength again); every item use bores the pet a step further
        mod = WEAK_CONSUMABLE_COEF if weak else 1.0   # applyItem(item, 0.1) when compliant
        if not is_food:
            if e.get("diminishing"):
                m = 1.0 - self.item_interest / MAX_ITEM_INTEREST
                if 0.0 < m < mod:
                    mod = m
            self.item_interest = _clamp(self.item_interest + e.get("interest_change", 0),
                                        0, MAX_ITEM_INTEREST)

        self._apply_item_stats(e, mod)               # the canon applyItem stat core
        if e.get("vitamin"):
            self.feed_vitamin()                          # guards against injury worsening
        if e["unfatigue"]:
            self.fatigue_length = 0.0                    # DVPet Fatigued flag only clears
            # fatigue-length; energy stays driven by the item's Energy column, not a full refill
        if e["undepressed"]:
            self.depressed = False               # the item snaps the STATE, not just the mood
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
