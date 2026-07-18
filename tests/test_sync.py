"""Cross-device cloud save: the persistence payload helpers, plus a real
round-trip through a live server subprocess (push on one 'device', pull on
another, last-write-wins, wrong-password rejection, offline = silent).
"""
import json
import os
import socket
import subprocess
import sys
import time

import pytest

from tuipet import persistence, cloudsync
from tuipet.pet import Pet


# ---- payload helpers (no network) ------------------------------------------

def test_save_dict_roundtrips_through_pet():
    pet = Pet(num=-1, stage="Rookie", vaccine=12, data_power=3, virus=4)
    data = persistence.to_save_dict(pet)
    assert "_saved_at" in data and data["_saved_at"] > 0
    back, _ = persistence.pet_from_save(data, catch_up=False)
    assert back is not None
    assert (back.stage, back.vaccine, back.data_power, back.virus) == ("Rookie", 12, 3, 4)


def test_pet_from_save_rejects_garbage():
    assert persistence.pet_from_save(None)[0] is None
    assert persistence.pet_from_save({"not": "a pet"})[0] is None       # missing required fields tolerated


def test_write_and_read_local_saved_at(tmp_path):
    p = str(tmp_path / "s.json")
    assert persistence.local_saved_at(p) == 0.0                          # no file
    persistence.write_save_dict({"stage": "Egg", "_saved_at": 1234.5}, p)
    assert persistence.local_saved_at(p) == 1234.5


# ---- live server round-trip ------------------------------------------------

def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def server(tmp_path):
    """A real server.py subprocess on a free port with temp accounts/saves."""
    port = _free_port()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {**os.environ,
           "TUIPET_PORT": str(port),
           "TUIPET_HOST": "127.0.0.1",
           "TUIPET_ACCOUNTS": str(tmp_path / "accounts.json"),
           "TUIPET_SAVES": str(tmp_path / "saves.json")}
    proc = subprocess.Popen([sys.executable, os.path.join(root, "server", "server.py")],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    uri = f"ws://127.0.0.1:{port}/"
    # wait until the port accepts connections
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.skip("server did not start")
    yield uri
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_push_then_pull_across_devices(server):
    a = {"num": 42, "name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0}
    assert cloudsync.push_save(server, "joel", "secret", a) is True       # device A claims + pushes
    got = cloudsync.pull_save(server, "joel", "secret")                   # device B pulls
    assert got["name"] == "Agumon" and got["_saved_at"] == 1000.0


def test_last_write_wins(server):
    cloudsync.push_save(server, "joel", "secret", {"name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0})
    cloudsync.push_save(server, "joel", "secret", {"name": "OLD", "stage": "Rookie", "_saved_at": 500.0})
    assert cloudsync.pull_save(server, "joel", "secret")["name"] == "Agumon"   # stale rejected
    cloudsync.push_save(server, "joel", "secret", {"name": "Greymon", "stage": "Champion", "_saved_at": 2000.0})
    assert cloudsync.pull_save(server, "joel", "secret")["name"] == "Greymon"  # newer wins


def test_wrong_password_is_blocked(server):
    cloudsync.push_save(server, "joel", "secret", {"name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0})
    assert cloudsync.pull_save(server, "joel", "WRONG") is None


# ---- boot-stamped leases (lobby-server audit 2026-07-05) ----------------------

def _conn(uri):
    from websockets.sync.client import connect
    return connect(uri, open_timeout=3, close_timeout=1)


def _login(ws, name, pw, boot=None, sync_only=True, pet=None):
    msg = {"t": "login", "name": name, "pw": pw}
    if sync_only:
        msg["sync_only"] = True
    if boot is not None:
        msg["boot"] = boot
    if pet is not None:
        msg["pet"] = pet
    ws.send(json.dumps(msg))
    for _ in range(5):
        m = json.loads(ws.recv(timeout=3))
        if m.get("t") in ("welcome", "login_failed"):
            return m
    return {}


def _cloud_name(uri, name, pw):
    got = cloudsync.pull_save(uri, name, pw)
    return (got or {}).get("name")


def _ack(ws):
    """Next `saved` verdict, skipping stray broadcasts (rosters reach everyone)."""
    for _ in range(5):
        m = json.loads(ws.recv(timeout=3))
        if m.get("t") == "saved":
            return m
    return {}


def test_older_launch_cannot_steal_the_lease_back(server):
    """The wifi-blip hole: a backgrounded phone's RECONNECT must not re-take
    save ownership from the session the player launched later."""
    phone = _conn(server)
    _login(phone, "joel", "secret", boot=100.0)
    desk = _conn(server)
    _login(desk, "joel", "secret", boot=200.0)         # the newer launch owns saves
    phone.close()
    phone2 = _conn(server)                              # the phone reconnects (same launch)
    _login(phone2, "joel", "secret", boot=100.0)
    phone2.send(json.dumps({"t": "save", "save": {
        "name": "FORK", "stage": "Rookie", "_saved_at": 9999.0}}))
    assert _ack(phone2) == {"t": "saved", "ok": False, "why": "lease"}   # dropped, and told WHY
    desk.send(json.dumps({"t": "save", "save": {
        "name": "TRUTH", "stage": "Rookie", "_saved_at": 500.0}}))
    assert _ack(desk) == {"t": "saved", "ok": True}
    assert _cloud_name(server, "joel", "secret") == "TRUTH"   # the fork was dropped
    phone2.close(); desk.close()


def test_live_lobby_login_does_not_stale_the_autosync(server):
    """Entering the lobby is not a device change: the same app's background
    SyncClient must keep its lease (a crash after a lobby visit used to lose
    everything since entry)."""
    sync = _conn(server)
    _login(sync, "joel", "secret", boot=100.0)
    lobby = _conn(server)
    m = _login(lobby, "joel", "secret", sync_only=False, pet={"name": "Agumon"})
    assert m.get("t") == "welcome"                      # live + sync coexist
    sync.send(json.dumps({"t": "save", "save": {
        "name": "KEPT", "stage": "Rookie", "_saved_at": 1000.0}}))
    assert _ack(sync) == {"t": "saved", "ok": True}         # the lease survived the lobby login
    assert _cloud_name(server, "joel", "secret") == "KEPT"
    lobby.close(); sync.close()


def test_real_syncclient_keeps_saving_after_a_lobby_login(server):
    """The full stack on ONE loop (the asyncio.Queue cross-loop gotcha): a real
    SyncClient autosaving while a real LobbyClient logs in on the same account —
    the autosave must still land afterwards."""
    import asyncio
    from tuipet.net import SyncClient, LobbyClient

    async def scenario():
        sync = SyncClient(server, "joel", "secret")
        st = asyncio.create_task(sync.run())
        for _ in range(60):
            if sync.connected:
                break
            await asyncio.sleep(0.05)
        assert sync.connected
        lobby = LobbyClient(server, "joel", "secret", pet={"name": "Agumon"})
        lt = asyncio.create_task(lobby.run())
        for _ in range(60):
            if lobby.state.connected:
                break
            await asyncio.sleep(0.05)
        assert lobby.state.connected                # live + sync coexist
        sync.push_save({"name": "KEPT", "stage": "Rookie", "_saved_at": 1000.0})
        await asyncio.sleep(0.5)
        st.cancel(); lt.cancel()

    asyncio.run(scenario())
    assert _cloud_name(server, "joel", "secret") == "KEPT"


def test_sync_ghost_is_mute_and_uninvitable(server):
    """A sync_only connection is not in the room: its chat must not reach the
    lobby and it can't be a session target."""
    ghost = _conn(server)
    _login(ghost, "joel", "secret", boot=100.0)
    live = _conn(server)
    _login(live, "mika", "pw2", sync_only=False, pet={"name": "Gabumon"})
    ghost.send(json.dumps({"t": "chat", "text": "boo"}))
    with pytest.raises(TimeoutError):
        while True:
            m = json.loads(live.recv(timeout=1.0))
            assert m.get("t") != "chat"                 # rosters may arrive; chat must not
    ghost.close(); live.close()


def test_startup_pull_mirrors_cloud_to_local(server, tmp_path, monkeypatch):
    # isolate_save (autouse) already sandboxes SAVE_PATH; push a cloud save, then
    # a fresh device's startup pull should write it locally.
    # the pushed blob must be a REAL save: the pull now validates it can become
    # a pet before overwriting local (a malformed cloud payload used to mean a
    # silent fresh-egg wipe)
    cloud_pet = Pet.from_num(100)      # a REAL record: the strict probe now rejects
    #                                    hand-built pets whose name/stage lie about their dex
    blob = persistence.to_save_dict(cloud_pet)
    blob["_saved_at"] = 9000.0
    cloudsync.push_save(server, "joel", "secret", blob)
    assert not os.path.exists(persistence.SAVE_PATH)
    assert cloudsync.sync_down_at_startup(server, "joel", "secret") == "pulled"
    assert json.load(open(persistence.SAVE_PATH))["name"] == "Gatomon"   # dex 100's real name
    # a second pull is a no-op (local is now as new as the cloud)
    assert cloudsync.sync_down_at_startup(server, "joel", "secret") == ""


def test_offline_is_silent():
    # nothing listening -> never raises, returns falsy
    assert cloudsync.pull_save("ws://127.0.0.1:1/", "joel", "secret", timeout=0.5) is None
    assert cloudsync.push_save("ws://127.0.0.1:1/", "joel", "secret", {"_saved_at": 1}, timeout=0.5) is False
    assert cloudsync.sync_down_at_startup("ws://127.0.0.1:1/", "joel", "secret", timeout=0.5) == ""


# ---- presence + private messages (online arc 2026-07-05) ---------------------

def _next_of(ws, want, tries=8):
    for _ in range(tries):
        m = json.loads(ws.recv(timeout=3))
        if m.get("t") == want:
            return m
    return {}


def test_roster_shows_playing_ghosts_deduped_per_account(server):
    """The lobby shows everyone ONLINE: sync-only players ride the roster as
    live=False ghosts; an account with BOTH connections gets ONE entry (the
    live one wins)."""
    ghost = _conn(server)
    _login(ghost, "joel", "secret", boot=100.0)
    live = _conn(server)
    _login(live, "mika", "pw2", sync_only=False, pet={"name": "Gabumon"})
    ros = _next_of(live, "roster")
    by = {p["name"]: p for p in ros["players"]}
    assert by["joel"]["live"] is False and by["mika"]["live"] is True
    # joel ALSO opens the lobby: still one entry, now live
    jlive = _conn(server)
    _login(jlive, "joel", "secret", sync_only=False, pet={"name": "Agumon"})
    ros = _next_of(live, "roster")
    joels = [p for p in ros["players"] if p["name"] == "joel"]
    assert len(joels) == 1 and joels[0]["live"] is True
    ghost.close(); live.close(); jlive.close()


def test_pm_reaches_every_connection_of_the_account(server):
    """A PM lands on the target's lobby login AND their home-screen sync
    ghost (the alert channel), and echoes pm_ok to the sender."""
    ghost = _conn(server)
    _login(ghost, "joel", "secret", boot=100.0)
    jlive = _conn(server)
    _login(jlive, "joel", "secret", sync_only=False, pet={"name": "Agumon"})
    mika = _conn(server)
    _login(mika, "mika", "pw2", sync_only=False, pet={"name": "Gabumon"})
    ros = _next_of(mika, "roster")
    joel_id = next(p["id"] for p in ros["players"] if p["name"] == "joel")
    mika.send(json.dumps({"t": "pm", "to": joel_id, "text": "yo"}))
    for ws in (jlive, ghost):
        m = _next_of(ws, "pm")
        assert (m.get("from_name"), m.get("text")) == ("mika", "yo")
    ok = _next_of(mika, "pm_ok")
    assert ok.get("to_name") == "joel" and ok.get("text") == "yo"
    ghost.close(); jlive.close(); mika.close()


def test_syncclient_inbox_carries_pms(server):
    """The real SyncClient surfaces PMs in .inbox -- the app's home-screen
    ✉ alert reads exactly this."""
    import asyncio
    from tuipet import net

    async def go():
        sc = net.SyncClient(server, "joel", "secret")
        task = asyncio.ensure_future(sc.run())
        for _ in range(40):
            if sc.connected:
                break
            await asyncio.sleep(0.1)
        assert sc.connected
        mika = await asyncio.to_thread(_conn, server)
        await asyncio.to_thread(_login, mika, "mika", "pw2", None, False, {"name": "Gabumon"})
        ros = await asyncio.to_thread(_next_of, mika, "roster")
        joel_id = next(p["id"] for p in ros["players"] if p["name"] == "joel")
        await asyncio.to_thread(mika.send, json.dumps({"t": "pm", "to": joel_id, "text": "hi joel"}))
        for _ in range(40):
            if sc.inbox:
                break
            await asyncio.sleep(0.1)
        task.cancel()
        await asyncio.to_thread(mika.close)
        return list(sc.inbox)

    inbox = asyncio.run(go())
    assert inbox and inbox[0] == ("mika", "hi joel")


def test_stop_sync_cancels_the_worker_not_just_flags_it():
    """Netplay audit 2026-07-18: the account switch set _stop and dropped the
    reference, but the old connection sat in `async for` until the socket
    died -- a live sync ghost in the roster after every switch.  _stop_sync
    must CANCEL the tracked worker like the lobby teardown does."""
    from types import SimpleNamespace
    from tuipet.app import TuiPetApp

    class _W:
        cancelled = False
        def cancel(self):
            self.cancelled = True

    sync = SimpleNamespace(_stop=False)
    w = _W()
    stub = SimpleNamespace(_sync=sync, _sync_worker=w)
    TuiPetApp._stop_sync(stub)
    assert sync._stop is True
    assert w.cancelled is True
    assert stub._sync is None and stub._sync_worker is None


# ---- the skew/size hardening (netplay audit 2026-07-18) ---------------------

def _server_mod():
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "server"))
    import server
    return server


def test_future_stamps_are_clamped_on_store(tmp_path, monkeypatch):
    """A fast wall-clock used to poison last-write-wins: one device stamping
    the future blocked the other device's REAL progress for as long as the
    skew.  The server now clamps a stored _saved_at to its own clock (+slack)
    and stamps its own receipt time alongside."""
    import asyncio, time
    server = _server_mod()
    monkeypatch.setattr(server, "SAVES_PATH", str(tmp_path / "saves.json"))
    monkeypatch.setattr(server, "SAVES", {})
    save = {"name": "Agumon", "stage": "Rookie", "_saved_at": time.time() + 9e9}
    assert asyncio.run(server._store_save("joel", dict(save))) is True
    stored = server.SAVES["joel"]
    assert stored["_saved_at"] <= time.time() + server.SAVE_STAMP_SLACK + 1
    assert stored["_srv_at"] <= time.time() + 1


def test_lease_seniority_is_server_first_seen_not_device_clocks(monkeypatch):
    """Lease ownership compared raw device wall-clocks: a lagging clock that
    launched LATER lost the lease to a fast clock that launched earlier.  Now
    seniority is the SERVER's first-seen time per launch stamp: latest login
    wins, a reconnect of an old launch still can't steal."""
    from types import SimpleNamespace
    server = _server_mod()
    monkeypatch.setattr(server, "LEASES", {})
    monkeypatch.setattr(server, "BOOT_SEEN", {})
    fast = SimpleNamespace(lease=None)     # clock runs YEARS ahead
    slow = SimpleNamespace(lease=None)     # clock runs behind -- but launches LATER
    server._take_lease(fast, "joel", boot=9e12)
    assert fast.lease is not None
    server._take_lease(slow, "joel", boot=100.0)
    assert slow.lease is not None, "the newest LOGIN must win, whatever its clock says"
    fast2 = SimpleNamespace(lease=None)    # the old launch reconnects (wifi blip)
    server._take_lease(fast2, "joel", boot=9e12)
    assert fast2.lease is None, "an old launch must not re-take the lease on reconnect"


def test_oversized_saves_are_refused_before_the_wire():
    """The server silently drops frames over 64KB -- a huge save would 'sync'
    forever without landing.  The pusher refuses pre-send and raises the flag
    the app's warn pass reads; the blocking quit-push refuses too."""
    from tuipet.net import SyncClient, SAVE_WIRE_MAX
    from tuipet import cloudsync
    c = SyncClient("ws://x", "joel")
    big = {"blob": "x" * (SAVE_WIRE_MAX + 1)}
    c.push_save(big)
    assert c.save_too_big is True and c._pending is None
    c.push_save({"name": "Agumon"})
    assert c.save_too_big is False and c._pending is not None
    assert cloudsync.push_save("ws://x/", "joel", "pw", big) is False


def test_saved_ack_why_maps_to_the_right_warning():
    """ok=False used to mean 'newer session' whatever the cause; the ack's
    `why` now separates the lease loss from a format rejection."""
    from tuipet.net import SyncClient
    c = SyncClient("ws://x", "joel")
    c._handle('{"t": "saved", "ok": false, "why": "invalid"}')
    assert c.save_invalid is True and c.cloud_dropped is False
    c._handle('{"t": "saved", "ok": false, "why": "lease"}')
    assert c.cloud_dropped is True
    c._handle('{"t": "saved", "ok": true}')
    assert c.cloud_dropped is False and c.save_invalid is False
    c._handle('{"t": "error", "msg": "Lobby is full."}')
    assert c.last_error == "Lobby is full."


def test_reconnect_grace_matches_the_servers_real_conflict_line():
    """The grace branch guarded on "already online" -- a string the server
    never sends (drifted dead branch).  It now matches the real line."""
    from tuipet.net import LobbyClient
    c = LobbyClient("ws://x/", "joel")
    c._had_welcome = True
    c._handle('{"t": "login_failed", "msg": "Signed in on a newer session."}')
    assert c._stop is False, "a session-conflict during reconnect keeps retrying"
    c._handle('{"t": "login_failed", "msg": "Wrong password."}')
    assert c._stop is True, "a credentials failure still ejects"
