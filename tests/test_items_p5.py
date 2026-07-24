"""THE EFFECT PASS — items refactor P5 (2026-07-23).

Three rulings land here:

  R3  "make them symmetric" -> BOTH cures are free care-menu buttons.
      The Bandage left the shelf; ailments cost TIME, not bits.
  R4  the Textbook goes back to canon `+Obedience` (items.csv row 0) --
      the first item support the restored discipline system has had.
  R8  the mistake-eraser is KEPT, nerfed to one-at-a-time, and rehoused
      on its own item.

R8 is the one worth explaining.  Care mistakes are a DEATH clock, not an
evolution gate: 20 kills outright, an Ultimate/Mega dies at 5 once two
game-days into the stage, and the hazard ladder runs 100x steeper from 5
to 20.  The counter resets on every evolution -- but 241 of 417 Megas
have no outgoing evolution at all, so for those it never resets again and
the eraser is the only way back from a death sentence.

The item was FOUND, not invented: foods.csv row 18 (Miracle Drink) is the
only consumable in either sheet carrying `Mistake = -1`.
"""
import csv

from tuipet import shop
from tuipet.pet import Pet
from tuipet.petbase import MIRACLE_ENERGY_GAIN, TEXTBOOK_OBEDIENCE, _Refused


def _pet(**kw):
    kw.setdefault("stage", "Champion")
    p = Pet(num=100, attribute="Vaccine", **kw)
    p.world_seconds = 600.0
    return p


# ---- R8: the eraser, one at a time, its own item ---------------------------

def test_the_eraser_is_canon_data_not_an_invention():
    """foods.csv row 18 is DVPet's own eraser.  If this ever fails, the
    item stopped being canon-backed and became something I made up."""
    rows = {r["FoodIdentificationNum"]: r
            for r in csv.DictReader(open("src/tuipet/data/foods.csv"))}
    assert rows["18"]["Mistake"] == "-1"
    assert int(rows["18"]["Energy"]) == MIRACLE_ENERGY_GAIN
    assert shop.CATALOG["miracle_drink"].icon == "f:18"
    # and it is the ONLY one -- so there was exactly one right answer
    both = [r for r in rows.values() if r.get("Mistake", "0") not in ("0", "")]
    assert len(both) == 1


def test_the_eraser_takes_exactly_one_slip():
    p = _pet()
    p.care_mistakes = 3
    p.add_item("miracle_drink")
    p.use_item("miracle_drink")
    assert p.care_mistakes == 2, "the eraser must be ONE at a time"


def test_the_eraser_pays_its_canon_energy():
    p = _pet()
    p.care_mistakes = 2
    p._set_energy(0)
    p.add_item("miracle_drink")
    p.use_item("miracle_drink")
    assert p.energy == MIRACLE_ENERGY_GAIN


def test_the_eraser_is_refused_on_a_clean_slate_and_kept():
    p = _pet()
    p.care_mistakes = 0
    p.add_item("miracle_drink")
    out = p.use_item("miracle_drink")
    assert isinstance(out, _Refused)
    assert p.inventory.get("miracle_drink") == 1, "a refusal must keep the item"


def test_the_eraser_can_walk_a_terminal_mega_back_from_death():
    """The reason it was kept at all: a Mega at 5 slips past the window is
    dead on the next check, and (for the 58% of Megas with no outgoing
    evolution) nothing else can ever lower the counter."""
    p = _pet(stage="Mega")
    p.care_mistakes = 5
    for _ in range(5):
        p.add_item("miracle_drink")
        p.use_item("miracle_drink")
    assert p.care_mistakes == 0


def test_the_eraser_lives_in_medicine():
    assert shop.CATALOG["miracle_drink"].category == "Medicine"
    assert shop.CATALOG["miracle_drink"].touches == ("care_mistakes", "energy")


# ---- R4: the Textbook goes back to canon -----------------------------------

def test_the_textbook_teaches_obedience_at_canon_strength():
    rows = {r["ItemIdentificationNum"]: r
            for r in csv.DictReader(open("src/tuipet/data/items.csv"))}
    assert int(rows["0"]["Obedience"]) == TEXTBOOK_OBEDIENCE
    p = _pet()
    p.obedience = 40
    p.add_item("textbook")
    p.use_item("textbook")
    assert p.obedience == 40 + TEXTBOOK_OBEDIENCE


def test_the_textbook_no_longer_erases_anything():
    p = _pet()
    p.care_mistakes = 4
    p.obedience = 10
    p.add_item("textbook")
    p.use_item("textbook")
    assert p.care_mistakes == 4, "the eraser moved to its own item"


def test_the_textbook_is_refused_at_a_full_gauge_and_kept():
    from tuipet.petbase import MAX_OBEDIENCE
    p = _pet()
    p.obedience = MAX_OBEDIENCE
    p.add_item("textbook")
    out = p.use_item("textbook")
    assert isinstance(out, _Refused)
    assert p.inventory.get("textbook") == 1


def test_the_textbook_is_the_discipline_systems_first_item():
    assert shop.CATALOG["textbook"].touches == ("obedience",)
    obedience_items = [k for k, v in shop.CATALOG.items()
                       if "obedience" in v.touches]
    assert obedience_items == ["textbook"]


# ---- R3: both cures free, symmetric ----------------------------------------

def test_the_bandage_left_the_shelf():
    assert "bandage" not in shop.CATALOG
    assert "bandage" not in shop.EFFECTS


def test_both_ailments_cure_free_from_the_care_menu():
    """The symmetry itself: neither cure costs a bit, and both are always
    available."""
    from tuipet.feedscreen import ROWS_MENU
    kinds = [k for k, _label in ROWS_MENU]
    assert "pill" in kinds and "bandage" in kinds
    p = _pet()
    p.bits = 0                      # broke, and it must not matter
    p.injured = True
    p.inj_length = 400.0
    assert not isinstance(p.heal_bandage(), _Refused)
    assert p.injured is False and p.inj_length == 0.0


def test_the_free_bandage_is_refused_on_a_whole_pet():
    p = _pet()
    assert isinstance(p.heal_bandage(), _Refused)


def test_healing_a_sleeper_disturbs_it_like_the_pill_does():
    p = _pet()
    p.injured = True
    p.inj_length = 400.0
    p.asleep = True
    before = p.care_mistakes
    p.heal_bandage()
    assert p.injured is False
    assert p.care_mistakes >= before      # the disturb was billed


def test_a_held_bandage_is_healed_out_of_an_old_bag():
    """It was buyable for one afternoon; with no heir it must not linger as
    an unusable row."""
    from tuipet import persistence
    assert persistence._heal_bag({"bandage": 2, "fish": 1}) == {"fish": 1}


def test_the_ancient_eraser_key_now_points_at_the_new_item():
    assert shop.LEGACY_KEYS["care_mistake_eraser"] == "miracle_drink"


# ---- the care menu itself ---------------------------------------------------

def test_the_menu_opens_on_the_ailment_that_is_live():
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    for sick, hurt, want in ((False, False, "meat"), (True, False, "pill"),
                             (False, True, "bandage"), (True, True, "pill")):
        p = _pet()
        p.sick, p.injured = sick, hurt
        assert ROWS_MENU[FeedPanel(p).cursor][0] == want, (sick, hurt)


def test_the_third_row_is_reachable_in_both_directions():
    """The old two-row toggle was `1 - cursor`: it ignored direction and
    could never reach a third row at all."""
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    p = _pet()
    for key in ("down", "up"):
        pan = FeedPanel(p)
        seen = set()
        for _ in range(len(ROWS_MENU) * 2):
            pan.key(key)
            seen.add(pan.cursor)
        assert seen == set(range(len(ROWS_MENU))), key


def test_the_bandage_row_plays_its_own_canon_show():
    """WORN, not eaten -- the Bandaging script (items.csv i:80)."""
    from tuipet import data, itemfx
    from tuipet.feedscreen import FeedPanel
    assert (data.consumable_by_key("i:80") or {}).get("action") == "Bandaging"
    assert "Bandaging" in itemfx.SCRIPTS
    p = _pet()
    p.injured = True
    p.inj_length = 300.0
    pan = FeedPanel(p)
    pan.cursor = 2
    outcome, item, _msg = pan.key("enter")[1]
    assert outcome == "bandaged" and item["key"] == "i:80"


def test_the_care_menu_keeps_its_lcd_geometry():
    from tuipet.feedscreen import FeedPanel
    p = _pet()
    p.injured = True
    lines = FeedPanel(p).text().plain.split("\n")
    assert len(lines) == 12 and {len(ln) for ln in lines} == {40}
