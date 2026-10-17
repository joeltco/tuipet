"""Approved UI report items 6–15; presentation budgets and live data survive."""
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.console import Console
from rich.style import Style
from rich.text import Text

from tuipet import menu, statusbox, theme
from tuipet.accountscreen import AccountPanel, CloudWaitPanel
from tuipet.albumscreen import AlbumPanel
from tuipet.app import TuiPetApp
from tuipet.dnascreen import DNAPanel, MASH_TICKS
from tuipet.eggguidescreen import EggGuidePanel
from tuipet.helpscreen import HelpPanel
from tuipet.optionsscreen import OptionsPanel, SoundPanel
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel


def pet():
    return Pet(num=29, name="Agumon", stage="Rookie", bits=9000,
               obedience=500, energy=100)


def fits(text, height=12, width=40):
    rows = text.plain.splitlines()
    assert len(rows) <= height
    assert max(map(cell_len, rows), default=0) <= width


def card(panel):
    output = []
    app = SimpleNamespace(pet=panel.pet, mode=panel,
                          stats_w=SimpleNamespace(update=output.append))
    statusbox.dna(app)
    return Text.from_markup(output[-1])


@pytest.mark.parametrize("phase", ["home", "charge", "stats", "roads", "road_detail", "bet", "result"])
def test_06_dna_data_headers_anchor_at_row_one(phase):
    panel = DNAPanel(pet())
    panel.phase = phase
    panel.won = ("DeepSaver", 1, 10, 1, 0)
    if phase == "road_detail":
        panel.road_i = 0
    text = panel.text()
    fits(text)
    assert text.plain.splitlines()[1] == "─" * menu.W
    assert TuiPetApp._center(None, text) is text


def test_06_activity_retains_all_scene_rows():
    panel = DNAPanel(pet())
    panel.phase = "mash"
    fits(panel.text())
    assert len(panel.text().plain.splitlines()) == 12
    assert "─" * menu.W not in panel.text().plain
    assert MASH_TICKS == 100


@pytest.mark.parametrize("factory", [AlbumPanel, EggGuidePanel,
                                      lambda p: ShopPanel(p, start_tab="Food"),
                                      lambda p: OptionsPanel(p, lambda: False, lambda: None)])
def test_07_selected_lists_use_full_shared_fill(factory):
    text = factory(pet()).text()
    rows = text.split("\n")
    selected = [row for row in rows if row.plain.startswith("▸ ")]
    assert len(selected) == 1
    row = selected[0]
    assert row.cell_len == menu.W
    for at in (0, menu.W - 1):
        assert row.get_style_at_offset(Console(), at) == Style.parse(theme.SEL)


def test_07_tabs_share_fill_without_literal_brackets():
    text = menu.tabs(["Food", "Items", "Honors"], 1)
    assert "[" not in text.plain
    assert text.cell_len == menu.W
    assert text.get_style_at_offset(Console(), 1) == Style.parse(theme.DIM)
    assert text.get_style_at_offset(Console(), 7) == Style.parse(theme.SEL)


def test_08_home_keeps_rows_and_distinct_live_power_roles():
    p = pet()
    p.vaccine, p.data_power, p.virus = 120, 45, 88
    rows = statusbox.home_lines(p)
    fits(Text.from_markup("\n".join(rows)), height=16, width=26)
    battle = next(row for row in rows if "Battle" in row)
    assert "0W / 0" in Text.from_markup(battle).plain
    power = next(row for row in rows if "Power" in row)
    assert "[dim]Power   [/]" in power
    assert all(f"[b {ink}]" in power for ink in (theme.LIFE, theme.POS, theme.NEG))
    assert "V120" in power and "D45" in power and "Vi88" in power   # compact again (Joel 2026-10-17, A)


def test_09_current_total_and_independent_facts_have_separate_grammar():
    panel = DNAPanel(pet())
    panel.phase = "charge"
    assert "x0 / 1 · energy -0" in panel.text().plain
    assert Text.from_markup(menu.hints(("ENTER", "open"), ("ESC", "back"))).plain == "ENTER open · ESC back"


def test_10_help_strip_and_dna_card_controls_are_not_duplicated():
    assert HelpPanel(pet()).strip() == menu.hints(("↑↓", "scroll"), ("PgUp/Dn", "page"), ("ESC", "back"))
    panel = DNAPanel(pet())
    for phase in ("home", "charge", "stats", "roads", "bet", "mash", "result"):
        panel.phase = phase
        panel.won = ("DeepSaver", 1, 10, 1, 0)
        assert "ESC" not in card(panel).plain
        assert "SPACE" not in card(panel).plain
        assert panel.strip()


@pytest.mark.parametrize("value", ["界" * 24, "📢" * 24, "AncientMegatherimon", "[b]name[/]"])
@pytest.mark.parametrize("width", [0, 1, 2, 9, 18])
def test_11_static_names_reserve_the_end_marker_in_cells(value, width):
    result = menu.ellipsis(value, width)
    assert cell_len(result) <= width
    if width and cell_len(value) > width:
        assert result.endswith("…") and result.count("…") == 1


@pytest.mark.parametrize("phase", ["home", "charge", "stats", "roads", "road_detail", "bet", "mash", "result"])
def test_12_dna_cards_have_one_divider_and_phase_live_values(phase):
    panel = DNAPanel(pet())
    panel.phase = phase
    panel.won = ("DeepSaver", 1, 10, 1, 0)
    text = card(panel)
    fits(text, height=16, width=26)
    assert text.plain.count("─" * 26) == 1
    if phase == "charge":
        assert "Charge x" in text.plain and "energy -" in text.plain
    else:
        assert "Stops at empty energy" not in text.plain
    if phase == "result":
        assert "Refund" in text.plain and "Deep Saver" in text.plain


def test_13_short_notices_and_account_notes_finish_on_row_twelve(monkeypatch):
    from tuipet import optionsscreen
    monkeypatch.setattr(optionsscreen, "is_browser", lambda: True)
    panels = [AccountPanel(name="audit"), AccountPanel(name="audit", note="Rejected."),
              CloudWaitPanel("audit"), SoundPanel(lambda: False, lambda: None)]
    for panel in panels:
        text = panel.text()
        fits(text)
        assert len(text.plain.splitlines()) == 12
        assert text.plain.splitlines()[0].strip()
        assert text.plain.splitlines()[-1].strip()


def test_14_shell_labels_meet_contrast_floor_for_all_themes():
    from tests.test_theme_contrast import _ratio
    for palette in theme.THEMES.values():
        derived = theme._derive(palette)
        assert _ratio(derived["LABEL"], theme.SHELL_BG) >= 3
        assert derived["SHELL"] == palette["border"]
        assert derived["BEZEL"] == palette["border"]
        assert derived["KEY"] == "cyan"


def test_15_feedback_uses_roles_and_escapes_literal_brackets():
    for kwargs, style in (({}, theme.INK), ({"action": True}, theme.INK_B),
                          ({"warning": True}, theme.NEG)):
        text = Text.from_markup(menu.feedback("Literal [b] name", **kwargs))
        assert text.plain == "Literal [b] name"
        assert text.get_style_at_offset(Console(), 0) == Style.parse(style)
    panel = ShopPanel(pet())
    assert Text.from_markup(panel.strip()).get_style_at_offset(Console(), 0) == Style.parse(theme.INK)
    assert panel.msg_t == 26
    assert menu.NOTE_HOLD == 16 and menu.NOTE_STEP == 2


def test_15_feedback_survives_cue_drain_and_marquee():
    from tuipet.sfx import drain
    panel = ShopPanel(pet())
    panel._flash("Not enough bits.", warning=True)
    panel.sfx = "error"
    drain(panel)
    assert Text.from_markup(panel.strip()).get_style_at_offset(Console(), 0) == Style.parse(theme.NEG)
    assert panel.msg_t == 26
    panel.anim()
    assert panel.msg_t == 25
    output = []
    fake = SimpleNamespace(msg_w=SimpleNamespace(update=output.append),
                           _hud_text=None, _hud_scroll=None)
    TuiPetApp._hud(fake, menu.feedback("[b] " + "warning " * 12, warning=True))
    assert output[-1].plain.startswith("[b] warning")
    first_style = output[-1].get_style_at_offset(Console(), 0)
    assert first_style.bgcolor is None
    assert first_style.color.triplet.hex == theme.shell_colors(theme.THEMES[theme.current()])["neg"]
    initial_hold = fake._hud_hold
    for _ in range(initial_hold * 2 + 4):
        TuiPetApp._hud_marquee(fake)
    assert output[-1].get_style_at_offset(Console(), 0) == first_style


def test_07_last_selected_row_keeps_fill_when_bottom_note_is_anchored():
    panel = DNAPanel(pet())
    panel.home_i = 3
    text = panel.text()
    row = next(row for row in text.split("\n") if row.plain.startswith("▸ "))
    assert row.cell_len == 38
    assert row.get_style_at_offset(Console(), 37) == Style.parse(theme.SEL)


def test_08_digicore_power_amounts_align_and_keep_semantic_roles():
    from tuipet.digicorescreen import _data_lines
    rows = _data_lines([("Vaccine", "120"), ("Data", "45"), ("Virus", "88")])
    for row, ink in zip(rows, (theme.LIFE, theme.POS, theme.NEG)):
        assert row.cell_len == 38
        assert row.get_style_at_offset(Console(), 37).color == Style.parse(ink).color
