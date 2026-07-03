"""Lobby polish — reconnect-with-backoff, roster notices, PvP round feedback.
Unit tests drive LobbyClient._handle / LobbyPanel.anim directly; the reconnect
integration test runs the real server.py subprocess and restarts it mid-session."""
import asyncio
import os
import socket
import subprocess
import sys
import time

import pytest

from tuipet.net import LobbyClient, LobbyState
from tuipet.pet import Pet
from tuipet import lobbyscreen


# ---- unit: _handle ----------------------------------------------------------

def test_wrong_password_stops_the_client_for_good():
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "login_failed", "msg": "Wrong password for that name."}')
    assert c._stop and c.state.login_failed


def test_already_online_after_a_welcome_is_a_transient_retry():
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "welcome", "id": 3, "name": "joel"}')
    c._handle('{"t": "login_failed", "msg": "That name is already online."}')
    assert not c._stop and c.state.login_failed is None       # the dead session reaps soon
    # ...but the same message on a FIRST login is a real rejection
    c2 = LobbyClient("ws://x/", "joel")
    c2._handle('{"t": "login_failed", "msg": "That name is already online."}')
    assert c2._stop and c2.state.login_failed


# ---- unit: panel ------------------------------------------------------------

class _StubClient:
    def __init__(self, state):
        self.state = state
    def respond(self, *a, **k): pass
    def relay(self, *a, **k): pass
    def update_pet(self, *a, **k): pass


def _panel(state):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = lobbyscreen.LobbyPanel(p, lambda name, pw, card: _StubClient(state),
                                 name="joel", pw="x")
    pan.status = "Up/Down pick · Enter chat/act · Esc leave"
    return pan


def test_reconnect_shows_status_not_a_dead_banner():
    s = LobbyState()
    s.connected = False
    s.reconnecting = True
    pan = _panel(s)
    pan.anim()
    assert "reconnecting" in pan.status
    s.connected, s.reconnecting = True, False
    pan.anim()
    assert pan.status == "Reconnected."


def test_roster_diff_lands_join_and_leave_notices_in_chat():
    s = LobbyState()
    s.connected = True
    s.me_id = 1
    s.roster = [{"id": 1, "name": "joel", "pet": {}}]
    pan = _panel(s)
    pan.anim()                                                # baseline: no announcements
    assert not s.chat
    s.roster = [{"id": 1, "name": "joel", "pet": {}}, {"id": 2, "name": "kai", "pet": {}}]
    pan.anim()
    s.roster = [{"id": 1, "name": "joel", "pet": {}}]
    pan.anim()
    assert ("", "kai joined") in s.chat and ("", "kai left") in s.chat


def test_guest_hp_bar_uses_its_own_trained_card():
    from tuipet import battle
    s = LobbyState()
    pan = _panel(s)
    pan.pet.full_health = 23                                  # trained past the stage table
    pan.is_host = False
    pan._battle_begin({"num": 4, "name": "X", "stage": "Champion", "hp": 15})
    assert pan.my_max == 23                                   # not MAX_HEALTH["Champion"]=15


def test_round_log_names_the_moves():
    s = LobbyState()
    pan = _panel(s)
    pan.is_host = True
    pan.opp_card = {"num": 100, "name": "Gatomon", "stage": "Champion"}
    pan.bphase = "wait"
    pan._apply_result({"host_dealt": 3, "guest_dealt": 1, "hattr": "Vaccine", "gattr": "Virus",
                       "hhp": 10, "ghp": 5, "over": False,
                       "host_alive": True, "guest_alive": True}, as_host=True)
    assert "3 dmg" in pan.bt_log and "1 dmg" in pan.bt_log
    assert pan.sfx in ("strongHit", "attackHit")              # every round sounds
    assert pan.bphase == "choose"


# ---- integration: real server, real drop -------------------------------------

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
           "TUIPET_SAVES": str(tmp_path / "saves.json")}
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


def test_lobby_client_survives_a_server_restart(tmp_path):
    port = _free_port()
    proc = _spawn(port, tmp_path)

    async def scenario():
        c = LobbyClient(f"ws://127.0.0.1:{port}/", "joel", "secret", {"name": "Gato"})
        c._backoff0 = 0.2
        task = asyncio.create_task(c.run())
        try:
            assert await _wait(lambda: c.state.connected), "never connected"
            nonlocal proc
            proc.terminate(); proc.wait(timeout=3)            # the drop
            assert await _wait(lambda: c.state.reconnecting), "no reconnect state"
            proc = _spawn(port, tmp_path)                     # the server returns
            assert await _wait(lambda: c.state.connected), "never reconnected"
            assert not c.state.login_failed                   # same password: quiet rejoin
        finally:
            task.cancel()

    try:
        asyncio.run(scenario())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
