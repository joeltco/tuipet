"""The message box marquee: long HUD messages must scroll, never clip."""
from tuipet.app import TuiPetApp, HUD_W


class _FakeMsg:
    def __init__(self): self.text = None
    def update(self, t): self.text = t


def _stub():
    s = TuiPetApp.__new__(TuiPetApp)            # bypass __init__ / Textual mount
    s.msg_w = _FakeMsg()
    s._hud_scroll = None; s._hud_off = 0; s._hud_hold = 0; s._hud_tick = 0
    return s


def test_short_message_renders_verbatim_without_scrolling():
    s = _stub()
    s._hud("Agumon is hungry!")
    assert s._hud_scroll is None
    assert s.msg_w.text == "Agumon is hungry!"
    # marquee is a no-op when nothing overflows
    before = s.msg_w.text
    s._hud_marquee()
    assert s.msg_w.text == before


def test_long_message_scrolls_and_reveals_every_part():
    s = _stub()
    msg = "Welcome back! (123m away) Your pet missed you."
    assert len(msg) > HUD_W                     # genuinely overflows the box
    s._hud(msg)
    assert s._hud_scroll == msg
    seen = set()
    for _ in range(2000):                       # ample frames to cover a full loop
        s._hud_marquee()
        if s.msg_w.text:
            seen.add(s.msg_w.text)
    # the head AND the tail (which used to be clipped) both surface while scrolling
    assert any("Welcome back!" in t for t in seen)
    assert any("missed you." in t for t in seen)
    # nothing ever exceeds the box width
    assert all(len(t.replace("\\\\[", "[")) <= HUD_W for t in seen)
