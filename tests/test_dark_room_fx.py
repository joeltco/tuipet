"""Dark-room care fx (bug report 2026-07-13, "seeing mon in white poses during
lights out sequence"): DVPet's lightsOff roomEffect is a FULLY-OPAQUE cover and
the care anims keep it up (SpriteAnim sets lightsOff inside the anims), so with
the lights out an fx shows NOTHING -- no pet, no props, no white poses.  The one
exception is the Assistant_Lights visit, which DVPet plays fully LIT: the room
toggles at the anim's final beat, so the switch AND the helper's exit render in
the lit room (the old cut at beat 18 left the exit playing white in the dark).
"""
import tuipet.app as app
from tuipet import arena
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _screen():
    s = app.Screen()
    s.on_mount()
    s.update = lambda t: None
    return s


def _spy(monkeypatch):
    cap = {}

    def spy(rows, cols, nrows, on, bg, mirror=False, xshift=0, yshift=0,
            overlay=None, bgimg=None, clip=None, overlay_free=None, free_ink=None):
        cap.update(rows=rows, on=on, bg=bg, overlay=list(overlay or []),
                   bgimg=bgimg, xshift=xshift)
        return ""

    monkeypatch.setattr("tuipet.arena.render_screen", spy)
    return cap


def test_dark_room_fx_shows_nothing(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(lights=False)
    s.start_fx("cheer")
    for _ in range(5):
        s.paint(p)
        assert cap["rows"] == [] and cap["overlay"] == [], \
            "the opaque lightsOff cover hides the pet and every prop"
        assert cap["bgimg"] is None and cap["bg"] == arena.VOID
        s.advance_fx()


def test_dark_room_sleep_settle_yawn_is_covered_too(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(lights=False)
    s.start_fx("yawn", pet=p)
    s.paint(p)
    assert cap["rows"] == [] and cap["overlay"] == [], \
        "the pre-sleep yawn tell is under the cover like any other fx"


def test_assist_lights_visit_plays_lit_end_to_end(monkeypatch):
    cap = _spy(monkeypatch)
    s = _screen()
    p = _pet(lights=False)
    s.start_fx("assist", pet=p)
    s.fx["act"] = "lights"
    s.fx["helper"] = 100
    for step in (2, 10, 19, 24, 27):
        s.fx["step"] = step
        s.paint(p)
        assert cap["on"] != arena.SIL_LIGHTSOFF and cap["bg"] != arena.VOID, \
            f"assist-lights step {step} must play in the lit room"
