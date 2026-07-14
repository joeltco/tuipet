"""Line anchoring — how a pet BINDS to a chart when several lines share a node.

lines.csv intentionally shares dex nodes across lines (Babydmon 955 sits in
slayerdra, breakdra AND draco, each line with its own children), so every
binding decision must be intentional, never csv-order luck:

* canonical_root: a name-hatched twin always becomes the CLASSIC line (the
  lowest root dex; 141x < 16xx by construction) — the 16xx device lines are
  entered only through their own eggs.
* adopt_line: a special evolution (jogress / divergence / Digimental / death
  rebirth) prefers its own line, then any line containing the road actually
  travelled (prev AND current form), then the lowest root.
* every special-evolution path re-anchors, and a legacy save with no line_id
  is adopted on load instead of riding the corpus engine forever.
"""
import pytest

from tuipet import data, lines, persistence
from tuipet.pet import Pet


def _by_num():
    _, by_num = data.load_sprites()
    if not by_num:
        pytest.skip("sprite assets not installed (run tools/setup_assets.sh)")
    return by_num


class _P:
    def __init__(self, num, line_id=""):
        self.num, self.line_id = num, line_id


# ---- canonical_root: the classic line always wins the name tie ---------------

def test_twins_hatch_the_classic_line():
    by_num = _by_num()
    # the audited name-collision twins: each name roots a classic 141x line
    # AND at least one 16xx device line; the classic root must win every time
    for twin, want_root, want_line in ((954, 1437, "petitmon"),
                                       (8, 1417, "pichimon"),
                                       (968, 1444, "sakumon"),
                                       (970, 1445, "zerimon"),
                                       (2, 1411, "ver1"),
                                       (928, 1426, "verX"),
                                       (938, 1430, "chibomon")):
        assert by_num[twin]["name"] == by_num[want_root]["name"]
        assert lines.canonical_root(twin) == (want_root, want_line), \
            f"twin {twin} must hatch the classic line {want_line}"


def test_every_name_collision_resolves_to_the_lowest_root():
    by_num = _by_num()
    roots = {lid: line["root"] for lid, line in lines.load_lines().items()}
    by_name = {}
    for lid, root in roots.items():
        rec = by_num.get(root)
        if rec:
            by_name.setdefault(rec["name"], []).append(root)
    collisions = {n: sorted(rs) for n, rs in by_name.items() if len(rs) > 1}
    assert collisions, "data drift: no name-colliding roots left to arbitrate"
    for name, rs in collisions.items():
        # arbitrate through any non-root twin of that name (skip names whose
        # only bearers ARE roots — those hatch directly, no tie to break)
        twin = next((n for n, r in by_num.items()
                     if r["name"] == name and n not in rs), None)
        if twin is None:
            continue
        root, _ = lines.canonical_root(twin)
        assert root == rs[0], f"{name} twin must bind the lowest root {rs[0]}"


# ---- adopt_line: own line, then road travelled, then lowest root --------------

def test_adopt_line_prefers_the_pets_own_line():
    p = _P(955, line_id="draco")
    assert lines.adopt_line(p) == "draco" and p.line_id == "draco"


def test_adopt_line_prefers_the_road_travelled():
    # Babydmon 955 sits in slayerdra, breakdra AND draco: the previous form
    # decides which chart the pet is actually walking
    p = _P(955)
    assert lines.adopt_line(p, prev=1615) == "draco"      # draco's own egg root
    q = _P(955)
    assert lines.adopt_line(q, prev=1613) == "breakdra"   # breakdra's egg root


def test_adopt_line_tiebreak_is_the_lowest_root():
    # no history: the binding must be data-stable, not csv-order —
    # slayerdra's root 1612 is the lowest of the three 955 owners
    p = _P(955)
    assert lines.adopt_line(p) == "slayerdra"


def test_adopt_line_off_chart_falls_to_corpus():
    p = _P(999999, line_id="draco")
    assert lines.adopt_line(p) == "" and p.line_id == ""


# ---- every special-evolution path re-anchors ----------------------------------

def _grown(num, by_num):
    p = Pet.from_num(num)
    p.stage = by_num[num]["stage"]
    return p


def test_digimental_jump_reanchors_the_line(monkeypatch):
    from tuipet import pet as pet_mod
    by_num = _by_num()
    p = _grown(1615, by_num)                    # draco's Petitmon root
    p.line_id, p.energy, p.max_energy = "draco", 24, 24
    p.inventory["i:15"] = 1
    monkeypatch.setattr(Pet, "check_refused", lambda self, **k: False)
    monkeypatch.setattr(pet_mod.evolution, "item_select", lambda pet, iid: 955)
    msg = p.use_item("i:15")
    assert "evolved" in msg and p.num == 955
    assert p.line_id == "draco", "the road travelled keeps the pet on its chart"


def test_death_rebirth_reanchors_the_line(monkeypatch):
    from tuipet import pet as pet_mod
    by_num = _by_num()
    p = _grown(1615, by_num)
    p.line_id = "draco"
    p.dead = True
    monkeypatch.setattr(pet_mod.evolution, "death_targets", lambda pet: [955])
    old = p.save_from_death()
    assert old == 1615 and p.num == 955
    assert p.line_id == "draco"


# ---- legacy saves: an empty line_id is adopted on load -------------------------

def test_legacy_save_without_line_id_is_adopted():
    by_num = _by_num()
    p = _grown(955, by_num)
    p.line_id = "slayerdra"
    blob = persistence.to_save_dict(p)
    blob.pop("line_id", None)                   # a save from before lines existed
    loaded, _msg = persistence.pet_from_save(blob, catch_up=False)
    assert loaded is not None
    assert loaded.line_id == "slayerdra", "mid-line pet must not ride the corpus engine"


def test_legacy_off_chart_save_stays_corpus():
    by_num = _by_num()
    num = next(n for n, r in by_num.items()
               if r["stage"] == "Mega"
               and not any(n in line["members"]
                           for line in lines.load_lines().values()))
    p = _grown(num, by_num)
    p.line_id = ""
    blob = persistence.to_save_dict(p)
    blob.pop("line_id", None)
    loaded, _msg = persistence.pet_from_save(blob, catch_up=False)
    assert loaded is not None and loaded.line_id == ""
