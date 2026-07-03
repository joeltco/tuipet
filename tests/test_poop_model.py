"""Poop model vs DVPet PhysicalState.poop()/startPoop(): meals advance the
bowel gauge, sleep holds it to 2x, backlog makes a bigger pile.  (Placement
law lives in test_poop_placement.py.)  NOTE: poop does NOT touch hunger --
the coupling is eat -> bmGauge -> poop -> weight, one-directional."""
from tuipet.pet import Pet
from tuipet import data


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    p.obedience = 500            # out-roll checkRefused: these tests exercise the bowel model
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_poop_does_not_drain_hunger():
    p = _pet(hunger=3)
    p._do_poop()
    assert p.hunger == 3                     # weight/mood/filth only


def test_meals_advance_the_bowel_gauge():
    p = _pet(hunger=1)
    t0 = getattr(p, "_poop_t", 0)
    meat = next(f for f in data.load_foods() if f["name"] == "Meat")
    assert meat["bm"] > 0                    # Meat carries BMGauge=3 in the csv
    p.feed(meat)
    assert getattr(p, "_poop_t", 0) > t0     # eating -> pooping sooner


def test_sleeping_pet_holds_it_until_desperate():
    p = _pet(asleep=True, anim="sleep")
    p._poop_t = p._poop_interval + 1         # due, but asleep
    n0 = p.poop
    p.tick(1.0)
    assert p.poop == n0                      # held
    p._poop_t = p._poop_interval * 2 + 1     # desperate (gauge >= 2x max)
    p.tick(1.0)
    assert p.poop == n0 + 1                  # goes even in its sleep


def test_backlog_makes_a_bigger_pile_and_sheds_extra():
    p = _pet(weight=30)
    p._poop_t = p._poop_interval * 1.6       # awake, huge backlog (remainder >= half)
    w0 = p.weight
    p.tick(1.0)
    assert p.poop == 1
    base = p._poop_size()
    assert p.poop_sizes[0] == min(4, base + 1)   # one size bigger
    assert p._poop_t == 0                        # gauge zeroed
    # sheds strictly more than a normal poop would
    p2 = _pet(weight=30)
    p2._poop_t = p2._poop_interval + 1
    p2.tick(1.0)
    assert (30 - p.weight) > (30 - p2.weight)
