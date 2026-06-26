"""Navigation keys play the scroll blip in any sub-screen, unless the screen sets
its own sfx (which wins). Non-nav keys with no sfx stay silent."""
from tuipet.app import TuiPetApp


class _Event:
    def __init__(self, key):
        self.key = key
    def stop(self): pass
    def prevent_default(self): pass


class _Screen:
    """Minimal panel: optionally raises an sfx on a given key."""
    def __init__(self, sfx_on=None, sfx_name=None):
        self.sfx = None
        self._sfx_on = sfx_on
        self._sfx_name = sfx_name
    def key(self, k):
        if k == self._sfx_on:
            self.sfx = self._sfx_name
        return None


def _app(mode):
    a = TuiPetApp.__new__(TuiPetApp)          # bypass Textual mount
    a.mode = mode
    a._mode_close = None
    a._played = []
    a.beep = lambda name=None, bell=True: a._played.append(name)
    a.repaint = lambda: None
    return a


def test_nav_key_plays_scroll():
    a = _app(_Screen())
    for k in ("up", "down", "left", "right", "j", "k", "tab"):
        a._played.clear()
        a.on_key(_Event(k))
        assert a._played == ["scroll"], f"{k!r} should beep scroll, got {a._played}"


def test_non_nav_key_is_silent_without_screen_sfx():
    a = _app(_Screen())
    a.on_key(_Event("enter"))
    assert a._played == []          # no nav, no screen sfx -> nothing


def test_screen_sfx_wins_over_scroll():
    # a screen that raises "select" on enter -> plays select, not scroll
    a = _app(_Screen(sfx_on="enter", sfx_name="select"))
    a.on_key(_Event("enter"))
    assert a._played == ["select"]
    # and a nav key on that same screen still scrolls
    a._played.clear()
    a.on_key(_Event("down"))
    assert a._played == ["scroll"]
