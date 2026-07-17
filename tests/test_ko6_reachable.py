"""KO6 reachability under the 0.5 HP race (rewritten 2026-07-17; the old
harness drove the classic engine's trained-HP axis, which left with it).

The gate's new axes are the race's own: the trained FORM (mega doubles 90%
of blasts), the win-rate term, training experience and full care gauges.
An underdog Ultimate fells a Mega roughly 1 bout in 3 at its best -- a
grind-gate, not a wall -- while a Mega meets a Mega evenly, and raids pay
KO6 at claim besides.  Pin the GRADIENT and the floor, not old numbers."""
import random

from tuipet import battle, data
from tuipet.pet import Pet


def _a_mega():
    return next(n for n in range(2000)
                if data.record_for(n).get("stage") == "Mega"
                and not data.is_placeholder(n))


def _winrate(stage, form, wins, batt, tr, trials=400):
    random.seed(9)
    mega = _a_mega()
    won = 0
    for _ in range(trials):
        p = Pet(num=205, stage=stage, attribute="Vaccine", obedience=500)
        p.world_seconds = 600.0
        p.energy = p.max_energy
        p.saved_hit_type = form
        p.wins, p.battles = wins, batt
        p.stage_trainings = p.total_trainings = tr
        me, foe = battle.Side.of_pet(p), battle.Side.wild(mega)
        _seq, mh, fh = battle.generate(me, foe)
        won += (fh <= 0 and mh > 0) or (mh > 0 and fh > 0 and mh > fh)
    return won / trials


def test_a_trained_ultimate_can_grind_ko6():
    wr = _winrate("Ultimate", "mega", 30, 40, 300)
    assert wr >= 0.22, f"KO6 is a WALL, not a gate: the trained Ultimate wins {wr:.0%}"


def test_the_form_and_care_gradient_has_teeth():
    trained = _winrate("Ultimate", "mega", 30, 40, 300)
    young = _winrate("Ultimate", "normal", 0, 0, 5)
    sloppy = _winrate("Ultimate", "miss", 0, 0, 0)
    assert trained > young > sloppy        # training and form MEAN something
    assert young <= 0.25                   # a fresh Ultimate has no business here


def test_a_mega_meets_a_mega_evenly():
    wr = _winrate("Mega", "mega", 30, 40, 300)
    assert wr >= 0.45                      # the intended KO6 farm: peer fights
