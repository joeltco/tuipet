"""Bug report 2026-10-14 (Joel, 0.6.6): "erasing my data didnt reset my
monster".  Erase wiped the device but the cloud kept the pet, and 0.6.5's
first-run sign-in brought it straight back.  Erase now wipes the cloud first."""
import asyncio
import os
import sys

from tuipet import cloudsync, persistence


def _srv(tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    server.SAVES_PATH = str(tmp_path / "saves.json")
    server.HOLDERS_PATH = str(tmp_path / "holders.json")
    server.SAVES = {}
    server.HOLDERS = {}
    return server


def test_the_server_wipe_clears_the_save_and_frees_the_cartridge(tmp_path):
    srv = _srv(tmp_path)
    srv.SAVES["joel"] = {"num": 29}
    srv.HOLDERS["joel"] = {"device": "phone"}
    assert asyncio.run(srv._wipe_account("joel")) is True
    assert "joel" not in srv.SAVES and "joel" not in srv.HOLDERS
    assert asyncio.run(srv._wipe_account("joel")) is False     # nothing left


def _erase(tmp_path, monkeypatch, wipe_ok):
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(persistence, "SAVE_PATH", str(tmp_path / "save.json"))
    monkeypatch.setattr(persistence, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    persistence.set_account("joel", "pw")
    order = []

    def wipe(uri, name, pw, timeout=None):
        order.append(("wipe", name, persistence.get_account()[0]))
        return wipe_ok

    monkeypatch.setattr(cloudsync, "wipe", wipe)
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet

    async def go():
        app = TuiPetApp(pet=Pet(num=29, name="Agumon", stage="Rookie", attribute="Vaccine"))
        app._start_sync = lambda: None
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            app.mode = None
            app._after_options(("erase",))
            for _ in range(20):
                await pilot.pause(0.05)
                if app._new_game:
                    break
            return app._new_game, getattr(app, "_boot_notice", "")
    new_game, hud = asyncio.run(go())
    return order, new_game, hud


def test_erase_wipes_the_cloud_before_the_login_is_gone(tmp_path, monkeypatch):
    order, new_game, _hud = _erase(tmp_path, monkeypatch, True)
    assert order == [("wipe", "joel", "joel")]            # wiped while still signed in
    assert new_game and not persistence.get_account()[0]


def test_an_unreachable_cloud_still_erases_the_device_and_says_so(tmp_path, monkeypatch):
    order, new_game, hud = _erase(tmp_path, monkeypatch, False)
    assert order and new_game
    assert "cloud still has your pet" in hud
