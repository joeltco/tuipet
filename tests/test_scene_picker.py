"""The E scene picker (restored 2026-07-17: "add the e action back to change
backgrounds").  The egg still decides the DEFAULT scene; a pick overrides it
for the pet's life and rides the save (bg_pick)."""
from dataclasses import asdict

from tuipet import backgrounds, data
from tuipet.backgroundscreen import BackgroundPanel
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_egg_decides_the_default_and_pick_overrides():
    p = _pet(egg_type=0)                            # greenhills
    assert p.background() == data.load_backgrounds()["greenhills"][0]
    p.pick_background("volcano")
    assert p.background() == data.load_backgrounds()["volcano"][0]
    p.pick_background("")                           # back to the egg's own
    assert p.background() == data.load_backgrounds()["greenhills"][0]


def test_every_pick_is_a_real_sheet_and_the_arena_is_not_one():
    sheets = data.load_backgrounds()
    assert backgrounds.PICKS
    assert all(k in sheets for k in backgrounds.PICKS)
    assert "tourneyBack" not in backgrounds.PICKS   # the arena is a room, not a pick


def test_pick_rides_the_save():
    p = _pet(bg_pick="datatunnel")
    assert asdict(p)["bg_pick"] == "datatunnel"     # persistence.asdict path


def test_panel_walks_previews_and_commits():
    p = _pet(egg_type=0)
    pan = BackgroundPanel(p)
    assert pan.rows[0] == ""                        # row 0 = the egg's own
    assert "egg's own" in pan._name("")
    pan.text(); pan.strip()
    pan.key("down"); pan.anim(); pan.text()
    pan.key("enter")
    assert p.bg_pick == pan.rows[1]
    pan.key("up"); pan.key("enter")                 # row 0: back to the egg
    assert p.bg_pick == ""
    assert pan.key("escape") == ("done", pan.msg)


def test_home_screen_binding():
    from tuipet.app import TuiPetApp
    assert any(b[:2] == ("e", "scenes") for b in TuiPetApp.BINDINGS)
