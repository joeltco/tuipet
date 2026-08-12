"""THE VARIATION-SELECTOR LAW (Joel 2026-08-12, "the heart emoji is breaking
the hud").

U+FE0F asks for emoji presentation, and it is the one width question rich and
terminals answer differently: rich counts '❤️' as TWO cells, the GPD over ssh
draws it as ONE.  Every cell budget downstream comes from rich's number, so one
heart in a lobby line pulled the message box's right edge in by a column.

GoingUnder's "Thanks buddy. I'll get to work right away ❤️" (2026-08-12 07:38Z)
was the first real emoji the lobby ever carried, and is the fixture below.
"""
import json

import pytest
from rich.cells import cell_len

from tuipet import net
from tuipet.net import LobbyClient, SyncClient

VS16 = chr(0xFE0F)
REAL = "Thanks buddy. I'll get to work right away ❤" + VS16   # as sent


def _frame(**kw):
    return json.dumps(kw)


# ---- the law --------------------------------------------------------------

def test_a_remote_heart_loses_the_selector_terminals_disagree_about():
    m, t = net.parse_msg(_frame(t="chat", from_name="GoingUnder", text=REAL))
    assert t == "chat"
    assert VS16 not in m["text"]
    assert cell_len(m["text"]) == cell_len(REAL) - 1     # the reclaimed column


def test_the_heart_itself_still_renders():
    """Normalising must not eat the glyph -- only its presentation request."""
    m, _ = net.parse_msg(_frame(t="chat", from_name="x", text=REAL))
    assert "❤" in m["text"]
    assert m["text"].startswith("Thanks buddy.")
    assert m["text"].endswith("❤")


@pytest.mark.parametrize("ch", ["\U0001F4E2", "\U0001F389", "\U0001F525"])
def test_emoji_that_carry_no_selector_are_left_alone(ch):
    """📢 / 🎉 / 🔥 are unambiguously two cells everywhere -- nothing to fix,
    so nothing is touched."""
    m, _ = net.parse_msg(_frame(t="chat", from_name="x", text=f"{ch} hi"))
    assert m["text"] == f"{ch} hi"
    assert cell_len(m["text"]) == 2 + 3


def test_a_sender_name_is_normalised_too():
    m, _ = net.parse_msg(_frame(t="chat", from_name="Roxi❤" + VS16, text="hi"))
    assert VS16 not in m["from_name"]


def test_a_roster_of_names_is_normalised():
    """Nested lists reach the roster column, which has its own cell budget."""
    m, _ = net.parse_msg(_frame(
        t="roster", players=[{"id": 1, "name": "Roxi❤" + VS16, "pet": "Gato"}]))
    assert VS16 not in m["players"][0]["name"]


def test_a_save_payload_is_never_normalised():
    """The one carve-out: a save is player DATA in transit.  Normalising a pet
    name inside a pulled cloud save would push the CHANGED name back up."""
    m, _ = net.parse_msg(_frame(
        t="welcome", save={"name": "Agu" + VS16, "stage": "Rookie"}, text="hi" + VS16))
    assert m["save"]["name"] == "Agu" + VS16          # untouched
    assert VS16 not in m["text"]                      # display text still normalised


# ---- the trap the parse-time placement exists to avoid ---------------------

def test_a_replayed_heart_line_is_still_recognised_as_a_duplicate():
    """_replayed dedups reconnect backlog by comparing a frame's text against
    what the pane already holds.  Normalising per-append instead of at parse
    would leave the two in different forms, and every heart line would
    reappear on every reconnect."""
    c = LobbyClient("ws://x/", "joel")
    c._handle(_frame(t="welcome", id=1, name="joel"))
    c._handle(_frame(t="chat", from_name="GoingUnder", text=REAL))
    assert len(c.state.chat) == 1
    c._handle(_frame(t="chat", from_name="GoingUnder", text=REAL, replay=True))
    assert len(c.state.chat) == 1                     # not printed twice


# ---- end to end, both surfaces --------------------------------------------

def test_the_lobby_pane_holds_a_normalised_line():
    c = LobbyClient("ws://x/", "joel")
    c._handle(_frame(t="welcome", id=1, name="joel"))
    c._handle(_frame(t="chat", from_name="GoingUnder", text=REAL))
    _nm, text = c.state.chat[-1]
    assert VS16 not in text


def test_the_home_screen_flash_gets_a_normalised_pm():
    """The ✉ flash is the HUD sink Joel actually saw break."""
    c = SyncClient("ws://x/", "joel")
    c._handle(_frame(t="pm", from_name="GoingUnder", text=REAL))
    _nm, text = c.inbox[-1]
    assert VS16 not in text


def test_the_hud_flash_of_a_remote_heart_measures_what_it_draws():
    """The whole point: the width the HUD budgets is the width the terminal
    draws.  Pinned as the CONCRETE cell count -- the same flash built from the
    raw wire text measures one column more, and that column is the bug."""
    from tuipet.app import _hud_plain
    c = SyncClient("ws://x/", "joel")
    c._handle(_frame(t="pm", from_name="GoingUnder", text=REAL))
    nm, text = c.inbox[-1]

    got = cell_len(_hud_plain(f"✉ [b]{nm}[/]: {text}"))
    raw = cell_len(_hud_plain(f"✉ [b]GoingUnder[/]: {REAL}"))   # un-normalised
    assert got == raw - 1
    assert got == 57                                            # ✉ + name + ': ' + body


# ---- the divergence found next door ---------------------------------------

def test_the_dm_composer_never_overruns_its_column():
    """lobbychat's module header says EVERY width decision goes through
    cell_len/set_cell_size/chop_cells.  The DM composer was the one input left
    measuring characters, and the overrun rides in on the PEER'S NAME: the
    prompt is built from `peer[:8]`, so eight wide glyphs are 8 characters but
    16 cells, and the field budgeted after them ran 8 columns past the box.

    Reachable by anyone: the server's _clean() strips newlines and truncates to
    24 CHARACTERS, with no character-class restriction at all."""
    from tuipet import lobbyscreen
    from tuipet.net import LobbyState
    from tuipet.pet import Pet

    peer = "\U0001F525" * 8            # 8 characters, 16 cells
    st = LobbyState()
    st.connected = True
    st.me_id, st.me_name = 1, "joel"
    st.roster = [{"id": 1, "name": "joel", "live": True},
                 {"id": 2, "name": peer, "live": True}]
    st.dms = {peer: [(peer, REAL)]}

    class _Stub:
        def __init__(self, state): self.state = state
        def respond(self, *a, **k): pass
        def relay(self, *a, **k): pass
        def update_pet(self, *a, **k): pass

    pan = lobbyscreen.LobbyPanel(Pet(num=100, stage="Champion"),
                                 lambda n, pw, c: _Stub(st), name="joel", pw="x")
    pan.phase = "dm"
    pan.dm_peer = (2, peer)
    pan.buf = "typing a reply"
    w = lobbyscreen.CHATW + lobbyscreen.ROSTW + 1     # the DM view's own width
    for line in pan._text_dm().plain.split("\n"):
        assert cell_len(line) <= w, f"{cell_len(line)} cells overran the {w}-cell box"
