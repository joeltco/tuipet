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


def test_signal_gated_eggs_are_reachable():
    """Every egg gated only on signals tuipet tracks must reach a non-locked state
    given some progress. Eggs gated on unmodelled systems (food/item/habitat/zone/
    password) are *expected* to stay locked and are excluded."""
    rules = data.load_egg_unlock()
    stranded = []
    for i in range(egg.count()):
        rule = rules.get(i)
        if rule and (rule["password"] or rule["food"] or rule["item"]
                     or rule["zone"]):
            continue                       # intentionally gated on an unmodelled system
        state, _ = egg.egg_state(i, _prog_for(rule), owned=set())
        if state == "locked":
            stranded.append(i)
    assert not stranded, f"signal-gated eggs unreachable: {stranded}"

def test_no_egg_gated_on_an_unmodeled_system():
    """_conditions_met hard-fails food/item/habitat/zone gates (tuipet does not model
    them), so any egg using ONLY those is permanently locked. Shipped data uses none;
    this guards a refresh from silently stranding an egg on an unmodeled gate."""
    rules = data.load_egg_unlock()
    stranded = []
    for idx, rule in rules.items():
        if rule["start"]:
            continue
        if any(rule[k] is not None for k in ("food", "item", "zone")):
            stranded.append((idx, [k for k in ("food", "item", "zone")
                                   if rule[k] is not None]))
    assert not stranded, f"eggs gated on unmodeled systems (permanently locked): {stranded}"
