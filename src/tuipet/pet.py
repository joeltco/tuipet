"""DVPet game model: a single virtual pet, its stats, and care logic.

Tier-5 split (2026-07-17): the constants + pure helpers live in petbase
(star-imported back, so `from .pet import X` never moved).
"""
from __future__ import annotations
import math  # noqa: F401
import random  # noqa: F401
from dataclasses import dataclass, field as _dcf
from . import data  # noqa: F401
from . import shop  # noqa: F401
from . import egg as egg_mod  # noqa: F401
from . import evolution  # noqa: F401
from . import lines as lines_mod  # noqa: F401
from . import backgrounds  # noqa: F401
from . import theme  # noqa: F401
from .petbase import *  # noqa: F401,F403  (the constant bed; __all__ carries _names)
from .petbattle import BattleMixin
from .petbody import BodyMixin
from .petcare import CareMixin
from .petdna import DnaMixin

@dataclass
class Pet(CareMixin, DnaMixin, BattleMixin, BodyMixin):
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
    dna_wager_pending: int = 0      # a paid mash in flight -- settled spoiled on relaunch (S2)
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
    dp: int = 0                     # Pen20 DP meter 0..4: full to jogress; 3h sleep refills it
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
    death_banked: bool = False      # this death's etch/seed ceremony already ran
    #                                 (rides the save: a quit mid-dying-beat used
    #                                 to disinherit the heir; audit 2026-07-19)
    # long-horizon clocks (persisted: losing these on reload forgave starvation,
    # wiped the bowel gauge and re-armed once-per-night mistakes -- audit 2026-07)
    _starve_t: float = 0.0          # the 12h starvation death clock
    _poop_t: float = 0.0            # the bowel gauge (written as durable state by meals)
    _filth_t: float = 0.0           # filth-mistake grace / post-mistake postpone
    _lights_t: float = 0.0          # lights-on sleep mistake (float(-inf) = once/night latch)
    _cal_t: float = 0.0             # calorie/hunger lapse accumulator
    _str_t: float = 0.0             # effort-decay accumulator
    # the four that escaped the lesson above (audit F8, fixed 2026-07-20):
    # quit-cycling billed call mistakes up to 7x faster (or forgave a 599s
    # window), never billed the assistant retainer, and shed DP progress
    _hunger_call_t: float = 0.0     # hunger-call answer window / post-mistake postpone
    _str_call_t: float = 0.0        # effort-call answer window / post-mistake postpone
    _ac_pay: float = 0.0            # the assistant's hourly retainer accumulator
    _dp_t: float = 0.0              # sleep DP-refill accumulator
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
    # (the old adventure fields -- adv_map/adv_zone/adv_seek/adv_loc -- left
    # with the world layer; BASIC VPET 2026-07-16.  The adventure REBUILD
    # 2026-07-20 tracks progression with ONE field: the number of zones
    # conquered = the index of the current frontier zone in adventure.ZONES.
    # Auto-persisted (asdict / fields(Pet)); old saves default to 0.)
    adv_progress: int = 0
    # THE RIVAL (cup fun arc 2026-07-21): the mon that last ELIMINATED you
    # from a cup bracket -- it re-seeds into future brackets its tier fits,
    # until revenge settles the grudge.  Real losses only, never forfeits.
    rival_num: int = -1
    rival_name: str = ""
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
    inventory: dict = _dcf(default_factory=dict)
    # the day's town-counter purchases {"day": ordinal, "<tid>:<key>": n} --
    # the authored maxStock caps a town's daily take (shops arc 2026-07-21:
    # DVPet's 375b town steak vs the 2000b catalog would otherwise be a
    # money printer through the demand resale)
    town_bought: dict = _dcf(default_factory=dict)
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
        # (the DVPet StartingUses grant -- Toilet/Bandage/Futon -- left with
        # the staple props: strict-DSprite items, 2026-07-17.  DSprite's
        # catalog has no furniture; a fresh device starts with an empty bag.)
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


        # (the sickness recovery lapse, the sick bowel-race penalty and the
        # 6h malady death left with the sickness system (BASIC VPET 2026-07-17); the injury/
        # fatigue/vitamin timers left with theirs, 2026-07-16)

        # incMistake's sickness risks (sickness/injury audit 2026-07-06):
        # filth rolls per pile with a misery pad, and ANY mistake while
        # fatigued adds a 1/1 whisper.  Canon's 50/50 poopCall branch is
        # PROVABLY DEAD in the shipped config (poop/filth audit: the filth
        # array holds 6 piles, MistakeFilthLimit is 7 -- countFilth can never
        # reach it), so it is not ported.
        # (incMistake's filth/fatigue sickness risks left with the sickness
        # system (BASIC VPET 2026-07-17))


        # (the filth sickness rolls left with the sickness system (BASIC VPET 2026-07-17); the
        # filth MOOD nag above is inert since the mood removal but stays as
        # the canon citation it became)


        # (the filth sickness rolls moved to _filth_effects -- canon shape; the
        # old flat roll also invented a STARVATION sickness canon does not have)

    WAKE_MINUTE = 7 * 60          # LINES_SPEC §5: every line form wakes at 7:00


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


    # (effect_name/call_paused -- the careEffect runtime, Futon-only -- left
    # with the staple props: strict-DSprite items, 2026-07-17)

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
        self.death_banked = False       # the NEXT death owes a fresh ceremony
        self.saved_from_death += 1
        self.hunger = HUNGER_AFTER_SAVED
        self.sick = False               # the clone's revival fix: a fresh
        #                                 revival must not come back sick
        self._starve_t = 0.0                          # the 12h clock restarts
        self.evol_bonus += BONUS_AFTER_SAVED
        # RevivalLifeInc RESTORES life -- the revived pet leaves with at
        # least REVIVAL_LIFE of runway.  The old unconditional jump was
        # canon-shaped for old-age deaths only: on a young pet's sickness/
        # poison/neglect rescue it silently BURNED the rest of the lifespan
        # down to that floor (SUSPECT S1 ruling 2026-07-20)
        self.age_seconds = min(self.age_seconds,
                               max(0.0, self.lifespan - REVIVAL_LIFE))
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
        if self.dead or self.stage == "Egg":
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
        """sleepNotNap: nod-off sits inside the real-sleep edge -- the yawning
        special idle's eligibility (and lights-out now means SLEEP).  Routed
        through the model-aware _near_bedtime so LINE pets (the wall-clock
        sleepers -- every hatch) roll their pre-bed yawn too; the pressure
        path inside is verbatim what stood here."""
        return self._near_bedtime(
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


    _ATTR3 = ("Vaccine", "Data", "Virus")


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
        """DERIVED (no mood meter): the word keys off LIVE state.  Unhappy
        when unwell or unfed; HAPPY when perfectly kept -- condition tier 3
        with nothing else wrong, the same "bright" bar the walk poses use.
        The old derivation stopped at Neutral, so every Happy consumer (the
        good birthday, the battle power doubling, the happy idle, the grade's
        +1) was unreachable for the life of the app (MED audit 2026-07-19)."""
        w = self.status_word()
        if w in ("sick", "starving", "needs cleaning"):
            return "Unhappy"
        if w == "ok" and self.condition() == 3:
            return "Happy"
        return "Neutral"

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


    # (apply_training -- the four-drill DVPet versus training, its attribute
    # power growth, taste-rank ledger and Effort-per-drill -- left with the
    # classic training system (0.5 TRAINING 2026-07-17).  Powers now grow
    # ONLY through battle wins (record_battle's canon setPower +1 stays);
    # Effort fills via the pill; the drill trains FORM.  The attr-rank
    # ledger below is INERT -- nothing warms it, and _power_bonus_attr
    # falls through to the species seed.)


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


    def _growth_period(self):
        """The growth curve's total: egg + every stage through the current one
        (canon _growthPeriod; the longevity leg credits life lived past it).
        Mega's 9e9 STAGE_DURATION is the "never auto-evolves" sentinel, not a
        duration -- summing it graded every Mega 0 (gameplay audit
        2026-07-19); the curve ends at REACHING the final form."""
        order = ("Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega")
        total = float(self.EGG_DURATION)
        for st in order:
            d = self.STAGE_DURATION.get(st, 0)
            if d < 9e8:
                total += d
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
        # (the obedience legs left with the discipline system: the meter is
        # pinned at 0, so `< BONUS_DEC_OBEDIENCE` docked EVERY graded life
        # -1 while the +1 was unreachable -- a removed system must not bill
        # a live formula (MED audit 2026-07-19))
        if self.battles and (self.wins / self.battles * 100.0) >= BONUS_INC_WIN_RATE:
            b += 1
        # longevity: whole days lived past the growth curve (negative if short).
        # int(x / D), not x // D: canon's Java long division truncates toward
        # ZERO, so a short life loses only its WHOLE missing days (digimemory
        # audit 2026-07-06 -- floor division over-penalized by one).  The day
        # is the MEMORIAL's day (86400s, "Lived N days"): the 1440 game-min
        # day paid +175..+295 for ANY natural life, swamping the card's +-1
        # fine structure (gameplay audit 2026-07-19)
        b += int((self.age_seconds - self._growth_period()) / 86400.0)
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


    # (the Play action left 2026-07-17: it was spoil() -- mood up, obedience
    # down -- and the mood system is gone, so all it did was punish obedience
    # for a hop.  The clone has no play key; the "play" fx/pose stays for the
    # toy items (itemfx Play/Bounce scripts).)


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
