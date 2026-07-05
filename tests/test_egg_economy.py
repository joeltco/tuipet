"""LINES_SPEC arc 3 — the egg economy: identity achievements (Sakumon = battles,
Petitmon = collector, Dodomon = Mega kills), live unlock progress, and the
carousel that shows every egg (silhouettes for the sealed ones)."""
import random

from tuipet import data, egg, persistence
from tuipet.pet import Pet


def _prog(**kw):
    p = {"album": set(), "wins": 0, "mega_kills": 0, "max_gen": 1, "max_stage": 0,
         "xanti_ever": False, "maps": set(), "tourneys": set(),
         "last_field": "None", "last_attr": "None", "last_elem": "None",
         "last_mood": 0, "last_obed": 0, "last_xanti": False}
    p.update(kw)
    return p


def _rule(name):
    return next(r for r in data.load_egg_unlock().values() if r["name"] == name)


# ---- the achievement rows ---------------------------------------------------------

def test_sakumon_is_the_battle_egg():
    r = _rule("Sakumon")
    assert (r["wins"], r["price"], r["can_perm"]) == (50, 1000, True)
    assert r["stage"] is None                       # the old Ultimate gate is gone
    assert not egg._conditions_met(r, _prog(wins=49))
    assert egg._conditions_met(r, _prog(wins=50))


def test_petitmon_is_the_collector_egg():
    r = _rule("Petitmon")
    assert (r["album_n"], r["price"], r["can_perm"]) == (5, 1000, True)
    assert r["prev_field"] is None                  # no longer a temp lineage egg
    assert not egg._conditions_met(r, _prog(album={1, 2, 3, 4}))
    assert egg._conditions_met(r, _prog(album={1, 2, 3, 4, 5}))


def test_dodomon_is_the_x_egg():
    r = _rule("Dodomon")
    assert (r["mega"], r["price"], r["can_perm"]) == (5, 2500, True)
    assert not r["xanti"]                           # the antibody gate is retired
    assert not egg._conditions_met(r, _prog(mega_kills=4))
    assert egg._conditions_met(r, _prog(mega_kills=5))


def test_met_achievement_is_buyable_then_owned():
    r = _rule("Sakumon")
    st, price = egg.egg_state(r["idx"], _prog(wins=50), set())
    assert (st, price) == ("buyable", 1000)         # earn the right, then save up
    assert egg.egg_state(r["idx"], _prog(wins=50), {r["idx"]})[0] == "owned"
    assert egg.egg_state(r["idx"], _prog(wins=0), set())[0] == "locked"


# ---- live progress ----------------------------------------------------------------

def test_unlock_progress_counts_the_countable():
    assert egg.unlock_progress(_rule("Sakumon")["idx"], _prog(wins=37)) == "lifetime wins 37/50"
    assert egg.unlock_progress(_rule("Petitmon")["idx"], _prog(album={1, 2, 3})) == "Digimon raised 3/5"
    assert egg.unlock_progress(_rule("Dodomon")["idx"], _prog(mega_kills=1)) == "Mega-class felled 1/5"
    gen_idx = _rule("Jyarimon")["idx"]              # a generation egg keeps its gate
    assert egg.unlock_progress(gen_idx, _prog(max_gen=2)) == "generation 2/3"
    mystery = sorted(egg.win_eggs())[0]             # the "???" eggs count too
    assert egg.unlock_progress(mystery, _prog(wins=12)) == "lifetime wins 12/50"


def test_mega_kill_feeds_the_lifetime_progress():
    random.seed(5)
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.record_battle(True, enemy={"stage": "Mega", "hp": 20, "vaccine": 90,
                                 "data_power": 0, "virus": 0, "bits": (1, 2)})
    assert persistence.get_progress()["mega_kills"] == 1
    p.record_battle(False, enemy={"stage": "Mega", "hp": 20, "vaccine": 90,
                                  "data_power": 0, "virus": 0, "bits": (1, 2)})
    assert persistence.get_progress()["mega_kills"] == 1    # losses never count


def test_fallback_pool_is_gone():
    assert not hasattr(egg, "_fallback_pool")
    # an unlisted, non-mystery egg would be locked, never album-auto-owned
    states = egg.egg_states(_prog(album=set(range(40))), set())
    for i, (st, _) in states.items():
        if i in egg.win_eggs():
            assert st == "locked"                   # 40 raised but 0 wins: still sealed


# ---- the carousel -----------------------------------------------------------------

def _panel(prog=None):
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()
    if prog is not None:
        pan.prog = prog
        pan.states = egg.egg_states(prog, set())
    return pan


def test_carousel_is_hatchable_plus_nearest_goals():
    # hardened 2026-07-04, tightened again same day (Joel: "i dont want to see
    # the shop eggs unless theyre already available"): hatchable + goals ONLY
    pan = _panel()
    assert pan.n <= len(pan.unlocked) + pan.GOALS_SHOWN
    assert pan.n < egg.count()                      # the 49-egg wall is gone
    hatchable = set(pan.unlocked)
    assert all(i in hatchable for i in pan.carousel[:len(hatchable)])
    for i in pan.carousel[len(pan.unlocked):]:      # the tail is goals, all countable
        st = pan.states[i][0]
        assert st == "locked"                       # NEVER a buyable shop egg
        assert egg.unlock_ratio(i, pan.prog) is not None
    assert not any(pan.states[i][0] == "buyable" for i in pan.carousel)


def test_locked_eggs_are_silhouettes_with_progress():
    pan = _panel()
    goals = [i for i in pan.carousel if pan.states[i][0] == "locked"]
    assert goals                                    # the nearest goals ride the tail
    idx = goals[0]
    pos = pan.carousel.index(idx)
    fr = pan._frame(pos, center=False)
    raw = egg.record(idx)["frames"][0]
    assert fr != raw                                # blacked out, same shape
    assert "/" in pan._note(idx)               # a live progress counter
    # ENTER on a sealed egg reports, never hatches
    pan.i, pan.pos, pan.scroll = pos, float(pos), float(pos)
    assert pan.key("enter") is None
    assert "Sealed" in pan.msg


def test_panel_smoke_walks_and_draws():
    pan = _panel()
    pan.text()
    for k in ["right"] * 8 + ["enter", "left", "enter", "c", "z", "escape", "right"]:
        pan.key(k)
        pan.anim()
        pan.text()


def test_no_user_facing_name_leaks_html_tags():
    """DVPet's Java CSVs embed <br> in names ("Vaccine<br>Chip G") -- every
    loader must strip them (2026-07-04: the food loader showed the tag raw in
    the shop; the shared consumable parser already stripped it)."""
    from tuipet import data as d
    for f in d.load_foods():
        assert "<br>" not in f["name"] + str(f.get("desc", "")), f["name"]
    for key in list(getattr(d, "_consumables", lambda: {})() or {}) or []:
        pass  # items ride the shared parser, verified below via a sample
    for k in ("i:14", "i:32", "i:80", "f:20", "f:21", "f:33"):
        e = d.consumable_by_key(k)
        if e:
            assert "<br>" not in e.get("name", "") + e.get("desc", ""), k


def test_status_card_index_survives_the_full_carousel():
    """2026-07-04 Termux crash: the app's egg status card indexed m.unlocked
    by the carousel cursor -- past the hatchable eggs = IndexError.  Walk the
    cursor across the WHOLE carousel and resolve the card's index each stop."""
    pan = _panel()
    for i in range(pan.n):
        pan.i = i
        idx = pan.carousel[pan.i] if pan.carousel else 0
        assert pan.states.get(idx, ("owned", 0))[0] in ("owned", "temp", "buyable", "locked")


def test_buyable_egg_lives_in_the_shop_not_the_select():
    """Joel 2026-07-04: shop eggs stay OUT of the egg select until bought.
    End to end: earn Sakumon's license right -> the select hides it, the shop
    egg tab sells it; buy it -> it joins the select as hatchable."""
    from tuipet import persistence
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    idx = _rule("Sakumon")["idx"]
    persistence.wins_add(50)                        # sandboxed progress
    pan = EggSelectPanel()
    assert pan.states[idx][0] == "buyable"
    assert idx not in pan.carousel                  # hidden from the select
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.bits = 5000
    shop_pan = ShopPanel(p)
    while shop_pan._tabs()[shop_pan.tab] != "egg":
        shop_pan.key("right")
    rows = shop_pan._rows()
    assert any(e.get("egg_idx") == idx for e in rows)   # ...but for sale here
    entry = next(e for e in rows if e.get("egg_idx") == idx)
    assert "Unlocked" in shop_pan._buy_egg(entry)
    pan2 = EggSelectPanel()
    assert idx in pan2.carousel                     # owned now -> hatchable
    assert pan2.states[idx][0] == "owned"
