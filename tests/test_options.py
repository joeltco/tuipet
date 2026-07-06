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


def test_erase_flows_into_the_egg_carousel_not_an_auto_egg():
    """Erase -> title -> (re)login -> the EGG-SELECT CAROUSEL.  The erase
    branch parked a placeholder Pet.new_egg() and reopened the title, but
    _new_game was only ever set at construction -- the post-title flow went
    straight home and the player woke up with an egg they never picked
    (Joel 2026-07-05: "automatically selected an egg for me??")."""
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet
    from tuipet import eggselectscreen, lobbyscreen, titlescreen

    async def go():
        p = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        app = TuiPetApp(pet=p)
        seen = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            app.mode = None
            app._after_options(("erase",))              # the options panel's verdict
            await pilot.pause()
            seen["title"] = isinstance(app.mode, titlescreen.TitlePanel)
            await pilot.press("enter")                  # past the title
            await pilot.pause()
            seen["account"] = isinstance(app.mode, lobbyscreen.AccountPanel)
            for ch in "joel":                           # re-create the account
                await pilot.press(ch)
            await pilot.press("enter")
            for ch in "pw":
                await pilot.press(ch)
            await pilot.press("enter")
            await pilot.pause()
            seen["carousel"] = isinstance(app.mode, eggselectscreen.EggSelectPanel)
        return seen

    seen = asyncio.run(go())
    assert seen["title"], "erase must return to the title"
    assert seen["account"], "the erased account must be re-created"
    assert seen["carousel"], "a fresh start must open the egg carousel, never auto-pick"
