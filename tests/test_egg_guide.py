"""The digitama guide (Joel 2026-07-12: "build the egg unlock guide screen").

The carousel stays available-only; the GUIDE is where every egg in the game
shows its state and — verbatim from eggUnlock.csv — what earns it, with the
live unlock_progress counter.  These tests pin the two-surface split, the
verbatim-data rule, the 38-col / 12-row LCD budget, and the hint convention."""
from tuipet import data, egg, persistence
from tuipet.eggguidescreen import EggGuidePanel, _wrap


def _rule(name):
    return next(r for r in data.load_egg_unlock().values() if r["name"] == name)


def _lines(panel):
    return panel.text().plain.split("\n")


# ---- the list ---------------------------------------------------------------------

def test_guide_lists_every_egg():
    pan = EggGuidePanel()                        # sandboxed = a fresh profile
    assert pan.n == egg.count()                  # ALL eggs, not just hatchable
    assert pan.n > len(egg.hatchable_eggs(pan.prog, set()))


def test_fresh_profile_marks():
    pan = EggGuidePanel()
    assert pan._tag(0) == "yours"                        # a starter
    assert pan._tag(_rule("Kuramon")["idx"]) == "locked"  # yes/no gate, unmet
    assert pan._tag(_rule("Sakumon")["idx"]) == "0/50"    # countable gate -> live count


def test_note_is_the_csv_description_verbatim():
    pan = EggGuidePanel()
    idx = _rule("Chibickmon")["idx"]
    pan.i = idx
    assert pan._note(idx) == _rule("Chibickmon")["desc"] == "Win 10 battles"


# ---- one egg's story --------------------------------------------------------------

def test_detail_locked_countable_shows_goal():
    pan = EggGuidePanel()
    idx = _rule("Dodomon")["idx"]                # Mega-kill gate
    rows = dict((l, v) for l, v in pan._detail_rows(idx) if l)
    assert rows["State"] == "locked"
    assert rows["Unlock"].startswith("Fell")     # csv desc (may wrap; first line)
    assert rows["Goal"] == "Mega-class felled 0/5"
    assert rows["Keeps"] == "forever"


def test_no_detail_row_ever_shows_a_price():
    """The licence cut (2026-07-17): the guide sells nothing."""
    pan = EggGuidePanel()
    for i in range(pan.n):
        assert "Price" not in dict(pan._detail_rows(i))


def test_detail_temp_lineage_egg_says_this_gen():
    pan = EggGuidePanel()
    idx = _rule("Kuramon")["idx"]                # dark-descendant temp egg
    rows = dict((l, v) for l, v in pan._detail_rows(idx) if l)
    assert rows["Keeps"] == "this generation only"


def test_wrap_rejoins_verbatim():
    """The unlock line may wrap but never rewrites the csv text."""
    for r in data.load_egg_unlock().values():
        if r["desc"]:
            assert " ".join(_wrap(r["desc"])) == r["desc"]


# ---- LCD budget + keys ------------------------------------------------------------

def test_every_page_fits_the_lcd():
    """38 cols, 12 rows -- list AND every detail page."""
    pan = EggGuidePanel()
    pages = [_lines(pan)]
    pan.key("enter")
    for _ in range(pan.n):
        pages.append(_lines(pan))
        pan.key("right")
    for pg in pages:
        assert len(pg) == 12
        assert all(len(ln) <= 38 for ln in pg)


def test_key_protocol():
    pan = EggGuidePanel()
    assert pan.key("down") is None and pan.i == 1
    assert pan.key("enter") is None and pan.detail
    pan.key("left")                              # detail paging wraps
    assert pan.i == 0
    pan.key("escape")
    assert not pan.detail                        # detail ESC -> back to the list
    assert pan.key("escape") == ("done", None)   # list ESC -> close


def test_strip_follows_the_hint_convention():
    from tuipet import menu
    pan = EggGuidePanel()
    assert pan.strip() == menu.hints(("↑↓", "browse"), ("ENTER", "story"), ("ESC", "out"))
    pan.key("enter")
    assert pan.strip() == menu.hints(("←→", "browse"), ("ESC", "back"))


def test_home_screen_binding():
    from tuipet.app import TuiPetApp
    assert any(b[:2] == ("n", "eggguide") for b in TuiPetApp.BINDINGS)


def test_n_opens_the_guide_in_the_real_app():
    """The home-screen binding, driven through the actual app: n opens the
    guide, ESC closes it (the fresh-profile account gate may sit between the
    title and home -- escape past it)."""
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet

    async def go():
        p = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter"); await pilot.pause()
            if app.mode is not None:               # account gate on a fresh profile
                await pilot.press("escape"); await pilot.pause()
            await pilot.press("n"); await pilot.pause()
            opened = type(app.mode).__name__
            await pilot.press("escape"); await pilot.pause()
            return opened, app.mode

    opened, after = asyncio.run(go())
    assert opened == "EggGuidePanel"
    assert after is None
