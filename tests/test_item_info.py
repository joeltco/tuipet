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

⛔ CORRECTION (2026-07-14).  I first claimed attribute conversion was NOT
implemented, having grepped for `FavAttribute` (which is empty on every row) and
found nothing.  That was wrong.  The conversion is encoded as the Va/Da/Vi
DELTAS -- Board Game is Vaccine -15 / Data +15 -- and pet.py applies it through
applyAttributeChange + _compensate_attrs(), which CONSERVES the total.  So
"Vaccine to Data" is real, and the descriptions do not lie.

We still GENERATE the effect line rather than quote the description, but for the
honest reason: a generated line carries the exact numbers and can never drift
from the data behind it.  The trade now renders as the trade it is (Va→Da15)
instead of two loose nudges that happened to cancel.
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


# ---------------------------------------------------------------- the trade

TRADES = ["Board Game", "Skateboard", "Dumbbell",
          "Computer Game", "Music Player", "Television"]


@pytest.mark.parametrize("name", TRADES)
def test_the_attribute_trade_is_symmetric_and_zero_sum(name):
    """The six trade toys move points BETWEEN the power counters. Nothing is
    created: exactly one donor, one recipient, equal magnitude."""
    e = _by_name(name)
    vals = [int(e.get(k) or 0) for k in ("vaccine", "data", "virus")]
    assert sum(vals) == 0, (name, vals)
    assert len([v for v in vals if v > 0]) == 1
    assert len([v for v in vals if v < 0]) == 1


def test_the_trade_actually_converts_and_conserves_the_total():
    """The mechanic is REAL — this is the test I should have written before
    claiming it wasn't implemented."""
    board = _by_name("Board Game")
    p = Pet(num=100, stage="Champion", attribute="Vaccine",
            vaccine=30, data_power=5, virus=5, obedience=500)
    p.inventory[board["key"]] = 1
    before = p.vaccine + p.data_power + p.virus

    p.use_item(board["key"])

    assert p.vaccine == 15 and p.data_power == 20, (p.vaccine, p.data_power)
    assert p.vaccine + p.data_power + p.virus == before, "the trade must conserve the total"


def test_a_trade_reads_as_a_trade_not_two_coincidences():
    """'Va-15 Da+15' is accurate but reads like two unrelated nudges."""
    assert "Va\u2192Da15" in shop.effect_tokens(_by_name("Board Game"))
    # ...and a one-way boost must NOT be dressed up as a trade
    chip = shop.effect_tokens(_by_name("Vaccine Chip"))
    assert "Va+15" in chip and not any("\u2192" in t for t in chip)


def test_the_effect_line_is_generated_not_quoted():
    """Generated = the exact numbers, and it can never drift from the data.
    (The description is TRUE — it is just prose, and prose goes stale.)"""
    board = _by_name("Board Game")
    assert "Vaccine to Data" in board["desc"]
    line = " ".join(shop.effect_tokens(board))
    assert board["desc"] not in line


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
