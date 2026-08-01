"""The STATUS box budget: #stats is physically 26x16 content (CSS 30x18
border-box).  Every painter must fit -- the status-box audit 2026-07-04 found
the DNA card 28 wide (its hint line wrapped mid-box) and raw-minutes ages
('4325m40s').  Same lesson as the LCD box-clip: pixels aren't the box."""
import re

from tuipet.pet import Pet

CARD_W, CARD_H = 26, 16


def _vis(line):
    return len(re.sub(r"\[/?[^\[\]]*\]", "", line))


from tuipet.app import Stats


class _FakeStats(Stats):
    """A Stats with the Textual plumbing stubbed out (never mounted)."""
    def __init__(self): self.txt = ""
    def update(self, t): self.txt = str(t)
    @property
    def border_subtitle(self): return ""
    @border_subtitle.setter
    def border_subtitle(self, v): pass


def _fits(fake, tag):
    lines = fake.txt.split("\n")
    assert len(lines) <= CARD_H, f"{tag}: {len(lines)} lines overflow the card"
    w = max(_vis(l) for l in lines)
    assert w <= CARD_W, f"{tag}: {w} cols overflow the card"


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.age_seconds = 3 * 86400 + 7000       # an older pet: worst-case widths
    p.bits = 99999
    p.dp = 3
    p.poop = 2
    p.sick = True
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_main_egg_and_grave_cards_fit_and_read_compact_ages():
    fake = _FakeStats()
    p = _pet()
    Stats.paint(fake, p)
    _fits(fake, "main")
    assert "3d01h" in fake.txt                  # compact age, not 4436m40s
    assert "◆◆◆" in fake.txt                    # the DP meter: pips on its own row
    assert "Care" in fake.txt                   # the evolution driver, no longer buried
    # the Va/Da/Vi Power ledger + the DMX Level now ride the home card too
    # (2026-07-24 "evaluate what we can fit"): both were live progression the
    # main card never showed.  Level folds into the Battle row.
    assert "Power" in fake.txt
    assert "Lv" in fake.txt
    assert "HP " not in fake.txt                # the classic trained-HP left with it
    Stats.paint(fake, Pet.new_egg(egg_type=1))
    _fits(fake, "egg")
    dead = _pet(dead=True)
    Stats.paint(fake, dead)
    _fits(fake, "grave")
    assert "Lived    3d01h" in fake.txt


def test_home_card_surfaces_level_and_the_attribute_powers():
    """Home-card surfacing 2026-07-24 (Joel "evaluate what we can fit"): the
    DMX Level and the Va/Da/Vi powers were live progression shown only on
    DigiCore.  Level folds into the Battle row; the powers get their own row,
    coloured by attribute.  Uncapped values (chips + wins both feed them)
    must still fit the 26-col card."""
    fake = _FakeStats()
    p = _pet()
    p.vaccine, p.data_power, p.virus = 120, 45, 88
    Stats.paint(fake, p)
    _fits(fake, "home/powers")
    assert "V120" in fake.txt and "D45" in fake.txt and "Vi88" in fake.txt
    assert "Lv" in fake.txt                      # level folded into Battle row
    # extreme uncapped powers + a maxed record still fit the box
    p.vaccine = p.data_power = p.virus = 9999
    p.wins, p.battles, p.trophies, p.exp = 999, 999, 99, 999999
    Stats.paint(fake, p)
    _fits(fake, "home/extreme")


# ---- card audit 2026-07-24: word-wrap, not char-slice --------------------

def test_wrap_never_splits_a_word_and_caps_with_ellipsis():
    """The helper the Options card now uses: word boundaries only, a lone
    over-wide token still breaks (never overruns the card), and past the cap
    the last line ends in an ellipsis rather than dropping the tail silently."""
    from tuipet import statusbox as sb
    out = sb.wrap("A flips launch auto-install", 3)
    assert all(len(l) <= CARD_W for l in out)
    assert "auto-install" in out                 # kept whole, not "auto-instal"
    out = sb.wrap(" ".join(["word"] * 15), 2)      # 15 words -> 3 lines, capped
    assert len(out) == 2 and out[-1].endswith("…")
    assert all(len(l) <= CARD_W for l in sb.wrap("x" * 40, 3))  # lone giant token


def test_options_card_wraps_every_desc_and_the_update_msg():
    """Joel "words are getting cut off": the Options card sliced desc[:26] /
    [26:52] and msg[:26] -- cutting 'auto-install' mid-glyph and dropping the
    restart prompt's tail.  Now every option's desc and the longest update
    message fit the card with NO word lost."""
    import re
    from tuipet import statusbox, optionsscreen as _opts

    class _Mode:
        def __init__(self, cursor, msg): self.cursor, self.msg = cursor, msg

    class _App:
        def __init__(self, mode): self.mode, self.stats_w = mode, _FakeStats()

    longest = "Updated! Restart now?  ENTER restarts · ESC later"
    for i, row in enumerate(_opts._ROWS):
        app = _App(_Mode(i, longest))
        statusbox.options(app)
        _fits(app.stats_w, f"options[{row}]")
        shown = re.sub(r"\[/?[^\[\]]*\]", "", app.stats_w.txt)
        for word in re.findall(r"[A-Za-z]+", _opts._DESC.get(row, "") + " " + longest):
            assert word in shown, f"{row}: lost the word {word!r}"


# ---- card audit 2026-07-24 sweep: the OTHER cards that char-sliced msgs ----

class _RenderApp:
    def __init__(self, mode, pet):
        self.mode, self.pet, self.stats_w = mode, pet, _FakeStats()


def _no_words_lost(fake, tag, *sources):
    shown = re.sub(r"\[/?[^\[\]]*\]", "", fake.txt)
    for src in sources:
        for word in re.findall(r"[A-Za-z0-9]+", src):
            assert word in shown, f"{tag}: lost {word!r}"


def test_scenes_card_wraps_its_picker_message():
    from tuipet import statusbox
    class _M:
        rows, cursor = [0, 1], 1
        msg = "pick a scene — it hangs behind the mon"    # 38 chars
        def _name(self, r): return "Digimon Sovereign Throne"
    p = _pet(); p.bg_pick = 0
    app = _RenderApp(_M(), p)
    statusbox.scenes(app)
    _fits(app.stats_w, "scenes")
    _no_words_lost(app.stats_w, "scenes", _M.msg)


def test_shop_card_wraps_the_longest_effect_line():
    from tuipet import statusbox, shop
    # skateboard carries the 51-char effect_line
    eff = shop.effect_line({"key": "skateboard"})
    assert len(eff) > 26                                   # the audit premise
    class _M:
        mode, cursor = "shop", 0
        def _rows(self):
            return [{"key": "skateboard", "name": "Skateboard", "price": 800}]
    p = _pet(); p.bits = 50
    app = _RenderApp(_M(), p)
    statusbox.shop(app)
    _fits(app.stats_w, "shop")
    _no_words_lost(app.stats_w, "shop", eff)


def test_digicore_card_wraps_its_note():
    from tuipet import statusbox
    class _M:
        pages, i = [("EvolutionState",), ("DATA",)], 0
        note = "It rests now — press N for a new egg."      # 37 chars
    app = _RenderApp(_M(), _pet())
    statusbox.digicore(app)
    _fits(app.stats_w, "digicore")
    _no_words_lost(app.stats_w, "digicore", _M.note)


def test_battle_card_wraps_the_result_note():
    from tuipet import statusbox
    class _M:
        battle, enemy, raid = None, {"name": "MetalGreymon"}, False
        hud_php, hud_fhp = 3, 4
        locked, done_anim, won, phase = "mega", False, False, "fighting"
        hud_note = "a draw — counts as a loss · record 12W/30"   # ~40 chars
    app = _RenderApp(_M(), _pet())
    statusbox.battle(app)
    _fits(app.stats_w, "battle")
    _no_words_lost(app.stats_w, "battle", _M.hud_note)


def test_the_home_and_egg_cards_name_the_festival():
    """⭐Bug report 2026-08-01 (Joel): "whyyyy is there a sun pixel sprite
    stuck on the lcd screen?"  It was the Crest of Courage — the Odaiba
    Memorial Day decoration, a prop that appeared in the arena corner on four
    dates a year and was named NOWHERE on the home screen -- a prop with no
    label reads as a stuck pixel.  The PROP itself was cut on 2026-08-01
    ("cut it"); this banner is what replaced it, and it is now the only
    on-screen sign that a festival is running.

    ⛔THIS ALSO FENCES THE ROW BUDGET.  The festival banner is the 16th row of
    a 16-row card, so a future 17th row would break the home card on four days
    a year and pass every other day.  Forcing a festival here turns that
    landmine into an always-on gate."""
    import datetime
    from tuipet import statusbox, tournament
    fake = _FakeStats()
    p = _pet()
    e = Pet(num=-1, name="", stage="Egg")
    e.world_seconds = 600.0
    for name, (m, d) in {"Odaiba Memorial Day": (8, 1),
                         "Christmas Festival": (12, 25),
                         "Halloween Festival": (10, 31),
                         "New Year Festival": (1, 1)}.items():
        tournament._today = (lambda mm, dd: (lambda: datetime.date(2026, mm, dd)))(m, d)
        for lines, tag in ((statusbox.home_lines(p), "home"),
                           (statusbox.egg_lines(e), "egg")):
            fake.txt = "\n".join(lines)
            _fits(fake, f"{tag} on {name}")
            assert name in fake.txt, f"{tag} card never names {name}"
    # ...and an ordinary day carries no banner at all
    tournament._today = lambda: datetime.date(2026, 6, 17)
    fake.txt = "\n".join(statusbox.home_lines(p))
    _fits(fake, "home, ordinary day")
    # (not a bare "★" check -- the Battle row wears ★{trophies} every day)
    for name in ("Odaiba", "Christmas", "Halloween", "New Year"):
        assert name not in fake.txt
