"""Every key a lobby hint names is PRESSED here and must do what the hint says.

The 0.6.42 empty-room line "P: ping ghosts" passed every test while P typed a
'p' into chat (Joel 2026-10-17).  Render tests check that words fit; these
check that the words are true.
"""
from rich.text import Text

from tuipet import lobbychat
from test_lobby_audit import _panel


def _pick(pan, name):
    pan.sel = [p["name"] for p in pan._others()].index(name)


def _strip(pan):
    return Text.from_markup(pan.strip()).plain


def test_open_room_footer_and_strip():
    assert lobbychat.HINTS_OPEN == "ENTER send/act · TAB ranks · ESC leave"
    pan, st = _panel()
    s = _strip(pan)
    assert "↑↓" in s and "ENTER" in s and "PgUp" in s
    pan.key("down")
    assert pan.sel == 1                       # ↑↓ pick
    pan.key("up")
    assert pan.sel == 0
    pan.key("pageup")
    assert pan.scroll > 0                     # PgUp log
    pan.key("escape")
    assert pan.scroll == 0                    # "ESC back to live"
    pan.key("enter")
    assert pan.action_for is not None         # empty ENTER acts
    pan.key("escape")
    pan.buf = "hi"
    pan.key("enter")
    assert pan.buf == ""                      # ENTER sends
    pan.key("tab")
    assert pan.phase == "ladder"              # TAB ranks
    pan.key("escape")
    assert pan.phase == "lobby"
    assert pan.key("escape") == ("done", None)  # ESC leave


def test_empty_room_hint_names_no_dead_key():
    pan, st = _panel()
    st.roster = st.roster[:1]
    st.chat = []
    plain = pan.text().plain
    assert "say hi" in plain and "P:" not in plain


def test_unread_nudge_keys_are_the_real_path():
    pan, st = _panel()
    st.unread.add("mika")
    s = _strip(pan)
    assert "unread" in s and "ENTER" in s and "V" in s
    pan.key("v")
    assert pan.phase == "lobby" and pan.buf == "v"   # V alone only types
    pan.buf = ""
    _pick(pan, "mika")
    pan.key("enter")                                  # pick + ENTER, then V
    pan.key("v")
    assert pan.phase == "dm" and pan.dm_peer[1] == "mika"


def test_live_peer_action_menu():
    pan, st = _panel()
    _pick(pan, "mika")
    pan.key("enter")
    s = _strip(pan)
    for word in ("B battle", "J jogress", "V/M PM", "X block"):
        assert word in s
    pan.key("m")
    assert pan.pm_to is not None
    assert "ENTER" in _strip(pan) and "ESC" in _strip(pan)
    pan.key("escape")
    assert pan.pm_to is None
    _pick(pan, "mika")
    pan.key("enter")
    pan.key("x")
    assert "mika" in st.blocked
    _pick(pan, "mika")
    pan.key("enter")
    assert _strip(pan).startswith("X unblock")
    pan.key("x")
    assert "mika" not in st.blocked


def test_ghost_ping_and_ladder_and_dm_keys():
    pan, st = _panel()
    st.roster[1]["live"] = False
    _pick(pan, "mika")
    pan.key("enter")
    assert "P ping" in _strip(pan)
    pan.key("p")
    assert pan.action_for is None and pan.status.startswith("Pinged")
    pan.key("tab")
    assert "TAB" in _strip(pan) and "ESC" in _strip(pan)
    pan.key("tab")
    assert pan.phase == "lobby"
    _pick(pan, "mika")
    pan.key("enter")
    pan.key("v")
    assert pan.phase == "dm" and "ESC" in _strip(pan)
    pan.buf = "yo"
    pan.key("enter")
    assert pan.buf == ""
    pan.key("escape")
    assert pan.phase == "lobby"
