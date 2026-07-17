"""Night-palette regression (2026-07): the pet is NEVER white over a habitat
background.  paint()'s audited rule (visual audit v0.2.118) used SIL_DAY day
OR night, but five pre-audit sites kept a `SIL_NIGHT if night` override --
every night-time care fx (clean, the post-training cheer/jeer) and the
training/battle/tournament/digicore scenes washed the sprite white.
SIL_NIGHT is reserved for the lights-off dark room (pure-black bg)."""
from rich.console import Console

from tuipet.pet import Pet
from tuipet import theme
import tuipet.app as app


def _pet(hour=22):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = hour * 60.0
    return p


def _ink_colors(text):
    con = Console(width=44)
    cols = set()
    for line in text.split("\n"):
        for seg in line.render(con):
            if seg.style and seg.style.color and "▀" in seg.text:
                t = seg.style.color.get_truecolor()
                cols.add(f"#{t.red:02x}{t.green:02x}{t.blue:02x}")
    return cols


def _no_white(text, label):
    assert theme.SIL_NIGHT.lower() not in {c.lower() for c in _ink_colors(text)}, \
        f"{label}: SIL_NIGHT ink leaked into a lit night scene"


def _screen():
    s = app.Screen()
    s.on_mount()
    s.update = lambda t: setattr(s, "last", t)
    s.frame_i = 6
    return s


def test_night_care_fx_keep_the_dark_silhouette():
    p = _pet()
    # (the night phase left -- BASIC VPET 2026-07-17: scenes are one look,
    # so the dark-silhouette law now holds around the clock)
    assert p.background() is not None
    for kind in ("clean", "cheer", "jeer", "spit", "eat", "heal"):
        s = _screen()
        s.start_fx(kind, poop=2 if kind == "clean" else 0)
        if kind == "clean":
            p.poop, p.poop_sizes = 2, [0, 1]
        for _ in range(6):
            s.advance_fx()
        s.paint(p)
        _no_white(s.last, f"fx:{kind}")
        p.poop, p.poop_sizes = 0, []


def test_night_scene_screens_keep_the_dark_silhouette():
    from tuipet import training, battlescreen, battle
    p = _pet()
    p.energy = p.max_energy
    p.check_refused = lambda **kw: False
    tp = training.TrainingPanel(p)
    tp.key("up"); tp.key("enter")                        # vaccine: pet-on-bg scene
    _no_white(tp.text(), "training:vaccine")
    bp = battlescreen.BattlePanel(p, battle.pick_enemy(p))
    _no_white(bp.text(), "battle")


def test_lights_off_still_owns_the_white():
    p = _pet()
    p.lights = False
    p.asleep = True                                      # the Zzz is the dark room's one glyph
    s = _screen()
    s.paint(p)                                           # dark room: white IS the ink
    assert theme.SIL_NIGHT.lower() in {c.lower() for c in _ink_colors(s.last)}
