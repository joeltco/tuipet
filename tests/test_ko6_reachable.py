"""KO6 evolution gates are REACHABLE against the corrected (Mega-only) counter.

The counter fix (v0.2.466) made KO6 mean what DMX says -- "Defeat N Stage VI
Digimon", Stage VI being EN **Mega**.  That is 2.6x stricter than what shipped,
and 88 Mega evolutions plus 12 Ultimate ones hang off it.  So the gates have to
be re-proved REACHABLE, not merely harder:

  * combat is an HP RACE -- BASE_ATTACK is a flat 5 for Rookie..Mega, so both
    sides deal ~5/round and whoever has more HP wins;
  * the pet's HP cap is AGE-gated (HEALTH_CAP_LADDER: 30 HP at 13+ game-days),
    while an early random Mega has 25 HP;
  * therefore an aged, HP-trained pet out-lasts a Mega, and a young one cannot
    touch it.  That IS the gate: it demands investment, not luck.

These pins lock the property.  If someone re-loosens the counter, or nerfs the
HP ladder, or moves the Megas, the reachability argument dies here.
"""
import csv
import os
import random
import re
import collections

from tuipet import battle, data
from tuipet.pet import Pet

INF = 10 ** 6


def _megas():
    return [e for e in data.load_enemies() if e["stage"] == "Mega"]


def _early_megas():
    return [e for e in _megas()
            if e["map"] == 1 and e["zone"] in (4, 5) and not e["boss"]]


def _winrate(stage, power, hp, foes, n=120, seed=7):
    """FREE style: the pet's own smart pick every round.  (The harness used
    to throw RANDOM orders at an obedience-0 pet and lean on the refusal
    roll to substitute the smart pick; the refusal left with the discipline
    system -- BASIC VPET 2026-07-16 -- and a real player picks well anyway,
    so Free style is the honest reachability claim.)"""
    random.seed(seed)
    wins = 0
    for i in range(n):
        p = Pet(num=-1, stage=stage, vaccine=power, data_power=power, virus=power)
        p.full_health = hp
        p.free_style = True
        b = battle.Battle(p, dict(foes[i % len(foes)]))
        guard = 0
        while not b.over and guard < 300:
            b.play_round(None)                    # Free: _own_choice picks
            guard += 1
        wins += 1 if b.won else 0
    return wins / n


# ---------------------------------------------------------------- reachability

def test_an_aged_trained_ultimate_can_fell_a_mega():
    """The KO6 2+ gate (62 Mega evolutions) must be winnable by a good pet."""
    wr = _winrate("Ultimate", 60, 25, _early_megas())     # 10+ game-days of HP
    assert wr >= 0.4, f"KO6 is a WALL, not a gate: aged Ultimate wins only {wr:.0%}"


def test_a_young_pet_cannot_fell_a_mega():
    """...and it must still MEAN something: a fresh Ultimate has no business
    beating a Mega.  (If this ever passes, the gate is free again.)"""
    wr = _winrate("Ultimate", 60, 15, _early_megas())      # under ~7 game-days
    assert wr <= 0.05, f"a 15 HP Ultimate beats Megas {wr:.0%} of the time -- gate is toothless"


def test_the_hp_ladder_can_out_last_a_mega():
    """The whole reachability argument rests on this: the pet's HP cap must be
    able to exceed an early Mega's HP, or no amount of play clears the gate."""
    from tuipet.pet import HEALTH_CAP_LADDER
    best_cap = max(cap for _d, cap in HEALTH_CAP_LADDER)
    worst_early_mega = max(e["hp"] for e in _early_megas())
    assert best_cap > worst_early_mega, (
        f"HP cap {best_cap} <= early Mega HP {worst_early_mega}: KO6 becomes unreachable")


def test_megas_are_reachable_inside_map_one():
    """A KO6 gate you can only satisfy on map 3 would strand every early line."""
    assert any(e["map"] == 1 for e in _megas()), "no Mega on map 1 -- KO6 unsatisfiable early"


# ---------------------------------------------------------------- no holes

def _span(rule):
    m = re.search(r"KO6 (\d+)(\+|-(\d+))?", rule or "")
    if not m:
        return None
    lo = int(m.group(1))
    if m.group(2) == "+":
        return (lo, INF)
    if m.group(3):
        return (lo, int(m.group(3)))
    return (lo, lo)                       # bare "KO6 0" == EXACTLY zero


def test_no_ko6_coverage_hole():
    """⛔ 'KO6 0' means EXACTLY zero.  A node offering a `KO6 0` exit beside a
    `KO6 2+` exit would strand a pet sitting on exactly ONE kill -- it would
    match neither branch and could never evolve.  No node may have such a hole."""
    path = os.path.join(data._DATA, "lines.csv")
    rows = list(csv.DictReader(open(path)))
    node = collections.defaultdict(list)
    for r in rows:
        node[(r["LineID"], r["Parents"], r["Stage"])].append(r)

    holes = []
    for key, rs in node.items():
        spans = [_span(r["Rule"]) for r in rs]
        if not any(spans) or any(s is None for s in spans):
            continue            # a KO6-free exit accepts any count -> covered
        lo = min(s[0] for s in spans)
        hi = max(s[1] for s in spans)
        covered = set()
        for a, b in spans:
            covered |= set(range(a, min(b, 12) + 1))
        # an INTERIOR gap is the bug; counts BELOW the minimum are just
        # "not qualified yet", which is the gate doing its job.
        interior = [k for k in range(lo, min(hi, 12) + 1) if k not in covered]
        if interior:
            holes.append((key, interior))

    assert not holes, f"KO6 coverage holes strand pets mid-ladder: {holes[:5]}"
