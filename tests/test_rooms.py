"""Password rooms (DSprite steal #6, 2026-07-14) + the offline-PM queue pin.

A room is a shared secret phrase: everyone who types `/room <phrase>` lands in
the same private scope — chat and roster are scoped, so battles/jogress follow
naturally; PMs and announcements stay global.  No registry: the room exists
exactly while clients carry its code.

The PM store-and-forward test is a REGRESSION PIN: the feature shipped 2026-07-12
as a box-only patch, and the 07-14 ladder redeploy silently clobbered it because
no repo test covered it.  Now it lives in git and in the suite.
"""
import asyncio
import os
import socket
import subprocess
import sys
import time

import pytest

from tuipet import lobbyscreen
from tuipet.net import LobbyClient, LobbyState
from tuipet.pet import Pet


def _srv():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server
    return server


# ---- unit: the server's scope plumbing ----------------------------------------

def test_room_code_normalizes_the_phrase():
    srv = _srv()
    assert srv._room_code("  Sea   Food ") == "sea food"
    assert srv._room_code("sea food") == "sea food"          # same room either way
    assert srv._room_code("") is None and srv._room_code(None) is None
    assert len(srv._room_code("x" * 99)) == srv.MAX_ROOM


def test_roster_is_scoped_and_ghosts_stay_in_main():
    srv = _srv()
    old = dict(srv.CLIENTS)
    srv.CLIENTS.clear()
    try:
        a, b, g = srv.Client(None), srv.Client(None), srv.Client(None)
        for c, name, live, room in ((a, "alice", True, "den"),
                                    (b, "bob", True, None),
                                    (g, "ghost", False, None)):
            c.name, c.live, c.room, c.logged = name, live, room, True
            srv.CLIENTS[c.id] = c
        main = {p["name"] for p in srv._roster(None)["players"]}
        den = {p["name"] for p in srv._roster("den")["players"]}
        assert main == {"bob", "ghost"}                       # ghosts only in main
        assert den == {"alice"}
    finally:
        srv.CLIENTS.clear()
        srv.CLIENTS.update(old)


# ---- unit: the panel's slash commands ------------------------------------------

class _RoomStub:
    def __init__(self):
        self.state = LobbyState()
        self.calls = []
    def room(self, code):
        self.calls.append(code)
    def relay(self, *a, **k): pass
    def respond(self, *a, **k): pass
    def update_pet(self, *a, **k): pass
    def chat(self, text):
        self.calls.append(("chat", text))


def _panel():
    p = Pet(num=100, stage="Adult", attribute="Vaccine")

    stub = _RoomStub()
    pan = lobbyscreen.LobbyPanel(p, lambda name, pw, card: stub, name="joel", pw="x")
    return pan, stub


def test_slash_room_and_leave_route_to_the_client():
    pan, stub = _panel()
    pan.buf = "/room sea food"
    pan._key_lobby("enter")
    assert stub.calls == ["sea food"] and pan.buf == ""
    pan.buf = "/leave"
    pan._key_lobby("enter")
    assert stub.calls == ["sea food", ""]
    pan.buf = "/help"
    pan._key_lobby("enter")
    assert "/room" in pan.status                              # unknown -> the help line
    assert stub.calls == ["sea food", ""]                     # nothing hit the wire
    pan.buf = "hello /room"                                   # only a LEADING slash commands
    pan._key_lobby("enter")
    assert ("chat", "hello /room") in stub.calls


def test_room_switch_is_not_a_wave_of_leaves():
    """Swapping scope replaces the whole roster; the join/left differ must
    re-baseline instead of printing everyone as departed."""
    pan, stub = _panel()
    s = pan.state
    s.connected = True
    s.me_id = 1
    s.roster = [{"id": 1, "name": "joel", "pet": {}},
                {"id": 2, "name": "kai", "pet": {}},
                {"id": 3, "name": "mika", "pet": {}}]
    pan.anim()                                                # baseline
    s.room = "den"                                            # room_ok landed...
    s.roster = [{"id": 1, "name": "joel", "pet": {}}]         # ...then the scoped roster
    pan.anim()
    assert not any("left" in tx for _, tx in s.chat)
    assert "room: den" in pan.status
    s.room = None                                             # back out
    s.roster = [{"id": 1, "name": "joel", "pet": {}},
                {"id": 2, "name": "kai", "pet": {}},
                {"id": 3, "name": "mika", "pet": {}}]
    pan.anim()
    assert not any("joined" in tx for _, tx in s.chat)


def test_room_ok_sets_state_and_logs_the_move():
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "room_ok", "room": "den"}')
    assert c.state.room == "den"
    assert ("", "— room: den —") in c.state.chat
    c._handle('{"t": "room_ok", "room": null}')
    assert c.state.room is None
    assert ("", "— main lobby —") in c.state.chat


# ---- integration: real server, three tamers ------------------------------------

def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _spawn(port, tmp_path):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {**os.environ, "TUIPET_PORT": str(port), "TUIPET_HOST": "127.0.0.1",
           "TUIPET_ACCOUNTS": str(tmp_path / "accounts.json"),
           "TUIPET_SAVES": str(tmp_path / "saves.json"),
           "TUIPET_PENDING": str(tmp_path / "pending_pms.json")}
    proc = subprocess.Popen([sys.executable, os.path.join(root, "server", "server.py")],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    pytest.skip("server did not start")


async def _wait(pred, timeout=8.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if pred():
            return True
        await asyncio.sleep(0.05)
    return False


def test_rooms_scope_chat_and_roster_but_not_pms(tmp_path):
    port = _free_port()
    proc = _spawn(port, tmp_path)

    async def scenario():
        uri = f"ws://127.0.0.1:{port}/"
        al = LobbyClient(uri, "alice", "pw", {"name": "Gato"})
        bo = LobbyClient(uri, "bob", "pw", {"name": "Agu"})
        ca = LobbyClient(uri, "cara", "pw", {"name": "Pata"})
        tasks = [asyncio.create_task(c.run()) for c in (al, bo, ca)]
        try:
            assert await _wait(lambda: all(c.state.connected for c in (al, bo, ca)))
            assert await _wait(lambda: len(al.state.roster) == 3)
            # alice + bob take the same phrase (case/spacing differ on purpose)
            al.room("Sea  Food")
            bo.room("sea food")
            assert await _wait(lambda: al.state.room == "sea food"
                               and bo.state.room == "sea food")
            assert await _wait(lambda: {p["name"] for p in al.state.roster}
                               == {"alice", "bob"})
            assert await _wait(lambda: {p["name"] for p in ca.state.roster} == {"cara"})
            # chat is scoped both ways
            al.chat("secret plans")
            assert await _wait(lambda: any(tx == "secret plans" for _, tx in bo.state.chat))
            ca.chat("main floor")
            await asyncio.sleep(0.5)
            assert not any(tx == "secret plans" for _, tx in ca.state.chat)
            assert not any(tx == "main floor" for _, tx in al.state.chat)
            # PMs stay global: cara reaches alice inside the room
            al_id = al.state.me_id
            ca.pm(al_id, "psst", "alice")
            assert await _wait(lambda: any(tx == "psst"
                                           for _, tx in al.state.dms.get("cara", [])))
            # /leave returns to main: roster refills, backlog replays
            al.room("")
            assert await _wait(lambda: al.state.room is None)
            assert await _wait(lambda: {p["name"] for p in al.state.roster}
                               == {"alice", "cara"})
            assert await _wait(lambda: any(tx == "main floor" for _, tx in al.state.chat))
        finally:
            for t in tasks:
                t.cancel()

    try:
        asyncio.run(scenario())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_offline_pm_queue_survives_in_the_repo(tmp_path):
    """REGRESSION PIN (2026-07-14): the 07-12 store-and-forward PM patch lived
    only on the prod box and the ladder redeploy wiped it.  A PM to an account
    with no live session must queue and deliver on its next login."""
    port = _free_port()
    proc = _spawn(port, tmp_path)

    async def scenario():
        uri = f"ws://127.0.0.1:{port}/"
        # dave claims his account, then leaves
        dv = LobbyClient(uri, "dave", "pw", {"name": "Vee"})
        task = asyncio.create_task(dv.run())
        assert await _wait(lambda: dv.state.connected)
        task.cancel()
        await asyncio.sleep(0.3)
        # alice PMs the OFFLINE dave by name (stale id 999)
        al = LobbyClient(uri, "alice", "pw", {"name": "Gato"})
        t2 = asyncio.create_task(al.run())
        assert await _wait(lambda: al.state.connected)
        al.pm(999, "welcome back", "dave")
        # sender is acked (their own thread copy saves) even though dave is away
        assert await _wait(lambda: any(tx == "welcome back"
                                       for _, tx in al.state.dms.get("dave", [])))
        # dave returns -> the held PM lands
        dv2 = LobbyClient(uri, "dave", "pw", {"name": "Vee"})
        t3 = asyncio.create_task(dv2.run())
        assert await _wait(lambda: any(tx == "welcome back"
                                       for _, tx in dv2.state.dms.get("alice", [])))
        t2.cancel()
        t3.cancel()

    try:
        asyncio.run(scenario())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
