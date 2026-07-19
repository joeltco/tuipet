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


def test_session_conflict_after_a_welcome_is_a_transient_retry():
    # the grace branch matches the server's REAL conflict line ("Signed in on
    # a newer session.") -- the old "already online" string was one the server
    # never sent, a drifted dead branch (netplay audit 2026-07-18)
    c = LobbyClient("ws://x/", "joel")
    c._handle('{"t": "welcome", "id": 3, "name": "joel"}')
    c._handle('{"t": "login_failed", "msg": "Signed in on a newer session."}')
    assert not c._stop and c.state.login_failed is None       # the dead session reaps soon
    # ...but the same message on a FIRST login is a real rejection
    c2 = LobbyClient("ws://x/", "joel")
    c2._handle('{"t": "login_failed", "msg": "Signed in on a newer session."}')
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
    pan.status = "↑↓ pick · ENTER chat · TAB ranks · ESC"
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


def test_sync_ghost_churn_never_reaches_the_chat():
    """The roxi pollution (Joel 2026-07-17): a home-screen sync ghost's
    reconnect loop gets a fresh connection id every drop, and the id-keyed
    diff announced each one as a lobby join/leave.  Ghosts (live=False) are
    sidebar-only; the chat speaks only of LIVE presences."""
    s = LobbyState()
    s.connected = True
    s.me_id = 1
    me = {"id": 1, "name": "joel", "pet": {}, "live": True}
    s.roster = [me]
    pan = _panel(s)
    pan.anim()
    for cid in (7, 8, 9):                          # roxi's ghost flaps: new id each drop
        s.roster = [me, {"id": cid, "name": "roxi", "pet": {}, "live": False}]
        pan.anim()
        s.roster = [me]
        pan.anim()
    assert not s.chat, f"ghost churn leaked into the chat: {s.chat}"
    # ...but roxi actually OPENING the lobby (live) announces exactly once
    s.roster = [me, {"id": 10, "name": "roxi", "pet": {}, "live": True}]
    pan.anim()
    assert s.chat == [("", "roxi joined")]


def test_live_reconnect_id_churn_is_not_a_join_wave():
    """A live player's reconnect swaps the connection id but keeps the name:
    the name-keyed diff stays quiet instead of stacking left+joined pairs."""
    s = LobbyState()
    s.connected = True
    s.me_id = 1
    me = {"id": 1, "name": "joel", "pet": {}, "live": True}
    s.roster = [me, {"id": 2, "name": "kai", "pet": {}, "live": True}]
    pan = _panel(s)
    pan.anim()
    s.chat.clear()
    s.roster = [me, {"id": 3, "name": "kai", "pet": {}, "live": True}]   # same kai, new id
    pan.anim()
    assert not s.chat


def test_both_bars_are_the_flat_race_hp():
    """0.5 BATTLE (2026-07-17): every bout is an HP race from 5 -- trained
    HP left with the classic engine.  A proto-3 card + commit begins clean."""
    import hashlib
    s = LobbyState()
    pan = _panel(s)
    pan.partner = (9, "kai")
    pan.phase, pan.bphase = "battle", "card"
    pan.bt_nonce = 7
    card = {"num": 4, "name": "X", "stage": "Champion", "proto": 3}
    pan._battle_begin(card, commit=hashlib.sha256(b"9").hexdigest())
    assert pan.my_max == pan.my_hp == 5
    assert pan.opp_max == pan.opp_hp == 5


def test_the_seeded_race_plays_identically_and_logs_damage():
    """0.5 BATTLE: both nonces in -> the precomputed race builds and each
    round logs plain damage (move names left with the pick-a-move engine)."""
    import hashlib
    from tuipet import lobbyscreen as lmod
    s = LobbyState()
    pan = _panel(s)
    pan.partner = (9, "kai")
    pan.phase, pan.bphase, pan.is_host = "battle", "card", True
    pan.bt_nonce = 7
    pan.bt_my_card = lmod._clamp_card({"num": 100, "stage": "Champion", "proto": 3})
    pan._battle_begin({"num": 4, "name": "X", "stage": "Champion", "proto": 3},
                      commit=hashlib.sha256(b"9").hexdigest())
    pan.bt_peer_nonce = 9
    pan._maybe_build()
    assert pan.battle is not None and pan.bphase == "fight"
    assert "dmg" in pan.bt_log


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
    pan.client.pm = lambda to, tx, nm=None: sent.append((to, tx, nm))
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
    assert sent == [(2, "yo", "mika")] and pan.pm_to is None        # sent + compose closed


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
    pan.client.pm = lambda to, tx, nm=None: sent.append((to, tx, nm))
    pan.key("enter")                        # open mika's action menu
    pan.key("v")                            # open the DM thread
    assert pan.phase == "dm" and pan.dm_peer == (2, "mika")
    assert "mika" not in s.unread           # opening clears unread
    for ch in "hi":
        pan.key(ch)
    pan.key("enter")
    assert sent == [(2, "hi", "mika")]       # typed line sent as a PM (name for offline queue)
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


# (test_jogress_ships_and_catches_the_partners_sickness left with the sickness system -- BASIC VPET 2026-07-17)


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


def test_the_engine_reads_species_truth_not_wire_claims():
    """0.5 BATTLE (2026-07-17): the race's foe Side is built from the
    SPECIES RECORD of the claimed num (Side.wild) -- a forged attribute
    string on the dict never reaches the hit formula, the same anti-forge
    line _clamp_card draws for PvP cards."""
    from tuipet import battle as battle_mod
    from tuipet.pet import Pet
    from tuipet import data
    q = Pet(num=102, name="Q", stage="Champion", attribute="Virus")
    q.world_seconds = 600.0
    rec = data.record_for(100)
    b = battle_mod.Battle(q, {"num": 100, "name": "X", "stage": "Champion",
                              "attribute": "FORGED"})
    assert b.foe.attribute == rec["attribute"]     # species truth
    card = battle_mod.battle_card(q)
    assert card["attribute"] == "Virus" and card["proto"] == 3
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
    # a proto-less card is a version mismatch in the 0.5 world: bout voided
    assert pan.bphase == "over" and "version" in pan.bt_outcome
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
    amap = {b[0]: b[1] for b in TuiPetApp.BINDINGS}
    # no battle/jogress ACTION on the home screen (the real invariant); the old
    # battle key "b" is now the bug reporter, and "j" (jogress) stays retired
    assert not hasattr(TuiPetApp, "action_battle")
    assert not hasattr(TuiPetApp, "action_jogress")
    assert "j" not in keys
    assert amap.get("b") == "bug"                                # never battle
    assert "l" in keys and "r" in keys and "u" in keys      # lobby, raid, cup


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


# ---- the folding player box + persistent DM threads (Joel 2026-07-10) -------

def _room(n=3):
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True}]
    for i in range(2, n + 2):
        s.roster.append({"id": i, "name": f"p{i}", "pet": {}, "live": True})
    return s


def test_right_folds_the_player_box_and_chat_widens():
    s = _room()
    s.chat.append(("p2", "x" * 30))              # wraps in the 25-col pane
    pan = _panel(s)
    assert "│" in pan.text().plain               # the divider = the box is up
    assert "x" * 30 not in pan.text().plain      # long line wrapped
    pan.key("right")                             # fold
    txt = pan.text().plain
    assert "│" not in txt                        # box (and divider) gone
    assert "x" * 30 in txt                       # chat re-wraps at full width
    assert ">p2" not in txt                      # no roster cursor row
    pan.key("left")                              # bring it back
    txt = pan.text().plain
    assert "│" in txt and ">p2" in txt


def test_folded_arrows_scroll_the_chat():
    s = _room()
    for i in range(20):
        s.chat.append(("p2", f"line {i}"))
    pan = _panel(s)
    pan.key("down")
    assert pan.sel == 1 and pan.scroll == 0      # box up: arrows pick players
    pan.key("right")                             # fold
    pan.key("up"); pan.key("up")
    assert pan.scroll == 2                       # folded: arrows scroll the log
    assert "▲2 back" in pan.text().plain
    assert "line 19" not in pan.text().plain     # the live tail scrolled away
    pan.key("down")
    assert pan.scroll == 1
    assert pan.sel == 1                          # the roster pick held its place
    pan.key("escape")
    assert pan.scroll == 0                       # Esc still snaps back to live
    pan.key("enter")
    assert pan.action_for is None                # no acting on an unseen pick
    pan.key("left")                              # box back up
    pan.key("down")
    assert pan.sel == 2                          # arrows drive the roster again


def test_folded_lines_never_overflow_the_box():
    s = _room()
    s.chat.append(("p2", "y" * 120))
    pan = _panel(s)
    pan.key("right")
    w = lobbyscreen.CHATW + lobbyscreen.ROSTW + 1
    for ln in pan.text().plain.split("\n"):
        assert len(ln) <= w, repr(ln)


def test_dm_threads_survive_leaving_the_pm_and_the_lobby():
    """Joel 2026-07-10: messages STAY after leaving a PM -- the thread and its
    unread badges persist on Esc (thread + lobby) and reload on reconnect."""
    from tuipet import persistence
    s = _room(1)
    s.roster[1]["name"] = "mika"
    s.dms["mika"] = [("mika", "hey"), ("joel", "yo")]
    s.unread.add("mika")
    pan = _panel(s)
    pan.key("enter"); pan.key("v")               # open the thread (reads it)
    pan.key("escape")                            # leave the PM -> saved
    dms, unread = persistence.get_dms()
    assert dms["mika"] == [("mika", "hey"), ("joel", "yo")]
    assert "mika" not in unread                  # read badge stuck
    s.dms["mika"].append(("mika", "one more"))
    s.unread.add("mika")
    pan.key("escape")                            # leave the LOBBY -> saved too
    dms, unread = persistence.get_dms()
    assert dms["mika"][-1] == ("mika", "one more") and "mika" in unread
    # a fresh session's connect path reloads the conversation
    s2 = _room(1)
    pan2 = _panel(s2)
    assert s2.dms["mika"][-1] == ("mika", "one more")
    assert "mika" in s2.unread


# ---- grammar sweep 2026-07-18 -----------------------------------------------

def test_dm_thread_scrolls_like_the_lobby_log():
    """'thread saved' is READABLE now: ↑↓/PgUp page the DM history, clamped
    at the head; sending or a first ESC snaps live, a second ESC leaves."""
    s = LobbyState()
    s.connected = True
    s.me_name = "joel"
    pan = _panel(s)
    pan.phase, pan.dm_peer = "dm", (2, "kai")
    s.dms["kai"] = [("kai", f"line {i}") for i in range(30)]
    tail = pan.text().plain
    assert "line 29" in tail and "line 5" not in tail
    pan.key("pageup")
    assert "line 29" not in pan.text().plain            # older window
    for _ in range(20):
        pan.key("pageup")
    assert "line 0" in pan.text().plain                 # clamped at the head
    assert "PgUp" in pan.strip()                        # overflow advertises the log keys
    pan.key("enter")                                    # (empty) send snaps live
    assert pan.dm_scroll == 0
    pan.key("pageup")
    pan.key("escape")                                   # first ESC: snap live
    assert pan.phase == "dm" and pan.dm_scroll == 0
    pan.key("escape")                                   # second ESC: to the lobby
    assert pan.phase == "lobby"


def test_ladder_lost_its_secret_q_g_closes():
    s = LobbyState()
    s.connected = True
    pan = _panel(s)
    pan.phase = "ladder"
    pan.key("q")
    pan.key("g")
    assert pan.phase == "ladder"                        # letters do nothing here
    pan.key("tab")
    assert pan.phase == "lobby"


def test_login_strip_says_out_not_back():
    """ESC at login leaves the lobby entirely — the strip speaks the app's
    leave-to-home word."""
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    pan = lobbyscreen.LobbyPanel(p, lambda name, pw, card: None)
    assert pan.phase == "login"
    assert "out" in pan.strip() and "back" not in pan.strip()


def test_pm_flush_keeps_undelivered_mail(tmp_path, monkeypatch):
    """Deliver-then-delete (server audit 2026-07-18): a socket dying
    mid-flush keeps the unsent PMs queued instead of persisting the loss."""
    import asyncio
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server as srv
    monkeypatch.setattr(srv, "PENDING_PATH", str(tmp_path / "pending.json"))
    srv.PENDING.clear()
    srv.PENDING["kai"] = [{"from_name": "joel", "text": f"m{i}", "ts": ""}
                         for i in range(5)]

    class _WS:
        def __init__(self, fail_after):
            self.sent, self.fail_after = 0, fail_after
        async def send(self, raw):
            if self.sent >= self.fail_after:
                raise RuntimeError("socket died")
            self.sent += 1

    class _Cl:
        name = "kai"
        def __init__(self, ws):
            self.ws = ws

    asyncio.run(srv._flush_pending(_Cl(_WS(2)), "kai"))     # dies after 2 sends
    assert [r["text"] for r in srv.PENDING["kai"]] == ["m2", "m3", "m4"]
    asyncio.run(srv._flush_pending(_Cl(_WS(99)), "kai"))    # healthy retry drains
    assert "kai" not in srv.PENDING


# ---- round 30 pins (lobby screen tidy, 2026-07-19) --------------------------

def test_ladder_page_holds_12_rows_with_a_full_board():
    """A full top-8 board ran the page to 14 rows and the LCD clipped the
    "you: rank" and "season resets" lines -- the page's whole point."""
    s = LobbyState()
    pan = _panel(s)
    pan.client.ladder = {"season": "2026-07",
                         "top": [[f"tamer{i}", 20 - i] for i in range(8)],
                         "you": [5, 12], "days_left": 13}
    pan.phase = "ladder"
    plain = pan.text().plain
    rows = plain.rstrip("\n").split("\n")
    assert len(rows) <= 12
    assert any("you: rank 5" in r for r in rows)
    assert any("season resets in 13 days" in r for r in rows)


def test_ladder_claim_notes_only_on_the_ack():
    """Take-then-send closed: the persistent claimed-note waits for the
    ladder_reward ack -- a claim lost to a dropped socket must leave the
    award claimable next session (the server still owes it)."""
    from tuipet import persistence
    s = LobbyState()
    pan = _panel(s)
    sent = []
    pan.client.ladder = {"award": {"season": "2026-07"}}
    pan.client.ladder_claim = lambda season: sent.append(season)
    pan.client.ladder_reward = None
    pan.anim()
    assert sent == ["2026-07"]                     # the ask went out...
    assert not persistence.ladder_award_claimed("2026-07")   # ...unnoted: retry-safe
    pan.anim()
    assert sent == ["2026-07"]                     # session guard: asked once
    pan.client.ladder_reward = {"ok": True, "season": "2026-07",
                                "rank": 1, "bits": 500}
    bits0 = pan.pet.bits
    pan.anim()
    assert pan.pet.bits == bits0 + 500             # the ack pays...
    assert persistence.ladder_award_claimed("2026-07")       # ...and NOW it notes


def test_reading_the_open_dm_thread_clears_its_badge():
    """net.py badges every incoming PM blind -- watching the message arrive
    in the open thread must count as reading it."""
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    pan = _panel(s)
    pan.phase, pan.dm_peer = "dm", (2, "mika")
    s.unread.add("mika")                           # the PM just landed
    pan.anim()
    assert "mika" not in s.unread


def test_the_dead_gate_does_not_teach_the_n_key():
    """The lobby has no N-for-egg -- N types into chat.  The home screens
    teach that key; the gate message stops pretending otherwise."""
    s = LobbyState()
    pan = _panel(s)
    pan.pet.dead = True
    msg = pan._session_gate("battle")
    assert "rests" in msg and "N" not in msg


def test_the_action_strip_mirrors_the_blocked_state_and_names_m():
    from tuipet.app import _hud_plain
    s = LobbyState()
    s.connected = True
    pan = _panel(s)
    pan.action_for = (2, "mika", True)
    live = pan.strip()
    assert "M" in live and "PM" in live            # the hidden key, surfaced
    assert len(_hud_plain(live)) <= 40
    s.blocked.add("mika")
    blocked = pan.strip()
    assert "unblock" in blocked and "battle" not in blocked
    pan.action_for = (3, "ghost", False)
    ghost = pan.strip()
    assert "ping" in ghost and "PM" in ghost
    assert len(_hud_plain(ghost)) <= 40


def test_the_dm_page_keeps_keys_on_the_strip_only():
    """The in-LCD 'ENTER send · ESC back' footer duplicated the strip; its
    row belongs to the thread history now (one hint surface per family)."""
    s = LobbyState()
    s.me_name = "joel"
    pan = _panel(s)
    pan.phase, pan.dm_peer = "dm", (2, "mika")
    plain = pan.text().plain
    assert "ENTER send" not in plain               # keys live on the strip...
    assert "ENTER" in pan.strip()                  # ...which still has them
    rows = plain.rstrip("\n").split("\n")
    assert len(rows) <= 12
