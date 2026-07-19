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


def test_quarantine_notice_survives_the_new_game_flow(tmp_path, monkeypatch):
    """A quarantined save's warning must actually REACH the player (title
    audit 2026-07-19): the new-game path skips the welcome hud (title ->
    carousel, strips own the box every frame), so the notice used to be
    composed and then swallowed -- the pet loss looked exactly like a
    first launch, the very thing the 07-14 sweep exists to prevent.  It
    rides the post-pick flash now."""
    import asyncio
    from tuipet import persistence
    monkeypatch.setattr(persistence, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(persistence, "SAVE_PATH", str(tmp_path / "save.json"))
    monkeypatch.setattr(persistence, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    (tmp_path / "save.json").write_text("{corrupt!!")
    (tmp_path / "save.json.bak").write_text("also corrupt")
    from tuipet.app import TuiPetApp

    async def go():
        app = TuiPetApp()
        assert app._new_game and "kept as" in app._boot_notice
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause(0.3)
            await pilot.press("enter")            # dismiss the title
            await pilot.pause(0.3)
            await pilot.press("enter")            # pick the first egg
            await pilot.pause(0.3)
            hud = str(app.msg_w.render())
            return hud

    hud = asyncio.run(go())
    assert "couldn" in hud or "kept as" in hud, hud
