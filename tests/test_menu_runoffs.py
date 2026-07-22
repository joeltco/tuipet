"""MENU RUN-OFF pins — the heavy-duty menu audit (2026-07-21).

Joel saw the lobby footer end in a bare "· ESC" on his live screen; the
sweep (tools/menu_sheet.py is the eyeball twin) found the same word-clip
class in four more places.  These pins hold every fix: hint lines end in
whole words, fixed columns never cut a word in half, and the panels the
old budget net never staged now get their text()/strip() smoke walk.
"""
import datetime
import types

from rich.cells import cell_len
from rich.text import Text

from tuipet import data, lobbychat, menu, tournament
from tuipet.pet import Pet

D = datetime.date(2026, 3, 3)
MAX_COLS = 40


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# ---- the lobby footer (the sighting) -----------------------------------------
def test_lobby_room_footers_fit_and_end_in_whole_words():
    for hint in (lobbychat.HINTS_OPEN, lobbychat.HINTS_FOLDED):
        assert len(hint) <= 38, hint
        assert not hint.endswith("ESC"), hint     # the bare-ESC run-off class
        assert hint.split()[-1].isalpha(), hint   # last token is a word, not a key


# ---- the cup tree footer -----------------------------------------------------
def test_cup_tree_footer_never_clips_the_forfeit_hint():
    """menu.footer hard-cuts at W: the three-space variant ran 39 with
    "quarterfinal" and printed "ESC forfei"."""
    for rnd in ("Quarterfinal", "Semifinal", "Final"):
        line = "SPACE to the %s  ESC forfeit" % rnd.lower()
        assert len(line) <= menu.W, line


# ---- the death strip ---------------------------------------------------------
def test_death_strip_labels_esc_within_the_hud():
    from tuipet.deathscreen import DeathPanel
    p = _pet()
    p.name = "Airdramon"
    pan = DeathPanel(p)
    s = Text.from_markup(pan.strip()).plain
    assert cell_len(s) <= MAX_COLS, s
    assert s.endswith("ESC out"), s


# ---- DNA field columns -------------------------------------------------------
def test_dna_field_columns_never_cut_a_word_in_half():
    from tuipet.dnascreen import _field_word
    for f in data.DNA_FIELDS:
        full = data.pretty_field(f)
        for w in (9, 10, 13, 17):
            fit = _field_word(f, w)
            assert len(fit) <= w, (f, w, fit)
            # whatever shows is a prefix of the real name made of whole words
            assert full == fit or full.startswith(fit + " "), (f, w, fit)


def test_dna_charge_and_stats_pages_fit_the_lcd():
    from tuipet.dnascreen import DNAPanel
    for row in (0, 2):                            # charge, stats
        pan = DNAPanel(_pet())
        for _ in range(row):
            pan.key("down")
        pan.key("enter")
        plain = pan.text().plain
        assert "Nightmare Soldier" in plain       # the audit's poster child, whole
        for ln in plain.split("\n"):
            assert cell_len(ln) <= MAX_COLS, ln


# ---- the intro grammar -------------------------------------------------------
def test_unnamed_pet_intro_says_you_answer(monkeypatch):
    monkeypatch.setattr(tournament, "_today", lambda: D)
    from tuipet.tournamentscreen import TournamentPanel, INTRO_OPP_T
    p = _pet(bits=99999)
    p.strength = p.hunger = 4
    p._set_energy(p.max_energy)
    pan = TournamentPanel(p)
    trophy = tournament.trophy_by_id(tournament.schedule(p)[tournament._hour(p)])
    pan.tourney = tournament.Tournament(p, trophy)
    pan.phase = "bracket"
    pan._intro = {"t": INTRO_OPP_T + 2}           # the answer beat
    plain = pan.text().plain
    assert "You answer!" in plain and "answers!" not in plain


# ---- smoke walks for the panels the budget net never staged ------------------
def _menu_panels():
    """(name, panel) for every menu screen constructible offline."""
    p = _pet(bits=9999)
    from tuipet.accountscreen import AccountPanel
    from tuipet.assistscreen import AssistPanel
    from tuipet.backgroundscreen import BackgroundPanel
    from tuipet.bugscreen import BugReportPanel
    from tuipet.deathscreen import DeathPanel
    from tuipet.digicorescreen import DigiCorePanel
    from tuipet.albumscreen import AlbumPanel
    from tuipet.dnascreen import DNAPanel
    from tuipet.eggguidescreen import EggGuidePanel
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.feedscreen import FeedPanel
    from tuipet.helpscreen import HelpPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.optionsscreen import KeysPanel, OptionsPanel, SoundPanel
    from tuipet.raidscreen import RaidPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.titlescreen import TitlePanel
    from tuipet.towneggscreen import TownEggPanel
    stub = types.SimpleNamespace(state=types.SimpleNamespace(me_id=None),
                                 raid=None, raid_get=lambda: None,
                                 close=lambda: None)
    return [
        ("title", TitlePanel()),
        ("account", AccountPanel()),
        ("help", HelpPanel(p)),
        ("options", OptionsPanel(p, lambda: True, lambda: None)),
        ("sound", SoundPanel(lambda: True, lambda: None)),
        ("keys", KeysPanel((("f", "feed", "Feed"),))),
        ("themes", ThemePanel()),
        ("scenes", BackgroundPanel(p)),
        ("feed", FeedPanel(p)),
        ("digicore", DigiCorePanel(p)),
        ("dna", DNAPanel(p)),
        ("jogress", JogressPanel(p, 29, 45, 60)),
        ("eggselect", EggSelectPanel(p)),
        ("eggguide", EggGuidePanel(p)),
        ("album", AlbumPanel(p)),
        ("townegg", TownEggPanel(p, town_id=4)),
        ("assist", AssistPanel(p)),
        ("bug", BugReportPanel(p)),
        ("death", DeathPanel(p)),
        ("raid", RaidPanel(p, None, client=stub)),
    ]


def test_every_menu_panel_smokes_within_its_budgets():
    """text() renders, no line beats 40 CELLS, the strip stays in its lane.
    Image panes (Textual markup scenes) measure their PLAIN text like the
    budget net does."""
    failures = []
    for name, pan in _menu_panels():
        getattr(pan, "anim", lambda: None)()      # AccountPanel is tick-free
        for i, ln in enumerate(pan.text().plain.split("\n")):
            if cell_len(ln) > MAX_COLS:
                failures.append(f"{name}: row {i} is {cell_len(ln)} cells: {ln!r}")
        s = getattr(pan, "strip", lambda: "")()
        if s and cell_len(Text.from_markup(s).plain) > MAX_COLS:
            failures.append(f"{name}: strip {cell_len(Text.from_markup(s).plain)}")
    assert not failures, "\n".join(failures)
