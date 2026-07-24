"""FESTIVAL GIFTS — the present is a surprise now (2026-07-24).

Joel: "wire up the festival gifts... presents should be just that, a
surprise... make these items actually work".

Three changes:
  * the gift POOL is a tier-weighted surprise from the whole giftable
    catalog, not four fixed treats -- and it "works" because it reaches
    real items, capped so a free gift is never a trap or a premium;
  * a FESTIVAL pet gifts ~3x as often and reaches one tier higher;
  * the present is WRAPPED -- the contents stay hidden behind the box on
    the amble and the reveal message opens it at the end.
"""
import collections
import random

from tuipet import shop
from tuipet.pet import Pet
from tuipet.petbase import GIFT_FESTIVAL_MULT

BANNED = {"poison_mushroom", "digimemory", "revive_floppy",
          "town_transport", "disaster_transport", "life_recovery"}


def _pet(**kw):
    return Pet(num=100, stage="Champion", attribute="Vaccine", **kw)


def _draw(festival, n=3000):
    p = _pet()
    random.seed(2)
    return collections.Counter(p._pick_gift(festival=festival) for _ in range(n))


# ---- the surprise pool ------------------------------------------------------

def test_the_gift_pool_is_a_wide_surprise_not_four_items():
    everyday = _draw(False)
    assert len(everyday) >= 15, "the pool must be a genuine surprise"


def test_a_gift_is_never_a_trap_road_tool_or_heirloom():
    for fest in (False, True):
        for k in _draw(fest):
            assert k not in BANNED, k


def test_everyday_gifts_top_out_at_uncommon():
    hi = max(shop.TIER_ORDER.index(shop.CATALOG[k].tier or "common")
             for k in _draw(False))
    assert shop.TIER_ORDER[hi] == "uncommon"


def test_festival_gifts_reach_the_rare_tier():
    hi = max(shop.TIER_ORDER.index(shop.CATALOG[k].tier or "common")
             for k in _draw(True))
    assert shop.TIER_ORDER[hi] == "rare"


def test_no_gift_is_ever_legendary():
    for fest in (False, True):
        for k in _draw(fest):
            assert shop.CATALOG[k].tier != "legendary", k


def test_common_treats_are_the_usual_gift():
    """Tier-weighted: a common gift is far likelier than a rare one, so a
    good pull stays a treat."""
    c = _draw(True)
    common = sum(n for k, n in c.items()
                 if (shop.CATALOG[k].tier or "common") == "common")
    rare = sum(n for k, n in c.items() if shop.CATALOG[k].tier == "rare")
    assert common > rare * 2


# ---- the festival frequency boost -------------------------------------------

def test_a_festival_pet_gifts_far_more_often():
    import tuipet.tournament as T

    def hits(hol):
        T.holiday = lambda today=None, h=hol: h
        n = 0
        random.seed(5)
        for _ in range(8000):
            q = _pet(obedience=75)
            q.gift_t = 999.0
            q._check_gift_call(1.0)
            if q.gift:
                n += 1
        return n

    orig = T.holiday
    try:
        plain, fest = hits(None), hits("Christmas Festival")
    finally:
        T.holiday = orig
    assert fest > plain * 2, (plain, fest)          # ~GIFT_FESTIVAL_MULT more
    assert GIFT_FESTIVAL_MULT == 3


# ---- the wrapped-present surprise -------------------------------------------

def test_the_gift_fx_carries_the_present_box_not_the_item():
    from tuipet import arenafx, grid
    from tuipet.arenafx import _FxCtx, GIFT_OUT

    class Host(arenafx.FxMixin):
        def __init__(self):
            self.fx = None
            self.frame_i = 0
            self.roamer = 0

        def update(self, *a, **k):
            pass

        def _pose_rows(self, pet, k, s):
            return ["1" * 8] * 8

        def _pose_rows_idx(self, pet, i):
            return ["1" * 8] * 8

    h = Host()
    p = _pet()
    h.start_fx("gift", icon="miracle_drink")     # even a "big" icon shows as a box
    drew = False
    for step in range(h.fx["steps"]):
        c = _FxCtx()
        c.rows, c.overlay, c.free = [], [], []
        c.xshift = c.yshift = 0
        c.px_h = grid.PXH
        c.bg = c.bgimg = None
        c.mirror = False
        h._fxk_gift(p, h.fx, step, c)
        if step >= GIFT_OUT and c.overlay:
            drew = True
    assert drew, "the present box never rode the return leg"


def test_the_reveal_is_deferred_to_the_end_of_the_amble():
    """action_gift teases first and stores the reveal; the app fires it only
    once the fx finishes -- so the contents are a genuine surprise."""
    import inspect
    from tuipet import appactions, app
    a = inspect.getsource(appactions.ActionsMixin.action_gift)
    assert "_pending_gift_reveal" in a
    assert "Let's see" in a or "see what" in a          # the tease
    assert "_pending_gift_reveal" in inspect.getsource(app)


def test_claiming_still_banks_the_item_and_clears_the_gift():
    p = _pet()
    p.gift = "cake"
    msg = p.claim_gift()
    assert "cake" in msg.lower() or "Cake" in msg
    assert p.inventory.get("cake") == 1
    assert p.gift == ""
