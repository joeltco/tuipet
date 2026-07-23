"""QOL polish pins (board: QOL_POLISH_2026_07_23.md).

Batch 1 -- the skip cluster + the pill reflex: a decided fight must not
cost ~20 timed presses, round boundaries must not eat skip input, the
hurry keys must be discoverable on the strip, and a sick pet's feed
menu must open on the cure the HUD just told you to give.
"""
from tuipet.battlescreen import SKIP_DEBOUNCE, BattlePanel
from tuipet.feedscreen import FeedPanel
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _locked_panel():
    """A BattlePanel with the bar locked and the first round animating."""
    pan = BattlePanel(_pet(), {"num": 100, "name": "Sparrowmon"})
    pan._start_fight("normal")
    assert pan.phase == "anim"
    return pan


# ---- B1: ESC = end it (fast-run to the deciding round) ----------------------

def test_escape_fast_runs_a_decided_fight_to_its_final_round():
    pan = _locked_panel()
    for _ in range(SKIP_DEBOUNCE + 1):
        pan.anim()
    pan.key("escape")
    # every remaining round resolved in one press; the DECIDING round's
    # timeline is loaded so the KO beat still plays out on screen
    assert pan.battle.over
    assert pan.phase in ("anim", "result")
    if pan.phase == "anim":
        for _ in range(len(pan.timeline) + 2):
            pan.anim()
    assert pan.phase == "result" and pan.done_anim
    assert pan.won == pan.battle.won


def test_escape_end_never_hangs_on_a_raid_that_goes_the_distance():
    """A survived raid's boss never falls -- battle.over may only arrive
    when the rounds run dry, and the fast-run must exit via the result
    (the phase guard), not spin."""
    pan = BattlePanel(_pet(), {"num": 214, "name": "Bossmon", "boss": True,
                               "pool": (5_000_000, 5_500_000)}, raid=True)
    pan._start_fight("normal")
    for _ in range(SKIP_DEBOUNCE + 1):
        pan.anim()
    pan.key("escape")
    assert pan.battle.over or pan.phase == "result"


# ---- B2: the debounce anchors on the LOCK, not the round --------------------

def test_round_boundaries_no_longer_eat_skip_presses():
    pan = _locked_panel()
    # play into round 2+: watch self.i wrap back to a small value
    guard = 0
    while True:
        prev = pan.i
        pan.anim()
        guard += 1
        assert guard < 5000, "never reached a second round"
        if pan.phase != "anim":            # a 1-round KO: nothing to test here
            return
        if pan.i < prev:                   # a fresh round just began
            break
    assert pan.i < SKIP_DEBOUNCE           # inside the old dead-window
    before = pan.i
    pan.key("space")                       # the mash press at the boundary...
    assert pan.i != before                 # ...lands (old code ate it)


def test_the_lock_debounce_still_guards_the_first_beats():
    pan = _locked_panel()
    pan.key("space")                       # the press that locked the bar, repeated
    assert pan.i == 0                      # still debounced right after the lock


# ---- B3: the hurry keys live on the strip -----------------------------------

def test_round_anim_strip_prompts_the_hurry_keys():
    pan = _locked_panel()
    s = pan.strip()
    assert "hurry" in s and "ESC" in s


# ---- C1: a sick pet's feed menu opens on the Pill ---------------------------

def test_feed_opens_on_the_pill_when_sick_and_meat_when_well():
    assert FeedPanel(_pet(sick=True)).cursor == 1     # Pill
    assert FeedPanel(_pet()).cursor == 0              # Meat
