"""Navigation/exit QoL: q quits the app from any non-text screen (not just the
main view), while text-entry screens keep q as a typed character. ESC still backs
out one level (unchanged)."""
from tuipet.app import TuiPetApp


class _Event:
    def __init__(self, key, character=None):
        self.key = key
        self.character = character
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


def test_eggselect_captures_text_only_while_entering_a_code():
    from tuipet import eggselectscreen
    p = eggselectscreen.EggSelectPanel.__new__(eggselectscreen.EggSelectPanel)
    p.entering = False
    assert p.captures_text is False           # browsing eggs -> q quits
    p.entering = True
    assert p.captures_text is True            # typing a secret code -> q is text


# --- punctuation in text screens ----------------------------------------------
# Textual names punctuation keys ("." -> "full_stop", "!" -> "exclamation_mark"),
# so a text panel's `len(k) == 1 and k.isprintable()` test dropped every symbol.
# on_key forwards event.character (the actual glyph) for text-capturing panels.

def test_punctuation_reaches_a_text_screen_as_the_character():
    s = _Screen(captures_text=True)
    a = _app(s)
    for name, glyph in (("full_stop", "."), ("comma", ","),
                        ("exclamation_mark", "!"), ("question_mark", "?"),
                        ("apostrophe", "'")):
        a.on_key(_Event(name, glyph))
    assert s.seen == [".", ",", "!", "?", "'"]   # glyphs, not the key NAMES


def test_nav_keys_still_arrive_by_name_in_a_text_screen():
    s = _Screen(captures_text=True)
    a = _app(s)
    for name in ("enter", "backspace", "up", "escape"):
        a.on_key(_Event(name, None))             # control keys carry no character
    assert s.seen == ["enter", "backspace", "up", "escape"]


def test_non_text_screen_ignores_character_translation():
    s = _Screen(captures_text=False, result=("done", "x"))
    a = _app(s)
    a.on_key(_Event("full_stop", "."))           # a hotkey screen keeps the NAME
    assert s.seen == ["full_stop"]


# --- toggle-close consistency: a screen's opening key also closes it -----------

def test_adventure_closes_with_its_opening_key():
    from tuipet import adventurescreen
    p = adventurescreen.AdventurePanel.__new__(adventurescreen.AdventurePanel)
    p.sub = None
    p.adv = type("A", (), {"done": False})()
    p.travelling = False
    assert p.key("a") == ("done", None)       # 'a' (opened it) also closes it


def test_tournament_closes_with_its_opening_key_in_all_phases():
    from tuipet import tournamentscreen
    p = tournamentscreen.TournamentPanel.__new__(tournamentscreen.TournamentPanel)
    p.sub = None
    p.phase = "select"
    p.sched = []
    p.cursor = 0
    assert p.key("u") == ("done", None)       # 'u' closes the cup, not just ESC
