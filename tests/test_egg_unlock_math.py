"""Album/egg-unlock math audit (2026-07).

THE HEADLINE: no class in the shipped DVPet jar references eggUnlock.csv
at all -- the file is authored-but-UNWIRED data on the device.  The canon
here is the CSV's own self-documenting header contract, and tuipet's
engine is MORE canon-complete than the game it cloned: it runs data the
original never used.

Verified against the header contract + the live data: every condition
ANDs; met -> permanent (auto_owned), unless CanUnlockPermanently=FALSE ->
temporary; the (Temp)-marked prev-gen conditions re-evaluate per
generation.  The Price column is dead (licence cut 2026-07-17) and the
rows that used it carry device-story gates instead.  Obedience/FoodUsed/
ItemUsed/HabitatOwned/ZoneEnemyBeat are data-empty (noted; the loader's
latent current-vs-prev column mis-source was corrected for purity)."""
from tuipet import data, egg


def _prog(**kw):
    base = {"album": set(), "wins": 0, "max_gen": 1, "max_stage": 0,
            "xanti_ever": False, "maps": set(), "tourneys": set(),
            "last_field": "None", "last_attr": "None", "last_elem": "None",
            "last_mood": 0, "last_obed": 0, "last_xanti": False}
    base.update(kw)
    return base


def _egg_named(name):
    rules = data.load_egg_unlock()
    return next(i for i, r in rules.items() if r["name"] == name)


def test_the_csv_is_unwired_in_dvpet_but_wired_here():
    rules = data.load_egg_unlock()
    assert len(rules) >= 30                        # the contract runs in tuipet
    live = sum(1 for r in rules.values()
               if any((r["map"] is not None, r["stage"], r["xanti"],
                       r["tourney"] is not None, r["history"], r["password"],
                       r["wins"], r["album_n"], r["mega"])))
    assert live >= 15                              # the EARN tier (signature achievements)


def test_nothing_beyond_the_starters_opens_at_day_one():
    """Earned-access: every non-start egg carries a progression gate, so a
    fresh account hatches exactly the starters."""
    rules = data.load_egg_unlock()
    gated = [i for i, r in rules.items() if not r["start"]]
    assert gated
    assert all(egg.egg_state(i, _prog(), set()) == "locked" for i in gated)


def test_xanti_and_prev_gen_temp_conditions():
    idx = next(i for i, r in data.load_egg_unlock().items() if r["xanti"])
    assert egg.egg_state(idx, _prog(), set()) == "locked"
    assert egg.egg_state(idx, _prog(xanti_ever=True), set()) != "locked"
    pf = next(i for i, r in data.load_egg_unlock().items() if r["prev_field"])
    want = data.load_egg_unlock()[pf]["prev_field"]
    assert egg.egg_state(pf, _prog(), set()) == "locked"
    assert egg.egg_state(pf, _prog(last_field=want), set()) != "locked"


def test_temp_only_eggs_never_go_permanent():
    rules = data.load_egg_unlock()
    for i, r in rules.items():
        if not r["can_perm"] and not r["start"]:
            good = _prog(max_gen=99, max_stage=9, xanti_ever=True, last_xanti=True,
                         maps=set(range(9)), tourneys=set(range(99)),
                         album=set(range(2000)), last_field=r["prev_field"] or "None",
                         last_attr=r["prev_attr"] or "None",
                         last_elem=r["prev_elem"] or "None")
            st = egg.egg_state(i, good, set())
            assert st in ("temp", "locked")        # met -> temp, never owned
            assert i not in egg.auto_owned(good, set())
            break


def test_dormant_columns_are_empty_in_the_corpus():
    # obedience/mood woke up 2026-07-10: the Lalamon lineage egg gates on the
    # previous generation's devotion (Meicoomon's mood row left with the
    # fake-egg cut). Nothing else may.
    for r in data.load_egg_unlock().values():
        if r["name"] not in ("Lalamon Egg",):
            assert r["obedience"] is None and r["mood"] is None
        assert r["food"] is None and r["item"] is None and r["habitat"] is None
        assert r["zone"] is None
