"""The swallowed-failure sweep (2026-07-13).

Three shipped bugs shared one shape: a failure the code swallowed and reported
to the player as SUCCESS (iOS saves, iOS sound, the dead Termux bridge). These
pin the rest of that class -- every path where tuipet PROMISES the player
something and could quietly fail to deliver.
"""
import importlib
import os
import tempfile

from tuipet import persistence


def test_a_rejected_cloud_save_is_heard_not_ignored():
    """The server ACKs every push with {"t":"saved","ok":...} and answers
    ok=False when it DROPPED it (a stale lease -- a newer session owns the
    saves).  The client had no "saved" branch, so a device whose lease was
    taken went on believing it was syncing while the server binned every
    push: cross-device progress vanished, silently."""
    from tuipet.net import SyncClient
    c = SyncClient("ws://x", "joel")
    assert c.cloud_dropped is False
    c._handle('{"t": "saved", "ok": true}')
    assert c.cloud_dropped is False, "an accepted save is not a drop"
    c._handle('{"t": "saved", "ok": false}')
    assert c.cloud_dropped is True, "a REFUSED save must be heard"


def test_the_app_warns_once_when_the_cloud_refuses_us(monkeypatch):
    import tuipet.app as appmod
    app = appmod.TuiPetApp.__new__(appmod.TuiPetApp)
    flashes = []
    app.flash = lambda t: flashes.append(t)

    class _Sync:
        cloud_dropped = True
    app._sync = _Sync()
    appmod.TuiPetApp._warn_if_cloud_dropped(app)
    appmod.TuiPetApp._warn_if_cloud_dropped(app)      # ...only once
    assert len(flashes) == 1
    assert "Cloud sync off" in flashes[0]


def test_a_bug_report_never_promises_a_send_it_cannot_make(monkeypatch):
    """`add_pending_bug` swallowed OSError, so on a read-only save dir the
    player was told 'saved; it will send next time' while the report was
    simply gone."""
    home = tempfile.mkdtemp()
    os.chmod(home, 0o555)
    try:
        monkeypatch.setenv("HOME", home)
        for k in ("TUIPET_SAVE_DIR", "XDG_DATA_HOME"):
            monkeypatch.delenv(k, raising=False)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)
        assert persistence.add_pending_bug({"text": "x"}) is False, \
            "an unstashable report must say so"
    finally:
        os.chmod(home, 0o755)
        from tuipet import persistio
        importlib.reload(persistio)   # SAVE_DIR's owner (tier-4 split)
        importlib.reload(persistence)


def test_a_stashable_bug_reports_success():
    d = tempfile.mkdtemp()
    old = persistence.SAVE_DIR
    try:
        persistence.SAVE_DIR = d
        assert persistence.add_pending_bug({"text": "x"}) is True
        assert os.path.exists(os.path.join(d, "pending_bugs.jsonl"))
    finally:
        persistence.SAVE_DIR = old
