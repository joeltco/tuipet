"""Completeness-critic sweep pins (2026-07-06): the last uncited canon
mechanics -- the attribute-trade compensation and the away-filth gate.
(The sweep's dead list: checkFilthyPersonality is DEFINED-NEVER-CALLED,
CareEffect Pause* flags all FALSE on the one shipped row, EvolFood ships
on a single row consumed by the audited food-req path.)"""
from tuipet.pet import Pet
from tuipet import data


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=140)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_attribute_trades_conserve_the_total():
    """compensateAttributes (x3 rotations): the six +-15 trade toys drain the
    OTHER powers when one bottoms out -- max(0,) used to forgive the debt."""
    p = _pet(vaccine=5, data_power=20, virus=0, compliance=True)
    e = data.consumable_by_key("i:0") or {}
    board = next(e for e in data.home_shop_pool()
                 if e.get("vaccine", 0) < 0 and e.get("data", 0) > 0)
    total0 = p.vaccine + p.data_power + p.virus
    p.vaccine += board["vaccine"]              # -15: vaccine -> -10
    p.data_power += board["data"]              # +15
    p._compensate_attrs()
    assert p.vaccine == 0
    assert p.vaccine + p.data_power + p.virus == total0   # conserved
    q = _pet(vaccine=0, data_power=0, virus=0)
    q.vaccine -= 15                            # nothing to borrow: the safe floor
    q._compensate_attrs()
    assert (q.vaccine, q.data_power, q.virus) == (0, 0, 0)


def test_the_home_mess_cannot_sicken_a_traveler():
    """poopable() gates countFilth on _isHome: away, the filth neither sours
    nor sickens (the piles wait for the homecoming)."""
    p = _pet(poop=4, poop_sizes=[2, 2, 2, 2])
    p.away = True
    m0 = p.mood
    for _ in range(1900):                      # past the 1800s filth window
        p._filth_effects(1.0)
    assert not p.sick
    p.away = False
    for _ in range(1900):
        p._filth_effects(1.0)
    # (the home-again mood bite left with the mood system)
