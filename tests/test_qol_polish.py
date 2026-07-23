"""QOL polish pins (board: QOL_POLISH_2026_07_23.md).

Batch 1 -- the skip cluster + the pill reflex: a decided fight must not
cost ~20 timed presses, round boundaries must not eat skip input, the
hurry keys must be discoverable on the strip, and a sick pet's feed
menu must open on the cure the HUD just told you to give.
"""
from tuipet.battlescreen import SKIP_DEBOUNCE, BattlePanel
from tuipet.feedscreen import FeedPanel
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _locked_panel():
    """A BattlePanel with the bar locked and the first round animating."""
    pan = BattlePanel(_pet(), {"num": 100, "name": "Sparrowmon"})
    pan._start_fight("normal")
    assert pan.phase == "anim"
    return pan


# ---- B1: ESC = end it (fast-run to the deciding round) ----------------------

def test_escape_fast_runs_a_decided_fight_to_its_final_round():
    pan = _locked_panel()
    for _ in range(SKIP_DEBOUNCE + 1):
        pan.anim()
    pan.key("escape")
    # every remaining round resolved in one press; the DECIDING round's
    # timeline is loaded so the KO beat still plays out on screen
    assert pan.battle.over
    assert pan.phase in ("anim", "result")
    if pan.phase == "anim":
        for _ in range(len(pan.timeline) + 2):
            pan.anim()
    assert pan.phase == "result" and pan.done_anim
    assert pan.won == pan.battle.won


def test_escape_end_never_hangs_on_a_raid_that_goes_the_distance():
    """A survived raid's boss never falls -- battle.over may only arrive
    when the rounds run dry, and the fast-run must exit via the result
    (the phase guard), not spin."""
    pan = BattlePanel(_pet(), {"num": 214, "name": "Bossmon", "boss": True,
                               "pool": (5_000_000, 5_500_000)}, raid=True)
    pan._start_fight("normal")
    for _ in range(SKIP_DEBOUNCE + 1):
        pan.anim()
    pan.key("escape")
    assert pan.battle.over or pan.phase == "result"


# ---- B2: the debounce anchors on the LOCK, not the round --------------------

def test_round_boundaries_no_longer_eat_skip_presses():
    pan = _locked_panel()
    # play into round 2+: watch self.i wrap back to a small value
    guard = 0
    while True:
        prev = pan.i
        pan.anim()
        guard += 1
        assert guard < 5000, "never reached a second round"
        if pan.phase != "anim":            # a 1-round KO: nothing to test here
            return
        if pan.i < prev:                   # a fresh round just began
            break
    assert pan.i < SKIP_DEBOUNCE           # inside the old dead-window
    before = pan.i
    pan.key("space")                       # the mash press at the boundary...
    assert pan.i != before                 # ...lands (old code ate it)


def test_the_lock_debounce_still_guards_the_first_beats():
    pan = _locked_panel()
    pan.key("space")                       # the press that locked the bar, repeated
    assert pan.i == 0                      # still debounced right after the lock


# ---- B3: the hurry keys live on the strip -----------------------------------

def test_round_anim_strip_prompts_the_hurry_keys():
    pan = _locked_panel()
    s = pan.strip()
    assert "hurry" in s and "ESC" in s


# ---- C1: a sick pet's feed menu opens on the Pill ---------------------------

def test_feed_opens_on_the_pill_when_sick_and_meat_when_well():
    assert FeedPanel(_pet(sick=True)).cursor == 1     # Pill
    assert FeedPanel(_pet()).cursor == 0              # Meat


# ============ Batch 2: menus & shops =========================================

def _fresh_shop(pet=None, **kw):
    from tuipet import shopscreen
    shopscreen._LAST_POS.clear()
    return shopscreen.ShopPanel(pet or _pet(bits=5000), **kw)


# ---- M1/M6: album + egg guide wrap; detail views page ----------------------

def test_album_and_eggguide_lists_wrap_both_ends():
    from tuipet.albumscreen import AlbumPanel
    from tuipet.eggguidescreen import EggGuidePanel
    for pan in (AlbumPanel(_pet()), EggGuidePanel()):
        pan.key("up")
        assert pan.i == pan.n - 1, type(pan).__name__   # top wraps to bottom
        pan.key("down")
        assert pan.i == 0, type(pan).__name__           # ...and back


def test_detail_views_honor_the_page_keys():
    from tuipet.albumscreen import AlbumPanel
    pan = AlbumPanel(_pet())
    pan.key("enter")                       # open the book
    assert pan.detail
    i0 = pan.i
    pan.key("pagedown")
    assert pan.i != i0                     # the leap lands (was a dead key)
    pan.key("pageup")
    assert pan.i == i0


# ---- M4/M7: shop cursor memory ----------------------------------------------

def test_shop_tabs_remember_their_cursor():
    pan = _fresh_shop()
    pan.key("down")
    pan.key("down")
    here = pan.cursor
    assert here != 0
    pan.key("right")                       # tab away...
    assert pan.cursor == 0
    pan.key("left")                        # ...and back
    assert pan.cursor == here


def test_shop_bag_toggle_keeps_both_positions():
    p = _pet(bits=5000)
    p.add_item("energy_drink")
    p.add_item("energy_drink")
    from tuipet import shopscreen
    pan = shopscreen.ShopPanel(p)
    pan.key("right")
    pan.key("down")
    shop_pos = (pan.tab, pan.cursor)
    pan.key("tab")                         # into the bag
    assert pan.mode == "bag"
    pan.key("tab")                         # back to the shop
    assert (pan.tab, pan.cursor) == shop_pos


def test_home_shop_reopens_where_you_left_off():
    from tuipet import shopscreen
    p = _pet(bits=5000)
    pan = _fresh_shop(p)
    pan.key("right")
    pan.key("down")
    pos = (pan.tab, pan.cursor)
    pan.key("escape")                      # leave the shop
    again = shopscreen.ShopPanel(p)
    assert (again.tab, again.cursor) == pos
    # town doors and explicit tabs are NOT hijacked by the memory
    town = shopscreen.ShopPanel(p, town_id=0, start_tab="Eggs")
    assert town.cursor == 0


# ---- M2: emptying a stack can't silently retarget a mash --------------------

def test_selling_the_last_of_a_stack_guards_the_next_press():
    p = _pet(bits=100)
    p.add_item("energy_drink")             # one of these...
    p.add_item("slim_drink")                 # ...and a neighbor
    pan = _fresh_shop(p, start_mode="bag")
    pan.key("right")                       # the drinks live on the Items tab
    keys = [r.get("key") for r in pan._rows()]
    pan.cursor = keys.index("energy_drink")
    pan.key("r")                           # sell the LAST one: stack empties
    assert pan._retarget                   # the guard is armed
    held0 = dict(p.inventory)
    pan.key("r")                           # the mash press...
    assert p.inventory == held0            # ...sells NOTHING
    assert "now on" in pan.msg             # and says where the cursor sits
    pan.key("r")                           # a deliberate press works again
    assert p.inventory != held0


def test_moving_the_cursor_disarms_the_retarget_guard():
    p = _pet(bits=100)
    p.add_item("energy_drink")
    p.add_item("slim_drink")
    pan = _fresh_shop(p, start_mode="bag")
    pan.key("right")                       # the drinks live on the Items tab
    keys = [r.get("key") for r in pan._rows()]
    pan.cursor = keys.index("energy_drink")
    pan.key("r")
    assert pan._retarget
    pan.key("down")                        # re-aiming on purpose...
    assert not pan._retarget               # ...clears the guard


# ---- M3: affordability at a glance ------------------------------------------

def test_unaffordable_shelf_rows_render_dim():
    from tuipet.theme import DIM
    pan = _fresh_shop(_pet(bits=0))        # broke: everything is short
    out = pan.text()
    assert any(sp.style == DIM and out.plain[sp.start:sp.end].strip()
               and "b" in out.plain[sp.start:sp.end]
               for sp in out.spans), "no dim shelf row for a broke tamer"


# ---- M5: the strip owns the keys (no contradicting footers) -----------------

def test_menu_family_footers_are_gone():
    """The Sound footer said "↑↓ pick ENTER go" while its strip said
    "←→ volume · ENTER hear it" -- both visible at once.  The strip is
    the single key surface now (QOL 2026-07-23)."""
    from tuipet.optionsscreen import OptionsPanel, SoundPanel
    from tuipet.themescreen import ThemePanel
    sp = SoundPanel(lambda: True, lambda: None)
    assert "ENTER go" not in sp.text().plain
    op = OptionsPanel(_pet(), lambda: True, lambda: None)
    assert "ENTER go" not in op.text().plain
    tp = ThemePanel(_pet())
    assert "ENTER keep" not in tp.text().plain
    assert "keep" in tp.strip()            # ...because the strip carries it


# ============ Batch 3: main view & care ======================================

# ---- C3/C4: standing buffs + the hired helper are visible at home -----------

def test_satiety_and_autoclean_wear_home_badges():
    from tuipet import statusbox
    p = _pet(world_seconds=1000.0)
    plain = " ".join(statusbox.care_deco(p))
    assert "sated" not in plain and "tidy" not in plain
    p.full_until = p.world_seconds + 2 * 3600.0
    p.auto_clean_until = p.world_seconds + 90.0
    plain = " ".join(statusbox.care_deco(p))
    assert "sated 2h" in plain and "tidy 1m" in plain
    p.world_seconds += 3 * 3600.0          # both windows expired
    plain = " ".join(statusbox.care_deco(p))
    assert "sated" not in plain and "tidy" not in plain


def test_the_hired_assistant_wears_a_home_badge():
    from tuipet import statusbox
    p = _pet()
    assert "helper" not in " ".join(statusbox.care_deco(p))
    p.set_auto_care(True)
    assert "helper" in " ".join(statusbox.care_deco(p))
    p.set_auto_care(False)
    assert "helper" not in " ".join(statusbox.care_deco(p))


# ---- C9: meat's refusal gates show BEFORE the pick --------------------------

class _CardW:
    def __init__(self):
        self.txt, self.border_subtitle = "", ""

    def update(self, t):
        self.txt = t


class _CardApp:
    def __init__(self, pet, mode):
        self.pet, self.mode, self.stats_w = pet, mode, _CardW()


def _feed_card(pet, cursor):
    from tuipet import statusbox
    pan = FeedPanel(pet)
    pan.cursor = cursor
    app = _CardApp(pet, pan)
    statusbox.feed(app)
    return app.stats_w.txt


def test_feed_card_flags_a_refusable_meat_row():
    p = _pet(sick=True)
    assert "refused — sick" in _feed_card(p, 0)
    p = _pet(poop=2)
    assert "refused — clean first" in _feed_card(p, 0)
    from tuipet.petcare import FULL_HUNGER
    p = _pet(hunger=FULL_HUNGER)
    assert "refused — belly is full" in _feed_card(p, 0)
    assert "refused" not in _feed_card(_pet(hunger=1), 0)   # feedable: no flag
    assert "refused" not in _feed_card(_pet(sick=True), 1)  # the pill row never


# ---- C8: lights-off on an exhausted pet reads as WORKING --------------------

def test_lights_off_when_exhausted_says_settling_down():
    p = _pet()
    p._set_energy(0)
    p.lights = True
    assert "settles down to rest" in p.toggle_lights()
    p.lights = False
    p.toggle_lights()                      # back on
    p._set_energy(p.max_energy)
    p.lights = True
    assert p.toggle_lights() == "Lights off."   # rested: the plain toggle


# ---- C6: space rides the gift binding ---------------------------------------

def test_space_is_a_gift_alias_on_the_home_view():
    from tuipet.app import TuiPetApp
    keys = [b[0] for b in TuiPetApp.BINDINGS if b[1] == "gift"]
    assert keys == ["enter,space"]
