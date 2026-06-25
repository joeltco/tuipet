"""The eggUnlock.csv condition engine: start eggs, locking, the password path, and
the reachability invariant (no signal-gated egg is permanently stranded as locked).
"""
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
        "wins": 99999, "max_gen": 99, "max_stage": 5, "xanti_ever": True,
        "maps": set(range(0, 200)), "tourneys": set(range(0, 200)),
        "last_field": "None", "last_attr": "None", "last_elem": "None",
        "last_mood": 99999, "last_obed": 99999, "last_xanti": True,
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


def test_password_egg_resolves():
    # 'Accentier' -> Carimon (case-insensitive); blanks/garbage resolve to None.
    idx = egg.password_egg("accentier")
    assert isinstance(idx, int)
    assert egg.password_egg("ACCENTIER") == idx
    assert egg.password_egg("") is None
    assert egg.password_egg("definitely-not-a-code") is None
    # the password egg stays locked through ordinary play (only the code frees it)
    state, _ = egg.egg_state(idx, _prog_for(data.load_egg_unlock().get(idx)), owned=set())
    assert state == "locked"


def test_buying_a_license_makes_it_owned():
    """A condition-met, priced egg is 'buyable'; once in `owned` it reads 'owned'."""
    rules = data.load_egg_unlock()
    buyable = None
    for i, r in rules.items():
        if r["start"] or r["price"] <= 0:
            continue
        if r["password"] or r["food"] or r["item"] or r["habitat"] or r["zone"]:
            continue
        st, price = egg.egg_state(i, _prog_for(r), owned=set())
        if st == "buyable":
            buyable = i
            assert price == r["price"] > 0
            break
    if buyable is None:
        import pytest
        pytest.skip("no purely signal-gated priced egg in this build")
    st, _ = egg.egg_state(buyable, _prog_for(rules[buyable]), owned={buyable})
    assert st == "owned"


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


def test_egg_select_cursor_starts_on_a_free_egg():
    """On a fresh account the egg picker must land on an owned (free) starter, not an
    unaffordable license egg (a new player has 0 bits)."""
    from tuipet.eggselectscreen import EggSelectPanel
    panel = EggSelectPanel()
    assert panel.unlocked, "a fresh account must have selectable eggs"
    idx = panel.unlocked[panel.i]
    state, price = panel.states[idx]
    assert state == "owned" and price == 0, \
        f"new-game cursor landed on {state} (price {price}); expected a free owned egg"


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
