"""No egg may be strictly DOMINATED by another (Joel 2026-07-14).

Slayerdra / Breakdra / Draco all hatched the identical Petitmon line and all
gated on the same thing -- AlbumCount 6 / 26 / 12 -- so Slayerdra strictly
dominated the other two: same reward, a quarter of the work.  Nobody would ever
unlock Draco or Breakdra.

Every other same-line group in the game is an ALTERNATE ROUTE (buy it with
adventure winnings / earn it in the lobby / earn it by raising well).  This pins
that rule: eggs that give the SAME thing must be earned in DIFFERENT ways.
"""
from tuipet import data, egg as egg_mod

# the gate columns a player can actually work toward
_GATES = ("album_n", "wins", "mega", "tourney", "connections", "price",
          "history", "password", "obedience", "mood", "gen", "xanti",
          "habitat", "stage", "prev_attr", "prev_elem", "prev_field",
          "item", "food", "map", "zone")


def _line_of(eid):
    """The full set of creatures this egg can ever reach."""
    evos = data.load_evolutions()
    roots = egg_mod._real_eggs()[eid].get("hatch", [])
    seen, frontier = set(roots), list(roots)
    while frontier:
        for k in evos.get(frontier.pop(), []):
            if k not in seen:
                seen.add(k)
                frontier.append(k)
    return frozenset(seen)


def _gate_kinds(rule):
    return frozenset(g for g in _GATES if rule.get(g) not in (None, "", 0, False, -1))


def test_same_line_eggs_are_earned_in_different_ways():
    rules = data.load_egg_unlock()
    by_line = {}
    for eid, r in rules.items():
        if r.get("start"):
            continue                       # the free starters may share a line
        by_line.setdefault(_line_of(eid), []).append((eid, r))

    for line, group in by_line.items():
        if len(group) < 2:
            continue
        kinds = [(_gate_kinds(r), r["name"]) for _e, r in group]
        # any two eggs on the same line must not be gated on the SAME single
        # thing -- that is what makes one of them strictly worse than the other
        for i, (k1, n1) in enumerate(kinds):
            for k2, n2 in kinds[i + 1:]:
                assert not (k1 and k1 == k2), (
                    f"{n1} and {n2} give the same line and are gated the same "
                    f"way ({sorted(k1)}) -- one of them is strictly dominated")


def test_the_dragon_trio_has_three_distinct_routes():
    rules = data.load_egg_unlock()
    by = {r["name"]: r for r in rules.values()}
    assert by["Slayerdra Egg"]["wins"] == 30        # the warrior's route
    assert by["Breakdra Egg"]["mega"] == 3          # the giant-slayer's route
    assert by["Draco Egg"]["album_n"] == 6          # the collector's route
    for name in ("Slayerdra Egg", "Breakdra Egg", "Draco Egg"):
        assert by[name]["desc"].strip(), "every route needs its own description"
