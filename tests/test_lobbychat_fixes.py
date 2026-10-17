"""Approved lobby/chat fixes; all transport probes use in-memory sockets."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest
from rich.cells import cell_len

from tuipet.net import LobbyClient, parse_msg
from tuipet.lobbybout import _clamp_card
from test_lobby_audit import _panel
from test_lobby_chat_polish import _rendered

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import server

spec = importlib.util.spec_from_file_location('lobby_admin_cli', Path(server.__file__).with_name('admin.py'))
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


class Wire:
    remote_address = ('192.0.2.1', 1)

    def __init__(self, frames=()):
        self.frames = iter(frames)
        self.sent = []
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return json.dumps(next(self.frames))
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, text):
        self.sent.append(json.loads(text))

    async def close(self):
        self.closed = True


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    for name in ('CLIENTS', 'ACCOUNTS', 'MODERATION', '_RATE_BUCKETS'):
        monkeypatch.setattr(server, name, {})
    monkeypatch.setattr(server, 'FEED_PATH', str(tmp_path / 'feed'))
    monkeypatch.setattr(server, 'MODERATION_PATH', str(tmp_path / 'moderation.json'))
    monkeypatch.setattr(server, 'CHAT_BACKLOG', server.deque(maxlen=30))
    monkeypatch.setenv('TUIPET_ADMIN_KEY', 'secret')
    monkeypatch.setattr(server, '_verify', lambda pw, acc: pw == 'ok')
    # No executor wakeup sockets are available in the sandbox.
    async def inline(func, *args):
        return func(*args)
    monkeypatch.setattr(server.asyncio, 'to_thread', inline)
    monkeypatch.setattr(server, 'PENDING', {})
    server.ACCOUNTS['alice'] = {'name': 'alice'}
    return tmp_path


def login(**kw):
    return dict(t='login', name='alice', pw='ok', **kw)


def test_flood_buckets_refill_and_reset(isolated):
    for kind, burst, refill in [('chat', 8, .5), ('pm', 8, .5), ('invites', 6, .1), ('pet', 12, 1), ('relay', 60, 6)]:
        assert all(server._token_allow(kind, 'alice', burst, refill, now=0) for _ in range(burst))
        assert not server._token_allow(kind, 'alice', burst, refill, now=0)
        assert server._token_allow(kind, 'alice', burst, refill, now=1 / refill)
    server._RATE_BUCKETS.clear()
    assert server._message_budget('chat', 'alice')


@pytest.mark.parametrize('kind,count', [('chat', 9), ('pm', 9), ('invite', 7), ('pet', 13), ('relay', 61)])
def test_flood_errors_are_visible(isolated, kind, count):
    ws = Wire([login()] + [dict(t=kind, text='hi', to='999', payload={}) for _ in range(count)])
    asyncio.run(server.handler(ws))
    error = next(m for m in ws.sent if 'slow down' in m.get('msg', ''))
    client = LobbyClient('', 'alice')
    client._handle(json.dumps(error))
    assert 'slow down' in client.state.error


def test_password_budgets_precede_hashing(isolated, monkeypatch):
    calls = []
    monkeypatch.setattr(server, '_verify', lambda *args: calls.append(args) or False)
    async def no_sleep(*args):
        pass
    monkeypatch.setattr(server.asyncio, 'sleep', no_sleep)
    for _ in range(10):
        asyncio.run(server.handler(Wire([login()])))
    ws = Wire([login()])
    asyncio.run(server.handler(ws))
    assert len(calls) == 10
    assert 'Too many failed' in ws.sent[0]['msg']
    # The name budget follows the account across IPs.
    ws = Wire([login()]); ws.remote_address = ('192.0.2.2', 1)
    asyncio.run(server.handler(ws))
    assert len(calls) == 10
    # The IP budget also protects another account.
    server.ACCOUNTS['bob'] = {'name': 'bob'}
    asyncio.run(server.handler(Wire([dict(t='login', name='bob', pw='bad')])))
    assert len(calls) == 10


def test_ip_socket_cap(isolated):
    for i in range(20):
        c = server.Client(Wire())
        server.CLIENTS[c.id] = c
    ws = Wire([login()])
    asyncio.run(server.handler(ws))
    assert 'Too many connections' in ws.sent[0]['msg']


@pytest.mark.parametrize('frame', [dict(t='pm', to=[]), dict(t='invite', to={}), dict(t='invite', to=2.5),
    dict(t='relay', to='1', payload=[]), dict(t='relay', to='1', payload={'card': 7})])
def test_wire_envelopes_rejected(isolated, frame):
    ws = Wire([login(), frame])
    asyncio.run(server.handler(ws))
    assert any(m.get('msg') == 'Invalid message envelope.' for m in ws.sent)


@pytest.mark.parametrize('payload', [[1], 7, 'bad', {'card': []}])
def test_client_ignores_bad_relay(payload):
    pan, _ = _panel()
    pan.partner = (2, 'mika')
    pan._on_relay({'from_id': 2, 'payload': payload})
    assert pan.phase == 'lobby'
    assert isinstance(_clamp_card(payload if not isinstance(payload, dict) else 7), dict)


def test_control_cleaning_on_all_boundaries():
    text = 'a\x00\x1b\t\x85\u202e\u2066\u200b\ufeff b'
    assert server._clean(text, 100) == 'a b'
    m, _ = parse_msg(json.dumps({'t': 'pm', 'from_name': text, 'text': text}))
    assert m['text'] == m['from_name'] == 'a b'
    assert admin._fmt({'kind': 'chat', 'name': text, 'text': text, 'ts': 'now'}) == 'now  <a b> a b'


@pytest.mark.parametrize('name', ['admin', 'SERVER', 'system', 'tuipet', 'mod', '📢alice', '✉alice', '\u200b'])
def test_new_system_names_rejected(isolated, name):
    ws = Wire([dict(t='login', name=name, pw='ok')])
    asyncio.run(server.handler(ws))
    assert ws.sent[0]['t'] == 'login_failed'


def test_legacy_reserved_and_control_names_still_login(isolated):
    for name in ('admin', '\u202ealice'):
        server.ACCOUNTS[name.lower()] = {'name': name}
        ws = Wire([dict(t='login', name=name, pw='ok')])
        asyncio.run(server.handler(ws))
        assert ws.sent[0]['t'] == 'welcome'


def test_private_reconnect_waits_for_scope_ack():
    async def probe():
        c = LobbyClient('', 'alice')
        c.state.room = 'friends'
        c._ws = Wire()
        c._on_connect()
        c.chat('private')
        sender = asyncio.create_task(c._send_loop())
        await asyncio.sleep(0)
        assert not c._ws.sent
        c._handle(json.dumps(dict(t='welcome', id=1, name='alice')))
        await asyncio.sleep(0)
        assert c._ws.sent == [dict(t='room', code='friends')]
        c._handle(json.dumps(dict(t='chat', replay=True, from_name='bob', text='main')))
        assert not c.state.chat
        c._handle(json.dumps(dict(t='room_ok', room='friends')))
        await asyncio.sleep(0)
        assert c._ws.sent[-1] == dict(t='chat', text='private')
        sender.cancel()
        await asyncio.gather(sender, return_exceptions=True)
    asyncio.run(probe())


def test_invites_expire_leave_and_recheck_gate():
    pan, st = _panel()
    inv = dict(t='invite', from_id=2, from_name='mika', kind='battle', _received=time.monotonic()-61)
    st.inbox.append(inv)
    pan._sent_invites.add((2, 'battle'))
    pan._invite_times[(2, 'battle')] = time.monotonic()-61
    pan.anim()
    assert not st.inbox and not pan.invite_prompt and not pan._sent_invites
    inv['_received'] = time.monotonic()
    st.inbox.append(inv)
    pan.anim()
    assert pan.invite_prompt
    st.roster = [p for p in st.roster if p['id'] != 2]
    pan.anim()
    assert not pan.invite_prompt
    st.roster.append(dict(id=2, name='mika', live=True))
    pan.invite_prompt = inv
    pan.pet.asleep = True
    pan._key_lobby('y')
    assert pan.phase == 'lobby' and not pan.invite_prompt
    assert pan.client.sent[-1][3] is False


def test_backlog_ids_distinguish_identical_messages(isolated):
    ws = Wire([login(), dict(t='chat', text='hi'), dict(t='chat', text='hi')])
    asyncio.run(server.handler(ws))
    frames = list(server.CHAT_BACKLOG)
    assert len(frames) == 2 and frames[0]['id'] != frames[1]['id']
    c = LobbyClient('', 'alice')
    for frame in frames + frames:
        c._handle(json.dumps(dict(frame, replay=True)))
    assert c.state.chat == [('alice', 'hi'), ('alice', 'hi')]
    c._handle(json.dumps(dict(t='chat', from_name='bob', text='old', replay=True)))
    c._handle(json.dumps(dict(t='chat', from_name='bob', text='old', replay=True)))
    assert c.state.chat.count(('bob', 'old')) == 1


def test_moderation_persists_enforces_and_audits(isolated):
    async def command(cmd, **kw):
        ws = Wire()
        await server._handle_admin(server.Client(ws), dict(t='admin', key='secret', cmd=cmd, name='alice', **kw))
        assert ws.sent[-1]['t'] == 'admin_ok'
    asyncio.run(command('mute', minutes=2))
    assert json.loads((isolated/'moderation.json').read_text(encoding='utf-8'))['alice']['mute'] > time.time()
    ws = Wire([login()] + [dict(t=kind, text='hi', to='999', payload={}) for kind in ('chat', 'pm', 'invite', 'relay')])
    asyncio.run(server.handler(ws))
    assert sum('muted' in m.get('msg', '') for m in ws.sent) == 4
    asyncio.run(command('unmute'))
    assert not server._moderated('alice')
    asyncio.run(command('ban'))
    ws = Wire([login()]); asyncio.run(server.handler(ws))
    assert ws.sent[0]['t'] == 'login_failed' and 'banned' in ws.sent[0]['msg']
    asyncio.run(command('unban'))
    live = server.Client(Wire()); live.logged = True; live.name = 'alice'
    server.CLIENTS[live.id] = live
    asyncio.run(command('kick'))
    assert live.ws.closed and 'kicked' in live.ws.sent[0]['msg']
    kinds = [json.loads(line)['kind'] for line in (isolated/'feed').read_text(encoding='utf-8').splitlines()]
    assert all(k in kinds for k in ('mute', 'unmute', 'ban', 'unban', 'kick'))


def test_status_fits_wide_cells():
    pan, _ = _panel()
    pan.status = 'invite → ' + '界' * 30
    assert all(cell_len(line) <= 38 for line in _rendered(pan))


def test_web_tilde_and_lobby_help():
    root = Path(__file__).resolve().parents[1]
    js = (root/'tools/web/loader.js').read_text(encoding='utf-8')
    assert "c === '~'" not in js
    assert "Escape:'escape'" in js
    from tuipet.helpscreen import HELP
    text = str(HELP)
    for phrase in ('type + ENTER', 'Empty ENTER', 'V/M PM', 'P ping', 'PgUp/PgDn', 'ESC leaves', 'online'):
        assert phrase in text


def test_watch_drains_rotated_inode(isolated, monkeypatch, capsys):
    feed = isolated/'watch'
    feed.write_text(json.dumps(dict(kind='chat', name='a', text='old'))+'\n', encoding='utf-8')
    monkeypatch.setattr(admin, 'FEED', str(feed))
    calls = []
    def rotate(_):
        if calls:
            raise KeyboardInterrupt
        calls.append(True)
        with feed.open('a', encoding='utf-8') as f:
            f.write(json.dumps(dict(kind='chat', name='a', text='old tail'))+'\n')
        feed.rename(isolated/'watch.1')
        feed.write_text(json.dumps(dict(kind='chat', name='b', text='replacement'*20))+'\n', encoding='utf-8')
    monkeypatch.setattr(admin.time, 'sleep', rotate)
    admin.cmd_watch()
    output = capsys.readouterr().out
    assert 'old tail' in output and 'replacement'*20 in output


def test_admin_cli_moderation_payload(monkeypatch, capsys):
    requests = []
    async def rpc(payload):
        requests.append(payload)
        return {'t': 'admin_ok'}
    monkeypatch.setattr(admin, '_rpc', rpc)
    for cmd in ('kick', 'ban', 'unban', 'unmute'):
        admin.cmd_moderate(cmd, 'alice')
        assert requests[-1] == dict(cmd=cmd, name='alice')
    admin.cmd_moderate('mute', 'alice', 5)
    assert requests[-1] == dict(cmd='mute', name='alice', minutes=5)
    assert 'mute: alice' in capsys.readouterr().out


def test_kick_does_not_automatically_rejoin():
    c = LobbyClient('', 'alice')
    c._handle(json.dumps(dict(t='error', msg='You were kicked by an administrator.')))
    assert c._stop and c.state.login_failed == 'You were kicked by an administrator.'


def test_loaded_chat_is_sanitized_at_render():
    pan, st = _panel()
    st.chat = [('mika\x1b\u202e', 'hi\x85\u2067\u200b')]
    text = pan._text_lobby().plain
    assert 'mika: hi' in text
    assert all(c not in text for c in ('\x1b', '\u202e', '\x85', '\u2067', '\u200b'))


def test_sent_invites_drop_on_roster_leave_and_gate_at_accept():
    pan, st = _panel()
    pan._sent_invites.add((2, 'battle'))
    st.roster = [p for p in st.roster if p['id'] != 2]
    st.inbox.append(dict(t='invite_resp', from_id=2, kind='battle', accept=True))
    pan.anim()
    assert not pan._sent_invites and pan.phase == 'lobby'
    st.roster.append(dict(id=2, name='mika', live=True))
    pan._sent_invites.add((2, 'battle'))
    pan.pet.asleep = True
    st.inbox.append(dict(t='invite_resp', from_id=2, kind='battle', accept=True))
    pan.anim()
    assert pan.phase == 'lobby'
    assert pan.client.sent[-1][0] == 'relay'


def test_mute_expiry_and_persisted_ban_load(isolated):
    server.MODERATION['alice'] = dict(mute=time.time()-1, ban=True)
    server._durable_json(server.MODERATION_PATH, server.MODERATION)
    loaded = server._load_mapping(server.MODERATION_PATH)
    server.MODERATION.clear()
    server.MODERATION.update(loaded)
    assert not server._moderated('alice')
    assert server._moderated('alice', banned=True)


def test_regular_room_switch_also_holds_chat_until_ack():
    async def probe():
        c = LobbyClient('', 'alice')
        c._ws = Wire()
        c._on_connect()
        c._handle(json.dumps(dict(t='welcome', id=1, name='alice')))
        c.room('friends')
        c.chat('private')
        task = asyncio.create_task(c._send_loop())
        await asyncio.sleep(0)
        assert c._ws.sent == [dict(t='room', code='friends')]
        c._handle(json.dumps(dict(t='room_ok', room='friends')))
        await asyncio.sleep(0)
        assert c._ws.sent[-1] == dict(t='chat', text='private')
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    asyncio.run(probe())


def test_string_targets_route_to_existing_peer(isolated):
    server.ACCOUNTS['bob'] = dict(name='bob')
    peer = server.Client(Wire())
    peer.name, peer.logged, peer.live = 'bob', True, True
    assert isinstance(peer.id, str)
    server.CLIENTS[peer.id] = peer
    ws = Wire([login(), dict(t='pm', to=peer.id, text='hello'),
               dict(t='invite', to=peer.id, kind='battle'),
               dict(t='relay', to=peer.id, payload=dict(kind='battle', card={}))])
    asyncio.run(server.handler(ws))
    assert all(any(frame['t'] == kind for frame in peer.ws.sent) for kind in ('pm', 'invite', 'relay'))
    client = LobbyClient('', 'alice')
    client.pm(-1, 'offline', to_name='bob')
    assert client._q.get_nowait()['to'] == '-1'
