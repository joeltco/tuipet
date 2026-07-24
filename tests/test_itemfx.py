"""Item-use animation scripts (item-anim audit 2026-07-07: "balloons and
futons have broken in game animations" — every toy funneled into canon's
Trampoline hop).  Each AnimationType now plays its own canon table (itemfx);
this pins the tables' shapes, the routing, and the end chains."""
from tuipet import data, itemfx
from tuipet.app import Screen
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel


class _FakeScreen:
    fx = None
    frame_i = 0
_FakeScreen.start_fx = Screen.start_fx
_FakeScreen.advance_fx = Screen.advance_fx


def test_every_script_is_well_formed():
    for act, sc in itemfx.SCRIPTS.items():
        assert sc["end"] in ("cheer", "jeer"), act
        assert max(sc.get("rows", {}), default=0) < sc["steps"], act
        assert all(b < sc["steps"] for b in sc["snds"]), act
        for row in sc.get("rows", {}).values():
            assert 0 <= row.get("i", 0) <= 3, act          # 4 extracted frames
        # replay every step: geometry math must never crash, and the item
        # must never sink through the floor
        for step in range(sc["steps"]):
            _f, _p, _ix, iy, _dx, _dy = itemfx.state(act, step, 8, 8, 24)
            assert iy <= 24 - 8 - 1, (act, step)


def test_play_is_canon_not_the_trampoline_hop():
    """playing(): pet flips 1<->5 while the toy runs frames, wash stings at
    the excited beats, and the fx resolves into cheer."""
    sc = itemfx.SCRIPTS["Play"]
    assert sc["snds"] == {6: "wash", 18: "wash", 30: "wash"}
    assert itemfx.state("Play", 0, 8, 8, 24)[1] == 1
    assert itemfx.state("Play", 6, 8, 8, 24)[1] == 5
    assert itemfx.state("Play", 12, 8, 8, 24)[1] == 1
    assert sc["end"] == "cheer"


def test_angry_surprise_ends_angry_and_jeers():
    assert itemfx.state("AngrySurprise", 30, 8, 8, 24)[1] == 4
    assert itemfx.state("AngrySurprise", 42, 8, 8, 24)[1] == 4
    assert itemfx.SCRIPTS["AngrySurprise"]["end"] == "jeer"


def test_bounce_ball_drops_hits_and_exits_left():
    top = itemfx.state("Bounce", 0, 8, 8, 24)
    assert top[3] < 0                                   # in from above the arena
    down = itemfx.state("Bounce", 13, 8, 8, 24)
    assert down[3] > top[3]                             # it fell
    hit = itemfx.state("Bounce", 14, 8, 8, 24)
    assert hit[1] == 5                                  # the pet lights up
    assert itemfx.SCRIPTS["Bounce"]["snds"][14] == "click"   # hitBall
    end = itemfx.state("Bounce", 30, 8, 8, 24)
    assert end[2] < hit[2]                              # carried away left


def test_lift_toggles_the_dumbbell_and_the_strain_pose():
    floor = 24 - 8 - 2                  # grounded 2px above the border (window law)
    up = itemfx.state("Lift", 6, 8, 8, 24)
    assert up[3] == floor - 6 and up[1] == 8
    dn = itemfx.state("Lift", 12, 8, 8, 24)
    assert dn[3] == floor and dn[1] == 1


def test_ride_carries_the_pet_off_left():
    mid = itemfx.state("Ride", 20, 8, 8, 24)
    assert mid[1] == 5 and mid[4] < 0                   # riding happy, moving left
    end = itemfx.state("Ride", 29, 8, 8, 24)
    assert end[4] < mid[4]                              # still sliding


def _bag_use(name):
    """Drive a real bag use of the named item; return the panel's verdict."""
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    e = next(x for x in [data.consumable_by_key(k) for k in data.load_icons()]
             if x and x.get("name") == name)
    p.add_item(e["key"])
    pan = ShopPanel(p, start_mode="bag")
    rows = pan._rows()
    for i, r in enumerate(rows):
        if r.get("key") == e["key"]:
            pan.cursor = i
            break
    else:
        for t in range(6):                              # find its tab
            pan.key("right")
            rows = pan._rows()
            hit = next((i for i, r in enumerate(rows) if r.get("key") == e["key"]), None)
            if hit is not None:
                pan.cursor = hit
                break
    return pan.key("enter"), e


def test_item_fx_plays_the_script_and_chains():
    s = _FakeScreen()
    s.start_fx("item", icon="i:0", script="Play")
    assert s.fx["steps"] == itemfx.SCRIPTS["Play"]["steps"]
    assert s.fx["snds"] == itemfx.SCRIPTS["Play"]["snds"]
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer"   # canon: resolves into cheer
    s2 = _FakeScreen()
    s2.start_fx("item", icon="i:0", script="AngrySurprise")
    for _ in range(s2.fx["steps"]):
        s2.advance_fx()
    assert s2.fx is not None and s2.fx["kind"] == "jeer"


def test_the_stage_lives_inside_the_window():
    """Bug report 2026-07-13 ("balloon sprite is broken and off screen"): the
    ITEM_X/PET_X/floor spots predated the window law -- toys hung past the
    left wall and sank below the grounded floor.  At the opening beat every
    grounded layout must place the WHOLE icon inside x[4,36) / above the
    floor line, for small (8x8) and tall (16x16, the balloon) icons alike."""
    from tuipet import grid
    for action, sc in itemfx.SCRIPTS.items():
        if sc["layout"] == "drop":              # enters from above by design
            continue
        for iw, ih in ((8, 8), (7, 16), (16, 16)):
            _f, _p, ix, iy, _dx, _dy = itemfx.state(action, 0, iw, ih, 24)
            assert ix >= grid.X0, (action, iw, ih, ix)
            assert ix + iw <= grid.X1, (action, iw, ih, ix)
            assert iy + ih <= grid.FLOOR, (action, iw, ih, iy)
    assert itemfx.PET_X + itemfx.SPRITE_W <= grid.X1


# ---- the canon item-show map (item-show audit 2026-07-23) -------------------
# Joel: "we have the vitamin sprite, correct? is all of that already wired
# in?"  It was not: all 26 non-food catalog items carry a 4-frame ripped
# strip, and only the 7 toys played a show.  shop.item_script now reads the
# CANON AnimationType column instead of a hand-map.

def test_the_toys_are_unchanged_by_the_canon_lookup():
    """Regression: the 7 hand-mapped toys must resolve identically now
    that the map is gone."""
    from tuipet import shop
    assert {k: shop.item_script(k) for k in
            ("ball", "skateboard", "xylophone", "video_game",
             "television", "bubble_bath", "cold_shower")} == {
        "ball": "Bounce", "skateboard": "Ride",
        "xylophone": "InteractXylophone", "video_game": "Play",
        "television": "InteractTelevision", "bubble_bath": "Bathe",
        "cold_shower": "Shower"}


def test_the_free_wins_are_wired():
    """Four items whose scripts were ALREADY written and whose art was
    already ripped, flashing bare text because the hand-map omitted them."""
    from tuipet import shop
    assert shop.item_script("textbook") == "Study"
    assert shop.item_script("dumbbell") == "Lift"
    assert shop.item_script("grow_capsule") == "Study"
    # (music_player used to resolve to its canon "Play" here; it is now an
    #  override -- see test_the_music_player_borrows_the_musical_show)


def test_own_door_items_are_never_hijacked():
    """The memory chip, both road transports, the road's Life Recovery and
    the Revive Floppy keep their own flows -- the Floppy especially: its
    canon type is Play, but it is used on a DEAD pet and the bag is
    unreachable at the grave, so that show could only ever be wrong."""
    from tuipet import shop
    for k in ("digimemory", "revive_floppy", "town_transport",
              "disaster_transport", "life_recovery"):
        assert shop.item_script(k) is None, k


def test_food_sheet_consumables_take_no_script():
    """`f:` items are EATEN -- foods.csv has no AnimationType at all -- so
    they ride the eat fx (like the pill), never a script."""
    from tuipet import shop
    for k in ("vitamin", "energy_drink", "sleeping_pill", "anti_evo_chip"):
        assert shop.item_script(k) is None, k


def test_every_wired_script_actually_exists():
    """No item may point at a script the painter cannot run."""
    from tuipet import shop, itemfx
    for k in shop.CATALOG:
        sc = shop.item_script(k)
        assert sc is None or sc in itemfx.SCRIPTS, (k, sc)


# ---- the eat show for food-sheet consumables (2026-07-23, Joel: "do the
# eat show for the consumables too") -----------------------------------------

def _bag_on(pet, key):
    """A bag panel with the cursor placed ON `key`.  ShopPanel REMEMBERS
    its tab+cursor between panels (_LAST_POS, a shipped QOL feature), so
    a pin must never assume it opens at row 0 -- that pollution is what
    made these pass alone and fail in file order."""
    from tuipet import shop, shopscreen
    shopscreen._LAST_POS.clear()
    pan = shopscreen.ShopPanel(pet, start_mode="bag")
    want = shop.CATALOG[key][0]
    for _ in range(40):                       # walk tabs, then rows
        cur = [ln for ln in pan.text().plain.splitlines()
               if ln.lstrip().startswith("▸")]
        if cur and want in cur[0]:
            return pan
        pan.key("down" if cur else "right")
    raise AssertionError(f"never reached {key} in the bag")


def test_every_food_sheet_item_is_eaten():
    """The canon rule is the SHEET: foods.csv has no AnimationType column
    because eating IS the animation.  So the six food-sheet CONSUMABLES
    eat like the pill does -- they used to flash bare text over ripped
    art -- and no actual food regresses."""
    from tuipet import shop
    for k in ("vitamin", "energy_drink", "slim_drink", "sleeping_pill",
              "caffeine_pill", "anti_evo_chip"):
        assert shop.item_is_eaten(k), k
    for k in shop.FOOD_KEYS:
        assert shop.item_is_eaten(k), k


def test_an_item_is_never_both_eaten_and_scripted():
    """`f:` eats, `i:` takes a script -- the two doors never overlap."""
    from tuipet import shop
    for k in shop.CATALOG:
        assert not (shop.item_is_eaten(k) and shop.item_script(k)), k


def test_the_bag_returns_the_eat_show_for_a_consumable():
    """The panel contract: using a food-sheet consumable closes the bag
    and hands the LCD an eat show carrying that item's OWN icon."""
    from tuipet.pet import Pet
    for key, icon in (("energy_drink", "f:17"), ("vitamin", "f:5"),
                      ("sleeping_pill", "f:34")):
        p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
        p.world_seconds = 600.0
        p.strength = 0
        p._set_energy(4)
        p.add_item(key)
        pan = _bag_on(p, key)
        res = pan.key("enter")
        assert res and res[0] == "done", (key, res)
        assert res[1][0] == "eat" and res[1][1] == icon, (key, res)


def test_the_sleeping_pill_eats_first_then_sleeps():
    """The one risky interaction: the pill's show must still be an EAT
    (the fx owns the whole arena paint, so the sleep lands after it)."""
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.add_item("sleeping_pill")
    pan = _bag_on(p, "sleeping_pill")
    res = pan.key("enter")
    assert res[1][0] == "eat"
    assert p.asleep                            # ...and it did go to sleep


# ---- the Bandage's show, restored (2026-07-23, Joel: "do the bandage
# animation") -----------------------------------------------------------------

def test_the_bandage_plays_its_canon_beats():
    """DVPet bandage(), recovered from git 44c6405~1: the med is held up
    beside the HURT pet (pose 9 throughout), pressed on at beat 4 (canon
    setLocY 53 -> 64), stepping its 4-frame strip at 0/8/13/18, ending
    23 into cheer."""
    sc = itemfx.SCRIPTS["Bandaging"]
    assert sc["steps"] == 24 and sc["end"] == "cheer"
    frames = [itemfx.state("Bandaging", b, 8, 8, 24)[0] for b in (0, 8, 13, 18)]
    assert frames == [0, 1, 2, 3]                     # the application strip
    assert all(itemfx.state("Bandaging", b, 8, 8, 24)[1] == 9
               for b in range(24))                    # treated the whole way
    held = itemfx.state("Bandaging", 0, 8, 8, 24)[3]
    pressed = itemfx.state("Bandaging", 4, 8, 8, 24)[3]
    assert pressed > held                             # it comes DOWN onto the pet


def test_the_bandage_never_leaves_the_window():
    """⚠ THE REMOVAL'S BUG (44c6405): the old port drew the strip at
    ABSOLUTE y0-4 -- above the window top (y6) -- and was deleted for it.
    Every y is floor-relative now; this walks all 24 beats to prove the
    med stays inside the arena for small and tall icons alike."""
    from tuipet import grid
    for iw, ih in ((8, 8), (16, 16)):
        for step in range(itemfx.SCRIPTS["Bandaging"]["steps"]):
            _f, _p, ix, iy, _dx, _dy = itemfx.state("Bandaging", step, iw, ih, 24)
            assert ix >= grid.X0, (step, iw, ix)
            assert ix + iw <= grid.X1, (step, iw, ix)
            assert iy >= 0, (step, ih, iy)            # NEVER above the window top
            assert iy + ih <= grid.FLOOR, (step, ih, iy)


def test_the_bandage_keeps_its_canon_animation_name():
    """The show survived R3 intact.  The bandage left the SHELF (its cure
    is a free care-menu action now), but items.csv row 80 still says
    Bandaging and the script is still the thing that plays -- only the
    door changed, from the bag to the F menu."""
    from tuipet import data
    assert (data.consumable_by_key("i:80") or {}).get("action") == "Bandaging"
    assert "Bandaging" in itemfx.SCRIPTS


def test_the_bandage_show_only_plays_when_it_treats_something():
    """A refused bandage plays nothing; a real cure plays Bandaging."""
    from tuipet.pet import Pet
    from tuipet.feedscreen import FeedPanel, ROWS_MENU
    row = [k for k, _l in ROWS_MENU].index("bandage")
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    pan = FeedPanel(p)
    pan.cursor = row
    assert pan.key("enter")[1][0] == "refused"        # healthy: no show
    p.injured = True
    p.inj_length = 300.0
    pan2 = FeedPanel(p)
    pan2.cursor = row
    outcome, item, _msg = pan2.key("enter")[1]
    assert outcome == "bandaged" and item["key"] == "i:80"
    assert not p.injured


# ---- the last three show gaps closed (2026-07-24, Joel: "wire porttoilet
# and use study for the chips") ----------------------------------------------

def test_every_item_has_a_show_path():
    """41 of 44 items showed correctly; port_potty, dna_crystal and
    x_antibody flashed bare text.  Now every item either eats, plays a
    script, or rides its own door -- none falls through to a text flash."""
    from tuipet import shop
    for k in shop.CATALOG:
        has = (k in shop._OWN_FLOW
               or shop.item_is_eaten(k)
               or bool(shop.item_script(k)))
        assert has, f"{k} has no show path"


def test_the_port_potty_plays_its_canon_sequence():
    """DVPet portToilet() -> poopToilet(false): the pet sits (pose 4) and
    strains, the poop lands at beat 18 (pose 5 + the poop sound), back to
    neutral, into cheer.  No wash beat -- flush=false."""
    from tuipet import shop
    assert shop.item_script("port_potty") == "PortToilet"
    sc = itemfx.SCRIPTS["PortToilet"]
    assert sc["end"] == "cheer"
    assert sc["snds"] == {18: "poop"}
    poses = [itemfx.state("PortToilet", b, 16, 16, 40)[1] for b in (0, 15, 18, 28)]
    assert poses == [4, 4, 5, 1]            # sit/strain -> relief -> neutral


def test_the_port_potty_never_leaves_the_window():
    """The layout law: every beat, both icon sizes, stays in the arena."""
    from tuipet import grid
    for iw, ih in ((8, 8), (16, 16)):
        for step in range(itemfx.SCRIPTS["PortToilet"]["steps"]):
            _f, _p, ix, iy, _dx, _dy = itemfx.state("PortToilet", step, iw, ih, 40)
            assert ix >= grid.X0 and ix + iw <= grid.X1, (step, iw, ix)
            assert 0 <= iy <= 40 - ih, (step, ih, iy)


def test_the_evolution_chips_borrow_the_study_show():
    """DNA Crystal and X-Antibody carry items.csv's ItemEvol type but do
    NOT evolve, so the evolution animation would lie.  Remapped to Study
    (Joel 2026-07-24): the pet absorbing data / the X-program."""
    from tuipet import shop
    assert shop.item_script("dna_crystal") == "Study"
    assert shop.item_script("x_antibody") == "Study"
    assert "Study" in itemfx.SCRIPTS


def test_the_music_player_borrows_the_musical_show():
    """The Music Player's canon Play type is the WASH-sound recreation show
    -- wrong for a waking SONG.  Remapped (Joel 2026-07-24) to the Xylophone's
    musical interaction: the same NOTE beats, its own i:9 icon."""
    from tuipet import shop
    assert shop.item_script("music_player") == "InteractXylophone"
    assert shop.item_script("music_player") != "Play"
    # the xylophone it borrows from is untouched
    assert shop.item_script("xylophone") == "InteractXylophone"
    # the show is a real, well-formed script
    assert "InteractXylophone" in itemfx.SCRIPTS


def test_the_override_is_ONLY_the_deliberate_remaps():
    """A guard: the remap must not silently swallow a real ItemEvol path
    (the crest Digimentals, which fire an actual evolution via their own
    door) or any other item.  Exactly three entries, each ruled by Joel:
    the two non-evolving chips -> Study, the music player -> the note show."""
    assert set(itemfx._SCRIPT_OVERRIDE) == {"dna_crystal", "x_antibody",
                                            "music_player"}


def test_a_bag_use_fires_the_show_for_all_three():
    from tuipet.pet import Pet
    from tuipet.shopscreen import ShopPanel

    def use(key, setup=None):
        p = Pet(num=100, stage="Champion", attribute="Vaccine")
        p.world_seconds = 600.0
        p.bits = 9999
        if setup:
            setup(p)
        p.add_item(key)
        pan = ShopPanel(p, start_mode="bag")
        pan.tab = pan._tabs().index("Items")
        rows = pan._rows()
        pan.cursor = next(i for i, e in enumerate(rows) if e.get("key") == key)
        return pan.key("enter")

    r = use("port_potty", lambda p: (setattr(p, "poop", 2),
                                     setattr(p, "poop_sizes", [1, 2])))
    assert r[1][0] == "item_use" and r[1][2] == "PortToilet"
    for k in ("dna_crystal", "x_antibody"):
        r = use(k)
        assert r[1][0] == "item_use" and r[1][2] == "Study", k
