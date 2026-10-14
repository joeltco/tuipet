"""The animation audit, home half (2026-10-14, Joel: "Fix all"): the care,
item, evolution and gift shows run at the audit's pace, a show already seen
plays fast, a fresh key skips a passive show, and the dying beat never
skips.  Every number here was slower before."""
from tuipet import arenafx, itemfx, persistence, training
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


def _secs(kind, **kw):
    """Seconds (10 Hz frames) until the show AND its chained tail end."""
    s = _S()
    s.start_fx(kind, pet=_PET, **kw)
    n = 0
    while s.fx:
        s.advance_fx()
        n += 1
    return n / 10


def test_the_shows_run_at_the_audits_pace():
    assert _secs("cheer") <= 1.0 and _secs("jeer") <= 0.8          # were 3.1
    assert _secs("evolve", old_num=4) <= 4.0                       # was 8.4
    assert _secs("inherit") <= 4.0                                 # was 8.1
    assert _secs("clean", poop=2) <= 2.0                           # was 5.3
    assert _secs("spit") <= 1.0                                    # was 2.5
    assert _secs("gift", icon="f:8") <= 2.5                        # 13.5 incl. cheer
    assert _secs("losing") <= 1.5                                  # was 5.0
    assert _secs("dna_charge") <= 2.0                              # was 4.4


def test_a_show_already_seen_plays_fast():
    first = _secs("item", script="Interact", icon="i:0")
    again = _secs("item", script="Interact", icon="i:0")
    assert first <= 3.0 and again <= 1.5 and again < first        # was 8.0 every time
    assert persistence.fx_seen("item:Interact")
    _secs("eat", icon="f:1")
    assert _secs("eat", icon="f:1") <= 1.3


def test_bathe_is_cut():
    assert "Bathe" not in itemfx.SCRIPTS


def test_a_fresh_key_skips_a_passive_show_but_never_the_dying_beat():
    s = _S()
    s.start_fx("evolve", old_num=4)
    assert not s.skip_fx()                                         # the starting key's mash
    s.advance_fx()
    s.advance_fx()
    assert s.skip_fx()
    s.advance_fx()
    assert s.fx["kind"] == "cheer"                                 # landed on the reveal
    d = _S()
    d.start_fx("dying")
    d.fx["step"] = 20
    assert not d.skip_fx() and d.fx["step"] == 20                  # taps are the rescue


def test_a_fast_show_still_plays_every_sound():
    s = _S()
    s.start_fx("evolve", old_num=4)
    assert s.fx["rate"] > 1
    want = set(s.fx["snds"].values())
    heard = set()
    while s.fx and s.fx["kind"] == "evolve":
        s.advance_fx()
        if s.fx and s.fx["kind"] == "evolve":
            for b in range(s.fx["prev"] + 1, s.fx["step"] + 1):
                if b in s.fx["snds"]:
                    heard.add(s.fx["snds"][b])
    assert heard == want


def test_the_training_verdict_is_short_and_skippable():
    assert training.VERDICT_T <= 4                                 # was 14
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    pan = training.TrainingPanel(p)
    pan._lock()
    for _ in range(3):
        pan.anim()
    pan.key("space")
    pan.anim()
    assert pan.auto_close is not None                              # straight to the verdict
    assert "skip" in pan.strip().lower()


def test_rates_are_pacing_only():
    """The beat tables (canon) are untouched: a rate just walks them faster."""
    assert set(arenafx.FX_RATE) | set(arenafx.FX_RATE_REPEAT) <= {
        "eat", "evolve", "inherit", "dna_charge", "losing", "gift", "clean",
        "spit", "poop", "assist", "play", "item"}
    assert "dying" in arenafx.FX_UNSKIPPABLE
