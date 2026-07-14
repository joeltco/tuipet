"""The game updates itself at launch (Joel 2026-07-14).

It checks PyPI once per launch and INSTALLS a newer release in the background,
then asks for a restart -- Python already imported the running code, so a fresh
install can only take effect next launch.  It must never claim an update it did
not make (the silent-failure law), and it must never force pip on someone who
does not want it.
"""
import asyncio
import os
import tempfile

import pytest

import tuipet.app as appmod
from tuipet import persistence as pers
from tuipet import update as upd


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setattr(pers, "SAVE_DIR", d)
    monkeypatch.setattr(pers, "SETTINGS_PATH", os.path.join(d, "settings.json"))


def _run(monkeypatch, latest, argv, upgrade, auto=True):
    app = appmod.TuiPetApp.__new__(appmod.TuiPetApp)
    app._update_msg = None
    pers.set_auto_update(auto)
    monkeypatch.setattr(upd, "latest_if_newer", lambda: latest)
    monkeypatch.setattr(upd, "upgrade_argv", lambda: argv)
    monkeypatch.setattr(upd, "run_upgrade", lambda: upgrade)
    monkeypatch.setattr(upd, "manual_command", lambda: "pip install -U tuipet")
    asyncio.run(appmod.TuiPetApp._check_update(app))
    return app


def test_a_newer_release_installs_itself_then_asks_for_a_restart(monkeypatch):
    app = _run(monkeypatch, "9.9.9", ["pip"], (True, "Updated"))
    assert app._updated_to == "9.9.9"
    assert "installed" in app._update_msg and "restart" in app._update_msg


def test_being_up_to_date_says_nothing(monkeypatch):
    app = _run(monkeypatch, None, ["pip"], (True, ""))
    assert app._update_msg is None


def test_a_failed_install_never_claims_success(monkeypatch):
    """The silent-failure law: a failure must not become a success message."""
    app = _run(monkeypatch, "9.9.9", ["pip"], (False, "pip exploded"))
    assert not getattr(app, "_updated_to", None)
    assert "installed" not in app._update_msg
    assert "pip install -U tuipet" in app._update_msg   # hand back the command


def test_a_host_that_cannot_self_install_is_told_the_command(monkeypatch):
    """iOS sandboxes subprocesses; a source checkout has no release to install."""
    app = _run(monkeypatch, "9.9.9", None, (True, ""))
    assert not getattr(app, "_updated_to", None)
    assert "pip install -U tuipet" in app._update_msg


def test_the_player_can_opt_out(monkeypatch):
    """Nobody is forced to have pip run for them: opting out still NOTIFIES."""
    app = _run(monkeypatch, "9.9.9", ["pip"], (True, "Updated"), auto=False)
    assert not getattr(app, "_updated_to", None)
    assert "9.9.9 out" in app._update_msg


def test_auto_update_defaults_on_and_persists():
    assert pers.get_auto_update() is True          # on by default
    assert pers.set_auto_update(False) is False
    assert pers.get_auto_update() is False         # ...and it sticks
    pers.set_auto_update(True)
    assert pers.get_auto_update() is True
