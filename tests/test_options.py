"""The OPTIONS menu (2026-07-04): theme/sound/new-egg/erase under one key,
freeing g/m/n from the action bar.  Beefed up 2026-07-07: Account (switch who's
signed in — the pet parks with the old login's cloud), Update (on-demand PyPI
check, threaded), Keys (every binding on a scrollable page), and the sound row
names its detected backend.  The erase is typed-YES gated and wipes the whole
local state (the cloud copy stays with the account)."""
import os

from tuipet import optionsscreen, persistence, sound, theme
from tuipet.optionsscreen import KeysPanel, OptionsPanel, _ROWS
from tuipet.pet import Pet


def _panel(sound_on=None, **kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    state = {"on": True if sound_on is None else sound_on}
    pan = OptionsPanel(p, lambda: state["on"],
                       lambda: state.__setitem__("on", not state["on"]), **kw)
    return pan, state


def _fits(pan):
    ls = pan.text().plain.split("\n")
    assert len(ls) <= 12 and max(len(l) for l in ls) <= 40


def _to(pan, row):
    while _ROWS[pan.cursor] != row:
        pan.key("down")


def test_row_surface_and_order():
    """The full switchboard, dangerous rows last (a fat-finger past 'new'
    must never land on the erase gate's neighbour)."""
    assert _ROWS == ("theme", "sound", "account", "update", "keys", "new", "erase")
    pan, _ = _panel()
    _fits(pan)
    for _ in _ROWS:                        # every cursor position renders in budget
        pan.key("down")
        _fits(pan)


def test_note_line_describes_the_selected_row():
    """The line under the list follows the cursor (Joel's live review
    2026-07-07: it sat frozen on a flavour line); action feedback overrides
    it until the next cursor move."""
    pan, _ = _panel()
    assert "recolor" in pan.text().plain          # theme selected at open
    pan.key("down")                               # -> sound
    assert "chirps" in pan.text().plain
    pan.key("enter")                              # toggle: feedback takes the line
    assert "sound:" in pan.text().plain
    pan.key("down")                               # move -> the new row's desc
    plain = pan.text().plain
    assert "switch login" in plain and "sound:" not in plain


def test_options_walk_fits_and_toggles_sound():
    pan, state = _panel()
    _fits(pan)
    pan.key("down")                       # -> Sound
    assert pan.key("enter") is None
    assert state["on"] is False           # the callback flipped it
    assert "off" in pan.text().plain
    _fits(pan)


def test_sound_row_names_the_backend(monkeypatch):
    """A silent install self-explains: the value says WHICH player was found,
    or that the terminal bell is all there is (the Termux no-player mystery)."""
    pan, _ = _panel(sound_on=True)
    monkeypatch.setattr(sound, "_PLAYER", ["paplay"])
    assert pan._value("sound") == "on · paplay"
    # the long player name must not clip mid-word into the 18-char value
    # column ("on · termux-media-" on Joel's live screen, 2026-07-07)
    monkeypatch.setattr(sound, "_PLAYER", ["termux-media-player", "play"])
    assert pan._value("sound") == "on · termux"
    monkeypatch.setattr(sound, "_PLAYER", None)
    assert pan._value("sound") == "on · bell only"
    pan2, _ = _panel(sound_on=False)
    assert pan2._value("sound") == "off"


def test_every_row_value_fits_the_column():
    """No value may exceed the 18-char column — an over-wide one clips with a
    dangling word ('save + progress +' on the live screen, 2026-07-07)."""
    persistence.set_account("W" * 24, "pw")        # the widest real account
    pan, _ = _panel()
    for row in _ROWS:
        v = pan._value(row)
        assert len(v[:18]) == len(v) or row == "account", (row, v)  # account tail-clips by design


def test_theme_row_hosts_the_live_picker():
    pan, _ = _panel()
    before = theme.current()
    pan.key("enter")                      # Theme
    assert pan.sub is not None
    _fits(pan)                            # the hosted picker stays in budget
    pan.key("escape")                     # cancel -> reverts + back to options
    assert pan.sub is None
    assert theme.current() == before


def test_account_row_hosts_the_switcher():
    """ENTER on Account opens the lobby AccountPanel; Esc keeps the login,
    a confirmed name+password closes options with the app's switch verdict.
    While the form is up, letters are TEXT (q must not quit)."""
    from tuipet.lobbyscreen import AccountPanel
    persistence.set_account("joel", "pw")
    pan, _ = _panel()
    _to(pan, "account")
    assert "joel" in pan.text().plain     # the row shows who's signed in
    pan.key("enter")
    assert isinstance(pan.sub, AccountPanel) and pan.captures_text
    _fits(pan)
    assert pan.key("escape") is None      # backed out -> still in options
    assert pan.sub is None and "kept" in pan.msg
    pan.key("enter")                      # reopen
    for ch in "ana":
        pan.key(ch)
    pan.key("enter")                      # name -> password field
    for ch in "pw2":
        pan.key(ch)
    assert pan.key("enter") == ("done", ("account", "ana", "pw2"))


def test_update_row_checks_pypi(monkeypatch):
    """The on-demand check: threaded (the PyPI probe blocks up to 4s), the
    value and message land when it returns.  Threads run synchronously here."""
    class _Now:
        def __init__(self, target, daemon=None):
            self._t = target

        def start(self):
            self._t()
    monkeypatch.setattr(optionsscreen.threading, "Thread", _Now)
    monkeypatch.setattr(optionsscreen.update_check, "latest_if_newer",
                        lambda: "9.9.9")
    pan, _ = _panel()
    _to(pan, "update")
    assert pan.key("enter") is None
    # the row now OFFERS the install (Joel 2026-07-13: the update option
    # actually updates); a second ENTER runs it
    assert pan._value("update") == "9.9.9 · ENTER installs"
    assert "pip install -U tuipet" in pan.msg
    _fits(pan)
    monkeypatch.setattr(optionsscreen.update_check, "run_upgrade",
                        lambda: (True, "Updated — restart tuipet to play the new version."))
    pan.key("enter")                                  # ...and it installs
    assert pan._value("update") == "restart to apply"
    assert "restart" in pan.msg.lower()
    _fits(pan)
    monkeypatch.setattr(optionsscreen.update_check, "latest_if_newer",
                        lambda: None)
    pan2, _ = _panel()
    _to(pan2, "update")
    pan2.key("enter")
    assert pan2._value("update") == "up to date"
    assert "no newer release" in pan2.msg


def test_update_row_shows_the_boot_hint():
    """The app's launch check already knows a release is out — the row says so
    before any manual probe."""
    pan, _ = _panel(update_hint=lambda: "⬆ tuipet 9.9.9 out — pip install -U tuipet")
    assert pan._value("update") == "new version out!"
    pan2, _ = _panel(update_hint=lambda: "")
    assert pan2._value("update").startswith("v")


def test_keys_page_lists_every_binding_and_scrolls():
    """The Keys row hosts a scrollable page of the app's REAL binding surface;
    every window position renders inside the 12x40 LCD."""
    from tuipet.app import TuiPetApp
    pan, _ = _panel(bindings=TuiPetApp.BINDINGS)
    assert pan._value("keys") == f"{len(TuiPetApp.BINDINGS)} bindings"
    _to(pan, "keys")
    pan.key("enter")
    assert isinstance(pan.sub, KeysPanel)
    plain = pan.text().plain
    assert "Feed" in plain                # the first binding is on page one
    _fits(pan)
    for _ in range(len(TuiPetApp.BINDINGS)):     # scroll to the bottom
        pan.key("down")
        _fits(pan)
    assert "Accept gift" in pan.text().plain     # the last binding scrolled in
    assert pan.key("escape") is None
    assert pan.sub is None                # back to the options list


def test_new_egg_row_hands_off():
    pan, _ = _panel()
    _to(pan, "new")
    assert pan.key("enter") == ("done", ("new",))


def test_erase_demands_a_typed_yes():
    pan, _ = _panel()
    _to(pan, "erase")
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


def test_switch_account_app_flow(monkeypatch):
    """The app-side switch (OPTIONS → Account → confirmed form): a wrong
    password ABORTS without switching (probe distinguishes badpw from
    no-save — a typo must not strand the player on a fresh start); a cloud
    save loads as the new pet; an empty account opens the egg carousel and
    the old local save must not leak in."""
    import asyncio
    from tuipet import cloudsync, eggselectscreen
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet

    from tuipet import data
    rec = data.load_sprites()[1][4]                # strict probe wants the DEX
    other = Pet(num=4, name=rec["name"],           # name/stage pairing exactly
                stage=rec["stage"], attribute="Vaccine")
    other.world_seconds = 10 * 60.0
    cloud = persistence.to_save_dict(other)
    pushes = []
    monkeypatch.setattr(cloudsync, "push_save",
                        lambda uri, n, pw, save: pushes.append((n, save)) or True)

    async def go():
        p = Pet(num=100, name="Champ", stage="Champion", attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        persistence.set_account("joel", "pw")
        app = TuiPetApp(pet=p)
        seen = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            app.mode = None
            # 1) wrong password: nothing switches
            monkeypatch.setattr(cloudsync, "probe",
                                lambda uri, n, pw: ("badpw", None))
            app._after_options(("account", "ana", "typo"))
            for _ in range(6):
                await pilot.pause()
            seen["badpw_kept"] = persistence.get_account()[0] == "joel"
            # 2) the new account has a cloud pet: it loads
            monkeypatch.setattr(cloudsync, "probe",
                                lambda uri, n, pw: ("ok", dict(cloud)))
            app._after_options(("account", "ana", "pw2"))
            for _ in range(6):
                await pilot.pause()
            seen["loaded"] = (persistence.get_account()[0] == "ana"
                              and app.pet.num == 4)
            seen["parked"] = any(n == "joel" and s.get("num") == 100
                                 for n, s in pushes)
            # 3) a fresh account: the egg carousel, never the old pet
            monkeypatch.setattr(cloudsync, "probe",
                                lambda uri, n, pw: ("ok", None))
            app._after_options(("account", "newbie", "pw3"))
            for _ in range(6):
                await pilot.pause()
            seen["fresh"] = (persistence.get_account()[0] == "newbie"
                             and isinstance(app.mode, eggselectscreen.EggSelectPanel)
                             and not os.path.exists(persistence.SAVE_PATH))
        return seen

    seen = asyncio.run(go())
    assert seen["badpw_kept"], "a bad password must not switch accounts"
    assert seen["loaded"], "the new account's cloud pet must load"
    assert seen["parked"], "the old pet must be pushed to the OLD account"
    assert seen["fresh"], "an empty account starts fresh at the carousel"
