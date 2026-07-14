"""Item info tells the whole truth (item-info audit 2026-07-14).

Joel: "do items have descriptions in shops and inventory" — they did not, and the
computed effect line was HIDING real consequences:

  * LIFESPAN.  Consumables carry `Seconds`, applied as `lifespan += seconds/60`
    real seconds (pet.py).  One real second is one game minute, so it lands as
    seconds/3600 GAME HOURS.  Miracle Drink costs -6h of your pet's life, Vitamin
    -1h, and the Gold Pill BUYS +12h — its entire reason to exist.  None of it
    appeared in the shop, the bag, or the feed page.
  * THE LAPSE ITEMS.  Med's `Cured` flag is FALSE; it works by shortening the
    illness (cure_lapse -2).  So "basic medicine to treat illness" displayed as,
    simply, "mood-10".

⛔ We deliberately do NOT render the authored `Description` column.  A dozen of
them advertise attribute conversion ("Board Game: Vaccine to Data") — a mechanic
tuipet does not implement.  Showing that text would have the shop make a promise
the game does not keep, which is the exact bug class the silent-failure law
exists to kill.  The effect line is GENERATED from the fields pet.py actually
reads, so it structurally cannot lie.
"""
import pytest

from tuipet import data, shop
from tuipet.pet import Pet

TW = 26          # menu.W - IC_W - 2: the info column beside the icon
ROWS = 2         # rows the effects get


def _all_consumables():
    out = []
    for pre in ("f", "i"):
        for i in range(250):
            e = data.consumable_by_key(f"{pre}:{i}")
            if e:
                out.append(e)
    return out


def _by_name(nm):
    e = next((c for c in _all_consumables() if c["name"] == nm), None)
    assert e, f"{nm} vanished from the data"
    return e


# ---------------------------------------------------------------- no truncation

def test_every_consumable_fits_without_silent_truncation():
    """Truncating the effect line is HOW the lifespan cost stayed invisible."""
    for e in _all_consumables():
        lines = shop.effect_lines(e, TW, ROWS)
        used = [ln for ln in lines if ln]
        assert len(used) <= ROWS, f"{e['name']} needs {len(used)} lines: {used}"
        for ln in used:
            assert len(ln) <= TW, f"{e['name']} overflows {TW} cols: {ln!r}"
        # nothing may be dropped on the floor.  An item with NO effects at all
        # (key items like the Digimentals) renders the "-" placeholder instead.
        toks = shop.effect_tokens(e)
        assert " ".join(used).split() == (toks or ["-"]), e["name"]


# ---------------------------------------------------------------- lifespan

@pytest.mark.parametrize("name,token", [
    ("Miracle Drink", "LIFE-6h"),     # Seconds -21600
    ("Gold Pill", "LIFE+12h"),        # Seconds +43200 — the whole point of the item
    ("Vitamin", "LIFE-1h"),           # Seconds  -3600
])
def test_lifespan_is_advertised(name, token):
    toks = shop.effect_tokens(_by_name(name))
    assert token in toks, f"{name} hides its lifespan effect: {toks}"
    assert toks[0] == token, "the costly one leads the line"


def test_a_trivial_lifespan_nudge_is_not_noise():
    """The toys carry Seconds=60 (+1 game-minute). That rounds to zero hours and
    is dropped, like any other stat that rounds away."""
    ball = _by_name("Ball")
    assert int(ball.get("seconds") or 0) == 60
    assert not any(t.startswith("LIFE") for t in shop.effect_tokens(ball))


# ---------------------------------------------------------------- the lapse items

def test_med_advertises_that_it_treats_illness():
    """Med's Cured flag is FALSE — it SHORTENS the illness (cure_lapse -2), and
    the shelf used to describe it as 'mood-10' and nothing else."""
    med = _by_name("Med")
    assert not med.get("cured")                 # the flag really is False
    assert int(med["cure_lapse"]) == -2
    assert "sick-2" in shop.effect_tokens(med), "Med hides its whole purpose"


# ---------------------------------------------------------------- never lie

def test_we_never_render_the_authored_description():
    """~12 descriptions promise attribute conversion, which tuipet does not
    implement. The effect line must be GENERATED, never quoted."""
    board = _by_name("Board Game")
    assert "Vaccine to Data" in board["desc"]           # the data really says it
    line = " ".join(shop.effect_tokens(board))
    assert "Vaccine to" not in line, "the shop is promising a mechanic we don't have"


# ---------------------------------------------------------------- all 3 surfaces

def test_shop_bag_and_feed_all_tell_the_same_story():
    """Vitamin costs an hour of life. Every surface that offers it must say so."""
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    vit = dict(_by_name("Vitamin"))
    vit["stock"] = 2
    p.inventory[vit["key"]] = 3

    shelf = " ".join(shop.slot_info(p, vit, TW))
    bag = " ".join(shop.sell_info(p, vit, TW))
    from tuipet.feedscreen import _effect_line
    feed = _effect_line(vit)

    for surface, text in (("shop", shelf), ("bag", bag), ("feed", feed)):
        assert "LIFE-1h" in text, f"the {surface} hides Vitamin's lifespan cost: {text!r}"
