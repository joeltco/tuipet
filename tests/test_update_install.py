"""The Update option actually updates (Joel 2026-07-13).

It used to only CHECK PyPI and tell you to run pip yourself.  Now ENTER
installs -- but only where we can honestly do it: the command differs by
install method, iOS cannot spawn a process at all, and a source checkout has
no release to install over.  A refusal must never masquerade as an update.
"""
import importlib
import subprocess

import pytest

from tuipet import hostinfo, update


def test_the_upgrade_targets_the_environment_we_actually_run_in():
    """`pip install -U tuipet` may belong to some OTHER python; the venv's own
    interpreter is the one hosting tuipet -- true for a plain pip install and
    for a pipx/uv tool venv alike."""
    import sys
    argv = update.upgrade_argv()
    if argv is None:
        pytest.skip("no installed tuipet in this environment")
    assert argv[:3] == [sys.executable, "-m", "pip"]
    assert "tuipet" in argv and "-U" in argv


def test_ios_refuses_honestly_and_hands_back_the_command(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("platform.machine", lambda: "iPhone15,2")
    importlib.reload(hostinfo)
    importlib.reload(update)
    try:
        assert update.install_method() == "blocked"
        assert update.upgrade_argv() is None       # iOS cannot spawn pip
        ok, msg = update.run_upgrade()
        assert ok is False and "by hand" in msg
    finally:
        importlib.reload(hostinfo)
        importlib.reload(update)


def test_a_source_checkout_is_told_to_git_pull(monkeypatch):
    monkeypatch.setattr(update, "current_version", lambda: None)
    assert update.install_method() == "source"
    assert update.upgrade_argv() is None
    ok, msg = update.run_upgrade()
    assert ok is False and "git pull" in msg


def test_a_failed_pip_never_reports_success(monkeypatch):
    """The whole point of the sweep: a failure must not become a success
    message."""
    class _R:
        returncode = 1
        stdout = b"ERROR: could not install"

    monkeypatch.setattr(update, "_RUN", lambda *a, **k: _R())
    if update.upgrade_argv() is None:
        pytest.skip("no installed tuipet in this environment")
    ok, msg = update.run_upgrade()
    assert ok is False
    assert "failed" in msg.lower() and "pip install -U tuipet" in msg


def test_a_timeout_never_reports_success(monkeypatch):
    def _boom(*a, **k):
        raise subprocess.TimeoutExpired("pip", 1)

    monkeypatch.setattr(update, "_RUN", _boom)
    if update.upgrade_argv() is None:
        pytest.skip("no installed tuipet in this environment")
    ok, msg = update.run_upgrade()
    assert ok is False and "timed out" in msg.lower()


def test_success_always_asks_for_a_restart(monkeypatch):
    """Python already imported the OLD code; we must never pretend the swap
    happened live."""
    class _R:
        returncode = 0
        stdout = b""

    monkeypatch.setattr(update, "_RUN", lambda *a, **k: _R())
    if update.upgrade_argv() is None:
        pytest.skip("no installed tuipet in this environment")
    ok, msg = update.run_upgrade()
    assert ok is True and "restart" in msg.lower()


def test_the_options_row_offers_the_install_then_asks_for_a_restart():
    from tuipet.optionsscreen import OptionsPanel
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = OptionsPanel(p, sound_get=lambda: True, sound_toggle=lambda: None)
    pan._upd = "9.9.9"                              # a newer release is known
    assert "ENTER installs" in pan._value("update")
    pan._installing = True
    assert pan._value("update") == "updating…"
    pan._installing, pan._updated = False, True
    assert pan._value("update") == "restart to apply"


def test_enter_on_restart_to_apply_actually_restarts():
    """The launch auto-update writes the new version to disk while the process
    keeps running the old code; the row then reads 'restart to apply'.  ENTER on
    it must RESTART -- not re-check and say 'up to date' (current_version reads
    the freshly-upgraded disk).  Regression: Joel 2026-07-20, 'the first reset
    should update the game'."""
    from tuipet.optionsscreen import OptionsPanel, _ROWS
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0

    # the launch auto-update path leaves its 'installed' word on the app's
    # update_hint (NOT self._updated -- that flag is the OPTIONS install's).
    pan = OptionsPanel(p, sound_get=lambda: True, sound_toggle=lambda: None,
                       update_hint=lambda: "✔ tuipet 9.9.9 installed — restart to play it")
    assert pan._value("update") == "restart to apply"          # display says restart
    pan.cursor = _ROWS.index("update")
    assert pan.key("enter") == ("done", ("restart",))          # ...and ENTER does it

    # the manual-install path (self._updated, no hint) restarts too
    pan2 = OptionsPanel(p, sound_get=lambda: True, sound_toggle=lambda: None)
    pan2._updated = True
    pan2.cursor = _ROWS.index("update")
    assert pan2.key("enter") == ("done", ("restart",))
