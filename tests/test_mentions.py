"""Mentions use in-memory transports, including the real chat handler."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import net, persistence
from tuipet.app import TuiPetApp
from tuipet.theme import INK_B
from test_lobby_audit import _panel
from test_lobbychat_fixes import Wire, login, server
from test_lobbychat_fixes import isolated as isolated


@pytest.mark.parametrize('text, expected', [
    ('@JOEL!', ['joel']), ('joel @joely mail@joel', []),
    ('@Joel Smith @joel @JOEL', ['joel smith', 'joel']),
    ('@日本語 @A+B!', ['日本語', 'a+b']),
])
def test_boundaries_and_longest_names(text, expected):
    assert net.mentioned_names(text, ['joel', 'Joel Smith', '日本語', 'A+B']) == expected


def test_completion_cycles_and_keeps_ladder():
    pan, st = _panel(buf='hey @jO')
    st.roster += [dict(id=4, name='Joel Smith')]
    pan.key('tab')
    assert pan.buf == 'hey @joel' and pan.phase == 'lobby'
    pan.key('tab')
    assert pan.buf == 'hey @Joel Smith'
    pan.key('tab')
    assert pan.buf == 'hey @joel'
    pan.key('backspace')
    pan.key('tab')
    assert pan.buf == 'hey @joel'
    pan.buf = ''
    pan.key('tab')
    assert pan.phase == 'ladder'


def test_highlight_and_rate_limited_cue(monkeypatch):
    client = net.LobbyClient('ws://unused', 'joel')
    pan, st = _panel()
    client.state = st
    st.roster += [dict(id=4, name='Joel Smith')]
    for i, text in enumerate(['joel', '@joely', '@Joel Smith', '@JOEL [red]']):
        client._handle(json.dumps(dict(t='chat', id=str(i), from_name='mika', text=text)))
    assert st.mentions_received == 1
    # a bare name still highlights (kept); only a true @joel counts as a mention
    assert [style for _, style in pan._chat_rows()] == [INK_B, INK_B, INK_B, INK_B]
    assert '[red]' in pan._text_lobby().plain
    monkeypatch.setattr('tuipet.lobbyscreen.time.monotonic', lambda: 100)
    pan.anim()
    assert pan.sfx == 'menu'
    pan.sfx = None
    client._handle(json.dumps(dict(t='chat', id='next', from_name='mika', text='@joel')))
    pan.anim()
    assert pan.sfx is None
    for message in [dict(id='replay', replay=True), dict(id='self', from_name='joel'),
                    dict(id='blocked', from_name='blocked')]:
        st.blocked.add('blocked')
        client._handle(json.dumps(dict(t='chat', text='@joel', **({'from_name': 'mika'} | message))))
    assert st.mentions_received == 2


def test_home_alert_escape_width_block_and_mute():
    persistence.set_blocked(['blocked'])
    client = net.SyncClient('ws://unused', 'joel')
    client._handle(json.dumps(dict(t='mention', from_name='blocked', text='secret')))
    assert not client.inbox
    for name in ['[/]Alice', '界' * 24]:
        client._handle(json.dumps(dict(t='mention', from_name=name, text='body stays hidden')))
        flashes = []
        stub = SimpleNamespace(_sync=client, mode=None, _flash_t=0, sound=False,
                               flash=flashes.append)
        stub.beep = lambda *a, **k: TuiPetApp.beep(stub, *a, **k)
        TuiPetApp._drain_pms(stub)
        plain = Text.from_markup(flashes[0]).plain
        assert plain.startswith('@ ') and plain.endswith(' mentioned you')
        assert cell_len(plain) <= 38
        assert 'body stays hidden' not in plain
        if name.startswith('['):
            assert plain == '@ [/]Alice mentioned you'
    client._handle('{"t":"future_unknown_frame"}')
    lobby = net.LobbyClient('ws://unused', 'joel')
    lobby._handle('{"t":"future_unknown_frame"}')
    assert not client.inbox and not lobby.state.chat


def peer(name, live=False, room=None):
    c = server.Client(Wire())
    c.name, c.logged, c.live, c.room = name, True, live, room
    server.CLIENTS[c.id] = c
    server.ACCOUNTS[name.lower()] = dict(name=name)
    return c


@pytest.mark.usefixtures("isolated")
def test_server_chat_mentions_scope_cap_clean_throttle():
    targets = [peer(n) for n in ['Bob', 'Bob Smith', 'Carol', 'Dave', 'Eve']]
    live = peer('Bob Smith', live=True)
    private = peer('Bob Smith', live=True, room='secret')
    text = '@ALICE @Bob Smith @BOB SMITH @Carol @Dave @Eve\x1b'
    ws = Wire([login(), dict(t='chat', text=text), dict(t='chat', text=text)])
    asyncio.run(server.handler(ws))
    for target in targets:
        alerts = [m for m in target.ws.sent if m['t'] == 'mention']
        assert len(alerts) == (1 if target.name in ['Bob Smith', 'Carol', 'Dave'] else 0)
        if alerts:
            assert alerts[0] == dict(t='mention', from_name='alice', text=server._clean(text, server.MAX_CHAT))
    assert not any(m['t'] == 'mention' for m in live.ws.sent + private.ws.sent)
    sender = peer('alice', live=True, room='private')
    server._RATE_BUCKETS.clear()
    asyncio.run(server._mention_alerts(sender, '@Bob'))
    assert not targets[0].ws.sent or all(m['t'] != 'mention' for m in targets[0].ws.sent)
    sender.room = None
    asyncio.run(server._mention_alerts(sender, '@Bob'))
    assert targets[0].ws.sent[-1]['t'] == 'mention'
    assert not server._rate_allow('mention', ('alice', 'bob'), 1, 60)
    last = server._RATE_BUCKETS[('mention', ('alice', 'bob'))][-1]
    assert server._rate_allow('mention', ('alice', 'bob'), 1, 60, now=last + 60)


def test_help_mentions_within_existing_budget():
    from tuipet.helpscreen import HELP
    assert any('@+TAB' in line for line, _ in HELP)
    assert len(HELP) <= 141
    assert all(cell_len(line) <= 38 for line, _ in HELP)


@pytest.mark.parametrize('record', [dict(mute=10**12), dict(ban=True)])
@pytest.mark.usefixtures("isolated")
def test_moderated_sender_cannot_alert(record):
    target = peer('Bob')
    server.MODERATION['alice'] = record
    asyncio.run(server.handler(Wire([login(), dict(t='chat', text='@Bob') ])))
    assert not any(m['t'] == 'mention' for m in target.ws.sent)
    assert not server.CHAT_BACKLOG


@pytest.mark.usefixtures("isolated")
def test_no_offline_queue_and_clipped_text():
    server.ACCOUNTS['offline'] = dict(name='Offline')
    sender = peer('alice', live=True)
    asyncio.run(server._mention_alerts(sender, '@Offline'))
    assert not server.PENDING
    target = peer('Bob')
    asyncio.run(server.handler(Wire([login(), dict(t='chat', text='@Bob ' + 'x' * 600)])))
    alert = next(m for m in target.ws.sent if m['t'] == 'mention')
    assert len(alert['text']) == server.MAX_CHAT


def test_dim_hint_shows_rest_of_name_and_right_accepts():
    pan, st = _panel(buf='hey @jO')
    assert pan._mention_hint() == 'el'
    row = next(line for line in pan._text_lobby().plain.splitlines() if line.startswith('say: '))
    assert row.startswith('say: hey @jOel')
    pan.key('right')
    assert pan.buf == 'hey @joel' and pan._mention_hint() == ''
    pan.buf = 'hey @zz'
    assert pan._mention_hint() == ''
    pan.buf = 'mail@jo'
    assert pan._mention_hint() == ''
