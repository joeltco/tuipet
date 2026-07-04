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


def test_every_egg_rides_the_carousel():
    pan = _panel()
    assert pan.n == egg.count()                     # hatchable + buyable + locked = all
    hatchable = set(pan.unlocked)
    assert all(i in hatchable for i in pan.carousel[:len(hatchable)])


def test_locked_eggs_are_silhouettes_with_progress():
    pan = _panel()
    locked = [i for i, (s, _) in pan.states.items() if s == "locked"]
    idx = _rule("Sakumon")["idx"]
    assert idx in locked
    pos = pan.carousel.index(idx)
    fr = pan._frame(pos, center=False)
    raw = egg.record(idx)["frames"][0]
    assert fr != raw                                # blacked out, same shape
    assert "lifetime wins 0/50" in pan._note(idx)
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
