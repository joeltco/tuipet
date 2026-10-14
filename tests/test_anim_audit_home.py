"""The animation audit, home half (2026-10-14).  Joel kept the SKIPS and
reversed the speed-ups ("i never told you to speed up animations"): every
home show plays at its original pace, every time, and a fresh key skips a
passive show -- never the dying beat."""
from tuipet import arenafx, itemfx, training
from tuipet.arena import Screen
from tuipet.pet import Pet


class _S(Screen):
    def __init__(self):
        self.fx = None
        self.frame_i = 0
        self.anim_key = None
        self.thunder_i = 0

    def update(self, t):
        pass


_PET = Pet(num=102, name="D", stage="Champion", attribute="Virus")


def _frames(kind, **kw):
    s = _S()
    s.start_fx(kind, pet=_PET, **kw)
    n = 0
    while s.fx and s.fx["kind"] == kind:
        s.advance_fx()
        n += 1
    return n


def test_the_shows_play_at_their_original_pace_every_time():
    assert arenafx.CHEER_STEPS == arenafx.JEER_STEPS == 31
    assert not arenafx.FX_RATE and not arenafx.FX_RATE_REPEAT
    assert _frames("cheer") == 31
    first = _frames("item", script="Interact", icon="i:0")
    again = _frames("item", script="Interact", icon="i:0")
    assert first == again == itemfx.SCRIPTS["Interact"]["steps"]
    assert training.VERDICT_T == 14


def test_bathe_is_cut():
    assert "Bathe" not in itemfx.SCRIPTS


def test_a_fresh_key_skips_a_passive_show_but_never_the_dying_beat():
    s = _S()
    s.start_fx("evolve", old_num=4)
    assert not s.skip_fx()                                         # the starting key's mash
    s.advance_fx()
    s.advance_fx()
    s.advance_fx()
    assert s.skip_fx()
    s.advance_fx()
    assert s.fx["kind"] == "cheer"                                 # landed on the reveal
    d = _S()
    d.start_fx("dying")
    d.fx["step"] = 20
    assert not d.skip_fx() and d.fx["step"] == 20                  # taps are the rescue


def test_the_training_strike_is_skippable():
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    pan = training.TrainingPanel(p)
    pan._lock()
    for _ in range(3):
        pan.anim()
    pan.key("space")
    pan.anim()
    assert pan.auto_close is not None                              # straight to the verdict
    assert "skip" in pan.strip().lower()
