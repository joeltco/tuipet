"""The Spirit shelf (2026-07-18): the ten Legendary Warrior spirit pairs,
sold beside the crest eggs on the clone's own Armor-Spirit shelf, opening
the corpus's dormant Frontier family (items 43-52 Human, 53-62 Beast, in
the canon element order).  A Beast form slides back to its Human form via
the digicore mode change; the one missing reversion edge (Bolgmon ->
Blitzmon, the audit's "NO BASE" row) is grafted in load_evolutions.
"""
import random

from tuipet import data, shop
from tuipet.pet import Pet


def _by_name(name):
    _, by = data.load_sprites()
    return next(n for n, r in by.items()
                if r["name"] == name and not data.is_placeholder(n))


def _fit(p):
    p.energy = p.max_energy
    p.battles, p.wins = p.battles + 20, p.wins + 16
    p.levels_fought = [3, 4, 5] * 3
    p.care_mistakes = 0


def _rookie(name):
    n = _by_name(name)
    _, by = data.load_sprites()
    p = Pet(num=n, stage="Rookie", attribute=by[n]["attribute"], obedience=500)
    p.world_seconds = 600.0
    _fit(p)
    return p


def test_twenty_spirits_on_the_armor_shelf():
    rows = [e for e in shop.catalog() if e["category"] == "Armor-Spirit"]
    spirits = [e for e in rows if e["key"].startswith("spirit_")]
    assert len(spirits) == 20
    assert len(rows) == 31                        # 11 crest eggs + 20 spirits
    h = [e for e in spirits if e["key"].endswith("_h")]
    b = [e for e in spirits if e["key"].endswith("_b")]
    assert len(h) == len(b) == 10
    assert all(e["price"] == 1500 for e in h)
    assert all(e["price"] == 3000 for e in b)


def test_the_spirit_map_is_the_canon_element_order():
    ids = Pet._SPIRIT_IDS
    assert ids["spirit_flame_h"] == 43 and ids["spirit_darkness_h"] == 52
    assert ids["spirit_flame_b"] == 53 and ids["spirit_darkness_b"] == 62
    assert len(ids) == 20


def test_the_full_frontier_loop():
    """Rookie -> Human spirit -> Beast spirit -> mode slide-back, on Flame
    AND on Thunder (whose reversion edge the audit found missing)."""
    for rookie, el, h_form, b_form in (("Agumon", "flame", "Agunimon", "Vritramon"),
                                       ("Elecmon", "thunder", "Blitzmon", "Bolgmon")):
        random.seed(7)
        p = _rookie(rookie)
        p.add_item(f"spirit_{el}_h")
        out = p.use_item(f"spirit_{el}_h")
        assert "spirit-evolved" in out
        assert data.record_for(p.num)["name"] == h_form
        _fit(p)
        p.add_item(f"spirit_{el}_b")
        assert "spirit-evolved" in p.use_item(f"spirit_{el}_b")
        assert data.record_for(p.num)["name"] == b_form
        _fit(p)
        _old, _msg = p.mode_change()
        assert data.record_for(p.num)["name"] == h_form   # the slide-back


def test_the_beast_spirit_is_a_gate_not_a_bypass():
    """The corpus's own design: Human spirits are entry-tier, but the BEAST
    row judges (Vritramon wants foes >=lv2 fought as the hybrid).  An
    unfought Agunimon holds the Beast spirit and nothing happens; a refusal
    keeps the item."""
    import random
    random.seed(7)
    p = _rookie("Agumon")
    p.add_item("spirit_flame_h")
    p.use_item("spirit_flame_h")
    assert data.record_for(p.num)["name"] == "Agunimon"
    p.energy = p.max_energy                        # rested but UNFOUGHT
    p.add_item("spirit_flame_b")
    out = p.use_item("spirit_flame_b")
    assert "can't" in out
    assert data.record_for(p.num)["name"] == "Agunimon"
    assert p.inventory.get("spirit_flame_b") == 1  # a refusal keeps the item


def test_the_bolgmon_reversion_edge_is_grafted():
    assert 1119 in data.load_evolutions().get(1129, [])
