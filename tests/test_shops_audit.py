"""THE SHOPS AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown shops audit next."

S1 (FIXED) — THE WAVE TEASE CHANGED BETWEEN LAUNCHES.  `wave_status`
picked the closest sealed Digimental wave with `max(set(sealed), ...)`.
That walks a SET, so when two waves tied on ratio the winner fell out of
string-hash iteration order — which Python randomises PER PROCESS.
Measured across seven `PYTHONHASHSEED` values, one identical save printed
either "wins 0/25 wake Light & Kindness" or "generation 0/5 wakes
Destiny"; 7% of sampled progress states sit on such a tie (any player at
gen 5+ with no armor evo and no wins).  A shop's character is supposed to
be STABLE — the same law that keeps a town's guest good crc32-ordered and
its daily deal fixed for the day.  Ties now break toward the NEAREST goal
(smallest `need`), which is also the more useful tease.

EVERYTHING ELSE MEASURED CLEAN, and the measurement ships as pins — the
same call as the evolution audit.  The most valuable of them is the
ANTI-PRINTER law, because that is the one an economy dies of:

  * The trade game IS profitable by design ("buy a family's exclusive ON
    DEAL, carry it to the OTHER family's towns"), and the F5 ruling
    (item sweep 2026-07-24) is what keeps it honest: a profitable flip
    must be RATIONED.  Every one of them is — pinned below.
  * I nearly "fixed" a system that was already ruled on.  All 8 chips sit
    at exactly the home flip (50% of catalog) while town DEMAND pays 70%,
    which reads like a standing money loop — until you measure the
    ration: 1-2 units per town per day, which is precisely what F5 turned
    the home deal into.  Bounded is the whole law.
  * The reachable ceiling is one town per adventure run (26 zones, one
    town each), so the "+68,170b/day perfect trader" a 26-town sweep
    suggests is not a thing a player can do.  Per visit it is +1,300 to
    +5,400b against a boss bounty of 100-3,000b — a side channel, not a
    replacement.
"""
import datetime
import os
import subprocess
import sys
import textwrap

import pytest

from tuipet import persistence, shop
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel

D = datetime.date(2026, 3, 3)          # an ordinary day
FEST = datetime.date(2026, 1, 1)       # a festival
TOWNS = sorted(range(30))
BLANK = {"album": {}, "mega_kills": 0, "max_stage": 0, "xanti_ever": False,
         "maps": set(), "wins": 0, "raids": 0, "max_gen": 1, "armor_evos": 0}


@pytest.fixture(autouse=True)
def _no_session_memory():
    """`shopscreen._LAST_POS` is MODULE-level session memory: the home
    shop reopens where you left it.  These tests park cursors on tabs no
    player would be sitting on, so without this they hand the next test a
    shop already open on Titles — which is exactly how this file first
    broke `test_shop_and_bag_cards`."""
    import tuipet.shopscreen as ss
    saved = dict(ss._LAST_POS)
    ss._LAST_POS.clear()
    yield
    ss._LAST_POS.clear()
    ss._LAST_POS.update(saved)


def _buyer(bits=10 ** 6):
    p = Pet(num=1455, stage="Champion", attribute="Vaccine", obedience=500)
    p.line_id = "ver1"
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.world_seconds = 12 * 60.0
    p.evo_blocked = True
    p.bits = bits
    return p


def _park(panel, key):
    """Put the cursor on `key` (tabs are an index, not the tab KEY)."""
    for t in range(len(panel._tabs())):
        panel.tab = t
        for i, row in enumerate(panel._rows()):
            if row.get("key") == key and not panel._is_header(row):
                panel.cursor = i
                return True
    return False


# ---- S1: the tease must not depend on the hash seed ---------------------

def test_the_wave_tease_is_the_same_in_every_process():
    """The bug, pinned the only way it can be: across REAL processes with
    different hash seeds.  A tie used to be a coin flip per launch."""
    code = (
        "from tuipet import shop\n"
        "B = {'album':{},'mega_kills':0,'max_stage':0,'xanti_ever':False,\n"
        "     'maps':set(),'wins':0,'raids':0,'max_gen':5,'armor_evos':0}\n"
        "print(shop.wave_status(B)[1])\n"
    )
    seen = set()
    for seed in ("0", "1", "2", "42", "1234"):
        env = dict(os.environ, PYTHONHASHSEED=seed,
                   PYTHONPATH=os.pathsep.join(sys.path))
        out = subprocess.run([sys.executable, "-c", code], env=env,
                             capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, out.stderr
        seen.add(out.stdout.strip())
    assert len(seen) == 1, f"the tease varied by hash seed: {seen}"


def test_a_tie_breaks_toward_the_nearest_goal():
    """Every sealed wave at ratio 0 -> the one needing the LEAST wins."""
    prog = dict(BLANK, max_gen=5)          # Destiny open; the rest tie at 0
    sealed, tease = shop.wave_status(prog)
    assert sealed
    assert "1st armor evo" in tease, tease   # need=1 beats need=25 and need=2


def test_a_clear_leader_still_wins():
    """The fix must not disturb the ordinary, untied case."""
    assert "Destiny" in shop.wave_status(dict(BLANK))[1]


# ---- the anti-printer law ----------------------------------------------

def test_every_profitable_town_flip_is_rationed():
    """THE law (F5, item sweep 2026-07-24): a flip that clears money must
    be BOUNDED.  Walk every town's every row, and for any good that
    resells above its shelf price somewhere else, prove the counter parts
    with a finite number of them in a day."""
    unbounded = []
    for tid in TOWNS:
        p = _buyer(10 ** 9)
        for row in shop.town_stock(tid, D, pet=p):
            best = max(shop.town_sell_price(row["key"], o)
                       for o in TOWNS if o != tid)
            if best <= row["price"]:
                continue                       # at-or-below water: fine
            sold = 0
            while sold < 50:
                cur = [r for r in shop.town_stock(tid, D, pet=p)
                       if r["key"] == row["key"]]
                if not cur or cur[0].get("left", 0) <= 0:
                    break
                if shop.town_buy(p, cur[0], today=D)[1] != "confirm":
                    break
                sold += 1
            if sold >= 50:
                unbounded.append((tid, row["key"]))
    assert not unbounded, f"an unrationed money loop: {unbounded}"


def test_the_ration_is_the_tier_ration():
    for key in ("gold_pill", "anti_evo_chip"):    # (omni is boss-only since 2026-10-14)
        tid = next(t for t in TOWNS
                   if any(r["key"] == key
                          for r in shop.town_stock(t, D, pet=_buyer())))
        p = _buyer(10 ** 9)
        sold = 0
        while sold < 20:
            cur = [r for r in shop.town_stock(tid, D, pet=p) if r["key"] == key]
            if not cur or cur[0].get("left", 0) <= 0:
                break
            if shop.town_buy(p, cur[0], today=D)[1] != "confirm":
                break
            sold += 1
        assert sold == shop.tier_stock(key)


def test_the_home_deal_reverts_to_full_price_and_stops_flipping():
    """F5's fix, re-measured end to end: spend the ration and the row goes
    back to full price — where no counter in the game pays more."""
    p = _buyer(10 ** 9)
    deal = [r for r in shop.home_stock(today=D, pet=p) if r.get("deal")][0]
    key, ration = deal["key"], deal["left"]
    assert ration == shop.tier_stock(key)
    for _ in range(ration):
        cur = [r for r in shop.home_stock(today=D, pet=p) if r["key"] == key][0]
        assert shop.town_buy(p, cur, today=D)[1] == "confirm"
    after = [r for r in shop.home_stock(today=D, pet=p) if r["key"] == key][0]
    assert not after.get("deal") and after.get("deal_spent")
    assert after["price"] == shop.entry(key)["price"]
    assert max(shop.town_sell_price(key, t) for t in TOWNS) <= after["price"]


def test_the_mash_guard_eats_the_first_full_price_press():
    """A spent ration is not a shut door — but a mash must not pay 2x by
    accident (the bag's `_retarget` grammar, F5)."""
    p = _buyer()
    panel = ShopPanel(p)
    key = shop.home_deal_key()
    assert _park(panel, key)
    ration, full = shop.tier_stock(key), shop.entry(key)["price"]
    spend = []
    for _ in range(ration + 2):
        before = p.bits
        panel.key("enter")
        spend.append(before - p.bits)
    assert spend[:ration] == [shop.deal_price(full)] * ration
    assert spend[ration] == 0              # the guard press costs nothing
    assert spend[ration + 1] == full       # and the next one is honest


def test_the_bag_retarget_guard_survives_a_mashed_sell():
    q = _buyer(bits=0)
    for k in ("steak", "steak", "cookie"):
        q.add_item(k)
    panel = ShopPanel(q, start_mode="bag")
    assert _park(panel, "steak")
    gains = []
    for _ in range(4):
        before = q.bits
        panel.key("r")
        gains.append(q.bits - before)
    assert gains[2] == 0, "the cursor shifted onto Cookie and sold it unasked"


# ---- the gates ----------------------------------------------------------

@pytest.mark.parametrize("maps,expected", [
    (0, set()), (1, {"shortcut"}),
    (2, {"shortcut", "rest_kit", "life_recovery"}),
])
def test_the_adventure_gate_opens_exactly_on_its_threshold(monkeypatch, maps,
                                                           expected):
    monkeypatch.setattr(persistence, "get_progress",
                        lambda: dict(BLANK, maps=set(range(maps))))
    on = {r["key"] for r in shop.home_stock(today=D, pet=_buyer())}
    assert on & set(shop.ADVENTURE_GATES) == expected


def test_a_sealed_digimental_reaches_no_shelf(monkeypatch):
    monkeypatch.setattr(persistence, "get_progress", lambda: dict(BLANK))
    sealed = {k for k in shop.DIGIMENTAL_GATES
              if not shop.digimental_open(k, BLANK)}
    assert sealed
    assert not sealed & {e["key"] for e in shop.catalog()}
    # ...but the bag can still render one you already own
    assert shop.entry(sorted(sealed)[0])


def test_every_priced_good_is_sold_somewhere(monkeypatch):
    monkeypatch.setattr(persistence, "get_progress",
                        lambda: dict(BLANK, maps=set(range(9))))
    seen = set()
    for tid in TOWNS:
        seen |= {r["key"] for r in shop.town_stock(tid, D, pet=_buyer())}
    for d in range(40):
        seen |= {r["key"] for r in shop.home_stock(
            today=D + datetime.timedelta(days=d), pet=_buyer())}
    priced = {k for k, v in shop.CATALOG.items() if v.price is not None}
    assert priced - seen == set(), "a priced good nobody sells"


# ---- the authored tables ------------------------------------------------

def test_every_authored_key_resolves():
    """A table naming a key the catalog lost is a row that silently
    vanishes from a shelf."""
    assert not set(shop._ROAD_ONLY) - set(shop.CATALOG)
    assert not set(shop.ADVENTURE_GATES) - set(shop.CATALOG)
    assert not set(shop._OWN_FLOW) - set(shop.CATALOG)
    assert not set(shop.LEGACY_KEYS.values()) - set(shop.CATALOG)


def test_every_catalog_entry_is_well_formed():
    for key, v in shop.CATALOG.items():
        assert v.name and v.icon and v.category and v.effect, key
        assert v.where in ("home", "road"), key
        assert v.price is None or v.price > 0, key
        assert v.category in shop.CATEGORY_ORDER, key


# ---- the ledger ---------------------------------------------------------

def test_the_daily_ledger_is_per_town():
    p = _buyer(10 ** 9)
    t0, t1 = TOWNS[0], TOWNS[1]
    row = [r for r in shop.town_stock(t0, D, pet=p) if r.get("left", 0) > 0][0]
    key = row["key"]
    for _ in range(row["left"]):
        cur = [r for r in shop.town_stock(t0, D, pet=p) if r["key"] == key][0]
        shop.town_buy(p, cur, today=D)
    assert [r for r in shop.town_stock(t0, D, pet=p)
            if r["key"] == key][0]["left"] == 0
    other = [r for r in shop.town_stock(t1, D, pet=p) if r["key"] == key]
    if other:                              # only if that town stocks it too
        assert other[0]["left"] > 0, "one town's ledger emptied another's shelf"


def test_the_ledger_survives_a_save_and_sweeps_at_midnight():
    p = _buyer(10 ** 9)
    deal = [r for r in shop.home_stock(today=D, pet=p) if r.get("deal")][0]
    for _ in range(deal["left"]):
        cur = [r for r in shop.home_stock(today=D, pet=p)
               if r["key"] == deal["key"]][0]
        shop.town_buy(p, cur, today=D)
    q, _msg = persistence.pet_from_save(persistence.to_save_dict(p))
    assert q.town_bought == p.town_bought
    assert not [r for r in shop.home_stock(today=D, pet=q)
                if r["key"] == deal["key"]][0].get("deal")
    tomorrow = D + datetime.timedelta(days=1)
    fresh = [r for r in shop.home_stock(today=tomorrow, pet=q)
             if r.get("deal")]
    assert fresh and fresh[0]["left"] == shop.tier_stock(fresh[0]["key"])


# ---- the deal rotation --------------------------------------------------

def test_a_town_runs_one_deal_a_day_and_never_the_same_one_twice():
    for tid in TOWNS[:6]:
        prev = None
        for d in range(120):
            day = D + datetime.timedelta(days=d)
            deals = [r for r in shop.town_stock(tid, day, pet=_buyer())
                     if r.get("deal")]
            if len(deals) > 1:
                continue                   # a festival puts the counter on sale
            assert len(deals) == 1
            assert deals[0]["key"] != prev
            prev = deals[0]["key"]


def test_a_deal_is_always_half():
    for tid in TOWNS[:8]:
        for r in shop.town_stock(tid, D, pet=_buyer()):
            if r.get("deal"):
                assert r["price"] == shop.deal_price(r["base_price"])


def test_a_festival_puts_the_whole_counter_on_sale():
    """Every EVERYDAY good is on sale on a festival; progression goods never
    are (shop/loot audit 2026-10-14)."""
    rows = shop.town_stock(TOWNS[0], FEST, pet=_buyer())
    assert rows and all(bool(r.get("deal")) == shop.deal_ok(r["key"]) for r in rows)


# ---- the egg market -----------------------------------------------------

def test_the_egg_bands_cover_every_earnable_digitama():
    pool = set(shop._sellable_eggs())
    covered = set()
    for t in TOWNS:
        band = shop.town_egg_stock(t)
        assert len(set(band)) == len(band), f"town {t} stocks a dupe"
        covered |= set(band)
    assert covered == pool


def test_no_two_towns_sell_an_identical_egg_band():
    bands = {tuple(shop.town_egg_stock(t)) for t in TOWNS}
    assert len(bands) == len(TOWNS)


def test_an_egg_is_bought_once_and_costs_real_bits():
    p = _buyer(bits=30000)
    idx = shop.town_egg_stock(TOWNS[0])[0]
    msg, sfx = shop.town_egg_buy(p, idx)
    assert sfx == "reward" and p.bits == 30000 - shop.egg_price(idx)
    assert shop.town_egg_buy(p, idx)[1] == "error"     # already owned
    # one egg a day across every counter (shop/loot audit 2026-10-14)
    other = next(i for i in shop.town_egg_stock(TOWNS[1]) if i != idx)
    assert shop.town_egg_buy(p, other)[1] == "error" and p.bits == 30000 - shop.egg_price(idx)
    broke = _buyer(bits=10)
    assert shop.town_egg_buy(broke, shop.town_egg_stock(TOWNS[1])[0])[1] == "error"
    assert broke.bits == 10


def test_an_egg_row_cannot_be_flipped_through_the_item_sell_path():
    row = dict(shop.town_egg_rows(TOWNS[0])[0])
    p = _buyer(bits=0)
    assert shop.sell(p, row)[1] == "error"
    assert p.bits == 0


# ---- the purse ----------------------------------------------------------

def test_the_purse_never_goes_negative_or_pays_for_nothing():
    row = [e for e in shop.home_stock(today=D, pet=_buyer())
           if not e.get("deal")][0]
    exact = _buyer(bits=row["price"])
    assert shop.buy(exact, row)[1] == "confirm" and exact.bits == 0
    short = _buyer(bits=row["price"] - 1)
    assert shop.buy(short, row)[1] == "error"
    assert short.bits == row["price"] - 1
    empty = _buyer(bits=100)
    assert shop.sell(empty, {"key": "steak", "name": "Steak"})[1] == "error"
    assert empty.bits == 100


# ---- the panels ---------------------------------------------------------

@pytest.mark.parametrize("kind", ["home", "bag", "town", "town-egg", "full-bag"])
def test_every_shop_panel_renders_inside_the_lcd(kind):
    from rich.text import Text

    from tuipet import grid
    from tuipet.towneggscreen import TownEggPanel
    p = _buyer()
    if kind == "home":
        panel = ShopPanel(p)
    elif kind == "bag":
        panel = ShopPanel(p, bag_only=True)
    elif kind == "town":
        panel = ShopPanel(p, town_id=4)
    elif kind == "town-egg":
        panel = TownEggPanel(p, town_id=0)
    else:
        for k in shop.CATALOG:
            p.add_item(k)
        panel = ShopPanel(p, start_mode="bag")
    for key in ("down", "down", "right", "enter", "tab", "down", "s", "r",
                "up", "left", "escape"):
        body = str(panel.text()).split("\n")
        assert len(body) <= grid.ROWS, f"{kind}: {len(body)} rows"
        for line in body:
            assert len(Text.from_markup(line).plain) <= grid.COLS, \
                f"{kind}: {line!r}"
        panel.strip()
        panel.key(key)


def test_every_dossier_fits_its_four_rows():
    """The info block holds exactly four 26-column rows — and the effect
    text has to SURVIVE that budget, not be silently clipped."""
    p = _buyer()
    for k in shop.CATALOG:
        p.add_item(k)
    panel = ShopPanel(p)
    for mode in ("shop", "bag"):
        panel.mode = mode
        for key in shop.CATALOG:
            e = dict(shop.entry(key), key=key, count=1)
            rows = panel._info(e, 26)
            assert len(rows) == 4, key
            assert all(len(str(r)) <= 26 for r in rows), key
            assert len(textwrap.wrap(shop.effect_line(e), 26)) <= 2, key


def test_fish_says_why_it_beats_free_meat():
    """First-5 audit #10 (2026-10-16): Fish cost 50b and read 'hunger +1' --
    the same as free Meat -- so newcomers saw no reason to buy it.  Its real
    edge (no weight gain; Meat adds 2g) is now on the shelf."""
    from tuipet import shop
    line = shop.effect_line({"key": "fish", "category": "Feed"})
    assert "no weight gain" in line and "Meat" in line
