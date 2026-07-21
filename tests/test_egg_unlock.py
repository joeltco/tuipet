"""The eggUnlock.csv condition engine: start eggs, locking, the password path, and
the reachability invariant (no signal-gated egg is permanently stranded as locked).
"""
import pytest

from tuipet import data, egg


EMPTY = {
    "album": set(), "wins": 0, "max_gen": 1, "max_stage": 0, "xanti_ever": False,
    "maps": set(), "raids": 0, "tourneys": set(), "last_field": "None", "last_attr": "None",
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
        "maps": set(range(0, 200)), "raids": 99999, "tourneys": set(range(0, 200)),
        "last_field": "None", "last_attr": "None", "last_elem": "None",
        "last_mood": 99999, "last_obed": 99999, "last_xanti": True,
        "connections": 99999, "festivals": set(range(0, 10)),
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
        state = egg.egg_state(i, EMPTY, owned=set())
        assert state == "owned", f"start egg {i} should be owned, got {state}"


def test_hatchable_includes_all_starts():
    rules = data.load_egg_unlock()
    sel = set(egg.hatchable_eggs(EMPTY, owned=set()))
    assert sel, "no eggs hatchable from a fresh account"
    for i, r in rules.items():
        if r["start"]:
            assert i in sel


def test_something_is_locked_initially():
    """A fresh account must NOT have everything unlocked (else progression is moot)."""
    states = egg.egg_states(EMPTY, owned=set())
    assert any(s == "locked" for s in states.values())


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
        state = egg.egg_state(i, _prog_for(rule), owned=set())
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


def test_condition_met_unlocks_without_any_purchase():
    """The licence cut (2026-07-17): meeting a can_perm rule's condition owns
    the egg outright -- no shop, no bits, no intermediate state."""
    from tuipet import persistence
    rules = data.load_egg_unlock()
    idx, r = next((i, r) for i, r in rules.items()
                  if r["wins"] and r["can_perm"] and not r["start"])
    assert egg.egg_state(idx, EMPTY, set()) == "locked"
    prog = dict(EMPTY, wins=r["wins"])
    assert egg.egg_state(idx, prog, set()) == "owned"         # met -> yours, free
    assert idx in egg.auto_owned(prog, set())                 # and it persists
    assert idx in egg.hatchable_eggs(prog, set())             # straight to the carousel


# ---- egg mood (Evolution.egg) -------------------------------------------------

def test_new_egg_starts_warm():
    from tuipet.pet import Pet, EGG_MOOD
    p = Pet.new_egg(generation=1, egg_type=0)
    assert p.mood == EGG_MOOD == 100                 # Evolution.egg: setMood(EggMood)


def test_carimon_left_with_the_fake_egg_cut():
    """The old password egg (Carimon, corpus 1050) had no covered device --
    cut 2026-07-17 with the rest of the fakes."""
    assert all(r["name"] != "Carimon" for r in data.load_egg_unlock().values())
    assert "Carimon" not in {egg.hatch_name(i) for i in range(egg.count())}


def test_prev_gate_vocabulary_lives_in_the_roster():
    """The reachability test above is SELF-FEEDING: _prog_for hands a rule
    its own prev_field/prev_attr back, so a renamed roster vocabulary
    (e.g. 'NatureSpirit' -> 'Nature Spirits') would still "open" the egg
    here while sealing it live -- no real pet could ever snapshot the
    stale value.  Pin the two vocabularies together, and every history
    gate to a real roster species (egg audit 2026-07-19)."""
    sp, _ = data.load_sprites()
    fields = {r.get("field") or "None" for r in sp}
    attrs = {r.get("attribute") or "None" for r in sp}
    nums = {r["num"] for r in sp}
    for i, r in data.load_egg_unlock().items():
        if r.get("prev_field") is not None:
            assert r["prev_field"] in fields, \
                f"egg {i}: prev_field {r['prev_field']!r} not a roster field"
        if r.get("prev_attr") is not None:
            assert r["prev_attr"] in attrs, \
                f"egg {i}: prev_attr {r['prev_attr']!r} not a roster attribute"
        for n in (r.get("history") or []):
            assert n in nums or data.canonical_num(n) in nums, \
                f"egg {i}: history num {n} not in the roster"


def test_map_eggs_unlock_by_clearing_adventure_regions():
    """The map-N eggs open when ADVENTURE clears region N (the profile `maps`
    set), with the raid fallback (N+1 bosses) still standing -- the map rows
    always meant 'region-boss cleared' (adventure rebuild 2026-07-20)."""
    u = data.load_egg_unlock()
    mapped = [(i, r) for i, r in u.items() if r.get("map") is not None]
    assert mapped                                     # there ARE map-gated eggs
    for i, r in mapped:
        n = r["map"]
        base = _prog_for(r)                           # every OTHER gate satisfied
        locked = {**base, "maps": set(), "raids": 0}
        assert not egg._conditions_met(r, locked)     # neither path -> locked
        assert egg._conditions_met(r, {**locked, "maps": {n}})      # adventure clears it
        assert egg._conditions_met(r, {**locked, "raids": n + 1})   # raid fallback
        assert "adventure map" in egg.unlock_progress(i, locked)    # the guide names it
        assert egg.unlock_progress(i, {**locked, "maps": {n}}) == ""  # cleared -> no gate text
