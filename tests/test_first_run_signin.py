"""A fresh install asks to sign in before the egg carousel (2026-10-14, Joel:
"If someone was to open a fresh install of tuipet, theyre forced to choose an
egg without signing in. Then that creates a shit load of problems").

A cloud pet comes onto this device WITH the cartridge (cloudsync.take), so the
saves made here are the ones the cloud keeps; ESC still starts a new pet."""
import asyncio

import pytest

from tuipet import cloudsync, persistence
from tuipet.accountscreen import AccountPanel
from tuipet.eggselectscreen import EggSelectPanel
from tuipet.pet import Pet


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(persistence, "SAVE_PATH", str(tmp_path / "save.json"))
    monkeypatch.setattr(persistence, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    calls = {"take": 0}
    cloud = {"gate": ("ok", None, None), "take": (True, None)}

    def gate(uri, name, pw, timeout=None):
        return cloud["gate"]

    def take(uri, name, pw, timeout=None):
        calls["take"] += 1
        return cloud["take"]

    monkeypatch.setattr(cloudsync, "gate", gate)
    monkeypatch.setattr(cloudsync, "take", take)
    return cloud, calls


def _cloud_pet_save():
    p = Pet(num=93, name="Greymon", stage="Champion", attribute="Vaccine")
    d = persistence.to_save_dict(p)
    d["_saved_at"] = 9e9
    return d


def _run(steps):
    from tuipet.app import TuiPetApp

    async def go():
        app = TuiPetApp()
        app._start_sync = lambda: None            # no live socket in tests
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause(0.3)
            await pilot.press("enter")            # dismiss the title
            await pilot.pause(0.3)
            out = await steps(app, pilot)
        return out
    return asyncio.run(go())


def test_a_fresh_install_asks_to_sign_in_and_esc_starts_a_new_pet(fresh):
    async def steps(app, pilot):
        first = type(app.mode)
        await pilot.press("escape")
        await pilot.pause(0.2)
        return first, type(app.mode)
    first, after = _run(steps)
    assert first is AccountPanel and after is EggSelectPanel


def test_signing_in_brings_the_cloud_pet_and_its_cartridge(fresh):
    cloud, calls = fresh
    cloud["gate"] = ("ok", _cloud_pet_save(), {"device": "other", "label": "phone"})

    async def steps(app, pilot):
        app._close_mode(("joel", "pw"))
        for _ in range(20):
            await pilot.pause(0.1)
            if not app._new_game:
                break
        return app.pet.num, app._new_game, app.mode
    num, new_game, mode = _run(steps)
    assert num == 93 and not new_game and mode is None
    assert calls["take"] == 1                     # the cartridge moved here
    assert persistence.get_account()[0] == "joel"
    assert persistence.holder_cache() is True


def test_an_account_without_a_pet_goes_to_the_carousel_signed_in(fresh):
    async def steps(app, pilot):
        app._close_mode(("newbie", "pw"))
        for _ in range(20):
            await pilot.pause(0.1)
            if isinstance(app.mode, EggSelectPanel):
                break
        return type(app.mode)
    assert _run(steps) is EggSelectPanel
    assert persistence.get_account()[0] == "newbie"


def test_a_wrong_password_comes_back_to_the_card(fresh):
    cloud, calls = fresh
    cloud["gate"] = ("badpw", None, None)

    async def steps(app, pilot):
        app._close_mode(("joel", "nope"))
        for _ in range(20):
            await pilot.pause(0.1)
            if isinstance(app.mode, AccountPanel):
                break
        return app.mode
    mode = _run(steps)
    assert isinstance(mode, AccountPanel) and "Wrong password" in mode.note
    assert not persistence.get_account()[0] and calls["take"] == 0


def test_a_failed_take_never_signs_in(fresh):
    cloud, _calls = fresh
    cloud["gate"] = ("ok", _cloud_pet_save(), None)
    cloud["take"] = (False, None)

    async def steps(app, pilot):
        app._close_mode(("joel", "pw"))
        for _ in range(20):
            await pilot.pause(0.1)
            if isinstance(app.mode, AccountPanel):
                break
        return app.mode, app._new_game
    mode, new_game = _run(steps)
    assert isinstance(mode, AccountPanel) and new_game
    assert not persistence.get_account()[0]


def test_an_existing_account_skips_the_card(fresh):
    persistence.set_account("joel", "pw")

    async def steps(app, pilot):
        return type(app.mode)
    assert _run(steps) is EggSelectPanel


def test_the_options_sign_in_takes_the_pet_too(fresh):
    """Signing in later from OPTIONS onto an account with a pet moves the
    cartridge here as well -- before, that path left this device a
    non-holder whose every save the cloud dropped."""
    cloud, calls = fresh
    cloud["gate"] = ("ok", _cloud_pet_save(), {"device": "other"})

    async def steps(app, pilot):
        await pilot.press("escape")                # new pet...
        await pilot.pause(0.2)
        await pilot.press("enter")                 # ...picked
        await pilot.pause(0.2)
        cloud["take"] = (False, None)
        await app._switch_account("joel", "pw")    # take refused: nothing moves
        refused = (bool(persistence.get_account()[0]), calls["take"])
        cloud["take"] = (True, None)
        await app._switch_account("joel", "pw")
        return refused, app.pet.num
    refused, num = _run(steps)
    assert refused == (False, 1)
    assert num == 93 and calls["take"] == 2
    assert persistence.get_account()[0] == "joel" and persistence.holder_cache() is True
