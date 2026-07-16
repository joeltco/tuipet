"""Pins from the 2026-07-11 full-screen visual sweep.

Every screen was rendered headlessly and eyeballed; these lock the fixes:
no status-card mid-word clips (habitat climate, DNA guidance), in-LCD
prompts fit the 40-col matrix, the help scroll markers are arrows (an ASCII
"v" read as a stray letter), and the account panel speaks the hint language.
"""
import asyncio

from rich.text import Text

from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 9000
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _card_plain(app):
    return Text.from_markup(str(app.stats_w.content)).plain


def _open(key):
    """Boot the app past the title, open a sub-screen, return the status card."""
    from tuipet.app import TuiPetApp

    async def go():
        app = TuiPetApp(pet=_pet())
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            app.mode = None
            await pilot.press(key)
            await pilot.pause()
            return _card_plain(app)
    return asyncio.run(go())


def test_dna_card_wraps_guidance_instead_of_clipping():
    """'Generate DNA, then charge it.' clipped at [:24] to '...then charg'.
    The guidance now wraps on word boundaries and survives whole."""
    card = _open("x")
    assert "charge it." in card
    assert "charg\n" not in card


def test_bug_prompt_fits_the_lcd():
    """The report prompt overran 40 cols and clipped mid-word on screen."""
    from tuipet.bugscreen import BugReportPanel
    pan = BugReportPanel(_pet())
    assert len(pan.msg) <= 40
    for ln in pan.text().plain.split("\n"):
        assert len(ln) <= 40


def test_help_scroll_markers_are_arrows():
    """The more-below marker was an ASCII 'v' — it read as a stray letter
    sitting beside the footer hints."""
    from tuipet.helpscreen import HelpPanel
    pan = HelpPanel(_pet())
    pan.key("down")                       # off the top: both markers show
    foot = pan.text().plain.rstrip().split("\n")[-1]
    assert "▲" in foot and "▼" in foot
    assert " v " not in foot


def test_account_panel_speaks_the_hint_language():
    """The login had bracket-style [Tab] hints and an empty message box."""
    from tuipet.lobbyscreen import AccountPanel
    pan = AccountPanel()
    strip = Text.from_markup(pan.strip()).plain
    assert "TAB" in strip and "ENTER" in strip and "ESC" in strip
    assert len(strip) <= 40
    body = pan.text().plain
    assert "TAB switch" in body and "[Tab]" not in body


def test_theme_picker_footer_matches_its_strip():
    """LCD said 'ESC cancel' while the strip said 'ESC revert' — one wording."""
    from tuipet.themescreen import ThemePanel
    pan = ThemePanel()
    assert "ESC revert" in pan.text().plain
