"""Album/egg-unlock math audit (2026-07).

THE HEADLINE: no class in the shipped DVPet jar references eggUnlock.csv
at all -- the file is authored-but-UNWIRED data on the device.  The canon
here is the CSV's own self-documenting header contract, and tuipet's
engine is MORE canon-complete than the game it cloned: it runs data the
original never used.

Verified against the header contract + the live data (42 rows): every
condition ANDs; price>0 + conditions met -> the egg SHOP, buying is
permanent; price=0 + met -> permanent (auto_owned), unless
CanUnlockPermanently=FALSE -> temporary; the (Temp)-marked prev-gen
conditions re-evaluate per generation.  Live gates all map and check:
CurrentGenerationReached (14 eggs), MapComplete (4), HasXAntibody (3),
TournamentBeat (3), StageReached (2), PrevGen Field/Attr/Elem (1 each),
DigimonInHistory (ChibiKiwimon needs dex 944 in the album), Password
(Carimon).  Obedience/Mood/FoodUsed/ItemUsed/HabitatOwned/ZoneEnemyBeat
are data-empty (noted; the loader's latent current-vs-prev column
mis-source was corrected for purity)."""
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


def test_explore_buy_eggs_are_always_in_the_shop():
    """Two-tier economy: an explore-buy egg has no achievement gate -- always in the
    town shops (buyable), and buying makes it permanent."""
    GATE = ("gen", "map", "stage", "xanti", "tourney", "prev_field", "prev_attr",
            "prev_elem", "history", "password", "wins", "album_n", "mega")
    idx = next(i for i, r in data.load_egg_unlock().items()
               if not r["start"] and r["price"] > 0
               and all(r.get(k) in (None, False) for k in GATE))
    r = data.load_egg_unlock()[idx]
    st, price = egg.egg_state(idx, _prog(), set())
    assert st == "buyable" and price == r["price"]     # no gate -> always buyable
    st, _ = egg.egg_state(idx, _prog(), {idx})
    assert st == "owned"                               # bought -> permanent


def test_history_gate_reads_the_album():
    idx = _egg_named("ChibiKiwimon")
    assert egg.egg_state(idx, _prog(album=set()), set())[0] == "locked"
    st, _ = egg.egg_state(idx, _prog(album={944}), set())
    assert st in ("buyable", "owned")              # dex 944 raised -> the gate opens


def test_xanti_and_prev_gen_temp_conditions():
    idx = next(i for i, r in data.load_egg_unlock().items() if r["xanti"])
    assert egg.egg_state(idx, _prog(), set())[0] == "locked"
    st, _ = egg.egg_state(idx, _prog(xanti_ever=True), set())
    assert st != "locked"
    pf = next((i for i, r in data.load_egg_unlock().items() if r["prev_field"]), None)
    if pf is not None:
        want = data.load_egg_unlock()[pf]["prev_field"]
        assert egg.egg_state(pf, _prog(), set())[0] == "locked"
        assert egg.egg_state(pf, _prog(last_field=want), set())[0] != "locked"


def test_temp_only_eggs_never_go_permanent():
    rules = data.load_egg_unlock()
    for i, r in rules.items():
        if not r["can_perm"] and not r["start"] and r["price"] == 0:
            good = _prog(max_gen=99, max_stage=9, xanti_ever=True, last_xanti=True,
                         maps=set(range(9)), tourneys=set(range(99)),
                         album=set(range(2000)), last_field=r["prev_field"] or "None",
                         last_attr=r["prev_attr"] or "None",
                         last_elem=r["prev_elem"] or "None")
            st, _ = egg.egg_state(i, good, set())
            assert st in ("temp", "locked")        # met -> temp, never owned
            assert i not in egg.auto_owned(good, set())
            break


def test_dormant_columns_are_empty_in_the_corpus():
    # obedience/mood woke up 2026-07-10: the Lalamon/Meicoomon lineage eggs
    # gate on the previous generation's devotion/affection. Nothing else may.
    for r in data.load_egg_unlock().values():
        if r["name"] not in ("Lalamon Egg", "Meicoomon Egg"):
            assert r["obedience"] is None and r["mood"] is None
        assert r["food"] is None and r["item"] is None and r["habitat"] is None
        assert r["zone"] is None
