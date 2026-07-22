"""Egg-guide truth audit (2026-07-22, the help-audit method): every
LockedDescription is the guide's ONLY story for its gate -- tourney gates
don't even have a live counter branch -- so each desc must tell the gate
it fronts.  Found and fixed: Dokimon claimed "a Mega tournament in
Summer" for plain Summer Open #147, Hack Egg a "Fall Champion Cup" that
does not exist (Fall Open #188).  Verified true in the same pass: the
raid family's strict-greater map comparator (map:0 = 1 boss -- no
off-by-one), the live "clear adventure map N" alternative (adventure
zone conquest still writes the maps channel), and every counter desc
carrying its real number."""
import re

from tuipet import data, tournament


def test_tourney_gated_eggs_name_their_actual_cup():
    rules = data.load_egg_unlock()
    for idx, r in rules.items():
        if r.get("tourney") in (None, -1):
            continue
        t = next((x for x in data.load_tournies() if x["id"] == r["tourney"]), None)
        assert t is not None, f"egg {idx}: gate cup {r['tourney']} left the roster"
        label = tournament.trophy_label(t)
        assert label in r["desc"], \
            f"egg {idx}: desc {r['desc']!r} does not name its gate cup {label!r}"


def test_counter_gated_eggs_tell_their_real_numbers():
    """A desc that says "Win 10" must gate on 10.  The raid family's map
    field is 0-based with a strict-greater check: map N = N+1 bosses."""
    rules = data.load_egg_unlock()
    for idx, r in rules.items():
        checks = [(r.get(k)) for k in
                  ("wins", "album_n", "mega", "festivals_n", "connections",
                   "obedience", "gen")]
        nums = set(re.findall(r"\d+", r["desc"]))
        for want in checks:
            if want in (None, -1, 0) or want is False:
                continue
            assert str(want) in nums or want == 1, \
                f"egg {idx}: desc {r['desc']!r} hides its gate value {want}"
        m = r.get("map")
        if m is not None and m != -1:
            assert str(m + 1) in nums, \
                f"egg {idx}: desc {r['desc']!r} vs map {m} (= {m + 1} bosses)"
