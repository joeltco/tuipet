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
from . import backgrounds
from . import theme


class _Refused(str):
    """A use_item result that did NOT consume the item.  Reads as a plain
    message everywhere else -- only use_item's consume check looks at the
    type (clone audit 2026-07-15: every refusal string used to burn the
    item)."""


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


WEEKEND_BIT_MULT = 1.5   # weekend COMBAT income bonus (DSprite study 2026-07-14)


def _weekend_mult(now=None):
    """The real Sat/Sun check (the player's local clock); `now` is an epoch
    override for tests."""
    import time as _time
    t = _time.localtime(_time.time() if now is None else now)
    return WEEKEND_BIT_MULT if t.tm_wday >= 5 else 1.0


def weekend_bonus(now=None):
    """x1.5 bit multiplier on real-world Sat/Sun.

    Applies to COMBAT/COMPETITION income only — battle-win bits and tournament
    purses — never to shop resells or refunds (those are sinks, scaling them
    would just cheapen items on weekends).  Kept as a thin wrapper around
    _weekend_mult so the test suite can pin it to a weekday (conftest) without
    losing the real logic.
    """
    return _weekend_mult(now)


def _enemy_level(enemy):
    """The foe's battle level.  DVPet's getLevel read power sums off the old
    enemy cards; 0.5 cards carry none (0.5 BATTLE 2026-07-17), so the STAGE
    rank is the level now -- the same 1..6 scale the corpus level_fought
    gates expect (Fresh 1 .. Mega 6)."""
    from . import data as _data
    return max(1, _data.stage_rank(enemy.get("stage", "Rookie")))


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
# DELIBERATE DIVERGENCE (refusal recalibration, Joel 2026-07-08): canon compares
# a roll in [0,100) against obedience on the 0..150 scale, so a pet only reliably
# obeys once obedience clears ~100 -- and rookies live at 25..75, refusing half to
# all of every feed/train/battle/care command.  Canon absorbs that because its
# clock runs for days and each refusal is a brief autonomous blip; tuipet's
# compressed, keypress-driven loop turns each into a hard "scold it again" stop.
# A flat grace added to obedience in the refusal gate (NOT the stat itself) lifts a
# normally-raised pet (obed 50..75) to ~85..100% compliance while a neglected one
# (obed 0..25) still visibly rebels (refuses ~35..60%).  Applied once in
# check_refused so every branch (food/attr/item/activity) shares it.
REFUSE_OBEDIENCE_GRACE = 40.0
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
CALL_MOOD_DEC = 1                    # CallMoodDec: a standing care call drains mood per window-min
EGG_MOOD = 100                      # EggMood: a new egg starts warm (Evolution.egg)
# Evolution.java per-stage ARRIVAL setters (egg/hatch audit 2026-07-06; the
# shipped ranges are all min==max -> deterministic)
FRESH_MOOD = -10                    # FreshMood: born grumpy (it's a newborn)
FRESH_OBEDIENCE = 75                # FreshObedienceMin/Max: born TRUSTING
START_NUTRITION = 6                 # StartProtein/StartMineral/StartVitamin
IN_TRAINING_OBEDIENCE = 50          # InTrainingObedienceMin/Max: toddler rebellion cap
IN_TRAINING_SLEEP_LAPSE = 360       # InTrainingSleepLapse: wakes with real bedtime pressure
ROOKIE_OBED_GOOD = 50               # RookieGoodObedience (Happy daily majority)
ROOKIE_OBED_DEFAULT = 25            # RookieDefaultObedience (Neutral majority)
ROOKIE_OBED_BAD = 0                 # RookieBadObedience (anything else, ties included)
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
ENERGY_BONUS_MOOD = -1              # EnergyBonusChanceGoodMood
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
# the charge bill moved onto ENERGY when the mood/spirit meters left (DNA
# slim, BASIC VPET 2026-07-16): canon billed 3/6 spirit per unit against a
# +-10 range -- the same "N charge sessions with recovery between" pacing,
# re-expressed on the meter that still exists.  Off-field charging costs
# double, exactly like the spirit bill it replaces.
DNA_SAME_FIELD_ENERGY, DNA_DIFF_FIELD_ENERGY = 1, 2
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

# HIGH-STAKES WAGERS (bit-sink design 2026-07-14).  The classic 1..99 wager
# banks bits into DNA 1:1; everything past the 99-DNA bank cap buys LAB WORK,
# not volume -- and is spent, never refunded:
#   >= 500  STABILIZED: an over/under-mashed sample never spoils -- the rate
#           clamps into the nearest real band instead of rolling None.
#   >= 2500 RESONANT: the two Fields adjacent to the landed band each bank
#           wager//5 DNA as splash (capped, no refund) -- one big roll tops
#           three banks for tamers who value their time over their bits.
MAX_DNA_WAGER = 9999
DNA_STABILIZER_BET = 500
DNA_RESONANT_BET = 2500


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
RANK_WORSE_INJ_ATTR = 5                 # RankChangeInjury: a worsening sours the attr that did it
RANK_WORSE_INJ_FORCED = 5               # RankChangeInjuryForced (it was pushed into it)
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
GLUTTON_FEED_MOOD = 1                   # GluttonFeedMoodChange: a glutton relishes any meal
NOT_GLUTTON_FEED_MOOD = -1              # NotGluttonFeedMoodChange: a picky eater resents each
ENTH_BAD_FOOD_FORCED = -1               # EnthusiasmChangeBadFoodForced (disliked + full + forced)
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
# ⛔ CLOCK-UNIT LAW: canon cadences are in GAME MINUTES and tuipet's clock maps
# one game minute onto ONE REAL SECOND (DAY_LENGTH 1440s = 1440 game min).  A
# `*Min=N` constant therefore ports to N REAL SECONDS -- never N x 60.  The six
# constants below were all converted with REAL minutes (cadence audit
# 2026-07-14; the same error already cost us TEMP_RATE and WEATHER_CHECK_SEC).
FILTH_MOOD_DEC_MIN = 5.0                # FilthMoodDecMin 5 game-min (was 300.0 = 5 game HOURS)
FILTH_SICK_BOUND = 200                  # FilthSickChanceBound 12000 real-min -> /60 game scale
FILTH_SICK_CHANCE = 1                   # FilthSickChance (x piles, per game-min)
FILTH_WORSE_CHANCE = 20                 # FilthWorseSickChance (x piles, already sick)
# ---- the DSprite sickness (rebuilt 2026-07-17, Joel: "dsprite didnt have
# sickness?" -- it DID, a thin one, so the classic machine's removal keeps
# the CLONE's rules): one flag, caught per game-minute from filth or
# overweight, cured ONLY by the pill.  No spell timer, no worsening, no
# contagion, no counters.  Constants verbatim from the clone (v0.4.12).
SICK_POOP_P = 0.015            # sickness per minute while filth is present
SICK_OVERWEIGHT_P = 0.00375    # per overweight step: floor(excess/(base*0.5))
DEATH_SICK_P = 7.5e-5          # the clone's per-minute death whisper while sick
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
BATTLE_ENERGY_COST = 5              # the 0.5 bout's toll (clone BATTLE_ENERGY_COST)
BATTLE_WEIGHT_COST = 4              # the 0.5 bout sheds real weight (clone)
EXP_PER_WIN = 100                   # DMX experience per defeated enemy.  The manual's
#                                     award is unspecified; 100 maps its canon level
#                                     thresholds onto tuipet's win pacing (LV5=8 wins,
#                                     LV8=20, LV10=50 -- humulos LV fix 2026-07-17)
TRAIN_ENERGY_COST = 2               # the 0.5 drill's swing (clone TRAIN_ENERGY_COST)
PILL_ENERGY_GAIN = 7                    # the DSprite pill (feed menu, BASIC VPET 2026-07-16)
PILL_WEIGHT_GAIN = 5
STOMACH_CAPACITY = 4                    # legacy fallback only -- see stomach_capacity()
# canon stomach (food audit 2026-07-15): capacity is a PER-SPECIES field
# (digimon.csv StomachCapacity, 8..40) that SHRINKS in old age --
# getStomachCapacity subtracts (geriatricAge - lifeRemaining) x 0.00021/real-s
# (max ~9 at death), floored at MinStomachCapacity.  It divides applyFood's
# diminishing modifier and gates feed()'s taste moods; the overeat line is
# 0.75 x capacity (OvereatLimitFactor).  tuipet's refuse-at-full stays the
# documented adaptation, so only the modifier/mood-gate sides apply here.
MIN_STOMACH_CAPACITY = 7                # MinStomachCapacity
OVEREAT_FACTOR = 0.75                   # OvereatLimitFactor (x capacity)
# canon 0.00021 per REAL second across the 43200s window (max dec ~9.07);
# tuipet's elderly window is GERIATRIC_REMAIN game-sec -- same endpoint shape
GERIATRIC_STOMACH_COEF = (43200 * 0.00021) / 21600.0
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
                        "Champion": 200, "Ultimate": 400, "Mega": 800}
# AutoCareStage*HourPrice shipped a flat 100 for every adult stage; the
# retainer now scales with the stage like the visit fee does (half the visit
# ladder) -- a Mega's hired help is a real running cost, not pocket change
# (bit-sink design, Joel 2026-07-14)
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
ALREADY_FATIGUED_ENTH_CHANGE = -1        # AlreadyFatiguedEnthusiasmChange
ALREADY_FATIGUED_OBED_DEC = 5            # alreadyFatiguedObedienceDec
ALREADY_FATIGUED_SICK_CHANCE = 1         # AlreadyFatiguedSickChance
FATIGUE_WORSE_SICK_CHANCE = 50           # FatigueWorseSickChance (a collapse can turn a cold critical)
GERIATRIC_FATIGUE_ENERGY_DEC = 1         # GeriatricFatigueEnergyDec (already-fatigued + old)
RANK_CHANGE_FATIGUE = 3                  # RankChangeFatigue (the hour + the drill sour on a collapse)
RANK_FATIGUE_FORCED = 2                  # RankChangeFatigueForced (it was pushed there)
OBEDIENCE_FATIGUE_FORCED = -3            # obedienceChangeFatigueForced
RANK_TRAIN_FAIL = 3                      # RankChangeTrainFail (a failed drill sours its attribute)
SPOIL_OBED_DEC = 10                      # SpoilObedienceDec (spoil(): it only obeys what it likes)
SPOIL_MOOD_INC = 10                      # SpoilMoodInc
DISLIKED_ATTR_OBEY = -20                 # DislikedAttributeObeyChange (the hated drill refuses more)
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

# X-Antibody: a special state that unlocks evolution into the "X" Digimon
# forms.  BINARY since the X slim (BASIC VPET 2026-07-16): None or Permanent
# -- the Temporary protoform (hour decay) and XProgram lost their granters
# with the DVPet item catalog.  Acquired by the shop chip or a Natural X
# evolution.
# BINARY since the X slim (BASIC VPET 2026-07-16): None or Permanent.  The
# Temporary protoform (hour-decay) lost its only granter with the DVPet
# item catalog and left; XProgram likewise.

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




ONLINE_BITS = {"win": 200, "draw": 150, "loss": 100}


def online_reward(won, draw=False, now=None):
    """The online purse (0.5 BATTLE 2026-07-17): win 200 / draw 150 /
    loss 100, weekend x1.5 -- PvP pays bits, never training."""
    base = ONLINE_BITS["draw" if draw else ("win" if won else "loss")]
    return int(base * weekend_bonus(now))


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
    saved_hit_type: str = "normal"  # the trained battle form (0.5 drill: mega/normal/miss)
    total_trainings: int = 0        # lifetime drills (the 0.5 hit formula's experience term)
    exp: int = 0                    # DMX battle experience (humulos canon: defeating an
    #                                 enemy pays experience; feeds the LV line gates)
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
    inj_length: float = 0.0         # DVPet _injLength (game-min until the injury heals)
    vitamin_lapse: float = 0.0      # DVPet _vitaminLapse (game-min of injury-worsening protection)
    bandage_lapse: float = 0.0      # DVPet _bandageLapse: bandage indicator after mending an injury (getBandage)
    nutr_protein: int = 0           # DVPet _protein (0..MaxProtein), from a meaty diet
    nutr_mineral: int = 0           # DVPet _mineral, from vegetables
    nutr_vitamin: int = 0           # DVPet _vitamin, from fruit
    battles: int = 0
    levels_fought: list = _dcf(default_factory=list)  # opponent levels beaten this stage (DVPet _levelsFought)
    # ---- evolution lines (LINES_SPEC.md): the legible bracket engine ----
    line_id: str = ""               # hatched-from line; "" = corpus fuzzy engine
    stage_trainings: int = 0        # drills attempted this stage (every attempt counts; Pen20)
    data_trainings: int = 0         # lifetime VERSUS (data) sessions -- the DM20 manual's
    #                                 cheat chart cycles on THESE alone (a vaccine mash must
    #                                 not shift the printed pattern; audit 2026-07-13)
    stage_battles: int = 0          # battles fought this stage
    battle_log: list = _dcf(default_factory=list)   # last-15 results 1/0 (persists across evolution; Pen20)
    mega_kills: int = 0             # lifetime Ultimate/Mega-class foes beaten (DMX KO6 gate)
    dp: int = 0                     # Pen20 DP meter 0..4: full to jogress; protein +1, 3h sleep refills
    bits: int = 0
    trophies: int = 0
    trophies_won: dict = _dcf(default_factory=dict)   # trophy id -> day-won label (the trophy room)
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
    free_style: bool = False        # _isFree: Battle Style toggle (Free vs Orders)
    gift: str = ""                  # pending gift-call present (consumable key; "" = none)
    # the DSprite item timers (BASIC VPET 2026-07-16, cloned from v0.4.x):
    full_until: float = 0.0         # premium meat satiety (game-seconds, world clock)
    auto_clean_until: float = 0.0   # smart potty (game-seconds)
    evo_blocked: bool = False       # anti-evo chip toggle
    gift_t: float = 0.0             # seconds toward the next GiftChanceMin roll
    # ---- home tournament (PhysicalState _trophySchedule/_foughtTrophiesToday) ----
    tourney_schedule: list = _dcf(default_factory=list)   # 24 hourly trophy ids (dailyChange re-roll)
    tourney_day: int = -1                                  # game day of the schedule
    fought_today: list = _dcf(default_factory=list)        # trophy ids fought today (SameDayRetry exempt)
    fought_hours: list = _dcf(default_factory=list)       # game hours whose cup has been RUN today
    #                                                       (Joel 2026-07-13: one entry per cup-hour)
    tourney_alarm: int = -1         # _tourneyAlarm: trophy id to be called for (-1 = unset)
    tourney_real: int = -1          # real-date ordinal of the schedule (cadence 2026-07-17)
    featured_day: int = -1          # real-date ordinal the featured cup last ran
    tourney_alert: bool = False     # TournamentAlert: the call is ringing (this hour only)
    full_health: int = STARTING_HEALTH_POINTS   # _fullHealthPoints: TRAINED battle HP
    perfect_wins: int = 0           # _perfectWins: HP-drill wins toward the next +1 HP
    # (the adventure fields -- adv_map/adv_zone/adv_seek/adv_loc -- left
    # with the world layer; BASIC VPET 2026-07-16)
    egg_type: int = 0
    bg_pick: str = ""               # picked home scene ("" = follow the egg; E picker 2026-07-17)
    lifespan: float = LIFE_START
    generation: int = 1
    dead: bool = False
    sick: bool = False              # the DSprite flag (clone-style, 2026-07-17): pill-cured only
    death_cause: str = ""           # what took it (memorial epitaph, audit 2026-07-05)
    world_seconds: float = 0.0
    # (the weather/temperature block lived here -- temp, day_temp, temp_goal,
    # weather -- removed whole with the weather system; BASIC VPET 2026-07-16)
    field: str = ""
    # (the habitat block lived here -- habitat, home_habitat, habitats,
    # habitat_record -- removed whole with the habitat system; the home scene
    # is wired to egg_type now.  BASIC VPET 2026-07-16)
    x_antibody: str = "None"
    effect_id: int = -1            # active care effect (careEffect.csv id; -1 = none)
    effect_t: float = 0.0          # remaining duration of the active care effect
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
            # the heir's ESTATE (death/rebirth + item audits): canon's
            # resetToEgg never touches bits, the bag or the trophy room --
            # all device-lifetime, all inherited.  (The care BONUS rides the
            # bonus_seed channel, granted by app._grant_digimemory -- the old
            # last_gen.bonus copy was a second, partial careBonusOnReset that
            # the seed always stomped; retired, digimemory audit 2026-07-06.)
            from . import persistence as _persist
            est = _persist.prev_gen_estate()
            pet.bits = est["bits"]
            pet.inventory = est["inventory"]
            pet.trophies = est["trophies"]
            pet.trophies_won = est["trophies_won"]   # beaten qualifiers persist (seasonBeat)
            bank = {f: int(v) for f, v in (est.get("dna_owned") or {}).items()}
            if bank:                                 # the DNA bank rides the estate
                pet.dna_owned = {f: bank.get(f, 0) for f in data.DNA_FIELDS}
        # a fresh game dawns at 8:00 -- world_seconds 0 is MIDNIGHT, inside every
        # bedtime window, and a hatchling born asleep is a rotten first minute
        pet.world_seconds = 8 * 60.0
        if generation <= 1:
            # canon items.csv StartingUses: the device begins with THREE
            # stocked items (item audit 2026-07-06 -- the old grant was the
            # Toilet alone): Toilet 100 flushes, Bandage 99, Futon 100
            pet.inventory["i:82"] = 100
            pet.inventory["i:80"] = 99
            pet.inventory["i:81"] = 100
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
                  field=r.get("field", ""))
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

    def _tick_growth(self, dt):
        """Aging + the ambient systems: X-decay, shop restock, toy interest,
        the gift call, the mood record / birthday, the anim clock."""
        # (the Temporary protoform decay left with the X slim)
        self.age_seconds += dt
        self.stage_seconds += dt
        # (the shop restock credits left with the rolled-slot shop; the
        # DSprite catalog is a fixed shelf -- BASIC VPET 2026-07-16)
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
        day = int(self.world_seconds // DAY_LENGTH)
        if getattr(self, "_exercise_day", -1) != day:    # DVPet checkExerciseTime: daily reset
            self._exercise_day = day
            self.exercise_today = 0
        # (the sickness recovery lapse, the sick bowel-race penalty and the
        # 6h malady death left with the sickness system (BASIC VPET 2026-07-17); the injury/
        # fatigue/vitamin timers left with theirs, 2026-07-16)

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
        # (incMistake's filth/fatigue sickness risks left with the sickness
        # system (BASIC VPET 2026-07-17))

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
        # (the asleep enthusiasmLapse left with the spirit system;
        # BASIC VPET 2026-07-16)
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
        # canon runs these in bed too: the filth nag+risk, and
        # poopWaitMoodCheck -- the HELD gauge (only a sleeper holds it) nags
        # (the mood lapse / call drain / depression left with the mood system)
        self._filth_effects(dt)
        if self._poop_t >= self._poop_interval:
            self._poop_wait_t = getattr(self, "_poop_wait_t", 0.0) + dt
            if self._poop_wait_t >= 1.0:                 # PoopWaitMin 1 game-min (was 60.0)
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
        """The filth nag + sickness risk, and the childhood personality
        tracker.  (The mood lapse left with the mood system; the obedience
        lapse, refusal expiry, tantrum clock and praise/scold window aging
        left with the discipline system -- BASIC VPET 2026-07-16.  DVPet has
        NO passive energy decay -- energy only moves via activity and sleep.)"""
        self._filth_effects(dt)
        # personalityTracker (taste/rank audit 2026-07-06): childhood care is
        # TALLIED through Fresh/InTraining/Rookie -- energy kept above 75% of
        # max builds restlessness, weight off Healthy builds gluttony (the
        # mood-tier disposition leg left with the mood system);
        # randOnChampion cashes the tally in at the Champion evolution
        self._rank_t = getattr(self, "_rank_t", 0.0) + dt
        if self._rank_t >= 59:
            self._rank_t = 0.0
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

    def _filth_effects(self, dt):
        """checkFilthMoodDec + the filth sickness rolls (canon re-audit 2026-07):
        every FilthMoodDecMin the mess costs species filth_mood x piles; every
        game-min each pile is a sickness risk (chance x piles vs the bound x the
        species multiplier -- the 12000 real-min bound rides the /60 game scale,
        which lands within a hair of the old hand-rolled rate while gaining the
        per-pile scaling and the worse-sick path the flat roll lacked).
        Away, canon's countFilth() reads 0 (poopable gates on _isHome): the
        home mess can't sicken a pet out on the road (sweep 2026-07-06)."""
        if getattr(self, "away", False):
            return
        if self.poop <= 0:
            return
        fm = self._phys().get("filth_mood", -1)
        if fm:
            self._filth_mood_t = getattr(self, "_filth_mood_t", 0.0) + dt
            if self._filth_mood_t >= FILTH_MOOD_DEC_MIN:
                self._filth_mood_t = 0.0
                self._set_mood(self.mood + fm * self.poop)
        # (the filth sickness rolls left with the sickness system (BASIC VPET 2026-07-17); the
        # filth MOOD nag above is inert since the mood removal but stays as
        # the canon citation it became)

    def _tick_hunger(self, dt):
        """hunger: the DVPet calorie buffer drains each lapse; emptying it drops
        a hunger heart, then refills.  The care MISTAKE is the call light
        (LINES_SPEC §5, canon on all three devices): hunger empty and unanswered
        for 10 minutes = ONE mistake, then the call is postponed — it no longer
        repeats every calorie cycle while starving."""
        if self.full_until and self.world_seconds < self.full_until:
            return                    # premium-meat satiety (DSprite item)
        # hungerCall: a single mistake per unanswered call, mirroring strengthCall
        if self.hunger == 0 and not self.asleep:
            self._hunger_call_t = getattr(self, "_hunger_call_t", 0.0) + dt
            # ⚖️ DELIBERATE, *not* a clock-unit slip (cadence audit 2026-07-14).
            # Canon gives you 10 GAME-min to answer the call -- and on the real
            # device, which runs in REAL time, that IS ten real minutes.  Under
            # tuipet's 60x compression the literal port would be TEN REAL
            # SECONDS to notice the alarm and feed, or take a PERMANENT care
            # mistake (20 = death; 5 kills an elder).  Unplayable in a terminal
            # you leave in the background.  So the CONTINUOUS pressures (mood
            # drain, filth, sickness rolls) run at the canon game-min cadence,
            # while the DISCRETE PUNISHMENTS keep a fair human response window.
            if self._hunger_call_t >= 600.0:                 # 10 real min to answer
                self._hunger_call_t = -3600.0                # AfterMistakeMinutesPostponed
                self._inc_mistake()
                self.mistake_day += 1  # + HungerDecAtZero MissedDayChange
                self._burn_life(HUNGER_MISTAKE_LIFE_DEC * max(1, self.care_mistakes))
                # hungerMistakePenalty: obedience +1 -- or -1 for a glutton.
                # NO scold window: canon opens those for refusals and the
                # discipline tantrum only -- neglect costs mistakes/obedience,
                # it never makes the pet "act up" (discipline audit 2026-07-06;
                # the invented window leaked -10 obedience per miss and fed
                # the refusal spiral)
                self._set_obedience(self.obedience
                                    + (HUNGER_MISTAKE_OBED_GLUTTON if self.glutton > 0
                                       else HUNGER_MISTAKE_OBED))
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
        # (canon's PostponePoopMoodChange -1 -- startPoop blocked by the anim
        # STATE machine -- has no tuipet counterpart BY ARCHITECTURE: the pile
        # drops the same tick the gauge crosses, so an awake pet can never be
        # made to hold it; poop/filth audit 2026-07-15)
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
            if self._str_call_t >= 600.0:                    # 10 real min to answer
                #   (the same deliberate response-window rule as the hunger call)
                self._str_call_t = -3600.0                   # AfterMistakeMinutesPostponed
                self._inc_mistake()
                self._set_obedience(self.obedience - 5)      # MistakeStrengthObedienceDec
                # no scold window on neglect (canon; discipline audit 2026-07-06)
                # -- strength drains to 0 on its own species timer, so this one
                # opened "misbehaving!" windows for free on a loop
        else:
            self._str_call_t = 0.0
        # (the nutrition macro lapse left with the nutrition system;
        # BASIC VPET 2026-07-16)
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

    def _near_bedtime(self, n):
        """checkMaxHoursBeforeSleep's clock half: asleep aside, is nod-off
        within `n` game-minutes?  Pressure pets read the sleep clock
        (sleepLimit - sleepLapse <= n, canon verbatim); line pets read the
        wall clock to their fixed bedtime."""
        iw = self._in_sleep_window()
        if iw is not None:
            if iw:
                return True
            bt = lines_mod.bedtime_minutes(self)
            return bt is not None and (bt - self.world_seconds % DAY_MINUTES) % DAY_MINUTES <= n
        return self.sleep_limit - self.sleep_lapse <= n

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
                    self.awake_lapse = max(0.0, self.awake_limit - self.sleep_lapse)
                    self._set_anim("yawn", 1.8)
            else:
                self._to_nap_t = 0.0                        # the light resets the wait

    def _check_death_caps(self):
        """The discrete mistake/injury caps + the Pen20 elder-frailty rule:
        ONE copy for both tick paths -- these gates were duplicated between the
        sleep tick and _tick_mortality and had to be edited in lockstep
        (refactor 2026-07-05).  True when the pet died."""
        if self.care_mistakes >= 20:                           # MaxCareMistakes
            self._die("neglect")
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
        # the DSprite sickness (clone rules, 2026-07-17): caught per game-min
        # from filth (never on the road -- countFilth reads 0 away) or from
        # overweight steps; while sick, the clone's per-minute death whisper
        # stands where the classic 6h malady death used to
        if not self.sick:
            p = (SICK_POOP_P if (self.poop > 0
                                 and not getattr(self, "away", False)) else 0.0)
            bw = self._base_weight()
            if bw > 0 and self.weight > bw:
                p += int((self.weight - bw) // (bw * 0.5)) * SICK_OVERWEIGHT_P
            if p > 0 and random.random() < p * dt:
                self.sick = True
        elif random.random() < DEATH_SICK_P * dt:
            self._die("sickness")
            return True
        # (the old continuous per-second "extra" drain was invented -- canon
        # burns lifespan through the EVENT penalties wired below instead)
        return self._check_old_age()


    @property
    def is_geriatric(self):
        return (not self.dead
                and self.stage in ("Rookie", "Champion", "Ultimate", "Mega")
                and (self.lifespan - self.age_seconds) < GERIATRIC_REMAIN)

    def stomach_capacity(self):
        """Canon getStomachCapacity: the SPECIES stomach (digimon.csv), shrunk
        linearly through old age toward MinStomachCapacity(7) -- an elder
        fills up on smaller meals (food audit 2026-07-15)."""
        cap = data.load_requirements().get(self.num, {}).get("stomach_capacity", 10)
        if self.is_geriatric:
            diff = max(0.0, GERIATRIC_REMAIN - max(0.0, self.lifespan - self.age_seconds))
            cap = max(MIN_STOMACH_CAPACITY, cap - int(diff * GERIATRIC_STOMACH_COEF))
        return cap

    # (day_phase/is_daytime and the season calendar left with the day/night
    # + seasons removal -- BASIC VPET 2026-07-17.  The wall clock stays: the
    # sleep system's bedtimes are clock hours, not phases.)


    @property
    def ideal_temp(self):
        return data.load_requirements().get(self.num, {}).get("ideal_temp", (40, 60))

    def background(self, file=None):
        """The home scene frame (or None).  The scene is WIRED TO THE EGG the
        pet hatched from and stands for its whole life -- the real device's
        per-version backgrounds, worn as the DSprite rebuild's rip set
        (habitats left; BASIC VPET 2026-07-16).  file overrides the sheet
        entirely (BackgroundAnim checkBack's special rooms: the
        tournament/PvP/raid arena).  One look per scene: the day-phase frame
        pick and the star-twinkle/ember night art left with the day/night
        system (BASIC VPET 2026-07-17)."""
        if file is not None:
            key = file
        else:
            # the egg decides the default; the E picker may override it
            # (Joel 2026-07-17: "add the e action back to change backgrounds")
            key = self.bg_pick or backgrounds.scene_for_egg(self.egg_type)
        frames = data.load_backgrounds().get(key)
        return frames[0] if frames else None

    def pick_background(self, key):
        """The E picker's commit: '' returns the scene to the egg's own."""
        self.bg_pick = key
        if not key:
            return "Back to the egg's own scene."
        return f"{backgrounds.name(key)} it is."

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

    # (the timeRanks system -- time_pref/seed_time_pref/favorite_time/
    # disliked_time -- left with the day/night system.  BASIC VPET 2026-07-17)

    # (the weather machine -- _update_weather, the thermostat, the futon's
    # temperature pin, the sick fever/chill swings -- was removed whole with
    # the weather system; BASIC VPET 2026-07-16)

    def _set_xantibody(self, state):
        """BINARY (the X slim): any raise lands Permanent; never downgrades."""
        if state != "None":
            self.x_antibody = "Permanent"

    # (buy_habitat/move_to -- the habitat buy/move economy -- left with the
    # habitat system: the home scene is wired to the egg now.  BASIC VPET
    # 2026-07-16)

    def _effect_energy_gain(self):
        """PhysicalState.getEffectEnergyGain: an ACTIVE care effect's energy
        rate joins sleep()'s divisor -- amount * (cadence / 60) with canon's
        integer division (a sub-hour cadence contributes 0)."""
        if self.effect_id < 0 or self.effect_t <= 0:
            return 0
        eff = data.load_care_effects().get(self.effect_id)
        if not eff:
            return 0
        amt, every = eff["energy"]
        return amt * (every // 60)

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

    # (the thermostat -- set_temp_goal/clear_temp_goal/heat_on -- the futon's
    # pause_temp and the ideal-band comfort mood (_temperature_effects) left
    # with the weather system; the habitat-compat affinity followed with the
    # habitat system itself -- BASIC VPET 2026-07-16.)

    def save_from_death(self):
        """PhysicalState.saveFromDeath: yanked back from the brink -- starving,
        a bonus point poorer, RevivalLifeInc of life restored -- and the DEATH
        EVOLUTION fires if a Death-special form will take the body (Devimon /
        Bakemon / Ponchomon / Dexmon...).  With none valid it lives on as-is.
        Returns the old num when a death evolution fired, else None."""
        self.dead = False
        self.saved_from_death += 1
        self.hunger = HUNGER_AFTER_SAVED
        self.sick = False               # the clone's revival fix: a fresh
        #                                 revival must not come back sick
        self._starve_t = 0.0                          # the 12h clock restarts
        self.evol_bonus += BONUS_AFTER_SAVED
        self.age_seconds = max(0.0, self.lifespan - REVIVAL_LIFE)   # lapsed = total - revival
        old = self.num
        targets = evolution.death_targets(self)
        if targets:
            self.evolve_to(targets[0])               # evol(dying=true): the dark rebirth
            # the dark rebirth is a special evolution like jogress: re-anchor
            lines_mod.adopt_line(self, prev=old)
        else:
            # no Death form takes it: it lives on -- the continuous death checks
            # need the fatal counters off the trigger line (a mechanical floor;
            # DVPet's checks are edge events so canon never faces this)
            self.care_mistakes = min(self.care_mistakes, 19)
            self.injuries = min(self.injuries, 19)
        self._set_anim("happy", 2.0)                  # the rescue ends in a cheer
        return old if targets else None

    def needs_care(self):
        """The PHYSICAL half of the care call -- what the '!' rail icon shows:
        an awake, hatched pet that is starving, effort-empty, sick, filthy or
        exhausted, or a SLEEPER with the lights burning (canon lightsCall, the
        one call that fires asleep).  The discipline family (praise/scold/
        tantrum) is NOT here -- it wears the teach bulb instead, so the two
        icons carry separate meanings (Joel 2026-07-11: '!' and the bulb
        always showed as a pair, never separate)."""
        if self.dead or self.stage == "Egg" or self.call_paused():
            return False
        if self.asleep:
            return bool(self.lights)             # lightsCall: it wants the dark
        return (self.hunger == 0 or self.strength == 0 or self.sick
                or self.poop >= 3 or self.energy <= 0)

    def needs_attention(self):
        """The FULL alarm predicate (HUD beep/nag + mood-lapse gate): physical
        needs OR an open discipline moment.  Split 2026-07-11: the '!' icon
        draws on needs_care() only; this union keeps the alarm and the
        mood-recovery block exactly as before (sleep-screens audit
        2026-07-06 semantics unchanged)."""
        # (the discipline half -- the teach bulb -- left with the discipline
        # system; BASIC VPET 2026-07-16)
        return self.needs_care()

    def near_bedtime(self):
        """sleepNotNap: the pressure sits inside the real-sleep edge -- the
        yawning special idle's eligibility (and lights-out now means SLEEP)."""
        return self.sleep_lapse >= self.sleep_limit - (
            SLEEP_NOT_NAP_MIN - self.restless * SLEEP_NOT_NAP_RESTLESS)

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
        if getattr(self, "evo_blocked", False):
            return                    # the anti-evo chip (DSprite item)
        if self.asleep or self.is_geriatric:
            return
        if getattr(self, "fx_hold", False):
            return          # an animation owns the screen; evolve on a quiet tick
        if self.stage_seconds < self.STAGE_DURATION.get(self.stage, 9e9):
            return
        # the armed DNA steer beats any chart (divergence: the wild road,
        # 2026-07-07) -- charging a Field to its stage threshold IS the
        # player's choice, and it opens the corpus graph's next-stage edge
        # in that Field; unarmed pets are untouched (highest_dna '' short-
        # circuits, so goldens and existing saves behave identically)
        target = evolution.divergence_target(self)
        if target is not None:
            prev = self.num
            self.evolve_to(target)
            lines_mod.adopt_line(self, prev=prev)   # re-anchor to any chart that claims
            return                        # the landing, else ride the corpus engine
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

    # (_apply_egg_habitat/_apply_natural_habitat/go_home_habitat left with
    # the habitat system -- the egg wires the scene directly now.  BASIC
    # VPET 2026-07-16)

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
        bits, exactly like the device. Returns the Field won ("None" = wasted).

        High-stakes wagers (2026-07-14): only min(amount, 99) is bankable volume --
        the premium above the cap is LAB WORK and never refunds. A STABILIZED
        wager (>=500) clamps a spoiled rate into the nearest real band; a
        RESONANT one (>=2500) splashes amount//5 DNA into the two adjacent
        Fields (capped, no refund)."""
        field = dna_field_for_rate(rate)
        if field == "None" and amount >= DNA_STABILIZER_BET:
            rate = min(max(rate, DNA_RATE_BANDS[0][0] + 1), DNA_RATE_BANDS[-1][0])
            field = dna_field_for_rate(rate)
        gained = min(amount, MAX_DNA_INVENTORY)
        total = self.dna_owned.get(field, 0) + gained
        if total > MAX_DNA_INVENTORY:
            self.bits += total - MAX_DNA_INVENTORY          # refund the overflow as bits
            total = MAX_DNA_INVENTORY
        self.dna_owned[field] = total
        if amount >= DNA_RESONANT_BET and field != "None":
            splash = amount // 5
            fields = [f for _, f in DNA_RATE_BANDS if f != "None"]
            i = fields.index(field)
            for j in (i - 1, i + 1):
                if 0 <= j < len(fields):
                    nb = fields[j]
                    self.dna_owned[nb] = min(self.dna_owned.get(nb, 0) + splash,
                                             MAX_DNA_INVENTORY)
        return field

    def apply_dna(self, field, amount):
        """PhysicalState.applyDNA: owned -> charged, at a cost (disturb/strength/mood/spirit/sick)."""
        owned = self.dna_owned.get(field, 0)
        if amount <= 0 or owned < amount:
            self._set_anim("refuse", 1.0)                   # Jeering: not enough DNA
            return False
        self.dna_owned[field] = owned - amount
        self.dna_applied[field] = self.dna_applied.get(field, 0) + amount
        # canon calls disturb() -- a NO-OP on an awake pet (its whole body is
        # asleep-gated); the old `disturb += 1` falsely marked the evolution
        # counter on every charge (jogress/DNA audit 2026-07-06).  The asleep
        # case never reaches here: can_charge_dna disturbs and blocks first.
        # applyDNA strength: overflowing the Effort gauge lands at limit-1, NOT
        # the cap (setExercise(getExerciseLimit() - 1)) -- DNA can't top you
        # off.  Canon's limit is the species MaxStrength (4..14); tuipet's
        # gauge is the real toy's FOUR HEARTS everywhere (UI/training/decay),
        # so the limit folds to 4 -- the established design, kept.  The cap is
        # limit-1 (=3), but it is a CEILING, never a penalty: a pet already at
        # 4 (trained to full) keeps its heart -- on the real device limit-1 of
        # a wide byte gauge is no real drop; the 4-heart fold turned that into
        # a whole heart, so clamp up-only (DNA audit 2026-07-08).
        gain = DNA_STRENGTH_CHANGE * amount
        self.strength = max(self.strength, min(self.strength + gain, 3))
        same = field == self.field
        # the charge bill (see the constants): energy, doubled off-field --
        # the mood/spirit bills left with their systems
        self._set_energy(self.energy
                         - (DNA_SAME_FIELD_ENERGY if same else DNA_DIFF_FIELD_ENERGY) * amount)
        # (applyDNA's per-unit sickness risk left with the sickness system
        # (BASIC VPET 2026-07-17) -- the ENERGY bill above is the charge's cost now)
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
        """Always False: the nutrition macros left (BASIC VPET 2026-07-16)."""
        return False


    def _species_food(self):
        r = data.load_requirements().get(self.num, {})
        return (r.get("food_pref", "None"), r.get("food_aversion", "None"),
                r.get("food_intol", []))


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


    def _become(self, num):
        """The species-swap prologue shared by evolution and mode change:
        identity, energy ceiling, X-antibody lock-in.  Returns the new
        form's requirements record."""
        _, by_num = data.load_sprites()
        r = by_num[num]
        self.num, self.name = num, r["name"]
        self.stage, self.attribute = r["stage"], r["attribute"]
        self.field = r.get("field", self.field)
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
        # Evolution.java's per-stage ARRIVAL setters (egg/hatch audit
        # 2026-07-06 -- none of these were ported; the missing fresh()
        # obedience 75 was the deepest root of the misbehaving-babies era):
        if self.stage == "Fresh":
            # fresh(): born TRUSTING (obedience 75) but grumpy (-10 mood),
            # hungry, full of energy, with a starter nutrition base 6/6/6
            self._set_mood(FRESH_MOOD)
            self._set_obedience(FRESH_OBEDIENCE)
            self.strength = 0
            self.hunger = 0
            self.energy = self.max_energy
        elif self.stage == "InTraining":
            # inTraining(): toddler rebellion -- obedience above 50 KNOCKS
            # BACK to 50; it wakes with the lights on and real bedtime
            # pressure (sleepLapse 360)
            if self.obedience > IN_TRAINING_OBEDIENCE:
                self._set_obedience(IN_TRAINING_OBEDIENCE)
            self.asleep, self.nap = False, False
            self.lights = True
            self.sleep_lapse = IN_TRAINING_SLEEP_LAPSE
        elif self.stage == "Rookie":
            # rookie(): the childhood report card SETS obedience -- a Happy
            # daily-mood majority earns 50, Neutral 25, anything else 0
            # (a TIE is Mood.None -> the switch default -> bad, canon exact)
            counts = self.daily_mood
            best = max(counts.values()) if counts else 0
            tops = [k for k, v in counts.items() if v == best and best > 0]
            major = tops[0] if len(tops) == 1 else None
            self._set_obedience(ROOKIE_OBED_GOOD if major == "Happy"
                                else ROOKIE_OBED_DEFAULT if major == "Neutral"
                                else ROOKIE_OBED_BAD)
        if was_young and self.stage == "Champion":
            # randOnChampion (taste/rank audit 2026-07-06): the childhood-care
            # tally becomes the adult temperament
            self._rand_on_champion()
        self.stage_seconds = 0.0
        # per-stage care record resets; the next stage's care decides the next form
        self.care_mistakes = self.overeat = self.disturb = 0
        self.stage_trainings = self.stage_battles = 0     # battle_log persists (Pen20 rolling window)
        self.injuries = 0
        self.inj_length = self.fatigue_length = 0.0
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
        """A NO-OP: the obedience meter left with the discipline system
        (pinned at its default; write-sites stay as inert citations)."""

    def _set_mood(self, value):
        """A NO-OP: the mood meter left with the mood system (BASIC VPET
        2026-07-16, converging on the clone sim).  The canon write-sites
        remain in place as inert citations and vanish with their own
        systems; the meter itself is pinned at 0 (Neutral)."""

    def mood_pct(self):
        """Neutral forever (the meter is gone); kept for the status bar."""
        return 50

    def condition(self):
        """CONDITION 0..3: how well-kept the pet is RIGHT NOW.  Care pays into
        SKILL, not just survival (2026-07-14): the training drills read this
        tier and widen their timing zones/windows for a well-kept pet -- a
        starved, exhausted one trains with a trembling paw.  The mean of
        three care gauges (mood left with its system), floored to a tier; a
        sick or injured pet never scores above 1."""
        score = (self.hunger / 4.0
                 + self.strength / 4.0
                 + max(0.0, self.energy) / float(max(1, self.max_energy))) / 3.0
        tier = max(0, min(3, int(score * 4)))
        return tier

    def current_mood(self):
        """DERIVED (the clone's rule): no mood meter -- the word keys off
        condition.  Unhappy when unwell or unfed, else Neutral."""
        w = self.status_word()
        return "Unhappy" if w in ("sick", "starving",
                                  "needs cleaning") else "Neutral"

    def _set_enthusiasm(self, value):
        """A NO-OP: the spirit meter left with the enthusiasm system (BASIC
        VPET 2026-07-16, converging on the clone sim).  The canon write-sites
        stay as inert citations and die with their own systems; the meter is
        pinned at 0."""

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
            # (the over-exertion fatigue left with the fatigue system; the
            # perfect-conditions bounce left with the day/night system)
        if raw < -self.max_energy:
            self._burn_life(MIN_ENERGY_LIFE_PENALTY)     # setEnergy's floor penalty
        self.energy = _clamp(raw, -self.max_energy, self.max_energy)

    # (_energy_bonus_save -- checkEnergyIncFromPerfectConditions -- left
    # with the day/night system: its trigger WAS the favourite time of day.
    # BASIC VPET 2026-07-17)

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

    def _manual_toilet(self, key):
        """Taking the pet to the Toilet (i:82) / Port. Potty (i:83) by hand --
        the missing half of toilet training (items audit 2026-07-17: the
        training path was dead code, so the starting 100 flushes never spent).
        Works only in the urgency window; during InTraining these visits ARE
        the training (MinToiletUsesToTrain 1)."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return _Refused("")
        if self.asleep:
            self._disturbed()                    # items.csv Disturb TRUE
        if not self.poop_urgent():
            self._set_anim("refuse", 1.0)
            return _Refused(f"{self.name} doesn't need to go.")
        self._poop_t = 0.0                       # the gauge empties in the bowl
        self._toilet_visit(key)                  # spends the flush, blesses, trains
        return "Whew — right in the bowl."

    def _futon(self):
        """The Futon (i:81): a tuck-in for a SLEEPER -- the one item that
        never disturbs (items.csv Disturb FALSE is the Futon's column; Joel
        chose full canon here).  Applies careEffect 0: +1 energy and +1 mood
        per hour cadence for 960 min, ending when the sleeper stirs."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return _Refused("")
        if not self.asleep:
            self._set_anim("refuse", 1.0)
            return _Refused("Save it for bedtime.")
        if self.effect_id == 0 and self.effect_t > 0:
            return _Refused("Already tucked in.")
        eff = data.load_care_effects().get(0)
        if not eff:
            return _Refused("")
        self.effect_id = 0
        self.effect_t = float(eff.get("duration", 960)) * 60.0
        self._eff_asleep = True                  # armed on a sleeper; wake ends it
        self.take_item("i:81")
        return "Tucked in — sleep runs deeper."

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
        # (the flush item's mood/obedience perks left with the item system)
        self._toilet_train()
        self._toilet_event = key                  # the app plays poopToilet
        self._set_anim("toilet", 3.8)

    def _do_poop(self, backlog=False):
        if self.auto_clean_until and self.world_seconds < self.auto_clean_until:
            self.poop = 0             # the smart potty flushes it (DSprite item)
            self.poop_sizes = []
            return
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
        # canon sleep(): the divisor is energyGain + getEffectEnergyGain() --
        # an active Futon (EnergyChange 1;60 -> +1) makes the rest MORE
        # efficient, so the night it sizes is SHORTER (sleep audit 2026-07-15)
        gain = max(1, getattr(self, "_sleep_energy_gain", 3) + self._effect_energy_gain())
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
            return "zzz…"
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
            # (the rough-waking sickness risks left with the sickness
            # system (BASIC VPET 2026-07-17))
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
        return "zzz… mind its sleep!"

    def _special_idle(self):
        """The special-idle families, canon shape (SpriteAnim's 1/1500 rolls;
        personality audit 2026-07-06): the visible TANTRUM while the
        discipline call stands (canon rolls it at 3x the family odds), then
        the personality mood idles -- gated like canon (rested, spirited,
        under-drilled, well) and keyed on the mood TIER: Happy bounces,
        Unhappy fumes, Neutral does nothing.  (The weathering family --
        nice-weather joy, the rain shake, the snow shiver -- left with the
        weather system; BASIC VPET 2026-07-16.)"""
        if getattr(self, "away", False):
            return                                   # no home idles on the road
        # the personality idles: canon gates -- energy >= max/3, spirit >= 0,
        # effort <= limit/2, not unwell (and the TIER, not raw mood)
        if (self.energy < self.max_energy / 3 or self.enthusiasm < 0
                or self.strength > 2):
            return
        m = self.current_mood()
        if m == "Happy":
            self._set_anim(random.choice(("play", "happy")), 2.0)
        elif m in ("Unhappy", "Depressed"):
            self._set_anim(random.choice(("angry", "tantrum")), 2.0)

    def check_refused(self, food=None, attr=None, energy_change=0.0, item=None):
        """The obedience refusal roll left with the discipline system (BASIC
        VPET 2026-07-16): the pet obeys care commands.  TWO meter rules
        survive because they are affordability, not temperament: the energy
        auto-refuse (a jogress/digimental/mode-change it cannot pay for) and
        feed()'s own full-belly head-shake."""
        self.refused = False
        if energy_change and self.energy + math.ceil(energy_change * self.max_energy) < 0:
            self._set_anim("refuse", 1.5)
            return True                  # can't afford the energy -> auto-refuse
        return False

    def refuse_attack(self, my_hp, enemy_hp):
        """Always False: the Orders-style mid-fight refusal left with the
        discipline system."""
        return False

    def stop_travel_prob(self):
        """PhysicalState.checkStopTravel as a per-fire PROBABILITY (the caller
        composes it over a full stride).  One draw per controller fire,
        r in [cap, cap + chance*3000); the energy fraction scales the draw
        DOWN, so a rested pet essentially never stops but a drained one plants
        its feet: refuse when r*(energy+1)/max - dispo*35 + obey - 5
        <= cap - obedience."""
        # the obedience walk-refusal left with the discipline system
        # (BASIC VPET 2026-07-16): only a truly DRAINED pet plants its feet
        energy_mod = 1.0 - (self.max_energy - (self.energy + 1)) / max(1, self.max_energy)
        return 1.0 if energy_mod <= 0 else 0.0

    def stop_travel_effects(self):
        """The refusal's side effects (split from the roll so it can compose)."""
        self.refused = True
        self._set_anim("refuse", 1.5)

    def check_stop_travel(self):
        """One canonical per-fire draw (kept for tests/direct callers)."""
        if random.random() < self.stop_travel_prob():
            self.stop_travel_effects()
            return True
        return False

    def check_compliant(self):
        """Always False ("never grudging"): compliance left with the
        discipline system.  Canon's True meant "it obeyed only because you
        spent its compliance token" -- the resentment branches (forced-feed
        rank souring, forced-fatigue obedience bills, grudging weak item
        application) key on it, so the willing constant is False."""
        return False

    def can_feed(self):
        """Guard for opening the feed menu (mirrors feed()'s own gates)."""
        if (_g := self._guard()) is not None:
            return _g
        return None

    def feed(self, food=None, assisted=False):
        """The DSprite feed (BASIC VPET 2026-07-16, cloned from v0.4.x): the
        F menu picks MEAT or PILL; the whole DVPet food catalog -- taste
        tiers, nutrition macros, calories, food evolutions -- left with it.
        Kept as the meat entry so the assistant and old callers still feed."""
        return self.feed_meat()

    def feed_meat(self):
        """Meat: hunger +1, weight +1.  Refused at a full belly (the head-
        shake; +1 overeat +1 weight -- the OF gate's sin, kept from canon's
        overeatPenalty).  Feeding a sleeper DISTURBS it first."""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if self.asleep:
            self._disturbed()
        self._last_meal_starving = self.hunger == 0          # eat(): wolfed down
        if self.hunger >= FULL_HUNGER:
            self._set_weight(self.weight + 1)
            self.overeat += 1
            self.mistake_day += 1                # OverStomachCapcityMissedDayChange
            self._poop_t = min(self._poop_interval, getattr(self, "_poop_t", 0) + 900)
            self._set_anim("refuse", 1.0)
            return f"{self.name} is too full!"
        self.hunger = _clamp(self.hunger + 1, 0, FULL_HUNGER)
        self._set_weight(self.weight + 1)
        # every meal advances the bowel gauge (applyFood: bmGauge += bmLapseInc)
        self._poop_t = getattr(self, "_poop_t", 0) \
            + self._poop_interval * self._phys().get("poop_lapse", 1) \
            / max(1, self._phys().get("poop_limit", 64))
        # (checkDirtyEating's filth-meal sickness risk left with the
        # sickness system (BASIC VPET 2026-07-17))
        self._set_anim("eat", 1.4)
        return "Fed Meat."

    def feed_pill(self):
        """The pill (clone rules): cures the sickness, strength +1, energy
        +7, weight +5.  Refused when there is nothing to cure or top up.
        Healing a sleeper DISTURBS it first.  (The classic spell machine
        left 2026-07-17; the DSprite flag is pill-cured ONLY.)"""
        if (_g := self._guard(asleep_blocks=False)) is not None:
            return _g
        if not self.sick \
                and self.strength >= 4 and self.energy >= self.max_energy:
            self._set_anim("refuse", 1.0)
            return f"{self.name} doesn't need it."
        if self.asleep:
            self._disturbed()
        self.sick = False
        self.strength = _clamp(self.strength + 1, 0, 4)
        self._set_energy(self.energy + PILL_ENERGY_GAIN)
        self._set_weight(self.weight + PILL_WEIGHT_GAIN)
        self._set_anim("heal", 1.4)
        return "Took the pill."

    def can_train(self):
        """canExercise (energy audit 2026-07-06): NO hard fatigue/energy gate --
        MinEnergyForActivity is -127 on the classic column (vacuous), and
        fatigue/sickness only SHADE the refusal roll (unwellMod) and the injury
        odds.  The 0.5 drill adds the clone's ONE hard gate: too drained to
        swing (0.5 TRAINING 2026-07-17)."""
        if (_g := self._guard()) is not None:
            return _g
        if self.energy < TRAIN_ENERGY_COST:
            return "Too tired to train."
        return None

    def max_health(self):
        """PhysicalState.getMaxHealth: the trained-HP CAP rises with lapsed life."""
        days = self.age_seconds / DAY_LENGTH
        for d, cap in HEALTH_CAP_LADDER:
            if days >= d:
                return cap
        return MAX_HEALTH_DEFAULT_CAP

    def _check_perfect_wins(self, force=True):
        """checkAndIncPerfectWins: every HP-drill success counts (force ==
        PracticeAlwaysIncPerfectWins TRUE) and every BATTLE WIN counts while the
        trained HP sits below its age cap (force=False rides canon's gate --
        Min{Strength,Hunger} are 0 at difficulty 0, so the HP-below-max clause
        is the whole test); each PerfectWinsLimit-th grows fullHealthPoints
        (HealthInc when it actually lands)."""
        if not force and self.full_health >= self.max_health():
            return ""
        self.perfect_wins += 1
        if self.perfect_wins % PERFECT_WINS_LIMIT == 0:
            before = self.full_health
            self.full_health = min(self.max_health(), self.full_health + PERFECT_WINS_HEALTH_INC)
            if self.full_health > before:
                return " HP +1!"                     # State.HealthInc
        return ""

    # (apply_training -- the four-drill DVPet versus training, its attribute
    # power growth, taste-rank ledger and Effort-per-drill -- left with the
    # classic training system (0.5 TRAINING 2026-07-17).  Powers now grow
    # ONLY through battle wins (record_battle's canon setPower +1 stays);
    # Effort fills via the pill; the drill trains FORM.  The attr-rank
    # ledger below is INERT -- nothing warms it, and _power_bonus_attr
    # falls through to the species seed.)

    def train_result(self, success):
        """One clone drill (0.5 rules): energy -2 (floored at 0), the
        counters that feed the LINES TR gates, and a clean strike sheds a
        little weight.  The verdict pose mirrors the old drills' cheer/sad
        tell so the after-train fx keep working."""
        self._calm_discipline_call()                 # a drill placates the call
        self.exercise_today += 1
        self.stage_trainings += 1                    # LINES_SPEC TR gate: every attempt counts
        self.total_trainings += 1                    # lifetime (the 0.5 hit formula reads it)
        # the Effort meter fills per drill, win or lose (canon setExercise +1;
        # Joel 2026-07-17 "its not filling the effort meter?" -- the clone left
        # strength to the pill, but the gauge visibly ticking up per drill is
        # the shipped feel and the DM20 rule)
        self.strength = _clamp(self.strength + 1, 0, 4)
        self._set_energy(max(0, self.energy - TRAIN_ENERGY_COST))
        if success and self.weight > self._base_weight():
            # the clone shed toward base, never below -- its weight model
            # floored AT base, so a bare max() here would fatten a classic
            # pet that runs light (caught live 2026-07-17)
            self._set_weight(self.weight - 1)
        self._set_anim("happy" if success else "sad", 1.8)
        return True

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

    def record_battle(self, won, enemy=None, online=False, source="battle",
                      free_style=None, low_health=False):
        """One battle, the 0.5 rules (clone record_battle, 2026-07-17):
        counters + flat costs, +2 trainings for a LOCAL bout.  KEPT from the
        classic version -- the progression channels the rest of the game
        feeds on: battle_log (Pen20 WIN gates), stage_battles (BTL gates),
        lifetime wins + the mystery-egg note, levels_fought, KO6 (a felled
        Mega, never in PvP -- untrusted cards), and the win's +1 power in
        the foe's attribute (the corpus checkStatTotal gates feed on it; a
        0.5 card's attribute string names the dominant power directly).
        The old free_style/low_health params are accepted-and-ignored for
        stragglers.  (Mood/compliance/contagion legs left with their
        systems; the perfect-wins HP ladder left with the classic battle.)"""
        if source == "pvp":
            online = True
        self.battles += 1
        self.stage_battles += 1                          # LINES_SPEC BTL gate (per-stage)
        self.battle_log = (self.battle_log + [1 if won else 0])[-15:]   # Pen20 rolling window
        self._set_energy(max(0, self.energy - BATTLE_ENERGY_COST))
        self._set_weight(max(1, self.weight - BATTLE_WEIGHT_COST))
        if not online:
            self.stage_trainings += 2                    # a local bout trains (clone rule)
        if not won:
            return ""
        self.wins += 1
        if not online:
            # DMX canon: defeating an enemy pays experience toward LEVEL (the
            # LV line gates).  PvP excluded like KO6 -- colluding tamers could
            # farm level-gated evolutions off untrusted cards.
            self.exp += EXP_PER_WIN
        from . import persistence as _persist
        total = _persist.wins_add(1)                     # lifetime wins (egg gates)
        if total in egg_mod.wins_thresholds():
            # a lifetime-wins egg gate just crossed (Zuba 75 / Hack 40 / V 25 /
            # Sakumon 50 / Chibickmon 10...): flash the nursery note
            self.egg_unlock_note = "A new egg appeared in the nursery!"
        if enemy:
            self.levels_fought.append(_enemy_level(enemy))
            # KO6: Stage VI is Mega, full stop; PvP excluded (untrusted
            # cards -- colluding tamers could farm it; egg/KO6 audit 2026-07-14)
            if enemy.get("stage") == "Mega" and not online:
                self.mega_kills += 1                     # LINES_SPEC KO6 gate
                _persist.mega_kills_add(1)               # ...and the X-egg progress
            # the win grows the pet's power in the foe's attribute (+1; a
            # HAPPY pet's favoured attribute doubles it, canon setPower)
            dom = enemy.get("attribute")
            if dom in self._ATTR3:
                inc = 1
                if self.current_mood() == "Happy" and dom == self._power_bonus_attr():
                    inc += BONUS_ATTRIBUTE_POWER
                if dom == "Vaccine":
                    self.vaccine += inc
                elif dom == "Data":
                    self.data_power += inc
                else:
                    self.virus += inc
        return "training +2" if not online else ""

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
        """Always 0 (fight on): the pet-initiated surrender/flee rode the
        obedience formula and left with the discipline system (BASIC VPET
        2026-07-16).  The PLAYER's surrender option stands."""
        return 0

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
        """A NO-OP: the praise window left with the discipline system."""

    def _open_scold(self):
        """A NO-OP: the scold window left with the discipline system."""

    def _calm_discipline_call(self):
        """A NO-OP: the tantrum left with the discipline system."""


    def _check_discipline_call(self):
        """A NO-OP: the spontaneous tantrum left with the discipline system."""

    def is_fatigued(self):
        """Always False: the fatigue system left (BASIC VPET 2026-07-16)."""
        return False

    def is_injured(self):
        """Always False: the injury system left (BASIC VPET 2026-07-16)."""
        return False

    def is_frail(self):
        """The frailty WARNING (Joel 2026-07-13, after MetalGreymon died with
        8 unseen mistakes): an Ultimate/Mega carrying 3+ care mistakes is
        closing on the 5-slip elder death (_check_death_caps) -- surface it
        BEFORE it lands.  Warning only; the death rule is unchanged."""
        return self.stage in ("Ultimate", "Mega") and self.care_mistakes >= 3

    def is_freezing(self):
        """Always False: ambient temperature left with the weather system
        (BASIC VPET 2026-07-16).  Kept as an API pin -- screens poke it."""
        return False

    def is_overheating(self):
        """Always False (same removal as is_freezing)."""
        return False

    # (_sicken/_worsen_sick/_check_sick/_check_worse_sick -- the whole
    # sickness machine -- left with the sickness system, BASIC VPET
    # 2026-07-17.  The pill is a tonic, filth is a mood/mistake matter,
    # and nothing is contagious.)


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
        """The pill (BASIC VPET 2026-07-16): the med/bandage staples left
        with the DVPet item system -- one staple treats everything, from the
        F menu (and the road's h key)."""
        return self.feed_pill()



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
        # longevity: whole days lived past the growth curve (negative if short).
        # int(x / D), not x // D: canon's Java long division truncates toward
        # ZERO, so a short life loses only its WHOLE missing days (digimemory
        # audit 2026-07-06 -- floor division over-penalized by one)
        b += int((self.age_seconds - self._growth_period()) / DAY_MINUTES)
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
        if getattr(self, "away", False):
            # doAutoCare/checkAutoCare both gate on _isHome: while the pet is
            # OUT (adventuring -- canon's teleport toggles it) the assistant
            # neither bills the retainer nor visits (auto-care audit 2026-07-06)
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
        elif act == "feed":
            self.feed_meat()                             # assistantFeed: the staple
        elif act == "strength":
            self.feed_pill()                             # the tonic tops effort/energy
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
        return "Played together — happy, but a bit spoiled."

    # ---- shop / items --------------------------------------------------------
    def buy_slot(self, slot):
        """Buy one from a town counter slot (the DSprite catalog behind every
        counter now -- BASIC VPET 2026-07-16)."""
        if slot.get("stock", 0) <= 0:
            return "Sold out."
        price = shop.purchase_price(slot)
        if self.bits < price:
            return "Not enough bits."
        self.spend_bits(price)
        slot["stock"] -= 1
        self.add_item(slot["key"])
        return f"Bought {slot['name']}."

    def sell(self, entry):
        """Resell one from the bag at half price."""
        key = entry["key"]
        if self.inventory.get(key, 0) <= 0:
            return "None to sell."
        val = shop.resell_price(entry)
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
            self.birthday_note = "A rough day… just a Candy."
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
        # the Happy-tier gate and the mood term left with the mood system
        # (BASIC VPET 2026-07-16): a WELL pet (not unwell) can find a present,
        # and obedience alone narrows the roll
        if (self.gift or self.asleep or self.stage in ("Egg", "Fresh", "InTraining")
                or self.current_mood() == "Unhappy"
                or getattr(self, "away", False)):   # checkGiftCall gates on _isHome:
            return                                  # presents are found AT HOME
        chance = int(OBEDIENCE_REFUSAL_CAP - self.obedience + GIFT_CHANCE_FACTOR)
        if chance > 0 and random.randrange(chance) == 0:
            self.gift = self._pick_gift()

    def _pick_gift(self):
        """The present pool (BASIC VPET 2026-07-16): a uniform pick from the
        DSprite catalog's treat tier (fruits and small care goods) -- the
        DVPet per-item GiftChance table left with the item system."""
        pool = ("best_fruit", "normal_fruit", "worst_fruit",
                "energy_drink", "care_mistake_eraser")
        return random.choice(pool)

    def claim_gift(self):
        """ClockTic.giftEnd: the present lands in the bag and the pet cheers."""
        key, self.gift = self.gift, ""
        if not key:
            return ""
        e = shop.entry(key) or {}
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
        # applyAttributeChange + compensateAttributes (completeness sweep
        # 2026-07-06): the six +-15 TRADE toys (Board Game, Skateboard,
        # Dumbbell...) conserve the total -- a power driven below 0 borrows
        # the deficit 1:1 from the others, rotating through all three (the
        # old max(0,) clip quietly forgave the unpaid part of the trade)
        self.vaccine += _sc(e["vaccine"])
        self.data_power += _sc(e["data"])
        self.virus += _sc(e["virus"])
        self._compensate_attrs()
        # canon applyItem: a Disposition item nudges the MOOD RANK (the
        # tracker the Champion re-roll cashes in), scaled like every stat
        self.mood_rank += _sc(int(e.get("t_disposition", 0) or 0))

    def _compensate_attrs(self):
        """compensateAttributes x3 rotations: each negative power borrows from
        the next two in canon's order.  (Canon's zero-all escape only fires
        when all THREE are negative -- with both banks empty its loop would
        spin forever; unreachable with the shipped symmetric trades, and the
        port floors the deficit at 0 instead of freezing.)"""
        def comp(main, weak, normal):
            while main < 0:
                if weak > 0:
                    weak -= 1
                    main += 1
                if main < 0 and normal > 0:
                    normal -= 1
                    main += 1
                if weak <= 0 and normal <= 0 and main < 0:
                    return 0, weak, normal       # the safe floor (see docstring)
            return main, weak, normal
        v, d, vi = self.vaccine, self.data_power, self.virus
        v, d, vi = comp(v, d, vi)
        d, vi, v = comp(d, vi, v)
        vi, v, d = comp(vi, v, d)
        self.vaccine, self.data_power, self.virus = v, d, vi

    def use_item(self, key):
        """Consume one inventory item -> a short result message ('' = the
        item does nothing here, None-equivalent = don't have it).  The
        DSprite item table, cloned from v0.4.x (BASIC VPET 2026-07-16): the
        DVPet consumable machine -- meds, bandages, vitamins, toys, futons,
        transports, digimentals, crafters -- left with the item system.  A
        _Refused message keeps the item ('consume on refusal' burned
        Rev.Floppies on live pets; clone audit 2026-07-15)."""
        if self.inventory.get(key, 0) <= 0:
            return "None left."
        # the crest eggs (Armor-Spirit): the ONE clone item family that maps
        # onto a classic system -- each virtue joins its Digimental's
        # EvolItemID, so the armor evolutions stay reachable (the dub swap is
        # deliberate: reliability->Purity(18), destiny->Fate(25))
        if key.startswith("egg_of_"):
            return self._crest_egg(key)
        # the DVPet staple props (items.csv 81-83; Joel 2026-07-17: "look at
        # what dsprite has for items... should be like a toilet"): they carry
        # their own guards -- the generic disturb/consume below never runs
        if key in ("i:82", "i:83"):
            return self._manual_toilet(key)
        if key == "i:81":
            return self._futon()
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
            "x_antibody": self._x_item,
            "training_pack": self._training_pack,
            "revive_floppy": self._revive_item,
            "super_carrot": self._super_carrot,
        }.get(key)
        if fx is None:
            return ""
        # life-state guard: only the Rev.Floppy works on the dead, and
        # NOTHING works on an egg
        if self.dead and key != "revive_floppy":
            return _Refused("")
        if self.stage == "Egg" or self.num < 0:
            return _Refused("")
        # item on a sleeper: the alarm wakes mistake-FREE (its whole point),
        # the sleeping pill is pointless, anything else DISTURBS -- then applies
        if self.asleep and key not in ("alarm_clock", "sleeping_pill"):
            self._disturbed()
        out = fx()
        if not isinstance(out, _Refused) and out is not None:
            self.take_item(key)
        return out

    # ⛔ JP/EN DIGIMENTAL GOTCHA (armor canon audit 2026-07-17, the KO6
    # stage-name class): JP 誠実 "Sincerity" is the EN dub's RELIABILITY
    # egg -- the WATER family (item 20: Submarimon/Depthmon/Tylomon...);
    # JP 純真 "Purity" is the EN dub's SINCERITY egg (item 18: Shurimon/
    # Ponchomon...).  The v0.5.5 map wired the EN names backwards, so the
    # Sincerity Egg sold the water armors and Reliability the ninjas.
    _CREST_IDS = {"egg_of_courage": 15, "egg_of_friendship": 16,
                  "egg_of_love": 17, "egg_of_reliability": 20,
                  "egg_of_knowledge": 19, "egg_of_sincerity": 18,
                  "egg_of_hope": 21, "egg_of_light": 22,
                  "egg_of_kindness": 23, "egg_of_miracles": 24,
                  "egg_of_destiny": 25}

    def _crest_egg(self, key):
        """A crest egg -> the classic Digimental item-evolution flow."""
        if self.dead or self.stage == "Egg" or self.num < 0:
            return _Refused("")
        item_id = self._CREST_IDS.get(key, -1)
        target = evolution.item_select(self, item_id)
        if target is None:
            self._set_anim("refuse", 1.0)
            return _Refused(f"{self.name} can't use that yet.")
        if self.asleep:
            self._disturbed()
        prev = self.num
        self.evolve_to(target)
        lines_mod.adopt_line(self, prev=prev)     # a special jump re-anchors
        self.take_item(key)
        self._set_anim("happy", 1.6)
        from . import persistence as _persist
        _persist.armor_add(1)                 # the crest-wave shop gate counts it
        return f"{self.name} armor-evolved!"

    def _gain_energy(self, n):
        self._set_energy(self.energy + n)
        return "Energy restored!"

    def _fruit(self, quality):
        if self.hunger >= FULL_HUNGER and quality >= 0:
            return _Refused("Refused - belly's full.")
        self.hunger = _clamp(self.hunger + 1, 0, FULL_HUNGER)
        if quality > 0:
            self.strength = _clamp(self.strength + quality - 1, 0, 4)
        elif quality == 0:
            self._set_weight(self.weight + 3)
        return "Munch."

    def _deadly(self):
        self.dead = True
        self.death_cause = "a deadly fruit"
        return "...that fruit was DEADLY."

    def _junk(self):
        self.hunger = FULL_HUNGER
        self._set_weight(self.weight + 4)
        self.care_mistakes += 1
        return "Delicious. Regrettable."

    def _premium_meat(self):
        self.hunger = FULL_HUNGER
        self.full_until = self.world_seconds + 12 * 60.0   # 12 game-hours of satiety
        return "Satiated for 12 hours."

    def _smart_potty(self):
        self.clean()
        self.auto_clean_until = self.world_seconds + 24 * 60.0   # a game day
        return "Auto-clean for 24 hours."

    def _erase_mistake(self):
        if self.care_mistakes <= 0:
            return _Refused("No mistakes to erase.")
        self.care_mistakes -= 1
        return "One mistake, forgotten."

    def _sleep_pill(self):
        if self.asleep:
            return _Refused("It's already asleep.")
        self._fall_asleep()
        self.lights = False
        return "Zzz..."

    def _alarm(self):
        """Wake Up Without Mistake: a clean wake, no disturb penalty."""
        if not self.asleep:
            return _Refused("It's already awake.")
        self.asleep = False
        self.nap = False
        self.lights = True
        self.awake_lapse = 0.0
        return "Rise and shine!"

    def _time_gear(self):
        self.stage_seconds += 120.0        # +120 game-minutes of growth
        return "Time lurches forward."

    def _anti_evo(self):
        self.evo_blocked = not getattr(self, "evo_blocked", False)
        return "Evolution " + ("BLOCKED." if self.evo_blocked else "unblocked.")

    def _x_item(self):
        """The X-Antibody chip: raises the X state (the classic X system)."""
        if self.x_antibody != "None":
            return _Refused("The antibody already runs in it.")
        self._set_xantibody("Permanent")
        from . import persistence as _persist
        _persist.note_xanti()
        return "The X-Antibody takes hold!"

    def _training_pack(self):
        self.stage_trainings += 5
        return "Training +5."

    def _revive_item(self):
        if not self.dead:
            return _Refused("No one needs reviving.")
        self.save_from_death()
        return "It LIVES."

    def _super_carrot(self):
        if self.weight <= 1:
            return _Refused("Nothing left to trim.")
        self._set_weight(max(1, self.weight - 10))
        return "Feather-light!"

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
        # sleepy keys on the pet's own bedtime window now (the night phase
        # left with the day/night system -- BASIC VPET 2026-07-17)
        if self._in_sleep_window() and not self.asleep and self.energy < self.max_energy // 2:
            return "sleepy"
        if self.mood <= MIN_UNHAPPY_MOOD:
            return "unhappy"
        if self.mood >= MIN_HAPPY_MOOD:
            return "happy"
        return "ok"
