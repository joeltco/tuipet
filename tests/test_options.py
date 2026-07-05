"""The OPTIONS menu (2026-07-04): theme/sound/new-egg/erase under one key,
freeing g/m/n from the action bar.  The erase is typed-YES gated and wipes
the whole local state (the cloud copy stays with the account)."""
import os

from tuipet import persistence, theme
from tuipet.optionsscreen import OptionsPanel
from tuipet.pet import Pet


def _panel(sound=None):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    state = {"on": True if sound is None else sound}
    pan = OptionsPanel(p, lambda: state["on"],
                       lambda: state.__setitem__("on", not state["on"]))
    return pan, state


def _fits(pan):
    ls = pan.text().plain.split("\n")
    assert len(ls) <= 12 and max(len(l) for l in ls) <= 40


def test_options_walk_fits_and_toggles_sound():
    pan, state = _panel()
    _fits(pan)
    pan.key("down")                       # -> Sound
    assert pan.key("enter") is None
    assert state["on"] is False           # the callback flipped it
    assert "off" in pan.text().plain
    _fits(pan)


def test_theme_row_hosts_the_live_picker():
    pan, _ = _panel()
    before = theme.current()
    pan.key("enter")                      # Theme
    assert pan.sub is not None
    _fits(pan)                            # the hosted picker stays in budget
    pan.key("escape")                     # cancel -> reverts + back to options
    assert pan.sub is None
    assert theme.current() == before


def test_new_egg_row_hands_off():
    pan, _ = _panel()
    pan.key("down"); pan.key("down")      # -> New egg
    assert pan.key("enter") == ("done", ("new",))


def test_erase_demands_a_typed_yes():
    pan, _ = _panel()
    for _ in range(3):
        pan.key("down")                   # -> Erase all data
    pan.key("enter")
    assert pan.confirm and pan.captures_text
    _fits(pan)
    for ch in "nah":
        pan.key(ch)
    assert pan.key("enter") is None       # wrong word -> kept
    assert not pan.confirm and "wasn't YES" in pan.text().plain
    pan.key("enter")                      # re-open the gate
    for ch in "YES":
        pan.key(ch)
    assert pan.key("enter") == ("done", ("erase",))


def test_erase_all_wipes_the_local_state():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    persistence.save(p)
    persistence.set_account("JoeltCo", "pw")
    persistence.wins_add(3)
    assert os.path.exists(persistence.SAVE_PATH)
    removed = persistence.erase_all()
    assert "save.json" in removed and "settings.json" in removed
    assert not os.path.exists(persistence.SAVE_PATH)
    assert not os.path.exists(persistence.SETTINGS_PATH)
    assert persistence.get_account() == (None, "")
    assert persistence.get_progress().get("wins", 0) == 0
