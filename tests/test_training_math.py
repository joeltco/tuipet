"""Training/tournament math audit (2026-07): canon re-verification vs the
decompile (PhysicalState.exercise/setExercise, ClockTic.onExerciseFinish,
Tournament.java, config.csv column 1).

Verified matching: every minigame constant (VaccineGameHitsMin 16/20/24,
VirusGameBarMin 86 + speeds 5/4/3, DataTrainShootFrame 10/7/5, difficulty
ranks //75 and //11, hpRounds 3/won 2), fail penalties (mood -10 /
obedience -1), fav/disliked-time mood+spirit numbers, fatigue odds
(60/40 +-5 compat), mood += enthusiasm, the tournament tables (bits/ages/
powers/health bands), the 7-NPC + player bracket, the attribute power
split (/2 main, /6 weak, /3 mid) and the QF/semi/final payout ladder.

Fixed (canon divergences):
 * exercise() runs BEFORE the success check: the Effort +1, the spirit
   costs and the fatigue-at-cap roll land WIN OR LOSE.
 * The success obedience+1 was invented; canon grants the PRAISE flag.
 * ExerciseWeightDec=0 (classic): no flat -2; the body cost is caloric --
   an activity decrement landing in deficit sheds ActivityWeightChange.
 * A neutral attribute costs -2 spirit (NotFavDec), not the disliked -3;
   a sour pet pays -1 on the HP drill (the None branch).
 * The purse truncates its running total per entrant (calcBits)."""
import random

from tuipet.pet import Pet
from tuipet import tournament


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500,
            energy=24, max_energy=24, weight=20, strength=0, mood=0)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_effort_fills_win_or_lose():
    p = _pet()
    p.apply_training(0, 0, game="hp")            # a total whiff
    assert p.strength == 1                       # exercise() ran anyway
    assert p.praise_flag is False                # ...but no praise for failing


def test_weight_sheds_only_in_calorie_deficit():
    p = _pet(calories=5)
    p.apply_training(2, 100, attribute="Vaccine", game="vaccine")
    assert p.weight == 20                        # buffered: no shed
    q = _pet(calories=-3)
    q.apply_training(2, 100, attribute="Vaccine", game="vaccine")
    assert q.weight == 19                        # deficit: ActivityWeightChange -1


def test_purse_truncates_per_entrant():
    p = _pet()
    t = object.__new__(tournament.Tournament)
    t.pet = p
    t.trophy = {"bit_mod": 1.1}
    t.entrants = [{"stage": "Rookie"}] * 7       # 125 x 1.1 = 137.5 each
    assert t._calc_bits() == 959                 # per-step floor; a float sum says 962


def test_purse_integer_modifiers_unchanged():
    p = _pet()
    t = object.__new__(tournament.Tournament)
    t.pet = p
    t.trophy = {"bit_mod": 1}
    t.entrants = [{"stage": "Champion"}] * 7
    assert t._calc_bits() == 7 * 150


def test_refused_drill_closes_the_menu_like_canon():
    """Canon onPreTrain: !canExercise -> _currentMenu = Menu.None + State.Refusing.
    The old silent stay-in-menu made a refusal look like a DEAD drill (the menu
    never renders self.flash) -- the 'virus training isn't working' report."""
    from tuipet import training
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=0)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    tp = training.TrainingPanel(p)
    tp.key("right")                                  # browse to an attribute drill (Vaccine)
    p.check_refused = lambda **kw: True              # force the roll
    r = tp.key("enter")
    assert r is not None and r[0] == "done" and "refuses" in r[1]
    assert tp.phase == "menu"                        # never entered play
    assert p.anim == "refuse"                        # State.Refusing for the LCD head-shake


def test_compliant_start_still_enters_play():
    from tuipet import training
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=1000)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    p.check_refused = lambda **kw: False
    tp = training.TrainingPanel(p)
    for _ in range(3):                               # browse the ring to Virus
        tp.key("right")
    assert tp.key("enter") is None                   # no close envelope on success
    assert tp.phase == "play" and tp.gkey == "virus"
    tp2 = training.TrainingPanel(p)
    tp2.key("4")                                     # number-key start routes the same
    assert tp2.phase == "play" and tp2.gkey == "virus"


# (test_species_time_seeds... left with the timeRanks system --
# BASIC VPET 2026-07-17)


