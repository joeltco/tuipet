"""Lobby chat polish (2026-07-14) — cell-width safety, the 📢 line, and mute.

⛔ THE CELL-WIDTH LAW.  The lobby is the ONE screen where a player types
arbitrary text, and an emoji or CJK glyph is TWO terminal cells wide while
counting as ONE character.  `s[:w].ljust(w)` and `len(s)` measure CHARACTERS, so
"🔥🔥 emoji 日本語" overflowed its 25-column budget and shoved the roster divider
`│` right off its column — the layout visibly tore.  Every width decision in
lobbyscreen now goes through cell_len / set_cell_size / chop_cells.
"""
from rich.cells import cell_len
from rich.console import Console

from tuipet import lobbyscreen
from tuipet.lobbyscreen import CHATW, _fit, _wrap
from tuipet.net import ANNOUNCE, LobbyState
from tuipet.pet import Pet
from tuipet.theme import INK, INK_B


class _Stub:
    def __init__(self, state): self.state = state
    def respond(self, *a, **k): pass
    def relay(self, *a, **k): pass
    def update_pet(self, *a, **k): pass


def _panel(state, **kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = lobbyscreen.LobbyPanel(p, lambda n, pw, c: _Stub(state), name="joel", pw="x")
    for k, v in kw.items():
        setattr(pan, k, v)
    return pan


def _state(chat=(), me="joel"):
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, me
    s.roster = [{"id": 1, "name": me, "live": True},
                {"id": 2, "name": "mika", "live": True}]
    s.chat = list(chat)
    return s


def _rendered(pan):
    con = Console(width=41, force_terminal=False, no_color=True)
    with con.capture() as cap:
        con.print(pan._text_lobby())
    return cap.get().rstrip("\n").split("\n")


# ---------------------------------------------------------------- cell width

def test_fit_measures_cells_not_characters():
    assert cell_len(_fit("🔥🔥", 10)) == 10          # 2 chars, 4 cells -> pad to 10
    assert cell_len(_fit("日本語テキスト", 8)) == 8   # 7 chars, 14 cells -> truncate to 8
    assert cell_len(_fit("ab", 5)) == 5


def test_wrap_never_exceeds_the_column_in_CELLS():
    for text in ("🔥🔥 emoji test 🐉 wide chars 日本語テキスト",
                 "日本語日本語日本語日本語日本語日本語",       # unbroken wide run
                 "plain ascii that wraps across the column nicely"):
        for line in _wrap(text, CHATW - 1):
            assert cell_len(line) <= CHATW - 1, (text, line, cell_len(line))


def test_the_roster_divider_never_tears():
    """The regression that started this: a wide glyph shoved `│` off its column."""
    s = _state([("mika", "🔥🔥 emoji test 🐉 wide chars 日本語テキスト"),
                ("mika", "ascii baseline")])
    for line in _rendered(_panel(s)):
        if "│" in line:
            col = cell_len(line.split("│")[0])
            assert col == CHATW, f"divider at cell {col}, expected {CHATW}: {line!r}"


def test_typed_emoji_cannot_overflow_the_input_line():
    """The input line scrolls as you type; a char-based tail slice let a typed
    emoji run past the frame."""
    s = _state()
    pan = _panel(s)
    pan.buf = "🔥" * 60
    for line in _rendered(pan):
        assert cell_len(line) <= 41, f"input line overflows the frame: {cell_len(line)}"


def test_the_empty_room_hint_is_not_clipped_mid_sentence():
    """It used to render as '— say hi, the room hears' — truncated with [:cw]."""
    s = _state()
    rows = [ln for ln in _rendered(_panel(s)) if "say hi" in ln]
    assert rows, "the empty room lost its hint"
    hint = rows[0].split("│")[0].strip()
    assert hint.endswith("—"), f"hint is clipped: {hint!r}"


# ---------------------------------------------------------------- the 📢 line

def test_the_announcement_is_the_loudest_line_in_the_room():
    """It used to render in plain INK as '📢: text' — indistinguishable from
    chatter, and reading like a PLAYER NAMED 📢 was talking."""
    s = _state([("mika", "hey all"), (ANNOUNCE, "v0.2.466 is out")])
    rows = _panel(s)._chat_rows()
    peer = next(r for r in rows if r[0].startswith("mika"))
    ann = next(r for r in rows if r[0].startswith(ANNOUNCE))
    assert ann[1] == INK_B, "the dev's line must stand out"
    assert peer[1] == INK, "sanity: ordinary chatter stays INK"
    assert not ann[0].startswith(f"{ANNOUNCE}:"), "no fake username colon"


# ---------------------------------------------------------------- mute

def test_blocking_sweeps_what_they_already_said():
    """net.py filters a blocked peer going FORWARD, but their existing lines sat
    on screen — so 'Blocked X.' was only half true."""
    s = _state([("mika", "spam one"), ("joel", "hi"), ("", "mika joined"),
                (ANNOUNCE, "a release")])
    s.unread.add("mika")
    pan = _panel(s)
    pan.action_for = (2, "mika", True)
    pan.key("x")

    speakers = [nm for nm, _ in s.chat]
    assert "mika" not in speakers, "the muted peer's lines are still in the log"
    assert "joel" in speakers, "muting mika must not touch anyone else"
    assert ANNOUNCE in speakers, "muting a peer must never eat the dev's line"
    assert "" in speakers, "join/leave notices are not a peer's speech"
    assert "mika" not in s.unread
    assert "mika" in s.blocked
