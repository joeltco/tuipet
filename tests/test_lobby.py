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
    pan.status = "↑↓ pick · Enter chat/act · Esc leave"
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


# ---- presence + PMs (online arc 2026-07-05) ----------------------------------

def test_playing_ghosts_are_message_only_targets():
    """The roster carries everyone online: a sync ghost (live=False) renders
    dim in the sidebar, and its action menu offers ONLY [M]essage -- battle
    and jogress invites need a live lobby login."""
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {}, "live": False}]
    pan = _panel(s)
    sent = []
    pan.client.pm = lambda to, tx: sent.append((to, tx))
    pan.client.invite = lambda *a: sent.append(("INVITE", a))
    assert "·mika" in pan.text().plain                      # ghost marker in the sidebar
    pan.key("enter")                                        # open mika's action menu
    assert pan.action_for == (2, "mika", False)
    assert "not in lobby" in pan.text().plain               # message/ping menu
    pan.key("b")                                            # invites are dead on a ghost
    assert pan.action_for is not None and not sent
    pan.key("m")                                            # compose opens
    assert pan.pm_to == (2, "mika")
    for ch in "yo":
        pan.key(ch)
    pan.key("enter")
    assert sent == [(2, "yo")] and pan.pm_to is None        # sent + compose closed


def test_ping_pulls_a_ghost_into_the_lobby():
    """A ghost can't be battle/jogress-invited, but [P]ing nudges them (via the PM
    channel that reaches their home-screen alert) to come to the lobby."""
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {}, "live": False}]
    pan = _panel(s)
    sent = []
    pan.client.ping = lambda to: sent.append(("PING", to))
    pan.key("enter")                                        # open mika's (ghost) menu
    assert pan.action_for == (2, "mika", False)
    assert "[P]ing" in pan.text().plain                     # ghost menu offers the ping
    pan.key("p")
    assert sent == [("PING", 2)] and pan.action_for is None


def test_pms_land_in_per_peer_dm_threads():
    """PMs open a private thread per peer (not the public feed): an incoming PM lands in
    dms[peer] and marks unread; your own sent echo (pm_ok) lands in the same thread."""
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "welcome", "id": 1, "name": "joel"}')
    c._handle('{"t": "pm", "from_id": 2, "from_name": "mika", "text": "hey"}')
    c._handle('{"t": "pm_ok", "to_name": "mika", "text": "sup"}')
    assert c.state.dms["mika"] == [("mika", "hey"), ("joel", "sup")]
    assert "mika" in c.state.unread
    assert not any(str(nm).startswith("✉") for nm, _ in c.state.chat)   # off the public room


def test_dm_thread_view_and_block():
    """[V]iew opens the private thread (clears unread) and typing sends a PM; [X] blocks a
    peer so their chat/PMs drop and the mute persists."""
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {}, "live": True}]
    s.dms["mika"] = [("mika", "hey")]
    s.unread.add("mika")
    pan = _panel(s)
    sent = []
    pan.client.pm = lambda to, tx: sent.append((to, tx))
    pan.key("enter")                        # open mika's action menu
    pan.key("v")                            # open the DM thread
    assert pan.phase == "dm" and pan.dm_peer == (2, "mika")
    assert "mika" not in s.unread           # opening clears unread
    for ch in "hi":
        pan.key(ch)
    pan.key("enter")
    assert sent == [(2, "hi")]              # typed line sent as a PM
    pan.key("escape")
    assert pan.phase == "lobby"
    pan.key("enter"); pan.key("x")          # block mika
    assert "mika" in s.blocked


def test_egg_sessions_are_gated_both_directions():
    """Egg-battle audit (2026-07-06): the lobby has NO stage gate (chat/PMs
    are fine for an egg) but sessions must honour the offline gates -- an egg
    could INVITE battle/jogress and ACCEPT a battle invite, and the PvP round
    replay then CRASHED on the egg's missing roster sheet."""
    from tuipet.pet import Pet
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {"name": "Gabumon"}, "live": True}]

    class _Stub:
        def __init__(self, state): self.state = state; self.sent = []
        def respond(self, *a, **k): self.sent.append(("respond",) + a)
        def relay(self, *a, **k): self.sent.append(("relay",) + a)
        def invite(self, *a, **k): self.sent.append(("invite",) + a)
        def update_pet(self, *a, **k): pass
        def pm(self, *a, **k): pass

    stub = _Stub(s)
    egg = Pet.new_egg()
    pan = lobbyscreen.LobbyPanel(egg, lambda n, p, c: stub, name="joel", pw="x")
    pan.key("enter"); pan.key("b")                      # egg tries to invite battle
    assert "Too young" in pan.status and not stub.sent
    pan.key("enter"); pan.key("j")                      # ...and jogress
    assert "Too young" in pan.status and not stub.sent
    s.inbox.append({"t": "invite", "from_id": 2, "from_name": "mika", "kind": "battle"})
    pan.anim()                                          # incoming invite auto-declines
    assert pan.invite_prompt is None and pan.phase == "lobby"
    assert stub.sent == [("respond", 2, "battle", False)]


def test_remote_invite_never_disturbs_a_sleeper():
    """Asleep sweep (2026-07-06): the invite auto-decline called can_battle,
    whose guard DISTURBS a sleeper (grumble-wake + mood hit + disturb count)
    and rolls a refusal -- a stranger's night invite silently woke the pet.
    The remote gate is PURE now: decline, pet untouched."""
    from tuipet.pet import Pet
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {"name": "Gabumon"}, "live": True}]

    class _Stub:
        def __init__(self, state): self.state = state; self.sent = []
        def respond(self, *a, **k): self.sent.append(("respond",) + a)
        def relay(self, *a, **k): pass
        def invite(self, *a, **k): pass
        def update_pet(self, *a, **k): pass
        def pm(self, *a, **k): pass

    stub = _Stub(s)
    pet = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
    pet.world_seconds = 2 * 60.0
    pet.asleep, pet.lights = True, False
    pan = lobbyscreen.LobbyPanel(pet, lambda n, p, c: stub, name="joel", pw="x")
    s.inbox.append({"t": "invite", "from_id": 2, "from_name": "mika", "kind": "battle"})
    pan.anim()
    assert stub.sent == [("respond", 2, "battle", False)]
    assert pet.asleep and pet.disturb == 0 and pet.mood == 0
    assert pan.invite_prompt is None


def test_jogress_ships_and_catches_the_partners_sickness(monkeypatch):
    """JogressProtocol ships the REAL sick state; startJogress rolls
    checkSick(90) -- fusing with a sick partner is a near-certain catch
    (jogress/DNA audit 2026-07-06)."""
    import random
    from tuipet.pet import Pet
    from tuipet import jogress
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {"name": "Gabumon"}, "live": True}]

    class _Stub:
        def __init__(self, state): self.state = state; self.sent = []
        def relay(self, *a, **k): self.sent.append(a)
        def respond(self, *a, **k): pass
        def invite(self, *a, **k): pass
        def update_pet(self, *a, **k): pass
        def pm(self, *a, **k): pass

    stub = _Stub(s)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus",
            sick=True, sick_length=100.0, dp=100)
    pan = lobbyscreen.LobbyPanel(p, lambda n, pw, c: stub, name="joel", pw="x")
    pan.client = stub
    pan._enter_session(2, "mika", "jogress", host=True)
    assert stub.sent and stub.sent[-1][1]["sick"] is True   # the wire carries it
    # ...and the receiving side catches at the fuse
    q_pan = lobbyscreen.LobbyPanel(Pet(num=102, name="D", stage="Champion",
                                       attribute="Virus", dp=100),
                                   lambda n, pw, c: stub, name="joel", pw="x")
    q_pan.jpartner_sick = True
    q_pan.jphase = "result"
    q_pan.jresult = {"num": 102}
    q_pan.partner = (2, "mika")
    q_pan.client = stub
    monkeypatch.setattr(jogress, "fuse", lambda pet, num: "Fused!")
    monkeypatch.setattr(random, "randrange", lambda n: 0)   # the 90% catch lands
    q_pan._key_jogress("enter")
    assert q_pan.pet.sick


def test_apply_dna_no_longer_marks_a_false_disturb():
    """canon applyDNA calls disturb() -- a no-op on an AWAKE pet; the old port
    incremented the evolution disturb counter on every charge."""
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.dna_owned["DragonsRoar"] = 5
    d0 = p.disturb
    p.apply_dna("DragonsRoar", 2)
    assert p.disturb == d0
    assert p.dna_applied["DragonsRoar"] == 2


def test_pvp_cards_ship_the_declared_attribute():
    """BattleProtocol ships the declared attribute (lobby audit 2026-07-06):
    the Battle honours it -- a Vaccine pet whose strongest power is Virus
    still fights AS Vaccine; wild enemies (and Free pets) derive from power."""
    from tuipet import battle as battle_mod
    from tuipet.pet import Pet
    p = Pet(num=102, name="D", stage="Champion", attribute="Vaccine",
            vaccine=1, data_power=1, virus=50)
    card = battle_mod.battle_card(p)
    assert card["attribute"] == "Vaccine"
    q = Pet(num=102, name="Q", stage="Champion", attribute="Virus")
    b = battle_mod.Battle(q, dict(card))
    assert b.enemy["attribute"] == "Vaccine"       # the declared type stands
    wild = dict(card)
    del wild["attribute"]
    b2 = battle_mod.Battle(q, wild)
    assert b2.enemy["attribute"] == "Virus"        # wild: strongest power derives


# ---- message handling across back-out/re-enter (audit 2026-07-06) -------------

def test_queued_pms_seed_the_fresh_lobby_pane():
    """PMs queued while in another sub-screen used to be clear()ed on lobby
    entry -- assumed shown by the lobby chat, but the fresh client never saw
    them.  They now seed the pane until the client is CONNECTED (after which
    the lobby's own copy makes the ghost's a duplicate)."""
    from types import SimpleNamespace
    from tuipet.app import TuiPetApp

    state = LobbyState()
    pan = _panel(state)
    sync = SimpleNamespace(inbox=[("gato", "hey!"), ("gato", "you there?")])
    stub = SimpleNamespace(_sync=sync, mode=pan, _flash_t=0)
    TuiPetApp._drain_pms(stub)                    # not connected -> seed + clear
    assert ("✉gato", "hey!") in state.chat and ("✉gato", "you there?") in state.chat
    assert sync.inbox == []
    state.connected = True                        # live: the lobby gets its own copy
    sync.inbox.append(("gato", "dupe"))
    TuiPetApp._drain_pms(stub)
    assert ("✉gato", "dupe") not in state.chat    # dropped as the duplicate
    assert sync.inbox == []


def test_reenter_evicts_stale_session_and_replays_chat(tmp_path):
    """The back-out/re-enter path end-to-end (audit 2026-07-06): the newest
    password-verified launch takes the room from its own lingering session
    (refusing it locked the account out for the ping-reaper window), and the
    server replays the rolling chat backlog so re-entry isn't a void."""
    port = _free_port()
    proc = _spawn(port, tmp_path)

    class _Booted(LobbyClient):
        def __init__(self, *a, boot=0.0, **k):
            super().__init__(*a, **k)
            self._boot = boot
        def _login_msg(self):
            return {"t": "login", "name": self.name, "pw": self.pw,
                    "pet": self.pet, "boot": self._boot}

    async def scenario():
        uri = f"ws://127.0.0.1:{port}/"
        a = _Booted(uri, "joel", "secret", {"name": "Gato"}, boot=100.0)
        a._backoff0 = 0.2
        ta = asyncio.create_task(a.run())
        assert await _wait(lambda: a.state.connected), "A never connected"
        a.chat("hello room")
        assert await _wait(lambda: ("joel", "hello room") in a.state.chat), "A's chat never echoed"

        # the same account comes back with a NEWER launch while A lingers
        b = _Booted(uri, "joel", "secret", {"name": "Gato"}, boot=200.0)
        b._backoff0 = 0.2
        tb = asyncio.create_task(b.run())
        try:
            assert await _wait(lambda: b.state.connected), "B was locked out by its own stale session"
            assert await _wait(lambda: ("joel", "hello room") in b.state.chat), \
                "the chat backlog was not replayed on re-entry"
            # A's reconnect (older boot) is refused terminally, not ping-ponged
            assert await _wait(lambda: a._stop or not a.state.connected), "A never displaced"
        finally:
            ta.cancel(); tb.cancel()

    try:
        asyncio.run(scenario())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_battle_relays_are_phase_gated():
    """Session audit 2026-07-07: a duplicate 'card' mid-fight used to re-run
    _battle_begin and RESET both HP bars; a stray 'result' outside the guest's
    wait re-applied a stale round."""
    s = LobbyState()
    pan = _panel(s)
    pan.phase, pan.partner, pan.is_host = "battle", (9, "kai"), False
    pan.bphase = "card"
    pan._on_relay({"from_id": 9, "payload": {"kind": "battle", "t": "card",
                                             "card": {"num": 4, "name": "X", "stage": "Champion", "hp": 15}}})
    assert pan.bphase == "choose"
    pan.my_hp = 3                                       # mid-fight, hurt
    pan._on_relay({"from_id": 9, "payload": {"kind": "battle", "t": "card",
                                             "card": {"num": 4, "name": "X", "stage": "Champion", "hp": 15}}})
    assert pan.my_hp == 3, "a stale card must not reset the fight"
    pan._on_relay({"from_id": 9, "payload": {"kind": "battle", "t": "result", "host_dealt": 9,
                                             "guest_dealt": 0, "hhp": 1, "ghp": 1, "over": False,
                                             "host_alive": True, "guest_alive": True}})
    assert pan.my_hp == 3, "a result outside 'wait' must be ignored"


def test_crossed_invites_consume_the_pending_prompt():
    """Both players invite each other: entering a session busy-declines and
    clears the other prompt instead of re-offering a dead invite later."""
    declines = []
    s = LobbyState()
    pan = _panel(s)
    pan.client.respond = lambda to, kind, accept, busy=False: declines.append((to, accept, busy))
    pan.client.relay = lambda *a, **k: None
    pan.invite_prompt = {"from_id": 7, "from_name": "kai", "kind": "battle"}
    pan._enter_session(7, "kai", "battle", host=True)
    assert pan.invite_prompt is None
    assert declines == [(7, False, True)]


def test_battle_and_jogress_are_lobby_only():
    """Design decision (Joel 2026-07-07): battles and jogress are ONLINE-ONLY
    -- PvE combat lives in adventure/cup, fusion needs a real roster partner.
    The home screen must expose neither key."""
    from tuipet.app import TuiPetApp
    keys = {b[0] for b in TuiPetApp.BINDINGS}
    assert "b" not in keys and "j" not in keys
    assert not hasattr(TuiPetApp, "action_battle")
    assert not hasattr(TuiPetApp, "action_jogress")
    assert "l" in keys and "a" in keys and "u" in keys      # the surviving routes


def _jogress_session(monkeypatch, peer_two_phase=True):
    """A panel sitting at the jogress RESULT screen with a stubbed partner."""
    from tuipet import jogress
    relays = []
    s = LobbyState()
    pan = _panel(s)
    pan.client.relay = lambda to, payload: relays.append(payload)
    fused = []
    monkeypatch.setattr(jogress, "can_jogress", lambda pet: None)
    monkeypatch.setattr(jogress, "resolve_online",
                        lambda pet, payload: {"num": 102, "name": "Devimon"})
    monkeypatch.setattr(jogress, "fuse", lambda pet, num: fused.append(num) or "Fused!")
    pan.phase, pan.jphase = "jogress", "waiting"
    pan.partner = (9, "kai")
    card = {"kind": "jogress", "attr": "Virus", "num": 56, "name": "Agumon", "sick": False}
    if peer_two_phase:
        card["confirm2"] = True
    pan._on_relay({"from_id": 9, "payload": card})
    assert pan.jphase == "result"
    pan.jshow = None                        # skip the scene: straight to the choice
    return pan, relays, fused


def test_jogress_two_phase_needs_both_confirms(monkeypatch):
    """Consent audit 2026-07-07: the fusion is permanent, so BOTH players say
    yes at the result screen -- one confirm alone must not fuse."""
    pan, relays, fused = _jogress_session(monkeypatch)
    pan._key_jogress("enter")
    assert {"kind": "jogress", "t": "confirm"} in relays
    assert not fused and pan.phase == "jogress", "one confirm must not commit"
    pan._on_relay({"from_id": 9, "payload": {"kind": "jogress", "t": "confirm"}})
    assert fused == [102] and pan.phase == "lobby"      # both in -> committed
    # ...and the reverse order works too
    pan2, _, fused2 = _jogress_session(monkeypatch)
    pan2._on_relay({"from_id": 9, "payload": {"kind": "jogress", "t": "confirm"}})
    assert not fused2, "the partner alone must not commit my pet"
    pan2._key_jogress("enter")
    assert fused2 == [102]


def test_jogress_escape_is_a_real_decline(monkeypatch):
    """ESC at the result screen declines for BOTH sides -- the old behavior
    committed on every key including escape."""
    pan, relays, fused = _jogress_session(monkeypatch)
    pan._key_jogress("escape")
    assert {"kind": "jogress", "t": "decline"} in relays
    assert not fused and pan.phase == "lobby"
    pan2, _, fused2 = _jogress_session(monkeypatch)
    pan2._on_relay({"from_id": 9, "payload": {"kind": "jogress", "t": "decline"}})
    assert not fused2 and pan2.phase == "lobby", "a partner's decline unwinds me too"


def test_jogress_legacy_peer_keeps_the_instant_commit(monkeypatch):
    """A pre-v0.2.350 peer has no decline and commits on any key: mirror it,
    or a mixed-version pair fuses one-sided again."""
    pan, relays, fused = _jogress_session(monkeypatch, peer_two_phase=False)
    pan._key_jogress("escape")
    assert fused == [102] and pan.phase == "lobby"
    assert not any(p.get("t") == "decline" for p in relays)


def test_jogress_partner_leaving_at_result_fuses_nobody(monkeypatch):
    pan, relays, fused = _jogress_session(monkeypatch)
    pan._key_jogress("enter")                    # I said yes; they vanish instead
    pan._on_relay({"from_id": 9, "payload": {"kind": "jogress", "abort": True}})
    assert not fused and pan.phase == "lobby"


def test_jogress_resolution_failure_notifies_the_partner(monkeypatch):
    """Jogress audit 2026-07-08: if my side can't resolve the fusion (a pet
    that dozed off or lost DP after inviting), I must relay an abort so the
    partner isn't left hanging at its result screen waiting for a confirm I'll
    never send.  Before the fix the failed side returned silently."""
    from tuipet import jogress
    relays = []
    s = LobbyState()
    pan = _panel(s)
    pan.client.relay = lambda to, payload: relays.append((to, payload))
    monkeypatch.setattr(jogress, "can_jogress", lambda pet: None)
    monkeypatch.setattr(jogress, "resolve_online", lambda pet, payload: None)  # no resonance
    pan.phase, pan.jphase = "jogress", "waiting"
    pan.partner = (9, "kai")
    card = {"kind": "jogress", "attr": "Virus", "num": 56, "name": "Agumon",
            "sick": False, "confirm2": True}
    pan._on_relay({"from_id": 9, "payload": card})
    assert pan.jphase == "failed"
    assert (9, {"kind": "jogress", "abort": True}) in relays, \
        "the failing side must tell the partner so it can't hang"


def test_malicious_pm_cannot_crash_the_flash():
    """Chat-input audit 2026-07-07: a PM's sender name and body are REMOTE
    strings.  The home ✉ alert renders as Rich MARKUP, so an unbalanced
    bracket ('[/]', '[red]') used to drop text or raise MarkupError.  They
    must now render literally."""
    from types import SimpleNamespace
    from rich.text import Text
    from tuipet.app import TuiPetApp

    flashed = []
    evil_name, evil_text = "[/]evil]", "pwn [red]you[/] [[["
    sync = SimpleNamespace(inbox=[(evil_name, evil_text)])
    stub = SimpleNamespace(_sync=sync, mode=None, _flash_t=0,
                           flash=lambda s: flashed.append(s),
                           beep=lambda *a, **k: None)
    TuiPetApp._drain_pms(stub)
    assert flashed, "the PM never flashed"
    rendered = Text.from_markup(flashed[0])                 # must not raise
    assert evil_name in rendered.plain                      # the name survives, literal
    assert "pwn" in rendered.plain and "you" in rendered.plain
    assert "[red]" in rendered.plain                        # their fake tag is INERT text


def test_chat_input_buffer_is_capped():
    """The local input buffer was unbounded -- a long paste grew it without
    limit (the server clips the SENT text, not the buffer)."""
    from tuipet import lobbyscreen
    s = LobbyState()
    pan = _panel(s)
    for _ in range(lobbyscreen.CHAT_MAX + 200):
        pan._edit("x")
    assert len(pan.buf) == lobbyscreen.CHAT_MAX
