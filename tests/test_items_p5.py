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


def test_the_eraser_became_the_WHOLE_SLATE():
    """⭐REPOINTED by the ITEM REFACTOR (2026-08-02).  The 7777b legendary
    erased ONE slip, which the 2000b Cold Compress already did -- and the
    Elixir now wipes the whole slate on Joel's own call, so a single scrub at
    four times the Compress's price was dead twice over.

    It scrubs the WHOLE SLATE now -- both counters.  The wipe briefly sat on
    the 2000b Elixir and Joel called that overpowered ("isnt a full care
    mistake wipe kind of over powered?"): at 2000b it matched the Cold
    Compress's price while doing infinitely more.  The biggest effect belongs
    to the scarcest bottle, and since rarity stopped meaning price (v0.5.337)
    that is this one -- legendary, ONE per shelf.  Canon's Mistake=-1 row still
    names the item (the test above); the scale is tuipet's ruling."""
    p = _pet()
    p.care_mistakes = 3
    p.mistake_day = 3
    p.add_item("miracle_drink")
    p.use_item("miracle_drink")
    assert p.care_mistakes == 0 and p.mistake_day == 0


def test_the_eraser_pays_its_canon_energy():
    p = _pet()
    p.care_mistakes = 2
    p._set_energy(0)
    p.add_item("miracle_drink")
    p.use_item("miracle_drink")
    assert p.energy == MIRACLE_ENERGY_GAIN


def test_the_ward_is_refused_while_one_is_already_running_and_kept():
    p = _pet()
    p.pardon_lapse = 500.0
    p.add_item("elixir")                       # the WARD lives on the Elixir
    out = p.use_item("elixir")
    assert isinstance(out, _Refused)
    assert p.inventory.get("elixir") == 1, "a refusal must keep the item"


def test_a_terminal_mega_can_still_be_walked_back_from_death():
    """The reason an eraser exists at all: a Mega at 5 slips past the window is
    dead on the next check, and (for the 58% of Megas with no outgoing
    evolution) nothing else can ever lower the counter.  That job moved to the
    MIRACLE DRINK's whole-slate wipe -- ONE bottle, not five, and it is the
    scarcest thing on the shelf, which is what an undo of the death clock
    should cost."""
    p = _pet(stage="Mega")
    p.care_mistakes = 5
    p.add_item("miracle_drink")
    p.use_item("miracle_drink")
    assert p.care_mistakes == 0


def test_the_eraser_lives_in_medicine():
    assert shop.CATALOG["miracle_drink"].category == "Cure"   # Medicine -> Cure, 2026-07-27
    assert shop.CATALOG["miracle_drink"].touches == ("care_mistakes", "mistake_day", "energy")


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


def test_the_textbook_led_a_whole_manners_economy():
    """P5 made the textbook discipline's FIRST item; the expansion
    (2026-07-26) grew the family -- foods and toys move manners now, in
    both directions.  The textbook stays the heavyweight (+20)."""
    assert shop.CATALOG["textbook"].touches == ("obedience",)
    obedience_items = {k for k, v in shop.CATALOG.items()
                       if "obedience" in v.touches}
    assert "textbook" in obedience_items and len(obedience_items) > 10


# ---- R3: both cures free, symmetric ----------------------------------------

def test_the_bandage_never_returns_to_the_shelf():
    """The ban, re-pinned after its THIRD revival died in an hour
    (2026-07-26: the expansion shipped it at 10b, Joel saw it and ruled
    "cut it out... its supposed to just be used for the animations for
    heal").  The wrap is the H show; no catalog key, ever."""
    assert "bandage" not in shop.CATALOG
    assert "bandage" not in shop.EFFECTS


def test_the_two_ailments_take_two_free_buttons(monkeypatch):
    """The final symmetry (2026-07-26): pill on F cures sickness, H heals
    injury -- both free -- and the canon time-heal (injLapse) stays
    underneath as the do-nothing path."""
    import tuipet.petbody as petbody
    from tuipet.feedscreen import ROWS_MENU
    kinds = [k for k, _label in ROWS_MENU]
    assert kinds == ["meat", "pill"]
    p = _pet()
    p.bits = 0                      # broke, and it must not matter
    p.injured = True
    p.inj_length = 400.0
    assert not isinstance(p.heal_bandage(), _Refused)
    assert p.injured is False and p.inj_length == 0.0
    monkeypatch.setattr(petbody.random, "random", lambda: 0.99)  # no hazard
    p2 = _pet()
    p2.injured, p2.inj_length = True, 400.0
    p2._tick_mortality(400.0)       # the untouched wound closes by itself
    assert p2.injured is False and p2.inj_length == 0.0


def test_the_bandage_is_refused_on_a_whole_pet():
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
    """The item is gone for good (re-ruled 2026-07-26 after the
    expansion's one-hour revival): a bandage bought in ANY brief shelf
    era must not linger as an unusable row."""
    from tuipet import persistence
    healed = persistence._heal_bag({"bandage": 2, "fish": 1,
                                    "i:80": 3, "i:82": 1})
    assert healed == {"fish": 1}


def test_the_ancient_eraser_key_now_points_at_the_new_item():
    assert shop.LEGACY_KEYS["care_mistake_eraser"] == "miracle_drink"


# ---- the care menu itself ---------------------------------------------------

def test_the_menu_opens_on_the_ailment_that_is_live():
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    # (the injured leg opens on MEAT now: its cure lives in the bag, not
    #  on this menu -- 2026-07-26)
    for sick, hurt, want in ((False, False, "meat"), (True, False, "pill"),
                             (False, True, "meat"), (True, True, "pill")):
        p = _pet()
        p.sick, p.injured = sick, hurt
        assert ROWS_MENU[FeedPanel(p).cursor][0] == want, (sick, hurt)


def test_every_feed_row_is_reachable_in_both_directions():
    """A standard list menu again (the shop-layout redo 2026-07-26
    superseded the brief RIGHT-column ruling): up/down cycles all three
    rows, honoring direction."""
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    p = _pet()
    for key in ("down", "up"):
        pan = FeedPanel(p)
        seen = set()
        for _ in range(len(ROWS_MENU) * 2):
            pan.key(key)
            seen.add(pan.cursor)
        assert seen == set(range(len(ROWS_MENU))), key


def test_the_h_heal_plays_the_canon_bandaging_show():
    """WORN, not eaten -- the Bandaging script (items.csv i:80), fired by
    the H action on a cure and by nothing on a refusal."""
    from tuipet import data, itemfx
    from tuipet.app import TuiPetApp
    assert (data.consumable_by_key("i:80") or {}).get("action") == "Bandaging"
    assert "Bandaging" in itemfx.SCRIPTS

    class _Scr:
        fx = None
        calls = []
        def start_fx(self, kind, **kw):
            self.calls.append((kind, kw))

    class _App:
        def _do(self, msg):
            self.said = msg

    app = _App()
    app.screen_w = _Scr()
    app.pet = _pet()
    TuiPetApp.action_heal(app)                        # healthy: refusal,
    assert app.screen_w.calls == []                   # no show
    app.pet.injured, app.pet.inj_length = True, 300.0
    TuiPetApp.action_heal(app)
    assert app.screen_w.calls == [("item", {"icon": "i:80",
                                            "script": "Bandaging"})]
    assert not app.pet.injured


def test_the_care_menu_keeps_its_lcd_geometry():
    """12 rows x 40 cols -- the classic pixel LCD scene again (restored
    2026-07-26: "just revert the feed menu to meat and pill lcd")."""
    from tuipet.feedscreen import FeedPanel
    p = _pet()
    p.injured = True
    lines = FeedPanel(p).text().plain.split("\n")
    assert len(lines) == 12 and {len(ln) for ln in lines} == {40}
