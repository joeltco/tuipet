"""Approved follow-ups: X samples, daily rematch prizes and festival hunts."""
from tuipet import adventure as A, data, shop
from tuipet.adventurescreen import AdventurePanel, ZonePickPanel
from tuipet.pet import Pet


def _x():
    return next(e for z in A.MAPS for e in z['randoms'] if A.x_sample_wild(e))


def test_x_sample(monkeypatch):
    a = A.Adventure(Pet(num=100))
    a.holiday = 'festival'
    e = _x()
    monkeypatch.setattr(A.random, 'random', lambda: 0)
    calls = []
    monkeypatch.setattr(A.random, 'randrange', lambda n: calls.append(n) or 1)
    assert 'x_program' not in a.award_drop(e)
    assert calls == [40]
    monkeypatch.setattr(A.random, 'randrange', lambda n: 0)
    got = a.award_drop(e)
    assert len(got) == 2 and got[0] in a.zone['wild_drops'] and got[1] == 'x_program'
    assert 'x_program' not in a.award_drop(e)
    fresh = A.Adventure(Pet(num=100))
    monkeypatch.setattr(A.random, 'random', lambda: 1)
    assert fresh.award_drop(e) == ['x_program']
    ordinary = next(e for z in A.MAPS for e in z['randoms']
                    if data.load_requirements()[e['num']]['xantibody'] not in ('Natural', 'Induced'))
    assert A.Adventure(Pet(num=100)).award_drop(ordinary) == []
    fresh.replay = True
    assert fresh.award_drop(dict(e, boss=True)) == []
    monkeypatch.setattr(fresh, '_roll_encounter', lambda: e)
    fresh._x_sample = False
    fresh.travel()
    assert '1/40 on win (one/run)' in fresh.last
    pan = AdventurePanel(Pet(num=100))
    pan._fighting_enemy = e
    pan._battle_done(type('Loss', (), {'won': False})())
    assert not pan.adv._x_sample


def test_daily_rematch(monkeypatch):
    monkeypatch.setattr(A.random, 'randrange', lambda n: 0)
    for z in A.MAPS:
        p = Pet(num=100)
        a = A.Adventure(p, z)
        a.replay = True
        boss = a.boss
        assert a.award_bits(boss) > 0
        base = z['reward'][0]
        assert a.award_drop(boss) == [base]
        assert base in ('vitamin', 'hp_chip', 'hp_chip_g', 'omni_chip_g')
        assert a.award_drop(boss) == []
        again = A.Adventure(p, z)
        again.replay = True
        assert again.award_bits(boss) == 0
        assert again.award_drop(boss) == []
    p = Pet(num=100)
    a = A.Adventure(p)
    a.replay = True
    monkeypatch.setattr(A.random, 'randrange', lambda n: 1)
    assert a.award_bits(a.boss) > 0
    assert a.award_drop(a.boss) == []
    monkeypatch.setattr(A.random, 'randrange', lambda n: 0)
    assert a.award_bits(a.boss) == 0
    assert a.award_drop(a.boss) == []
    p.road_bounty['day'] = shop._today_ordinal() - 1
    assert a.award_bits(a.boss) > 0
    assert a.award_drop(a.boss) == [a.zone['reward'][0]]


def test_festival_weights(monkeypatch):
    a = A.Adventure(Pet(num=100))
    pool = [dict(_x(), chance=w) for w in (1, 2, 4, 8)]
    monkeypatch.setattr(a, '_wild_pool', lambda: pool)
    monkeypatch.setattr(A.random, 'random', lambda: 0)
    seen = []
    monkeypatch.setattr(A.random, 'choices', lambda pool, weights, k: seen.append(weights) or [pool[0]])
    for holiday, expected in ((None, [1, 2, 4, 8]), ('festival', [2, 4, 8, 8])):
        a.holiday = holiday
        a._roll_encounter()
        a._roll_hazard()
        assert seen[-2:] == [expected, expected]
    a.hunt = pool[0]['num']
    calls = []
    monkeypatch.setattr(A.random, 'randrange', lambda n: calls.append(n) or 0)
    a._roll_encounter()
    assert calls == [8]
    assert A.ENCOUNTER_CHANCE == .20
    pan = ZonePickPanel(Pet(num=100))
    pan.holiday = 'festival'
    text = pan.text().plain
    assert '1→2,2→4,4→8' in text
    assert len(text.splitlines()) <= 12
    assert all(len(row) <= 40 for row in text.splitlines())
