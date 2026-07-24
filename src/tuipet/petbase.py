"""The pet's CONSTANT BED + pure helpers (tier-5 stage A, 2026-07-17):
every tuning number, canon table and pure function the sim reads --
extracted whole from pet.py's pre-class region so the coming mixins (and
pet.py itself) can star-import one leaf module and resolve every name in
their own namespace.  `from .pet import ANYTHING` still works: pet.py
star-imports this module back under the __all__ below."""
from __future__ import annotations


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
# (the DVPet lifespan clock -- LIFE_START / STAGE_LIFE / the whole LifeDec
# burn economy -- left with the DSprite mortality ruling, Joel 2026-07-22:
# "we gotta do it how dsprite does. life bar must be a dvpet forgotten
# relic".  Death is the clone's per-minute hazard roll now; age alone
# defines the elder.)
GERIATRIC_AGE_DAYS = 15      # the clone's elder line: age_days >= 15 (v0.4.12 L926)
AGE_DAY = 86400.0            # one REAL day of age_seconds (the clone's DAY_MINUTES scale)
GERIATRIC_REMAIN = 21600.0   # stomach-shrink window: the first N seconds past the elder line

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
# (BonusLifeInc/Dec + BonusEvolutionLife left with the lifespan clock --
# DSprite mortality 2026-07-22; the birthday still moves evol_bonus + items)
# DVPet DigiMemory / inheritance (PhysicalState.setNewDigimemory / getDigimemory,
# item 32 anim Inherit; config.csv DigimemoryAttributeCoefficient / LifeInc).  The
# departed etches its attack powers -- scaled by the care bonus it died holding --
# into the Digimemory; the HEIR uses the item to add Va/D/Vi.  (The chip's
# lifespan leg left with the lifespan clock -- DSprite mortality 2026-07-22;
# old chips' "seconds" payloads load fine and are simply not applied.)
DIGIMEMORY_ATTR_COEF = 0.01         # DigimemoryAttributeCoefficient
# (the birthday grants speak the TUIPET catalog keys since 2026-07-18 --
# the raw DVPet food ids landed items the strict bag could neither show
# nor use, a reward the player never received; item review 2026-07-18)
GOOD_BIRTHDAY_FOOD = "cupcake"
BAD_BIRTHDAY_FOOD = "candy"
NORMAL_BIRTHDAY_FOOD = "cookie"
WIN_RATE_BONUS_COEF = 0.1           # winRateRookieBonusIncCoefficient (champion: 0.1*winRate - 5)
# saveFromDeath: frantic taps during the dying beat can pull the pet back
HITS_TO_SAVE = 30                   # HitsToSave 175 mouse-clicks over DVPet's ~7s jingle,
                                    #   scaled to a ~6/s keyboard mash over tuipet's 5s beat
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
# THE BODY TELLS (canon special-idle rolls, restored 2026-07-23: both fx
# shipped fully painted and NOTHING ever fired them).  Each fx's own
# docstring names its trigger, and these are those numbers:
# poopDance rolls "while the need APPROACHES (>= 80%% of the interval)"
# -- canon dances on a FULL gauge, but tuipet fires the poop the moment
# it fills, so the tell has to come earlier; yawning() is "the
# special-idle tell that bedtime NEARS", i.e. the last tenth of the
# awake window (the doze-off keeps its own simple two-pose yawn anim).
POOPDANCE_AT = 0.8                      # fraction of the bowel gauge
YAWN_AT = 0.9                           # fraction of awake_limit
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
# (DVPet toilet training -- MinToiletUsesToTrain / the SelfToilet branch and
# its stage/obedience gates -- left with the staple props: strict-DSprite
# items, 2026-07-17)
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
# ---- the DSprite mortality (rebuilt 2026-07-22, Joel: "we gotta do it how
# dsprite does. life bar must be a dvpet forgotten relic"): NO lifespan
# clock, no burns -- death is ONE per-minute hazard roll, the sum of the
# first matching mistake bracket, the sick whisper above, and the first
# matching age bracket.  A healthy pet with <5 mistakes under age 15 CANNOT
# die by the roll.  Tables verbatim from the clone (v0.4.12 L45-47); the
# discrete nets (20-mistake cap, Pen20 frailty, 12h starvation) stand
# beneath it as before -- Pen20 is LINES_SPEC §5 contract, not clock.
DEATH_MISTAKES = ((20, 0.0015), (15, 3.75e-4), (10, 7.5e-5), (5, 1.5e-5))
DEATH_AGE = ((25, 3.75e-4), (20, 1.5e-4), (15, 3.75e-5))
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
BATTLE_MIN_ENERGY = 10              # the source's battle gate (canon gates 2026-07-18,
#                                     decompile L11746: energy < 10 refuses the fight)
# THE INJURY ROLL (canon restoration 2026-07-23: the decompile's
# BattleInjury table, adapted to today's tree -- the fatigue/mood
# coefficients left with their systems).  Chance out of BATTLE_INJ_BOUND
# per LOCAL recorded bout: condition good/bad x vitamin active or not,
# +BATTLE_INJ_LOSS on a loss, +BATTLE_INJ_BAD_AGE for an elder or an
# InTraining baby.  "Bad" condition = starving, drained, weight >= 8g
# off base, or already sick.  A live vitamin is the canon guard
# (good_v 0 / bad_v 25 -- the vitamin's second job on the device).
# INJURY RECOVERY (P4 ruling 2026-07-23): canon heals a wound on a clock
# -- `randint(1, 12) * InjLapseMin` game-min -- and v0.5.205 shipped the
# ailment WITHOUT it, leaving a 300b shop-only Bandage as the only cure
# while its sibling ailment has a free infinite one.  Restored, with the
# lapse SCALED: canon's 29 is device real-minutes, which under THE UNIT
# LAW would be 29 real SECONDS here (an injury gone before you noticed),
# while the flat /60 precedent would run up to 5.8 real HOURS (longer
# than any session).  300 game-min = 5 real minutes a lapse, so a wound
# lasts 5-60 real minutes of play.  The Bandage stays the INSTANT cure:
# it now buys time rather than being the only door.
MIN_INJ_LENGTH, MAX_INJ_LENGTH = 1, 12  # Min/MaxInjLength, canon
INJ_LAPSE_MIN = 300                     # game-min per lapse (canon 29 = device real-min)
BATTLE_INJ_BOUND = 1000
BATTLE_INJ_TABLE = {"good_v": 0, "good_nv": 3, "bad_v": 25, "bad_nv": 100}
BATTLE_INJ_LOSS = 50                # BattleInjuryWonFactor, added on a LOSS
BATTLE_INJ_BAD_AGE = 10             # BattleInjuryBadAgeFactor (elder OR baby)
DEATH_INJ_P = 7.5e-5                # the death whisper while hurt (sick's scale)
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
# tuipet's shrink runs over the GERIATRIC_REMAIN window PAST the elder line
# (age-based since the DSprite mortality port 2026-07-22) -- same endpoint shape
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
# (the ENTIRE LifeDec family -- HungerMistake/Sick/Injury/WorseMalady/
# Fatigue/GeriatricFatigue/XAntibody LifeDec, live and dormant alike --
# left with the lifespan clock: DSprite mortality, Joel 2026-07-22.
# Neglect kills through the hazard tables below now, not through burns.)
# (the X-PROGRAM survival roulette constants left with their item -- the
# X-Program sample was cut with the strict-DSprite shelf 2026-07-17 and
# nothing rolled them since; dossier audit 2026-07-22.  The X-Antibody
# CHIP never carried the roulette.)
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
# one (food 43); asleep it cleans, then dims a lit room.  Every visit bills the
# stage price AND costs bond -- mood -10,
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
# (GoodNutritionLifespanDecCoefficient left with the lifespan clock -- it
# never had a consumer here; DSprite mortality 2026-07-22)
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
# (BadMedLifeDec + BadVitaminLifeDec left with the lifespan clock --
# DSprite mortality 2026-07-22; they had no live consumer since the
# medicine slim anyway)
BAD_MED_BM_INC = 6                       # BadMedBMInc (bowel gauge lurch)
BAD_VITAMIN_MOOD_DEC = 8                 # BadVitaminMoodDec
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




# every name (underscored included) rides the star-import back into pet.py
# and into each mixin module -- the tier-5 name-resolution contract
__all__ = [n for n in dir() if not n.startswith("__")]
