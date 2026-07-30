"""HOW OFTEN the pet asks for something — the call clocks fixed 2026-07-30.

Joel, working through the sickness audit's flags: "fix those two also", then
"fix the hunger and strength ones too".  Every one of them carried the same slip
as the filth-sickness bound: a real-SECONDS shape sitting on a clock that counts
game-MINUTES.

  * the MISCHIEF call rolled `dt / (60.0 * 90.0)` -- "90 minutes" written in
    seconds -- so a tantrum arrived once every 3.75 GAME-DAYS (90 real min),
    while canon's whole checkDisciplineCall family (target 16, bound
    DisciplineCallChance 150 - (ObedienceRefusalCap 100 - obedience), checked
    every DisciplineCallMin 59 minutes) sat in petbase.py with no consumers.
  * the FILTH tantrum waited on a magic `1800` -- "30 minutes" in seconds --
    so a pet stood in a full room for 1.25 GAME-DAYS before complaining, then
    postponed itself -3600 where canon's AfterMistakeMinutesPostponed is -60
    (the LIGHTS call in the same file had it right all along).

These pins are about cadence, in the units a player feels.  Nothing here pins
the CONSEQUENCES: the scold window's fairness and the Pen20 rule that filth
costs no care mistake are pinned below because both are what make a brisker
call safe.
"""
import random
import statistics

from tuipet import petbase
from tuipet.pet import Pet

GAME_MIN_PER_GAME_DAY = 1440.0


def _pet(obedience=None, piles=0):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    p.poop, p.poop_sizes = piles, [2] * piles
    if obedience is not None:
        p.obedience = obedience
    return p


def _mischief_p(obedience):
    bound = max(1, petbase.DISCIPLINE_CALL_CHANCE
                - (petbase.OBEDIENCE_REFUSAL_CAP - obedience))
    return petbase.DISCIPLINE_TARGET_CHANCE / bound / petbase.DISCIPLINE_CALL_MIN


# ---- the mischief call ------------------------------------------------------

def test_the_mischief_clock_is_canons_own_family():
    assert petbase.DISCIPLINE_CALL_MIN == 59            # DisciplineCallMin
    assert petbase.DISCIPLINE_TARGET_CHANCE == 16       # DisciplineCallTargetChance
    assert petbase.DISCIPLINE_CALL_CHANCE == 150        # DisciplineCallChance
    assert petbase.OBEDIENCE_REFUSAL_CAP == 100         # ObedienceRefusalCap


def test_a_tantrum_arrives_within_a_game_day_not_once_a_week():
    """The defect, in player units: 3.75 game-days between tantrums meant a
    pet that essentially never asked for discipline."""
    mean_days = 1.0 / _mischief_p(100) / GAME_MIN_PER_GAME_DAY
    assert mean_days < 1.0, mean_days
    assert mean_days > 0.1, mean_days            # not a nag every few minutes
    old = 1.0 / (1.0 / (60.0 * 90.0)) / GAME_MIN_PER_GAME_DAY
    assert old > 3.0 and mean_days < old / 5     # strictly, hugely more often


def test_manners_change_the_odds_the_canon_way():
    """A rude pet acts up more, a well-mannered one less -- the obedience term
    the hand-made rate could not express at all."""
    assert _mischief_p(10) > _mischief_p(100) > _mischief_p(150)


def test_the_tantrum_really_fires_on_the_real_tick():
    """Drive _tick_mortality and measure, so the pins can't pass on arithmetic
    while the wiring is dead (the way the filth roll once did)."""
    random.seed(5)
    waits = []
    for _ in range(120):
        p = _pet(obedience=100)
        t = 0
        while not p.discipline_call and t < 5 * GAME_MIN_PER_GAME_DAY:
            p.world_seconds += 1.0
            if p._tick_mortality(1.0):
                break
            t += 1
        if p.discipline_call:
            waits.append(t)
    assert len(waits) > 110, f"only {len(waits)}/120 pets ever acted up"
    med_days = statistics.median(waits) / GAME_MIN_PER_GAME_DAY
    assert 0.05 < med_days < 1.0, med_days


def test_the_scold_window_stays_human_fair():
    """What makes a brisker call safe: canon's ScoldWindowMax is 2 MINUTES;
    tuipet answers in 600 game-min = 10 REAL minutes.  If this shrinks, the
    cadence above becomes a mistake treadmill."""
    p = _pet()
    p.world_seconds = 1000.0
    p._open_scold()
    assert p.scold_window - p.world_seconds >= 600.0


# ---- the filth tantrum -----------------------------------------------------

def test_the_filth_clock_and_its_postpone():
    assert petbase.FILTH_ACT_UP_MIN == 30
    assert petbase.CALL_POSTPONE_MIN == -60.0          # canon, not -3600
    assert petbase.LIGHTS_MISTAKE_POSTPONE == petbase.CALL_POSTPONE_MIN


def test_a_full_room_draws_a_complaint_in_minutes_not_days():
    p = _pet(piles=3)
    hits = []
    for _ in range(int(2 * GAME_MIN_PER_GAME_DAY)):
        p.world_seconds += 1.0
        p.poop, p.poop_sizes = 3, [2, 2, 2]            # nobody cleans up
        before = p.scold_window
        p._tick_body(1.0)
        if p.scold_window != before:
            hits.append(p.world_seconds)
    assert hits, "a pet in a full room never complained"
    first = hits[0]
    assert 25 <= first <= 35, f"first complaint at {first} game-min"
    # grace 30 + postpone 60 => roughly one complaint per 90 game-min after
    gaps = [b - a for a, b in zip(hits, hits[1:])]
    assert gaps and 80 <= statistics.median(gaps) <= 100, statistics.median(gaps)


def test_filth_acting_up_still_costs_no_care_mistake():
    """LINES_SPEC §5 / Pen20: care mistakes are unanswered CALL LIGHTS only.
    The complaint may now be brisk precisely because it is not a punishment."""
    p = _pet(piles=4)
    before = p.care_mistakes
    for _ in range(int(3 * GAME_MIN_PER_GAME_DAY)):
        p.world_seconds += 1.0
        p.poop, p.poop_sizes = 4, [2, 2, 2, 2]
        # a well-fed, well-drilled pet: the ONLY thing wrong is the room, so a
        # mistake here could only have come from the filth (the hunger and
        # strength call lights DO cost mistakes, and would mask this)
        p.hunger, p.strength = 4, 4
        p._tick_body(1.0)
    assert p.care_mistakes == before
    assert p.discipline_call is False            # it opens a window, not a call


def test_a_clean_room_resets_the_clock():
    p = _pet(piles=3)
    for _ in range(20):
        p._tick_body(1.0)
    p.poop, p.poop_sizes = 0, []
    p._tick_body(1.0)
    assert p._filth_t == 0


# ---- the neglect cooldown (Joel: "fix the hunger and strength ones too") ----
#
# Every call light postpones itself after billing a mistake, and canon's
# AfterMistakeMinutesPostponed is -60.  The LIGHTS call always used it; filth,
# HUNGER and STRENGTH carried -3600 under the same canon citation -- 60x too
# long.  The 600-game-min (10 REAL minute) answer window is the deliberate
# adaptation and is NOT touched; only the repeat rate is.

def _tended(**kw):
    """A pet with exactly one thing wrong, awake, so one call path is isolated
    (the lights call bills mistakes that look like yours otherwise)."""
    p = _pet()
    p.energy = p.max_energy
    p.asleep = False
    p.lights = True
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_every_call_postpones_by_the_canon_minute():
    assert petbase.CALL_POSTPONE_MIN == -60.0
    assert petbase.LIGHTS_MISTAKE_POSTPONE == petbase.CALL_POSTPONE_MIN


def test_the_hunger_call_keeps_its_ten_real_minute_window():
    p = _tended(hunger=0)
    for _ in range(599):
        p.asleep = False
        p._tick_hunger(1.0)
    assert p.care_mistakes == 0, "the answer window shrank"
    p._tick_hunger(1.0)
    assert p.care_mistakes == 1
    assert p._hunger_call_t == petbase.CALL_POSTPONE_MIN


def test_the_strength_call_keeps_its_window_and_takes_the_canon_cooldown():
    p = _tended(strength=0)
    for _ in range(599):
        p.asleep = False
        p.strength = 0
        p._tick_body(1.0)
    assert p.care_mistakes == 0, "the answer window shrank"
    p.strength = 0
    p._tick_body(1.0)
    assert p.care_mistakes == 1
    assert p._str_call_t == petbase.CALL_POSTPONE_MIN


def test_an_empty_gauge_bills_again_on_the_canon_cycle():
    """600 window + 60 postpone = a mistake per 660 AWAKE game-min (11 real
    min).  At -3600 it was 4200 (70 real min), which is what made a pet you
    never drill effectively unpunishable."""
    p = _tended(strength=0)
    marks = []
    for i in range(2000):
        p.asleep = False
        p.strength = 0
        before = p.care_mistakes
        p._tick_body(1.0)
        if p.care_mistakes > before:
            marks.append(i)
    assert len(marks) >= 3, marks
    gaps = [b - a for a, b in zip(marks, marks[1:])]
    assert all(650 <= g <= 670 for g in gaps), gaps


def test_starvation_still_outruns_the_hunger_cooldown():
    """Why the hunger leg barely moves, and why that is correct: nothing about
    the cooldown matters once STARVE_DEATH_MIN ends an empty belly.  One
    mistake, then the pet starves."""
    assert petbase.STARVE_DEATH_MIN == 720
    p = _tended(hunger=0)
    for _ in range(1500):
        if p.dead:
            break
        p.asleep = False
        p.hunger = 0
        p._tick_hunger(1.0)
        p._tick_mortality(1.0)
    assert p.dead and p.death_cause == "starvation"
    assert p.care_mistakes == 1, p.care_mistakes
