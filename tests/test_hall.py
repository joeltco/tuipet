"""The HALL OF MEMORY (Joel 2026-07-26: "build the hall of memory") — the
lineage's own book.  Headstones were already banked (snapshot_prev_gen, the
LEGACY roll) but only ever read as data rows; the hall gives every elder a
portrait and an epitaph.  These pins hold: the record carries the portrait
fields, the panel walks clean in every state (the panel-smoke law), old
records degrade to the grave instead of guessing, and the LEGACY page's
ENTER is the door."""
from tuipet import data, persistence
from tuipet.hallscreen import HallPanel
from tuipet.pet import Pet


def _elder(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.name, p.generation = "Testmon", 3
    p.age_seconds = 2 * 86400 + 3600.0
    p.trophies, p.wins, p.battles = 2, 7, 11
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _walk(pan, keys):
    for k in keys:
        pan.anim()
        assert pan.text().plain
        assert pan.strip()
        pan.key(k)
    assert pan.text().plain


# ---- the record --------------------------------------------------------------

def test_the_headstone_carries_the_portrait_fields():
    """A fallen elder's stone knows its form, its killer and its record."""
    p = _elder(dead=True, death_cause="sickness")
    persistence.snapshot_prev_gen(p)
    (r,) = persistence.load_settings()["progress"]["legacy"]
    assert r["num"] == 100 and r["cause"] == "sickness"
    assert r["wins"] == 7 and r["battles"] == 11 and r["cups"] == 2
    assert r["dead"] is True


def test_a_live_retire_is_remembered_without_a_cause():
    persistence.snapshot_prev_gen(_elder())
    (r,) = persistence.load_settings()["progress"]["legacy"]
    assert r["dead"] is False and r["cause"] == ""


# ---- the panel ---------------------------------------------------------------

def test_an_empty_hall_stands_and_leaves():
    pan = HallPanel()
    assert "no elders rest here yet" in pan.text().plain
    assert "generation one" in pan.text().plain
    assert pan.key("down") is None            # nothing to browse
    assert pan.key("escape") == ("done", None)


def test_the_hall_walks_list_and_portrait():
    persistence.snapshot_prev_gen(_elder(dead=True, death_cause="old wounds"))
    persistence.snapshot_prev_gen(_elder())
    pan = HallPanel()
    assert pan.n == 2
    plain = pan.text().plain
    assert "Testmon" in plain and "HALL OF MEMORY" in plain
    # newest first: the live retire (·) leads, the fallen elder (†) follows
    _walk(pan, ["down", "up", "pagedown", "enter", "right", "left",
                "pageup", "escape", "down"])
    assert pan.key("escape") == ("done", None)


def test_the_epitaph_speaks_the_fate_it_knows():
    persistence.snapshot_prev_gen(_elder(dead=True, death_cause="sickness"))
    persistence.snapshot_prev_gen(_elder())
    pan = HallPanel()
    # the full line (it marquees on the 40-col note when over-wide)
    assert "fell of sickness" in pan._epitaph(pan.elders[1])
    assert "walked to the next egg" in pan._epitaph(pan.elders[0])
    assert "7 wins" in pan._epitaph(pan.elders[0])
    pan.detail = True
    pan.i = 1                                     # the fallen elder renders it
    assert "fell of" in pan.text().plain


def test_an_old_headstone_stands_behind_the_grave():
    """Records banked before the portrait fields (no num/cause) must not
    guess: the grave glyph stands in, and the epitaph is just 'fell'."""
    d = persistence.load_settings()
    d.setdefault("progress", {})["legacy"] = [
        {"gen": 1, "name": "Oldmon", "stage": "Rookie",
         "age": 86400.0, "cups": 0, "dead": True}]
    persistence.save_settings(d)
    pan = HallPanel()
    grave = (data.load_effects().get("grave") or [[]])[0]
    assert pan._portrait_rows(pan.elders[0]) == grave
    pan.detail = True
    plain = pan.text().plain
    assert "OLDMON" in plain and "fell" in plain
    assert "fell of" not in plain                 # no invented cause


# ---- the door ----------------------------------------------------------------

def test_the_legacy_pages_enter_opens_the_hall():
    from tuipet.digicorescreen import DigiCorePanel
    pan = DigiCorePanel(_elder(), start="LEGACY")
    assert pan.pages[pan.i][0] == "LEGACY"
    from rich.text import Text
    assert "the hall of memory" in pan.text().plain
    assert "ENTER hall" in Text.from_markup(pan.strip()).plain
    assert pan.key("enter") == ("done", ("hall",))


def test_the_hall_round_trips_to_the_legacy_shelf():
    """The app's digicore callback opens the hall and walks back to the
    LEGACY page — the TROPHIES→ALBUM round-trip's exact shape."""
    from tuipet.app import TuiPetApp

    class _Stub:
        pet = _elder()
        opened = []
        _after_digicore = TuiPetApp._after_digicore

        def _open_mode(self, panel, cb=None):
            self.opened.append(type(panel).__name__)
            self._cb = cb

    stub = _Stub()
    TuiPetApp._after_digicore(stub, ("hall",))
    assert stub.opened == ["HallPanel"]
    stub._cb(None)                                # leaving the hall...
    assert stub.opened[-1] == "DigiCorePanel"     # ...reopens the book
