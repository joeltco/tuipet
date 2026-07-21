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
    assert (r["wins"], r["can_perm"]) == (50, True)           # EARN tier
    assert r["stage"] is None                       # the old Ultimate gate is gone
    assert not egg._conditions_met(r, _prog(wins=49))
    assert egg._conditions_met(r, _prog(wins=50))


def test_petitmon_is_the_collector_egg():
    r = _rule("Petitmon")
    # the album records one entry per STAGE; tier-spread (2026-07-20) eased the
    # collector gate 15->10 so it sits on the Earned tier's low album rung
    assert (r["album_n"], r["can_perm"]) == (10, True)        # EARN tier
    assert r["prev_field"] is None                  # no longer a temp lineage egg
    assert not egg._conditions_met(r, _prog(album=set(range(1, 10))))    # 9
    assert egg._conditions_met(r, _prog(album=set(range(1, 11))))        # 10


def test_dodomon_is_the_x_egg():
    r = _rule("Dodomon")
    assert (r["mega"], r["can_perm"]) == (5, True)            # EARN tier
    assert not r["xanti"]                           # the antibody gate is retired
    assert not egg._conditions_met(r, _prog(mega_kills=4))
    assert egg._conditions_met(r, _prog(mega_kills=5))


def test_met_achievement_is_earned_free():
    """Meeting the condition unlocks the egg outright -- no bits, ever
    (the licence economy died 2026-07-17)."""
    r = _rule("Sakumon")
    assert egg.egg_state(r["idx"], _prog(wins=50), set()) == "owned"   # earned -> yours
    assert egg.egg_state(r["idx"], _prog(wins=0), set()) == "locked"


# ---- live progress ----------------------------------------------------------------

def test_unlock_progress_counts_the_countable():
    assert egg.unlock_progress(_rule("Sakumon")["idx"], _prog(wins=37)) == "lifetime wins 37/50"
    assert egg.unlock_progress(_rule("Petitmon")["idx"], _prog(album={1, 2, 3})) == "species recorded 3/10"
    assert egg.unlock_progress(_rule("Dodomon")["idx"], _prog(mega_kills=1)) == "Mega-class felled 1/5"


def test_mega_kill_feeds_the_lifetime_progress():
    random.seed(5)
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.record_battle(True, enemy={"stage": "Mega", "hp": 20, "vaccine": 90,
                                 "data_power": 0, "virus": 0, "bits": (1, 2)})
    assert persistence.get_progress()["mega_kills"] == 1
    p.record_battle(False, enemy={"stage": "Mega", "hp": 20, "vaccine": 90,
                                  "data_power": 0, "virus": 0, "bits": (1, 2)})
    assert persistence.get_progress()["mega_kills"] == 1    # losses never count


def test_fallback_pool_and_mystery_eggs_are_gone():
    assert not hasattr(egg, "_fallback_pool")
    assert not hasattr(egg, "_WIN_EGGS")            # the "???" eggs left with the cut
    assert "???" not in {egg.hatch_name(i) for i in range(egg.count())}


# ---- the carousel -----------------------------------------------------------------

def _panel(prog=None):
    from tuipet.eggselectscreen import EggSelectPanel
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
    assert all(pan.states[i] in ("owned", "temp") for i in pan.carousel)
    assert not any(pan.states[i] == "locked" for i in pan.carousel)


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


def test_a_gated_egg_is_hidden_until_earned_then_appears():
    """Earned-access after the licence cut: a gated egg stays OUT of the
    carousel until its milestone is met, then joins it directly -- no shop
    in between, and the panel persists the win (auto_owned)."""
    from tuipet import persistence, egg as egg_mod
    from tuipet.eggselectscreen import EggSelectPanel
    idx = _rule("Sakumon")["idx"]                    # the battle egg: 50 wins
    assert egg_mod.egg_state(idx, _prog(), set()) == "locked"
    assert idx not in EggSelectPanel().carousel      # locked -> hidden
    persistence.wins_add(50)
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()                           # milestone met on open
    assert idx in pan.carousel                       # earned -> hatchable, no purchase
    assert idx in persistence.get_eggs_owned()       # and persisted permanent


def test_fresh_profile_carousel_never_empty():
    """Eggselect audit 2026-07-05: _egg() does `pos % self.n` -- an empty
    carousel would ZeroDivision.  The data guarantees the floor: the
    DefaultUnlock starters are always hatchable, so the carousel can't be
    empty even on a wiped profile."""
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()                        # sandboxed = a fresh profile
    assert pan.n >= 5                             # the starter floor
    assert len(pan.carousel) == pan.n > 0
    pan.key("right")                              # nav + render on the floor
    assert pan.text() is not None


def test_carousel_polish_scene_mystery_and_new_badge():
    """Carousel polish 2026-07-18: the backdrop follows the browsed egg's
    wired scene, a multi-target digitama keeps its mystery, and an unraised
    species wears the ★new badge (raised ones don't)."""
    from tuipet import backgrounds, data as _d
    pan = _panel()
    # scene: the browsed egg's own backdrop, not a flat void
    idx0 = pan.carousel[0]
    want = _d.load_backgrounds()[backgrounds.scene_for_egg(idx0)][0]
    assert pan._scene_bg(idx0) == want
    # ★new on a fresh profile; gone once the species is raised
    note = pan._note(idx0)
    assert "★new" in note
    tgt = egg.hatch_targets(idx0)[0]
    persistence.album_add(tgt)
    assert "★new" not in pan._note(idx0)
    # a multi-target egg never wears the EGG label as a hatchling name
    multi = next((i for i in range(egg.count())
                  if len(egg.hatch_targets(i)) > 1), None)
    if multi is not None:
        assert "???" in pan._note(multi)
        assert "two fates" in pan._note(multi)


def test_the_guide_sentinel_never_reaches_new_egg():
    """Termux crash 2026-07-18: N (guide) on the retire/death carousel handed
    the literal 'guide' to Pet.new_egg as an egg_type.  Both pick paths must
    route the sentinel to the guide and back, and new_egg must never see it."""
    from tuipet.app import TuiPetApp
    opened = []
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = Pet(num=100, stage="Champion", attribute="Vaccine")
    app.pet.world_seconds = 600.0
    app._open_mode = lambda panel, cb=None: opened.append(type(panel).__name__)
    app._do = lambda msg: opened.append(("msg", msg))
    app._hatch_new("guide", gen=5)
    assert opened == ["EggGuidePanel"]            # the guide opens, nothing hatches
    app._hatch_new(None, gen=5)
    assert opened[-1] == ("msg", "Kept your current partner.")


def test_the_carousel_is_pure_scene_with_neighbour_peeks():
    """Carousel redo 2026-07-19 (Joel's bug report): the LCD is HEADER +
    SCENE only -- the dossier lives on the status card, the words on the
    strip -- and the neighbour egg edges PEEK again at rest (cutting them
    in 0.5.87 'went backwards')."""
    from tuipet.eggselectscreen import EggSelectPanel, CENTER, SPACING, WINDOW
    pan = EggSelectPanel()
    pan.scroll = pan.pos = 1.0
    plain = pan.text().plain
    assert "hatches:" not in plain and "browse" not in plain \
        and "ESC" not in plain                     # pure scene, no text block
    assert len(plain.rstrip("\n").split("\n")) == 12   # header 2 + scene 10
    # the strip speaks: hints normally, the tease on its beat, msg first
    assert "browse" in pan.strip()
    pan.frame_i = 130
    if pan.locked and pan.hint:
        assert "more out there" in pan.strip()
    pan.msg = "verdict!"
    assert pan.strip() == "verdict!"
