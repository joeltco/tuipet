"""Joel's month-long festival rulings, with one injected local calendar."""
import datetime as dt
import json

import pytest
from rich.cells import cell_len

from tuipet import adventure as A, holidays as H, persistence as P, shop, statusbox, tournament as T
from tuipet.pet import Pet


def on(monkeypatch, month, day, year=2026):
    date = dt.date(year, month, day)
    monkeypatch.setattr(T, "_today", lambda: date)
    return date


def pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", bits=100000, obedience=500)




@pytest.mark.parametrize('month,day,season,exact', [
    (9,30,None,False), (10,1,'halloween',False), (10,16,'halloween',False),
    (10,30,'halloween',False), (10,31,'halloween',True), (11,1,None,False),
    (11,30,None,False), (12,1,'christmas',False), (12,24,'christmas',False),
    (12,25,'christmas',True), (12,26,'christmas',False), (12,31,'christmas',False),
    (1,1,None,True)])
@pytest.mark.parametrize('year', [2026,2027])
def test_calendar_edges(monkeypatch, month, day, season, exact, year):
    d = on(monkeypatch, month, day, year)
    assert T.holiday_season() == T.holiday_season(d) == season
    assert bool(T.holiday()) == exact
    assert bool(T.festival()) == bool(exact or season)
    banner = statusbox.festival_line()
    assert bool(banner) == bool(exact or season)
    if season:
        assert season.title() in banner
    assert cell_len(banner or '') <= 24


def test_parked_run_refreshes_bits_pool_and_finds(monkeypatch):
    on(monkeypatch,10,31)
    p = pet()
    a = A.Adventure(p, zone=A.MAPS[20])
    e = {'num':230, 'bits':(10,10)}
    assert a.award_bits(e) == 20
    assert 230 in {e['num'] for e in a._wild_pool()}
    a.loc = 1
    monkeypatch.setattr(A.random, 'random', lambda: .2)
    monkeypatch.setattr(A.random, 'choice', lambda pool: 'capsule_a')
    assert a._roll_find() == ('capsule_a', True)
    on(monkeypatch,11,1)
    assert a.award_bits(e) == 10
    assert 230 not in {e['num'] for e in a._wild_pool()}
    assert a._roll_find() is None
    on(monkeypatch,12,1)
    assert a.award_bits(e) == 10
    assert a._roll_find() == ('capsule_a', True)
    on(monkeypatch,12,25)
    assert a.award_bits(e) == 20
    on(monkeypatch,12,26)
    assert a.award_bits(e) == 10
    on(monkeypatch,1,1,2027)
    assert a._roll_find() == ('capsule_a', True)


@pytest.mark.parametrize('month,day,floor', [(10,1,16),(10,31,24),(12,1,16),(12,25,24),(12,26,16)])
def test_exact_species_weights_pools_and_hunts(monkeypatch, month, day, floor):
    on(monkeypatch,month,day)
    before = json.dumps(A.MAPS, sort_keys=True)
    expected = ({6:[30,32,59],14:[121,99,601,181],20:[479,216,230],28:[1031]}
                if month == 10 else {3:[26,39],5:[26,39],4:[991],9:[175],14:[136]})
    for zi,z in enumerate(A.MAPS):
        targets = expected.get(zi, [])
        assert list(A.season_targets(z)) == targets
        pool = A.effective_pool(z)
        assert len(pool) == len({e['num'] for e in pool})
        assert set(targets) <= A.hunt_targets(z).keys()
        for e in pool:
            w = A.spawn_weight(e,T.festival())
            base = A.spawn_weight(dict(e,season_target=False),True)
            assert w == (max(base,floor) if e['num'] in targets else base)
            if e['num'] in targets:
                assert e['stage'] == z['tier']
    assert json.dumps(A.MAPS, sort_keys=True) == before
    on(monkeypatch,11,1)
    assert all(A.effective_pool(z) == [dict(e,season_target=False) for e in z['randoms']] for z in A.MAPS)






def test_old_saves_sync_and_season_notice(monkeypatch):
    P.save_settings({'progress':{'wins':7}})
    on(monkeypatch,10,1)
    assert H.notice().startswith('Halloween is here!')
    assert H.notice() is None
    block=P.progress_for_sync()
    assert P.merge_progress(block) is False
    assert P._prog()['wins'] == 7
    assert 'holiday_notice_seen' in block
    on(monkeypatch,11,1)
    assert H.notice() is None
    on(monkeypatch,12,1)
    assert H.notice().startswith('Christmas is here!')
    on(monkeypatch,10,1,2027)
    assert H.notice().startswith('Halloween is here!')


def test_the_seasonal_tint_is_gone(monkeypatch):
    """Joel 2026-10-17 ("Theres seasonal colors?? Where??" -> A): the home tint
    was invisible at 15% and muddy brown when stronger; it is removed, along
    with its Options toggle.  October home art is the plain scene."""
    from tuipet import arena
    from tuipet.optionsscreen import _ROWS
    on(monkeypatch,10,16)
    assert not hasattr(H, 'tint') and 'colors' not in _ROWS
    p=pet()
    assert arena.Screen()._background.__code__.co_names.count('tint') == 0
    assert p.background() == p.background()


def test_capsule_opening_day_rarity(monkeypatch):
    on(monkeypatch,12,16)
    p=pet()
    cap=[]
    monkeypatch.setattr(p,'_pick_gift',lambda festival=False:cap.append(festival) or 'fish')
    for month,day,expected in [(12,16,True),(12,26,True),(1,2,False)]:
        on(monkeypatch,month,day)
        p.add_item('capsule_a')
        assert p.use_item('capsule_a')
        assert cap[-1] is expected




def test_selected_hunt_expires_without_crashing(monkeypatch):
    on(monkeypatch,10,31)
    a=A.Adventure(pet(),zone=A.MAPS[20],hunt=230)
    assert a.hunt==230
    on(monkeypatch,11,1)
    a.loc=1
    monkeypatch.setattr(A.random,'random',lambda:0)
    monkeypatch.setattr(A.random,'randrange',lambda *args:0)
    assert a._roll_encounter()['num']!=230




@pytest.mark.parametrize('month,day,fun', [(9,30,False),(10,1,True),(10,31,True),(11,1,False),
                                         (11,30,False),(12,1,True),(12,26,True),(12,31,True),(1,2,False)])
def test_cups_and_pet_gift_calendar(monkeypatch,month,day,fun):
    on(monkeypatch,month,day)
    p=Pet(num=100,stage='Champion',obedience=80,attribute='Vaccine',bits=100000)
    sched=T.schedule(p)
    slot=next(i for i,tid in enumerate(sched) if tid>=0 and i!=T._hour(p)
              and T._eligibility_rest(p,T.trophy_by_id(tid)) is None)
    assert (T.eligibility_at(p,T.trophy_by_id(sched[slot]),slot) is None)==fun
    rolls=[]
    gifts=[]
    monkeypatch.setattr('tuipet.petbody.random.randrange',lambda n:rolls.append(n) or 0)
    monkeypatch.setattr(p,'_pick_gift',lambda festival=False:gifts.append(festival) or 'fish')
    p.gift_t=0
    p.hunger=4
    p.energy=12
    p._check_gift_call(100000)
    assert gifts==[fun]
    from tuipet.petbase import OBEDIENCE_REFUSAL_CAP, GIFT_CHANCE_FACTOR, GIFT_FESTIVAL_MULT
    chance=int(OBEDIENCE_REFUSAL_CAP-p.obedience+GIFT_CHANCE_FACTOR)
    assert rolls[-1]==(max(1,chance//GIFT_FESTIVAL_MULT) if fun else chance)




@pytest.mark.parametrize('month,day', [(10,1),(10,31),(12,1),(12,25),(12,31)])
def test_home_egg_shop_picker_budgets_and_real_tint(monkeypatch,month,day):
    from rich.text import Text
    from tuipet import arena, theme
    from tuipet.adventurescreen import ZonePickPanel
    from tuipet.shopscreen import ShopPanel
    on(monkeypatch,month,day)
    p=pet()
    p.adv_progress=29
    egg=Pet.new_egg()
    for subject in (p,egg):
        lines=statusbox.egg_lines(subject) if subject.num==-1 else statusbox.home_lines(subject)
        assert len(lines)<=16
        assert all(cell_len(Text.from_markup(ln).plain)<=26 for ln in lines)
        assert T.holiday_season().title() in '\n'.join(lines)
    for panel in (ZonePickPanel(p),ShopPanel(p)):
        lines=panel.text().plain.splitlines()
        assert len(lines)<=12
        assert all(cell_len(ln)<=40 for ln in lines)
    screen=arena.Screen()
    screen.on_mount()
    painted=[]
    screen.update=painted.append
    old_theme=theme.current()
    try:
        for name in ('mono','gameboy'):
            theme.apply(name)
            screen.paint(p)
            assert all(cell_len(ln)<=40 for ln in painted[-1].plain.splitlines())
            assert len(painted[-1].plain.splitlines())<=12
    finally:
        theme.apply(old_theme)


@pytest.mark.parametrize('month,day,expected', [(10,1,[]),(10,31,['Halloween Festival']),
                                             (12,1,[]),(12,25,['Christmas Festival']),
                                             (12,26,[])])
def test_conquest_credit_remains_exact_date(monkeypatch,month,day,expected):
    from types import SimpleNamespace
    from tuipet.adventurescreen import AdventurePanel
    on(monkeypatch,month,day)
    panel=AdventurePanel(pet(),zone=A.MAPS[0])
    panel._fighting_boss=True
    panel._fighting_enemy=A.MAPS[0]['bosses'][0]
    panel._battle_done(SimpleNamespace(won=True))
    assert P._prog().get('festivals',[])==expected


@pytest.mark.parametrize('month,day,fun', [(9,30,False),(10,1,True),(10,31,True),(11,1,False),
                                         (11,30,False),(12,1,True),(12,25,True),(12,26,True),(12,31,True),(1,2,False)])
def test_existing_goods_seasonal_discounts(monkeypatch, month, day, fun):
    on(monkeypatch,month,day)
    p=pet()
    assert len(shop.CATALOG)==112
    for e in shop.home_stock(pet=p):
        if fun and shop.deal_ok(e['key']):
            assert e['deal'] and e['price']==shop.deal_price(e['base_price'])
    for tid in (3,6,14,20):
        for e in shop.town_stock(tid,pet=p):
            if fun and shop.deal_ok(e['key']):
                assert e['deal'] and e['price']==shop.deal_price(e['base_price'])
    assert 'holiday_receipts' not in P._PROG_SETS
