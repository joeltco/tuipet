"""Tier-2 professionalism pins (sweep 2026-07-14): the first five minutes.
No account wall before gameplay, no release notes for brand-new installs, a
help nudge on the fresh egg, a confirm before retiring a living pet, weather
finally explained, and the egg guide reachable from the picker."""
from tuipet import persistence
from tuipet.app import TuiPetApp
from tuipet.eggselectscreen import EggSelectPanel
from tuipet.helpscreen import HELP
from tuipet.optionsscreen import OptionsPanel, _ROWS
from tuipet.pet import Pet


def _options(pet):
    return OptionsPanel(pet, lambda: True, lambda: None)


def _to(pan, row):
    while _ROWS[pan.cursor] != row:
        pan.key("down")


# ---- the account wall is gone -------------------------------------------------

def test_title_flows_straight_to_the_game_without_an_account():
    app = TuiPetApp.__new__(TuiPetApp)             # no Textual mount needed
    calls = []
    app._post_title = lambda: calls.append("post")
    app._open_mode = lambda *a, **k: calls.append("wall")
    assert not persistence.get_account()[0]        # sandbox: no account on disk
    app._after_title()
    assert calls == ["post"]                       # no name+password screen first


# ---- release news is for returning players only --------------------------------

def test_whats_new_skipped_and_stamped_on_a_first_install():
    app = TuiPetApp.__new__(TuiPetApp)
    app._new_game = True
    assert app._whats_new() is None
    from tuipet import update
    assert persistence.load_settings()["seen_version"] == update.current_version()
    app._new_game = False                          # ...and it STAYS skipped
    assert app._whats_new() is None


def test_whats_new_still_greets_a_returning_player():
    app = TuiPetApp.__new__(TuiPetApp)
    app._new_game = False
    wn = app._whats_new()
    assert wn and "WHAT'S NEW" in wn


# ---- retiring a LIVING pet asks first -------------------------------------------

def test_new_egg_over_a_living_pet_needs_a_confirm():
    pan = _options(Pet(num=100, name="Agumon", stage="Champion"))
    _to(pan, "new")
    assert pan.key("enter") is None                # no instant hand-off
    assert pan.confirm_new and "retire Agumon" in pan.msg
    assert "retire" in pan.strip()                 # hints() returns markup text
    assert pan.key("enter") == ("done", ("new",))  # ENTER confirms


def test_new_egg_confirm_esc_keeps_the_pet():
    pan = _options(Pet(num=100, name="Agumon", stage="Champion"))
    _to(pan, "new")
    pan.key("enter")
    assert pan.key("escape") is None
    assert not pan.confirm_new and "kept Agumon" in pan.msg


def test_dead_pet_and_egg_hand_off_without_ceremony():
    dead = Pet(num=100, name="Agumon", stage="Mega")
    dead.dead = True
    pan = _options(dead)
    _to(pan, "new")
    assert pan.key("enter") == ("done", ("new",))
    pan = _options(Pet.new_egg())
    _to(pan, "new")
    assert pan.key("enter") == ("done", ("new",))


# ---- the egg guide is reachable from the picker -------------------------------------

def test_egg_picker_offers_the_guide():
    pan = EggSelectPanel(Pet.new_egg())
    assert "guide" in pan.strip()                  # hints() returns markup text
    assert pan.key("n") == ("done", "guide")


def test_fresh_egg_flash_points_at_help():
    import inspect
    src = inspect.getsource(TuiPetApp._after_egg_pick)
    assert "? = help" in src                       # the one-time nudge on a new egg
