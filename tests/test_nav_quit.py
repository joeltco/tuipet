"""Navigation/exit QoL: q quits the app from any non-text screen (not just the
main view), while text-entry screens keep q as a typed character. ESC still backs
out one level (unchanged)."""
from tuipet.app import TuiPetApp


class _Event:
    def __init__(self, key):
        self.key = key
    def stop(self): pass
    def prevent_default(self): pass


class _Screen:
    """Minimal panel. captures_text toggles the q-as-quit exemption; result is
    what key() returns."""
    def __init__(self, captures_text=False, result=None):
        self.captures_text = captures_text
        self._result = result
        self.seen = []
    def key(self, k):
        self.seen.append(k)
        return self._result


def _app(mode):
    a = TuiPetApp.__new__(TuiPetApp)
    a.mode = mode
    a._mode_close = None
    a._quit = 0
    a._closed = []
    a.action_quit = lambda: setattr(a, "_quit", a._quit + 1)
    a._close_mode = lambda r: a._closed.append(r)
    a.beep = lambda *x, **k: None
    a.repaint = lambda: None
    return a


def test_q_quits_from_a_normal_screen():
    a = _app(_Screen())                      # not text, returns None
    a.on_key(_Event("q"))
    assert a._quit == 1 and a._closed == []


def test_q_is_a_character_in_text_screens():
    s = _Screen(captures_text=True)
    a = _app(s)
    a.on_key(_Event("q"))
    assert a._quit == 0                       # never quits while typing
    assert s.seen == ["q"]                    # the screen got the keystroke


def test_quit_result_triggers_action_quit():
    a = _app(_Screen(result=("quit", None)))  # e.g. q on the title
    a.on_key(_Event("q"))
    assert a._quit == 1


def test_done_result_still_closes_not_quits():
    a = _app(_Screen(result=("done", "x")))
    a.on_key(_Event("enter"))
    assert a._quit == 0 and a._closed == ["x"]


def test_title_q_quits_other_keys_start():
    from tuipet import titlescreen
    t = titlescreen.TitlePanel.__new__(titlescreen.TitlePanel)
    assert t.key("q") == ("quit", None)
    assert t.key("enter") == ("done", None)
    assert t.key("a") == ("done", None)


# (adventure/tournament toggle-close tests removed — those screens were stripped.)
# (eggselect secret-code test removed — the DVPet password/unlock path was stripped;
#  DM20 egg select is a free version-starter picker with no text entry.)
