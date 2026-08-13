"""⛔ THE CELL-WIDTH LAW, menu edition (2026-08-12).

menu.W is a budget in terminal CELLS, and an emoji or CJK glyph is ONE
character but TWO cells.  app.py's HUD was fixed for this in bug #32 (Joel
v0.5.264, "what is space t?") and lobbyscreen in the 2026-07-14 chat polish --
menu.py was the last surface still counting characters, and it is the one
EVERY sub-screen's header/rows/note/footer goes through.

Measured before the fix: note("📢 …") rendered 39 cells into the 38-cell box,
and header(long_title, "12/40") rendered 41.  The overflow wraps onto the
LCD's invisible second row, which is how bug #32 presented in the first place.
"""
import pytest
from rich.cells import cell_len

from tuipet import menu

LOUD = "\U0001F4E2"        # 📢 -- 1 char, 2 cells; the dev's own announce prefix
PARTY = "\U0001F389"       # 🎉
CJK = "日本語のなまえ"      # 7 chars, 14 cells

WIDE_INPUTS = [
    pytest.param(f"{LOUD} Thanks buddy. I'll get to work right away", id="loudspeaker-head"),
    pytest.param(f"Thanks buddy, see you soon {PARTY}{PARTY}", id="emoji-tail"),
    pytest.param(CJK * 4, id="cjk-run"),
    pytest.param(f"{LOUD}{PARTY}" * 12, id="all-wide"),
    pytest.param("x" * 80, id="plain-overlong"),
    pytest.param("BAG", id="short-ascii"),
]


def _lines(t):
    return [ln for ln in t.plain.split("\n") if ln]


# ---- every surface, every input -------------------------------------------

@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_note_never_overruns_the_box(s):
    for ln in _lines(menu.note(s, tick=0)):
        assert cell_len(ln) <= menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_footer_never_overruns_the_box(s):
    for ln in _lines(menu.footer(s)):
        assert cell_len(ln) <= menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_footer_note_never_overruns_the_box(s):
    for ln in _lines(menu.footer_note(s, tick=0)):
        assert cell_len(ln) <= menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_a_row_is_exactly_the_box_wide(s):
    """Rows are a FIXED field -- the selected-row inversion paints the whole
    line, so a short row must pad and a wide one must not spill."""
    for ln in _lines(menu.row(s)):
        assert cell_len(ln) == menu.W
    for ln in _lines(menu.row(s, selected=True)):
        assert cell_len(ln) == menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
@pytest.mark.parametrize("right", ["", "12/40", "9999b"])
def test_header_never_overruns_the_box(s, right):
    for ln in _lines(menu.header(s, right)):
        assert cell_len(ln) <= menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
@pytest.mark.parametrize("right", ["", "99b"])
def test_bar_never_overruns_the_box(s, right):
    for ln in _lines(menu.bar(s, right)):
        assert cell_len(ln) <= menu.W


@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_icon_info_never_overruns_its_column(s):
    from rich.text import Text
    out = Text()
    menu.icon_info(out, [" " * menu.IC_W] * menu.IC_ROWS, [s] * menu.IC_ROWS)
    for ln in _lines(out):
        assert cell_len(ln) <= menu.W


# ---- the marquee, at every offset -----------------------------------------

@pytest.mark.parametrize("s", WIDE_INPUTS)
def test_the_marquee_holds_the_box_at_every_step(s):
    """One frame over budget is one frame of torn layout -- the window has to
    be right at EVERY tick, not just the head."""
    for tick in range(0, 400):
        assert cell_len(menu._scrolled(s, tick)) <= menu.W


# ---- the right-hand field is what the header exists to protect ------------

def test_a_full_width_title_yields_to_the_right_hand_field():
    """The right field carries the count / page / cost.  The old max(1, ...)
    floor kept the whole title and pushed the pair to W + len(right) + 1."""
    t = menu.header("x" * 80, "12/40")
    line = _lines(t)[0]
    assert cell_len(line) <= menu.W
    assert line.endswith("12/40")          # the count survived the clip


def test_the_right_hand_field_survives_a_wide_title():
    line = _lines(menu.header(CJK * 6, "9999b"))[0]
    assert cell_len(line) <= menu.W
    assert line.endswith("9999b")


# ---- the ordinary case must not have moved --------------------------------

def test_plain_ascii_chrome_is_unchanged():
    """The fix is a unit correction, not a redesign: for text with no wide
    glyph, character math and cell math agree and the output is identical."""
    assert menu.row("Meat").plain == "  Meat".ljust(menu.W) + "\n"
    assert menu.row("Meat", selected=True).plain == "▸ Meat".ljust(menu.W) + "\n"
    assert menu.note("It IGNORED you!").plain == "It IGNORED you!\n"
    assert menu.footer("ESC back").plain == "ESC back"
    hdr = _lines(menu.header("BAG", "3/12"))
    assert hdr[0] == "BAG" + " " * (menu.W - 3 - 4) + "3/12"
    assert cell_len(hdr[1]) == menu.W          # the divider rule
