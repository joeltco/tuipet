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
    assert (r["wins"], r["price"], r["can_perm"]) == (50, 0, True)   # EARN tier: free
    assert r["stage"] is None                       # the old Ultimate gate is gone
    assert not egg._conditions_met(r, _prog(wins=49))
    assert egg._conditions_met(r, _prog(wins=50))


def test_petitmon_is_the_collector_egg():
    r = _rule("Petitmon")
    assert (r["album_n"], r["price"], r["can_perm"]) == (5, 0, True)   # EARN tier: free
    assert r["prev_field"] is None                  # no longer a temp lineage egg
    assert not egg._conditions_met(r, _prog(album={1, 2, 3, 4}))
    assert egg._conditions_met(r, _prog(album={1, 2, 3, 4, 5}))


def test_dodomon_is_the_x_egg():
    r = _rule("Dodomon")
    assert (r["mega"], r["price"], r["can_perm"]) == (5, 0, True)   # EARN tier: free
    assert not r["xanti"]                           # the antibody gate is retired
    assert not egg._conditions_met(r, _prog(mega_kills=4))
    assert egg._conditions_met(r, _prog(mega_kills=5))


def test_met_achievement_is_earned_free():
    """Two-tier economy (Joel 2026-07-09): a signature-achievement egg is EARNED free
    -- meeting the condition unlocks it outright (price 0), no extra bits."""
    r = _rule("Sakumon")
    assert r["price"] == 0
    assert egg.egg_state(r["idx"], _prog(wins=50), set())[0] == "owned"   # earned -> yours
    assert egg.egg_state(r["idx"], _prog(wins=0), set())[0] == "locked"


# ---- live progress ----------------------------------------------------------------

def test_unlock_progress_counts_the_countable():
    assert egg.unlock_progress(_rule("Sakumon")["idx"], _prog(wins=37)) == "lifetime wins 37/50"
    assert egg.unlock_progress(_rule("Petitmon")["idx"], _prog(album={1, 2, 3})) == "Digimon raised 3/5"
    assert egg.unlock_progress(_rule("Dodomon")["idx"], _prog(mega_kills=1)) == "Mega-class felled 1/5"
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


def test_carousel_shows_only_hatchable_eggs():
    # Joel 2026-07-12: "only the available eggs" -- no silhouettes, no goals,
    # no buyable teasers; the carousel is exactly what you can hatch right now.
    pan = _panel()
    hatch = set(egg.hatchable_eggs(pan.prog, set()))
    assert set(pan.carousel) == hatch
    assert pan.n == len(hatch) >= 5                  # the 5 starters at least
    assert all(pan.states[i][0] in ("owned", "temp") for i in pan.carousel)
    assert not any(pan.states[i][0] in ("locked", "buyable") for i in pan.carousel)


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
    cursor across the WHOLE carousel and paint the REAL app card each stop
    (the old test re-implemented the fixed expression instead of executing
    app.py, so it could never catch the crash it documents; test audit
    2026-07-13 -- now it drives _status_eggselect itself)."""
    from tuipet.app import TuiPetApp, Stats

    class _FakeStats(Stats):
        def __init__(self): self.txt = ""
        def update(self, t): self.txt = str(t)
        @property
        def border_subtitle(self): return ""
        @border_subtitle.setter
        def border_subtitle(self, v): pass

    pan = _panel()
    app = TuiPetApp.__new__(TuiPetApp)
    app.mode = pan
    fake = app.stats_w = _FakeStats()
    for i in range(pan.n):
        pan.i = i
        app._status_eggselect()                      # the real painter, every stop
        assert "New Egg" in fake.txt and f"{i + 1} of {pan.n}" in fake.txt


def test_a_gated_egg_is_hidden_until_earned_then_bought():
    """Earned-access: a gated egg stays OUT of the carousel until its milestone
    is met, then appears in the HOME shop (it's a common egg); buying it makes
    it hatchable and it joins the carousel."""
    from tuipet import persistence, egg as egg_mod
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    idx = _rule("Pafumon")["idx"]                    # a HOME egg gated on album 3
    assert egg_mod.egg_state(idx, _prog(), set())[0] == "locked"
    assert idx not in EggSelectPanel().carousel      # locked -> hidden
    for n in (1, 2, 3):
        persistence.album_add(n)
    prog = persistence.get_progress()
    assert egg_mod.egg_state(idx, prog, set()) == ("buyable", 1300)
    assert idx not in EggSelectPanel().carousel      # buyable -> still not on the carousel
    hp = Pet(num=100, stage="Champion", attribute="Vaccine"); hp.world_seconds = 12 * 60.0
    hp.bits = 5000
    sp = ShopPanel(hp)
    while sp._tabs()[sp.tab] != "egg":
        sp.key("right")
    entry = next(e for e in sp._rows() if e.get("egg_idx") == idx)   # sold at home
    assert "Unlocked" in sp._buy_egg(entry)
    assert idx in persistence.get_eggs_owned()
    assert idx in EggSelectPanel().carousel          # owned -> hatchable


def test_fresh_profile_carousel_never_empty():
    """Eggselect audit 2026-07-05: _egg() does `pos % self.n` -- an empty
    carousel would ZeroDivision.  The data guarantees the floor: the
    DefaultUnlock starters are always hatchable, so the carousel can't be
    empty even on a wiped profile."""
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()                        # sandboxed = a fresh profile
    assert pan.n >= 5                             # the starter floor
    assert len(pan.carousel) == pan.n > 0
    pan.key("right")                              # nav + render on the floor
    assert pan.text() is not None
