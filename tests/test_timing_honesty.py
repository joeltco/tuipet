"""The bar-lock reflex honesty rework (Joel 2026-07-23: "i hit the
center every time, what are you talking about").

The marker steps every 100ms and a seen-centered press lands ~200-300ms
later (human reaction + terminal latency).  The old lock graded the
single live position, so a small window silently failed presses the
player SAW land -- the same class as the hazard dodge's rework.  Now:
ONE grading source (strikefx.grade_lock) for the drill and the bout,
a LOCK_GRACE of trailing steps, the 2px marker counting both its
pixels, and the window floored at 3px (a 1px window was a 100ms
target -- physically impossible in a terminal).
"""
from tuipet import strikefx
from tuipet.battlescreen import BattlePanel, mega_window
from tuipet.pet import Pet
from tuipet.strikefx import grade_lock
from tuipet.training import TrainingPanel


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_a_slightly_late_press_still_grades_mega():
    """The marker was IN the window within LOCK_GRACE steps of the press:
    the player saw a centered hit -- grade the hit they saw."""
    lo, hi = 11, 13
    assert grade_lock([13, 14, 15], lo, hi) == "mega"      # 2 steps late
    assert grade_lock([14, 15, 16], lo, hi) == "normal"    # 3 steps: too late


def test_the_two_pixel_marker_counts_both_pixels():
    """bar = lo-1 puts the marker's RIGHT pixel inside the window --
    visually in, so graded in (the old left-pixel-only rule failed it)."""
    assert grade_lock([10], 11, 13) == "mega"
    assert grade_lock([9], 11, 13) == "normal"


def test_the_window_never_shrinks_below_three():
    """o = 0 used to give a 1px window -- one 100ms step.  Floor: 3."""
    p = _pet(hunger=0, strength=0, battles=10, wins=0)
    p._set_energy(0)
    lo, hi = mega_window(p)
    assert hi - lo + 1 == 3


def test_both_panels_grade_through_the_grace():
    """The drill and the bout share the ONE source, trailing history
    included -- neither is a hand-copy anymore."""
    for pan in (BattlePanel(_pet()), TrainingPanel(_pet())):
        pan.mega_lo, pan.mega_hi = 11, 13
        pan._bar_hist, pan.bar = [13, 14], 15              # saw it centered
        if isinstance(pan, BattlePanel):
            pan.phase = "ready"
            pan._lock_bar()
            assert pan.locked == "mega"
        else:
            pan._lock()
            assert pan.grade == "mega"


def test_the_veteran_rule_lives_in_the_one_source():
    """battles >= 999 never whiffs -- VERBATIM v0.4.12, now in grade_lock."""
    assert grade_lock([0], 11, 13, veteran=True) == "mega"


def test_the_grace_is_what_the_history_holds():
    strikefx_grace = strikefx.LOCK_GRACE
    pan = TrainingPanel(_pet())
    for _ in range(10):
        pan.anim()
    assert len(pan._bar_hist) == strikefx_grace            # trailing steps only


def test_the_dig_meter_grades_through_the_grace_too():
    """The adventure dig meter was the THIRD hand-copy of the lock rule
    (Joel 2026-07-23: "and the dig action in adventure is ok? the one
    that uses the bar?") -- it grades through grade_lock now, grace,
    2px marker and veteran rule included."""
    from tuipet.adventurescreen import AdventurePanel
    pan = AdventurePanel(_pet())
    pan._find = "meat"
    pan._dig()
    m = pan._scene["meter"]
    m["lo"], m["hi"] = 11, 13
    m["hist"], m["bar"] = [13, 14], 15                     # saw it centered
    pan._scene["t"] = 999                                  # meter phase is live
    pan._lock_dig()
    assert pan._scene["grade"] == "mega"
    assert "×2" in pan._find_msg                           # the bonus copy banked


def test_the_intro_mash_cannot_lock_the_bar():
    """THE bug behind "im getting my ass kicked" (Joel 2026-07-23: "i was
    already landing megas every time in training"): training has no
    intro, the battle does -- mashing SPACE through the banner, the very
    next press hit the just-started bar at the LEFT EDGE and locked a
    miss/normal before the player ever started timing.  His save wore
    the fingerprint: training megas, saved form "normal".  A lock now
    arms LOCK_ARM_T ticks after the bar appears; ESC stays live."""
    from tuipet.battlescreen import LOCK_ARM_T
    pan = BattlePanel(_pet())
    pan.key("space")                          # mash: skip the intro
    assert pan.phase == "ready"
    pan.key("space")                          # mash: the very next press
    assert pan.battle is None                 # NOT locked at the left edge
    for _ in range(LOCK_ARM_T):
        pan.anim()
    pan.bar = (pan.mega_lo + pan.mega_hi) // 2
    pan.key("space")                          # a deliberate, timed lock
    assert pan.battle is not None and pan.locked == "mega"


def test_escape_stays_live_through_the_arm_window():
    """Backing out was never a timed action -- the mash guard must not
    trap the player in the ready screen."""
    pan = BattlePanel(_pet())
    pan.key("space")                          # skip the intro
    assert pan.key("escape") == ("done", None)
    assert pan.ran_away
