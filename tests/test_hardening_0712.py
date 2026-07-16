"""Regression guards for the 2026-07-12 hardening + polish pass.

Crash-hardening:
  C1  a full / read-only / quota'd disk must not crash a save (best-effort I/O)
  C2  a lobby invite frame missing `from_name` must not KeyError
  C3  the lobby send loop must requeue, not drop, the frame it already dequeued
Coverage gap:
  the get_dms/save_dms corrupt-entry + pruning + tail-trim contract
Polish:
  P1  the Options Keys page shows glyphs (?/Enter), not Textual key ids
  P2  the home help line drops the lobby-only jogress
  P3  the battle surrender strip matches its in-LCD footer wording
"""
import asyncio

from tuipet import persistence
from tuipet.net import LobbyState, LobbyClient
from tuipet.pet import Pet
from tuipet import lobbyscreen


# --- shared minimal lobby panel (mirrors tests/test_lobby.py::_panel) --------
class _StubClient:
    def __init__(self, state):
        self.state = state
    def respond(self, *a, **k): pass
    def relay(self, *a, **k): pass
    def update_pet(self, *a, **k): pass


def _panel(state):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    return lobbyscreen.LobbyPanel(p, lambda name, pw, card: _StubClient(state),
                                  name="joel", pw="x")


# --- C1: disk errors are swallowed, real bugs still surface ------------------
def test_atomic_write_survives_a_disk_error(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("No space left on device")
    monkeypatch.setattr(persistence.os, "makedirs", boom)
    # must NOT propagate out of the (timer-driven) caller
    persistence._atomic_write_json(str(tmp_path / "save.json"), {"x": 1})


def test_atomic_write_still_raises_on_a_real_bug(tmp_path):
    # a non-serializable payload is a programming bug, not a disk fault --
    # only OSError is best-effort; this must still surface
    import pytest
    with pytest.raises(TypeError):
        persistence._atomic_write_json(str(tmp_path / "s.json"), {"bad": {1, 2}})


# --- C2: a from_name-less invite frame must not crash the drain --------------
def test_invite_resp_without_from_name_does_not_crash():
    s = LobbyState()
    pan = _panel(s)
    # a relayed / malformed busy-decline with no from_name (protocol drift)
    s.inbox.append({"t": "invite_resp", "from_id": 9, "kind": "battle", "busy": True})
    pan.anim()                                       # drains the inbox
    assert "busy" in pan.status and "?" in pan.status  # rendered via the fallback


# --- C3: a failed send requeues the dequeued frame instead of losing it ------
def test_send_loop_requeues_a_dropped_frame():
    async def go():
        c = LobbyClient("ws://x", "joel")

        class DeadWS:
            async def send(self, *a):
                raise RuntimeError("socket closed")

        c._ws = DeadWS()
        c._q.put_nowait({"t": "move", "n": 1})
        await c._send_loop()                         # dequeue -> send fails -> requeue
        return c._q

    q = asyncio.run(go())
    assert q.qsize() == 1
    assert q.get_nowait() == {"t": "move", "n": 1}


# --- coverage: get_dms/save_dms corrupt-entry + pruning + tail contract ------
def test_get_dms_filters_corrupt_entries():
    persistence.save_settings({
        "dms": {"a": [["a", "hi"], ["x"], "nope", ["b", "yo", "extra"]]},
        "dm_unread": ["a"],
    })
    dms, unread = persistence.get_dms()
    # 1-element + non-list dropped; a >=2 entry is truncated to a 2-tuple
    assert dms["a"] == [("a", "hi"), ("b", "yo")]
    assert unread == {"a"}


def test_save_dms_prunes_empty_threads_and_orphan_unread():
    persistence.save_dms({"a": [("a", "hi")], "b": []}, unread={"a", "b", "ghost"})
    dms, unread = persistence.get_dms()
    assert set(dms) == {"a"}          # the empty thread is dropped
    assert unread == {"a"}            # unread badges for absent threads pruned


def test_save_dms_trims_to_the_persisted_tail():
    long = [("a", str(i)) for i in range(60)]
    persistence.save_dms({"a": long}, unread=set())
    dms, _ = persistence.get_dms()
    assert len(dms["a"]) == persistence.DM_KEEP     # 50
    assert dms["a"][-1] == ("a", "59")              # newest survives the trim


# --- P1: the Options Keys page shows glyphs, not Textual identifiers ---------
def test_options_keys_page_shows_glyphs_not_ids():
    from tuipet import optionsscreen
    rows = optionsscreen.KeysPanel([
        ("question_mark", "help", "Help"),
        ("enter", "gift", "Accept gift"),
        ("f", "feed", "Feed"),
    ]).rows
    assert "question_mark" not in "\n".join(rows)
    assert rows[0].startswith("?")
    assert rows[1].startswith("ENTER")
    assert rows[2].startswith("f")


# --- P2: jogress is lobby-only; the home DNA line must not claim it ----------
def test_help_home_line_drops_the_lobby_only_jogress():
    from tuipet import helpscreen
    texts = [t for t, _kind in helpscreen.HELP]
    assert "x DNA   d digicore" in texts
    assert not any("jogress" in t and "DNA" in t for t in texts)


# --- P3: the surrender strip speaks the same words as its footer/note --------
def test_battle_surrender_strip_matches_its_footer_wording():
    from tuipet import battlescreen, battle
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    bp = battlescreen.BattlePanel(p, battle.pick_enemy(p))
    bp.phase = "surrender_ask"
    line = bp.strip()
    assert "allow" in line and "flee" not in line
