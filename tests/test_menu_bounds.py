"""Menu-bounds sweep (audit 2026-07-07): every strip fits HUD_W statically with
WORST-CASE content -- long fields marquee (render.marquee) while the chrome and
key hints stand still; the app's _hud whole-line marquee stays as the safety
net, but a strip that ALWAYS overflowed slid its hints out of view."""
from rich.text import Text

from tuipet.pet import Pet
from tuipet.render import marquee

LCD_COLS, HUD_W = 40, 40
LONGEST = "AncientMegatherimon"          # the widest real dex name (19)


def _plain(markup):
    return len(Text.from_markup(markup).plain) if markup else 0


def _pet(**kw):
    p = Pet(num=649, stage="Mega", attribute="Vaccine", obedience=500)   # 19-char name
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_marquee_holds_then_scrolls_and_loops():
    assert marquee("short", 10, 99) == "short"               # fits: untouched at any step
    s = "ABCDEFGHIJKL"                                        # 12 into a 6-slot
    assert marquee(s, 6, 0) == "ABCDEF"                       # head hold
    assert marquee(s, 6, 7) == "ABCDEF"                       # still holding (hold=8)
    assert marquee(s, 6, 9) == "BCDEFG"                       # sliding
    n = len(s + "   ") + 8
    assert marquee(s, 6, n) == marquee(s, 6, 0)               # loops back to the head
    for step in range(2 * n):
        assert len(marquee(s, 6, step)) == 6                  # the window never overflows


def test_habitat_strip_fits_at_every_step():
    from tuipet.habitatscreen import HabitatPanel
    pan = HabitatPanel(_pet(bits=99999))
    for _ in range(80):                                       # roll full marquee loops
        pan.anim()
        assert _plain(pan.strip()) <= HUD_W
        pan.key("down")


def test_death_strip_states_fit_with_the_longest_name():
    from tuipet.deathscreen import DeathPanel
    dead = _pet()
    dead.dead = True
    dead.death_cause = "neglect"
    mem = {"name": LONGEST, "num": 649, "vaccine": 99, "data": 99, "virus": 99, "seconds": 60.0}
    pan = DeathPanel(dead, new_mem=dict(mem), old_mem=dict(mem),
                     grade_kept=99, banked_new=True, hold=0)
    for presses in ((), ("e",), ("e",)):                      # etch -> only-one -> the epitaph
        for k in presses:
            pan.key(k)
        for _ in range(60):
            pan.anim()
            assert _plain(pan.strip()) <= HUD_W


def test_lobby_jogress_lines_fit_with_a_24_char_partner():
    from tuipet import lobbyscreen
    from tuipet.net import LobbyState

    class _Stub:
        def __init__(self, state): self.state = state
        def relay(self, *a, **k): pass
        def respond(self, *a, **k): pass
        def update_pet(self, *a, **k): pass

    s = LobbyState()
    pan = lobbyscreen.LobbyPanel(_pet(), lambda n, pw, c: _Stub(s), name="me", pw="pw")
    pan.phase, pan.jphase = "jogress", "waiting"
    pan.partner = (2, "W" * 24)                               # server MAX_NAME
    for _ in range(80):
        pan.anim()
        lines = pan.text().plain.split("\n")
        assert max(map(len, lines)) <= LCD_COLS
    pan.jphase, pan.jresult = "result", {"num": 649, "name": LONGEST}
    from tuipet import jogressscreen
    show = jogressscreen.JogressPanel(pan.pet, 649, 286, 649)
    show.phase = "fused"
    pan.jshow = show
    assert _plain(pan.strip()) <= HUD_W                       # the fused strip


def test_travelling_and_hp_drill_strips_fit_at_the_extremes():
    from tuipet.adventure import Adventure
    from tuipet.adventurescreen import AdventurePanel
    pan = AdventurePanel(_pet(bits=999))
    pan.adv.last = "Travelling… 100%"                         # the widest travelling note
    pan.travelling = True
    assert _plain(pan.strip()) <= HUD_W
    from tuipet.training import TrainingPanel, GAMES
    p = _pet(compliance=True)
    p.check_refused = lambda **kw: False
    tp = TrainingPanel(p)
    tp.gi = next(i for i, g in enumerate(GAMES) if g[0] == "hp")
    tp._start_game()
    assert _plain(tp.strip()) <= HUD_W
