"""The eggUnlock.csv condition engine: start eggs, locking, the password path, and
the reachability invariant (no signal-gated egg is permanently stranded as locked).
"""
import pytest

from tuipet import data, egg


EMPTY = {
    "album": set(), "wins": 0, "max_gen": 1, "max_stage": 0, "xanti_ever": False,
    "maps": set(), "tourneys": set(), "last_field": "None", "last_attr": "None",
    "last_elem": "None", "last_mood": 0, "last_obed": 0, "last_xanti": False,
}


def _prog_for(rule):
    """A progress state that satisfies every *signal* gate of one rule. prev_* are
    set to the rule's required values (a single generation can only match one set,
    which is why reachability is proven per-egg, not with one global maxed state)."""
    p = {
        "album": set(range(0, 4000)),
        "wins": 99999, "mega_kills": 99999, "max_gen": 99, "max_stage": 5,
        "xanti_ever": True,
        "maps": set(range(0, 200)), "tourneys": set(range(0, 200)),
        "last_field": "None", "last_attr": "None", "last_elem": "None",
        "last_mood": 99999, "last_obed": 99999, "last_xanti": True,
        "connections": 99999,
    }
    if rule:
        if rule["prev_field"] is not None:
            p["last_field"] = rule["prev_field"]
        if rule["prev_attr"] is not None:
            p["last_attr"] = rule["prev_attr"]
        if rule["prev_elem"] is not None:
            p["last_elem"] = rule["prev_elem"]
        for n in (rule["history"] or []):
            p["album"].add(n)
    return p


def test_start_eggs_owned_from_nothing():
    rules = data.load_egg_unlock()
    starts = [i for i, r in rules.items() if r["start"]]
    assert starts, "expected at least one starter egg"
    for i in starts:
        state, price = egg.egg_state(i, EMPTY, owned=set())
        assert state == "owned", f"start egg {i} should be owned, got {state}"


def test_selectable_includes_all_starts():
    rules = data.load_egg_unlock()
    sel = set(egg.selectable_eggs(EMPTY, owned=set()))
    assert sel, "no eggs selectable from a fresh account"
    for i, r in rules.items():
        if r["start"]:
            assert i in sel


def test_something_is_locked_initially():
    """A fresh account must NOT have everything unlocked (else progression is moot)."""
    states = egg.egg_states(EMPTY, owned=set())
    assert any(s == "locked" for s, _ in states.values())


def test_signal_gated_eggs_are_reachable():
    """Every egg gated only on signals tuipet tracks must reach a non-locked state
    given some progress. Eggs gated on unmodelled systems (food/item/habitat/zone/
    password) are *expected* to stay locked and are excluded."""
    rules = data.load_egg_unlock()
    stranded = []
    for i in range(egg.count()):
        rule = rules.get(i)
        if rule and (rule["password"] or rule["food"] or rule["item"]
                     or rule["habitat"] or rule["zone"]):
            continue                       # intentionally gated on an unmodelled system
        state, _ = egg.egg_state(i, _prog_for(rule), owned=set())
        if state == "locked":
            stranded.append(i)
    assert not stranded, f"signal-gated eggs unreachable: {stranded}"

def test_egg_gate_cross_references_exist():
    """Every egg gate must point at a real, reachable game object; otherwise the egg
    is silently stranded. Guards against a data refresh adding an egg gated on a
    trophy/map/Digimon/field that does not exist."""
    rules = data.load_egg_unlock()
    tourneys = {t["id"] for t in data.load_tournies()}
    nmaps = len(data.load_maps())
    _, by = data.load_sprites()
    fields = {r.get("field") for r in by.values()}
    attrs = {r.get("attribute") for r in by.values()}
    elems = {r.get("element") for r in by.values()}
    bad = []
    for idx, rule in rules.items():
        if rule["tourney"] is not None and rule["tourney"] not in tourneys:
            bad.append((idx, "tourney", rule["tourney"]))
        if rule["map"] is not None and not (0 <= rule["map"] < nmaps):
            bad.append((idx, "map", rule["map"]))
        for n in (rule["history"] or []):
            if n not in by:
                bad.append((idx, "history", n))
        if rule["prev_field"] is not None and rule["prev_field"] not in fields:
            bad.append((idx, "prev_field", rule["prev_field"]))
        if rule["prev_attr"] is not None and rule["prev_attr"] not in attrs:
            bad.append((idx, "prev_attr", rule["prev_attr"]))
        if rule["prev_elem"] is not None and rule["prev_elem"] not in elems:
            bad.append((idx, "prev_elem", rule["prev_elem"]))
    assert not bad, f"egg gates referencing nonexistent objects (egg stranded): {bad}"


def test_no_egg_gated_on_an_unmodeled_system():
    """_conditions_met hard-fails food/item/habitat/zone gates (tuipet does not model
    them), so any egg using ONLY those is permanently locked. Shipped data uses none;
    this guards a refresh from silently stranding an egg on an unmodeled gate."""
    rules = data.load_egg_unlock()
    stranded = []
    for idx, rule in rules.items():
        if rule["start"]:
            continue
        if any(rule[k] is not None for k in ("food", "item", "habitat", "zone")):
            stranded.append((idx, [k for k in ("food", "item", "habitat", "zone")
                                   if rule[k] is not None]))
    assert not stranded, f"eggs gated on unmodeled systems (permanently locked): {stranded}"


def test_hatchable_and_buyable_partition_the_unlocked():
    """hatchable (owned+temp) and buyable are disjoint and together = non-locked.
    A progressed account has both; a fresh one has only the free starters."""
    prog = dict(EMPTY, max_stage=3, maps={0, 1}, album=set(range(1, 10)))
    hatch = set(egg.hatchable_eggs(prog, set()))
    buy = {i for i, _ in egg.buyable_eggs(prog, set())}
    sel = set(egg.selectable_eggs(prog, set()))
    assert hatch and buy, "a progressed account has free eggs AND buyable ones"
    assert hatch.isdisjoint(buy)
    assert hatch | buy == sel


def test_egg_shop_buy_unlocks_for_hatching():
    """Buying an egg in the shop spends bits, owns it permanently, and moves it from
    'buyable' to 'hatchable' (it then shows up in the egg select)."""
    from tuipet.shopscreen import ShopPanel
    from tuipet.pet import Pet
    from tuipet import persistence
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["stage"] == "Rookie" and not data.is_placeholder(n)), None)
    if num is None:
        pytest.skip("sprite assets not installed")
    pet = Pet.from_num(num)
    pet.bits = 5000

    persistence._note_max("max_stage", 3)                    # reach the milestones
    for n in range(1, 10):
        persistence.album_add(n)
    prog = persistence.get_progress()
    owned = persistence.get_eggs_owned()
    buyable = egg.buyable_eggs(prog, owned)
    assert buyable, "a progressed account has buyable eggs"
    idx, price = buyable[0]
    assert idx not in egg.hatchable_eggs(prog, owned)         # not hatchable yet

    from tuipet import shop as _shop
    msg, sfx = _shop.buy(pet, egg.shop_egg_entry(idx, price))
    assert "licensed" in msg
    assert pet.bits == 5000 - price                          # bits spent

    prog2 = persistence.get_progress()
    owned2 = persistence.get_eggs_owned()
    assert idx in owned2                                      # owned permanently
    assert idx in egg.hatchable_eggs(prog2, owned2)          # now hatchable in egg select
    assert idx not in {i for i, _ in egg.buyable_eggs(prog2, owned2)}  # gone from the shop

    # can't double-buy, and can't buy without bits
    msg, sfx = _shop.buy(pet, egg.shop_egg_entry(idx, price))
    assert sfx == "error" and "Already" in msg
    nxt = egg.buyable_eggs(prog2, owned2)
    if nxt:
        pet.bits = 0
        msg, sfx = _shop.buy(pet, egg.shop_egg_entry(*nxt[0]))
        assert "Need" in msg


# ---- password redemption + egg mood (Evolution.egg) --------------------------

def test_new_egg_starts_warm():
    from tuipet.pet import Pet, EGG_MOOD
    p = Pet.new_egg(generation=1, egg_type=0)
    assert p.mood == EGG_MOOD == 100                 # Evolution.egg: setMood(EggMood)


def test_carimon_is_earned_by_conquering_the_world():
    """The old password egg is now a free achievement: clear all 5 regions."""
    idx = next(r["idx"] for r in data.load_egg_unlock().values() if r["name"] == "Carimon")
    assert data.load_egg_unlock()[idx]["password"] is None      # no code any more
    assert egg.egg_state(idx, dict(EMPTY, maps={0, 1, 2}), set())[0] == "locked"
    assert egg.egg_state(idx, dict(EMPTY, maps={0, 1, 2, 3, 4}), set()) == ("owned", 0)
