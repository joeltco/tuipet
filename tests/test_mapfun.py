"""Approved mapfun #1–5; exact egg IDs stay separate from album names."""
import random
from collections import Counter

from tuipet import adventure as A, data, egg, persistence, shop
from tuipet.adventurescreen import AdventurePanel, ZonePickPanel
from tuipet.pet import Pet


def test_hunt_board(monkeypatch):
    p = Pet(num=100)
    z = A.MAPS[0]
    persistence.wild_beaten_add(0, z['randoms'][0]['num'])
    pan = ZonePickPanel(p)
    text = pan.text().plain
    assert 'beaten 1/' in text and 'H hunt: none' in text
    assert 'finds 12%' in text
    assert all(len(r) <= 40 for r in text.split('\n'))
    assert persistence.get_album() == set()


def test_rare_treasure():
    for z in A.MAPS:
        assert {'life_recovery', 'rest_kit'} <= set(z['find_keys'])
        assert 'shortcut' not in z['find_keys']
        for n in range(4):
            pool = A.find_pool(z, {'maps': set(range(n))})
            for k in ('life_recovery', 'rest_kit'):
                assert (k in pool) == (n >= shop.ADVENTURE_GATES[k])
    assert A.FIND_CHANCE == .12
    assert shop.tier_weight('life_recovery') == 2
    assert shop.tier_weight('rest_kit') == 1


def test_wild_drop(monkeypatch):
    a = A.Adventure(Pet(num=100))
    a.holiday = 'festival'
    a.replay = True
    monkeypatch.setattr(A.random, 'random', lambda: .119)
    assert a.award_drop(a.zone['randoms'][0])[0] in a.zone['wild_drops']
    monkeypatch.setattr(A.random, 'random', lambda: .12)
    assert a.award_drop(a.zone['randoms'][0]) == []
    for z in A.MAPS:
        assert not set(z['wild_drops']) & set(A.ROAD_ITEMS)
        assert set(z['wild_drops']) == set(z['find_keys']) - {'life_recovery', 'rest_kit'}


def test_drop_only_win_and_message(monkeypatch):
    pan = AdventurePanel(Pet(num=100))
    wild = pan.adv.zone['randoms'][0]
    monkeypatch.setattr(A.random, 'random', lambda: 0)
    for result in (None, type('Loss', (), {'won': False})()):
        pan._fighting_enemy = wild
        pan._battle_done(result)
        assert pan.adv.drops == 0
    pan._fighting_enemy = wild
    pan._battle_done(type('Win', (), {'won': True})())
    assert pan.adv.drops == 1
    assert 'Victory! It drops' in pan.adv.last
    assert persistence.get_album() == set()


def test_rare_weights():
    found = set()
    for z in A.MAPS:
        for e in z['randoms']:
            r = data.load_requirements()[e['num']]
            weight = 1 if r['hidden_evo'] else {'Natural': 4, 'Induced': 2}.get(r['xantibody'], 8)
            assert e['chance'] == weight
            found.add(weight)
            assert not data.is_placeholder(e['num'])
            assert not 1651 <= e['num'] <= 1658
            assert z['id'] == 'islandnight' or not 1623 <= e['num'] <= 1650
    assert found == {1, 2, 4, 8}


def test_rare_encounter_text(monkeypatch):
    a = A.Adventure(Pet(num=100))
    e = next(e for z in A.MAPS for e in z['randoms'] if e['chance'] == 1)
    monkeypatch.setattr(a, '_roll_encounter', lambda: e)
    a.travel()
    assert '(Hidden)' in a.last
    from tuipet.battlescreen import BattlePanel
    panel = BattlePanel(a.pet, enemy=e, wild=True)
    panel._render_scene_frame({"m": "reveal", "view": "foe"})
    assert panel.hud_note.startswith('Hidden:')


def test_hunt_rate_and_reachability(monkeypatch):
    assert egg.unreachable_wild_rows() == []
    targets = [(z, n) for z in A.MAPS for n in A.hunt_targets(z)]
    assert targets
    for z, n in targets:
        assert any(e['num'] == n and e['chance'] > 0 for e in z['randoms'])
        zi = A.zone_index(z)
        assert n not in A.hunt_targets(z, {'wilds_beaten': {f'{zi}:{n}'}})
    z, n = targets[0]
    a = A.Adventure(Pet(num=100), z, hunt=n)
    assert a.hunt == n
    # Remove residual target probability to measure the reserved branch alone.
    monkeypatch.setattr(A, 'ENCOUNTER_CHANCE', 1)
    other = next(e for e in z['randoms'] if e['num'] != n)
    monkeypatch.setattr(A.random, 'choices', lambda *args, **kw: [other])
    state = random.getstate()
    try:
        random.seed(20261015)
        counts = Counter(a._roll_encounter()['num'] for _ in range(32000))
    finally:
        random.setstate(state)
    assert abs(counts[n] / 32000 - 1/8) < .006
    assert A.Adventure(Pet(num=100), z).hunt is None
    assert A.Adventure(Pet(num=100), z, hunt=-1).hunt is None
    pan = ZonePickPanel(Pet(num=100, adv_progress=len(A.MAPS)))
    pan.cursor = pan.indices.index(A.zone_index(z))
    pan.key('h')
    assert pan.key('enter')[1] == (z, n)
