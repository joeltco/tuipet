"""Raid durability/security regressions, including real mixed-version wire traffic."""
import copy
import json
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from tuipet import battle, data, persistence
from tuipet.pet import Pet
from test_raid import _panel, _srv, _view, _mega
from test_sync import server as local_server, _conn  # noqa: F401, F811


def setup_hit(tmp_path, monkeypatch):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000)
    import raid_combat
    num = next(int(n) for n, r in raid_combat.SPECIES.items() if r['stage'] == 'Rookie')
    monkeypatch.setattr(srv, 'SAVES', {'joel': persistence.to_save_dict(Pet.from_num(num))})
    monkeypatch.setattr(srv, 'HOLDERS', {'joel': {'device': 'here'}})
    c = SimpleNamespace(name='joel', device='here')
    m = {'raid': srv.RAID['boss']['id'], 'request': 'request-00000001', 'damage': 99999999}
    return srv, c, m, raid_combat


def test_forged_damage_and_presence_never_control_credit(tmp_path, monkeypatch):
    srv, c, m, combat = setup_hit(tmp_path, monkeypatch)
    monkeypatch.setattr(combat, 'volley', lambda save, boss: (3, save['num']))
    c.pet = {'num': srv.RAID['boss']['num'], 'stage': 'Mega'}
    r = srv._raid_verified_hit(c, m, now=1001)
    assert r['ok'] and r['dealt'] == 15000
    assert srv._raid_verified_hit(c, dict(m, damage=-1), now=90000) == r
    assert srv.RAID['attempts']['joel']['left'] == 2
    srv.RAID = srv._load_raid()
    assert srv._raid_verified_hit(c, m, now=90000) == r
    assert srv.RAID['attempts']['joel']['left'] == 2
    wrong = dict(m, request='request-00000002', raid='obsolete')
    assert not srv._raid_verified_hit(c, wrong, now=1002)['ok']
    assert srv.RAID['attempts']['joel']['left'] == 2


def test_legacy_missing_cloud_and_nonholder_fail_safely(tmp_path, monkeypatch):
    srv, c, m, _ = setup_hit(tmp_path, monkeypatch)
    assert 'Update' in srv._raid_verified_hit(c, {'damage': 20}, now=1001)['why']
    c.device = 'elsewhere'
    assert not srv._raid_verified_hit(c, m, now=1001)['ok']
    c.device = 'here'
    srv.SAVES.clear()
    assert not srv._raid_verified_hit(c, m, now=1001)['ok']
    assert srv._raid_attempts('joel', now=1001)['left'] == 3


def test_remaining_hp_caps_rank_but_preserves_participation(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000)
    srv.RAID['boss']['hp'] = 1
    assert srv._raid_hit('casual', 20, srv.RAID['boss']['num'], now=1001)['dealt'] == 1
    row = srv.RAID['history'][-1]
    assert row['board']['casual']['damage'] == 1
    reward = srv._raid_claim('casual', row['id'], now=1002, acks=True)
    assert reward['ok'] and reward['defeated']


def test_clock_rollback_never_refunds_attempts(tmp_path):
    srv = _srv(tmp_path)
    for _ in range(3):
        srv._raid_hit('joel', 0, None, now=1000)
    assert srv._raid_attempts('joel', now=87400)['left'] == 3
    srv._raid_hit('joel', 0, None, now=87400)
    assert srv._raid_attempts('joel', now=1000)['left'] == 2
    assert srv._raid_attempts('joel', now=87400)['left'] == 2


def test_write_failure_never_acks_and_retry_recovers(tmp_path, monkeypatch):
    srv, c, m, combat = setup_hit(tmp_path, monkeypatch)
    monkeypatch.setattr(combat, 'volley', lambda save, boss: (1, save['num']))
    replace = srv.os.replace
    def fail_main(src, dst):
        if dst == srv.RAID_PATH:
            raise OSError('disk refused')
        replace(src, dst)
    monkeypatch.setattr(srv.os, 'replace', fail_main)
    assert not srv._raid_verified_hit(c, m, now=1001)['ok']
    monkeypatch.setattr(srv.os, 'replace', replace)
    srv.RAID = srv._load_raid()
    assert srv._raid_verified_hit(c, m, now=1001)['dealt'] == 5000
    assert srv._raid_attempts('joel', now=1001)['left'] == 2
    Path(srv.RAID_PATH).write_text('{broken', encoding='utf-8')
    srv.RAID = srv._load_raid()
    assert srv._raid_verified_hit(c, m, now=1001)['dealt'] == 5000


def test_invalid_schema_recovers_backup_and_never_resets(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000)
    original = copy.deepcopy(srv.RAID)
    Path(srv.RAID_PATH).write_text('{"boss": [], "board": []}', encoding='utf-8')
    assert srv._load_raid() == original
    Path(srv.RAID_PATH + '.bak').write_text('{} bad', encoding='utf-8')
    with pytest.raises(RuntimeError):
        srv._load_raid()


def test_old_history_copy_migrates_and_outstanding_survives_rotation(tmp_path):
    srv = _srv(tmp_path)
    fixture = Path(__file__).with_name('fixtures') / 'raid_legacy.json'
    Path(srv.RAID_PATH).write_bytes(fixture.read_bytes())
    srv.RAID = srv._load_raid()
    before = copy.deepcopy(srv.RAID)
    # Loading adds only fields; no existing board, counts or payouts change.
    for key in ('board', 'attempts', 'claimed', 'paid', 'history'):
        assert srv.RAID[key] == json.loads(fixture.read_text(encoding='utf-8'))[key]
    for i in range(8):
        srv._raid_rotate(now=2_000_000_000 + i * 900000)
    assert len(srv.RAID['history']) == 5
    assert srv._raid_award('regular-1')['id'] == before['history'][-1]['id']
    assert srv._raid_pending('paid-player')['items'] == ['vitamin']
    srv._save_raid()
    srv.RAID = srv._load_raid()
    assert srv._raid_pending('paid-player')


def test_reward_checkpoint_crash_and_replay(tmp_path, monkeypatch):
    p = Pet.from_num(_mega())
    p.bits = 100
    r = {'id': 'durable-claim', 'bits': 5000, 'items': ['vitamin'], 'defeated': True}
    # Simulate termination after the save commit, before settings projection/ACK.
    def crash(_):
        raise RuntimeError('power cut')
    with monkeypatch.context() as m:
        m.setattr(persistence, 'merge_progress', crash)
        with pytest.raises(RuntimeError):
            persistence.raid_checkpoint(p, r)
    saved = json.loads(Path(persistence.SAVE_PATH).read_text(encoding='utf-8'))
    assert saved['bits'] == 5100 and saved['inventory']['vitamin'] == 1
    assert saved['mega_kills'] == 1 and saved['progress']['raids'] == 1
    back, _ = persistence.pet_from_save(copy.deepcopy(saved))
    assert back is not None
    assert not persistence.raid_checkpoint(back, r)
    assert back.bits == 5100 and back.mega_kills == 1
    assert 'durable-claim' in persistence.to_save_dict(back)['progress']['raids_paid']


def test_reward_write_failure_changes_nothing_and_no_ack(monkeypatch):
    pan = _panel()
    before = copy.deepcopy(pan.pet.__dict__)
    def fail(*args, **kwargs):
        raise OSError('full')
    monkeypatch.setattr(persistence, '_atomic_write_json', fail)
    pan._apply_reward({'ok': True, 'id': 'failed', 'bits': 500, 'items': [], 'defeated': False})
    assert pan.pet.__dict__ == before
    assert not any(call[0] == 'ack' for call in pan.client.calls)
    assert 'not saved' in pan.msg


@pytest.mark.parametrize('bad', [None, -1, '500', 99999999])
def test_invalid_reward_never_stamps_receipt(bad):
    p = Pet.from_num(_mega())
    with pytest.raises(ValueError):
        persistence.raid_checkpoint(p, {'id': 'bad', 'bits': bad, 'items': []})
    assert not p.raid_receipts


def test_rate_budgets_account_ip_and_registration(tmp_path, caplog):
    srv = _srv(tmp_path)
    srv._RATE_BUCKETS.clear()
    for scope, limit, window in [('raid-account', 90, 60), ('raid-ip', 900, 60),
                                  ('registration-ip', 5, 3600), ('registration-name', 3, 86400)]:
        assert all(srv._rate_allow(scope, 'one', limit, window, now=1000) for _ in range(limit))
        assert not srv._rate_allow(scope, 'one', limit, window, now=1000)
        assert srv._rate_allow(scope, 'two', limit, window, now=1000)
        assert srv._rate_allow(scope, 'one', limit, window, now=1000 + window)
    assert 'rate rejected' in caplog.text


def test_generated_combat_matches_existing_engine(tmp_path):
    _srv(tmp_path)
    import raid_combat
    for stage in ('InTraining', 'Rookie', 'Champion', 'Ultimate', 'Mega'):
        num = next(int(n) for n, r in raid_combat.SPECIES.items() if r['stage'] == stage)
        p = Pet.from_num(num)
        p.energy, p.hunger, p.strength = p.max_energy, 4, 4
        boss = _mega()
        for seed in range(100):
            expected = battle.generate_raid(battle.Side.of_pet(p), battle.Side.wild(boss, boss=True),
                                            rng=random.Random(seed).random)[1]
            actual, _ = raid_combat.volley(persistence.to_save_dict(p), boss, rng=random.Random(seed).random)
            assert actual == expected


def test_cooldown_shows_error_claim_preview_and_12x40():
    pan = _panel()
    pan.client.raid = _view(_mega(), start=90000, now=100,
                           award={'id': 'pending', 'bits': 5000, 'items': 3})
    pan.msg = 'Claim sent…'
    assert 'Claim sent' in pan.text().plain
    pan.frame_i = 40
    assert '5000b + 3 items' in pan.text().plain
    for line in pan.text().plain.splitlines():
        from rich.cells import cell_len
        assert cell_len(line) <= 40
    assert len(pan.text().plain.splitlines()) == 12


def receive(ws, kind):
    for _ in range(30):
        m = json.loads(ws.recv(timeout=3))
        if m['t'] == kind:
            return m
    raise AssertionError('missing ' + kind)


def login(ws, name='wire', device='device-A', sync=True):
    ws.send(json.dumps({'t': 'login', 'name': name, 'pw': 'secret', 'device': device,
                        'boot': 123, 'sync_only': sync, 'pet': {'num': _mega()}}))
    return receive(ws, 'welcome')


def test_old_and_new_clients_against_local_server(local_server):  # noqa: F811
    with _conn(local_server) as ws:
        login(ws)
        ws.send(json.dumps({'t': 'raid_get'}))
        view = receive(ws, 'raid')
        ws.send(json.dumps({'t': 'raid_hit', 'damage': 20}))
        assert 'Update' in receive(ws, 'raid_hit')['why']
        # 0.6.37 can still view, claim (including ACK), and save after refusal.
        ws.send(json.dumps({'t': 'raid_claim', 'raid': 'missing', 'acks': True}))
        assert not receive(ws, 'raid_reward')['ok']
        num = next(n for n, r in data.load_sprites()[1].items() if r['stage'] == 'Rookie')
        save = persistence.to_save_dict(Pet.from_num(num))
        ws.send(json.dumps({'t': 'save', 'save': save}))
        assert receive(ws, 'saved')['ok']
        m = {'t': 'raid_hit', 'raid': view['boss']['id'], 'request': 'wire-request-0001',
             'damage': 99999999, 'num': _mega()}
        ws.send(json.dumps(m))
        hit = receive(ws, 'raid_hit')
        assert hit['ok'] and hit['dealt'] <= 100000
        ws.send(json.dumps(m))
        assert receive(ws, 'raid_hit') == hit
        ws.send(json.dumps({'t': 'raid_get'}))
        assert receive(ws, 'raid')['attempts'] == 2


def test_registration_limit_survives_reconnects(local_server):  # noqa: F811
    from websockets.sync.client import connect
    for i in range(21):
        with connect(local_server, open_timeout=3) as ws:
            ws.send(json.dumps({'t': 'login', 'name': f'new-{i}', 'pw': 'secret', 'sync_only': True}))
            kind = 'welcome' if i < 20 else 'login_failed'
            response = receive(ws, kind)
            if i == 20:
                assert 'limit' in response['msg']


def test_full_handler_claim_sync_ack_and_rate_limits(tmp_path, monkeypatch):
    """Run actual protocol routing without sockets (sandbox denies AF_INET)."""
    import asyncio
    srv = _srv(tmp_path)
    for attr, filename in [('ACCOUNTS_PATH', 'accounts.json'), ('SAVES_PATH', 'saves.json'),
                            ('HOLDERS_PATH', 'holders.json'), ('FEED_PATH', 'feed.jsonl')]:
        monkeypatch.setattr(srv, attr, str(tmp_path / filename))
    for attr in ('ACCOUNTS', 'SAVES', 'HOLDERS', 'CLIENTS', 'LEASES', 'BOOT_SEEN', '_RATE_BUCKETS'):
        monkeypatch.setattr(srv, attr, {})
    srv._raid_rotate()
    srv.RAID['boss']['hp'] = 1
    srv._raid_hit('wire', 1, None)
    rid = srv.RAID['history'][-1]['id']

    class Transport:
        remote_address = ('192.0.2.1', 1234)
        request = None
        def __init__(self):
            self.incoming = asyncio.Queue()
            self.outgoing = asyncio.Queue()
        def __aiter__(self):
            return self
        async def __anext__(self):
            value = await self.incoming.get()
            if value is None:
                raise StopAsyncIteration
            return json.dumps(value)
        async def send(self, text):
            await self.outgoing.put(json.loads(text))

    async def direct(fn, *args):
        return fn(*args)
    monkeypatch.setattr(srv.asyncio, "to_thread", direct)

    async def run():
        ws = Transport()
        task = asyncio.create_task(srv.handler(ws))
        async def exchange(message, kind):
            await ws.incoming.put(message)
            for _ in range(20):
                response = await asyncio.wait_for(ws.outgoing.get(), 3)
                if response['t'] == kind:
                    return response
            raise AssertionError('missing response')
        try:
            assert (await exchange({'t': 'login', 'name': 'wire', 'pw': 'secret',
                                    'sync_only': True, 'device': 'held', 'boot': 123}, 'welcome'))
            assert 'Update' in (await exchange({'t': 'raid_hit', 'damage': 99999}, 'raid_hit'))['why']
            reward = await exchange({'t': 'raid_claim', 'raid': rid, 'acks': True}, 'raid_reward')
            assert reward['ok']
            # A lost response is the same durable grant.
            assert await exchange({'t': 'raid_claim', 'raid': rid, 'acks': True}, 'raid_reward') == reward
            p = Pet.from_num(_mega())
            persistence.raid_checkpoint(p, reward)
            checkpoint = persistence.to_save_dict(p)
            # Failure to write cloud must leave the outstanding reward held.
            store = srv._store_save
            async def fail(*args):
                raise OSError('full disk')
            monkeypatch.setattr(srv, '_store_save', fail)
            response = await exchange({'t': 'raid_ack', 'protocol': 2, 'raid': rid,
                                       'save': checkpoint}, 'raid_reward')
            assert not response['ok'] and srv._raid_pending('wire')
            monkeypatch.setattr(srv, '_store_save', store)
            await ws.incoming.put({'t': 'raid_ack', 'protocol': 2, 'raid': rid, 'save': checkpoint})
            await exchange({'t': 'raid_get'}, 'raid')
            # Drain the earlier queued claim view, then use processing barrier.
            await exchange({'t': 'raid_get'}, 'raid')
            await asyncio.sleep(0)
            assert srv._raid_pending('wire') is None
            assert srv._load_saves()['wire']['bits'] == checkpoint['bits']
            assert srv._load_raid()['claimed'][rid] == ['wire']
            # A replayed ACK carries an old snapshot; never rewind newer play.
            newer = dict(checkpoint, bits=checkpoint['bits'] + 100)
            await srv._store_save('wire', newer)
            await ws.incoming.put({'t': 'raid_ack', 'protocol': 2, 'raid': rid, 'save': checkpoint})
            await exchange({'t': 'raid_get'}, 'raid')
            await asyncio.sleep(0)
            assert srv._load_saves()['wire']['bits'] == newer['bits']
            srv.RAID['boss']['start'] = srv.time.time() - 1
            srv.RAID['boss']['end'] = srv.time.time() + 604800
            verified = await exchange({'t': 'raid_hit', 'raid': srv.RAID['boss']['id'],
                                       'request': 'handler-forge-0001', 'damage': 99999999,
                                       'stage': 'Mega', 'num': _mega()}, 'raid_hit')
            assert verified['ok'] and verified['authoritative'] and verified['dealt'] <= 2000000
            # Per-account limit applies through the actual handler boundary.
            srv._RATE_BUCKETS[('raid-account', 'wire')] = __import__('collections').deque(
                [srv.time.monotonic()] * 90)
            denied = await exchange({'t': 'raid_hit', 'raid': srv.RAID['boss']['id'],
                                     'request': 'rate-request-0001'}, 'raid_hit')
            assert denied['retryable'] and 'limit' in denied['why']
        finally:
            await ws.incoming.put(None)
            await asyncio.wait_for(task, 3)
    asyncio.run(run())


def test_outbox_survives_new_client_and_receipt_clears_it():
    from tuipet.net import LobbyClient
    c = LobbyClient('ws://127.0.0.1:9', 'joel')
    c.raid = {'protocol': 2, 'boss': {'id': 'boss-1'}}
    c.raid_hit(999, 'boss-1', 'durable-request-1')
    assert persistence.raid_outbox('joel')[0]['request'] == 'durable-request-1'
    again = LobbyClient('ws://127.0.0.1:9', 'joel')
    again._handle(json.dumps({'t': 'raid', 'protocol': 2, 'boss': {'id': 'boss-1'}}))
    assert again._q.get_nowait()['request'] == 'durable-request-1'
    again._handle(json.dumps({'t': 'raid_hit', 'ok': True, 'request': 'durable-request-1'}))
    assert persistence.raid_outbox('joel') == []


def test_new_client_does_not_replay_hits_to_old_server():
    from tuipet.net import LobbyClient
    c = LobbyClient('ws://127.0.0.1:9', 'joel')
    c.raid = {'boss': {'end': 1000}}
    c.raid_hit(3)
    assert persistence.raid_outbox('joel') == []
    assert c._q.get_nowait()['damage'] == 3
    c._handle(json.dumps({'t': 'raid', 'boss': {'end': 1000}}))
    assert c._q.empty()


def test_claim_partial_write_recovers_same_grant(tmp_path, monkeypatch):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000)
    srv.RAID['boss']['hp'] = 1
    srv._raid_hit('joel', 20, None, now=1001)
    rid = srv.RAID['history'][-1]['id']
    replace = srv.os.replace
    def fail_primary(src, dst):
        if dst == srv.RAID_PATH:
            raise OSError('primary refused')
        replace(src, dst)
    with monkeypatch.context() as m:
        m.setattr(srv.os, 'replace', fail_primary)
        assert not srv._raid_claim('joel', rid, now=1002, acks=True)['ok']
    srv.RAID = srv._load_raid()
    held = copy.deepcopy(srv.RAID['paid'][rid]['joel'])
    again = srv._raid_claim('joel', rid, now=1003, acks=True)
    assert again['ok'] and again['bits'] == held['bits'] and again['items'] == held['items']
    assert srv.RAID['claimed'][rid] == ['joel']


def test_oversized_live_pool_scales_once_without_resetting_board(tmp_path):
    srv = _srv(tmp_path)
    srv._raid_rotate(now=1000)
    b = srv.RAID['boss']
    b['max_hp'], b['hp'] = 440000000, 220000000
    srv.RAID['board'] = {'regular': {'damage': 220000000, 'ts': 1001}}
    srv._save_raid()
    loaded = srv._load_raid()
    assert loaded['boss']['id'] == b['id']
    assert loaded['boss']['max_hp'] == 30000000 and loaded['boss']['hp'] == 15000000
    assert loaded['board'] == srv.RAID['board']
    srv.RAID = loaded
    srv._save_raid()
    assert srv._load_raid()['boss']['hp'] == 15000000
