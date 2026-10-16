"""Browser seams are importable and testable without Pyodide or real saves."""
import asyncio
import json
import sys
from types import SimpleNamespace

import pytest

from tuipet.web import is_browser
from tuipet.web.driver import key_event
from tuipet.web.socket import BrowserSocket


def test_platform_and_unicode_key(monkeypatch):
    assert not is_browser()
    monkeypatch.setattr(sys, 'platform', 'emscripten')
    assert is_browser()
    event = key_event('é', 'é')
    assert event.key == 'é' and event.character == 'é'
    assert key_event('ctrl+c').key == 'ctrl+c'


def test_driver_writes_ansi_unicode(monkeypatch):
    from tuipet.web.driver import BrowserDriver
    writes = []
    monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(bridgeWrite=writes.append))
    BrowserDriver.write(None, '\x1b[31m▀🐾\x1b[0m')
    assert writes == ['\x1b[31m▀🐾\x1b[0m']


def test_serialized_flush_and_failure(monkeypatch):
    from tuipet.web import storage
    async def run():
        active = 0
        calls = []
        async def persist():
            nonlocal active
            active += 1
            assert active == 1
            await asyncio.sleep(0)
            calls.append('durable')
            active -= 1
        monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(persist=persist))
        monkeypatch.setattr(storage, '_lock', None)
        await asyncio.gather(storage.flush(), storage.flush())
        assert calls == ['durable', 'durable']
        async def fail():
            raise OSError('quota')
        monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(persist=fail))
        with pytest.raises(OSError, match='quota'):
            await storage.flush()
    asyncio.run(run())


class Proxy:
    def __init__(self, fn): self.fn, self.destroyed = fn, False
    def __call__(self, event): self.fn(event)
    def destroy(self): self.destroyed = True


class Socket:
    def __init__(self):
        self.callbacks = {}
        self.readyState = 0
        self.bufferedAmount = 0
        self.sent = []
        self.closes = []
    def addEventListener(self, name, callback):
        self.callbacks[name] = callback
        if name == 'message':
            asyncio.get_running_loop().call_soon(self.open)
    def open(self):
        self.readyState = 1
        self.callbacks['open'](None)
    def removeEventListener(self, name, callback): self.callbacks.pop(name)
    def close(self, code=1000): self.readyState = 3; self.closes.append(code)
    def send(self, data): self.sent.append(data)
    def message(self, data): self.callbacks['message'](SimpleNamespace(data=data))


def test_socket_text_size_close_and_cleanup(monkeypatch):
    async def run():
        socket = Socket()
        proxies = []
        def proxy(fn):
            p = Proxy(fn); proxies.append(p); return p
        monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(WebSocket=SimpleNamespace(new=lambda _:socket)))
        monkeypatch.setitem(sys.modules, 'pyodide', SimpleNamespace())
        monkeypatch.setitem(sys.modules, 'pyodide.ffi', SimpleNamespace(create_proxy=proxy))
        async with BrowserSocket('wss://example.invalid', max_size=4) as ws:
            await ws.send('é')
            assert socket.sent == ['é']
            socket.message('▀')
            assert await ws.recv() == '▀'
            with pytest.raises(TypeError): await ws.send(b'bytes')
            socket.message('ééé')
            assert socket.closes == [1009]
            with pytest.raises(ConnectionError): await ws.recv()
        assert not socket.callbacks
        assert all(p.destroyed for p in proxies)
    asyncio.run(run())


def test_async_cloud_preserves_read_and_ack_gates(monkeypatch):
    from tuipet.web import cloud
    sent = []
    responses = []
    class Connection:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def send(self, data): sent.append(json.loads(data))
        async def recv(self): return json.dumps(responses.pop(0))
    monkeypatch.setattr(cloud, '_connect', lambda *a:Connection())
    monkeypatch.setattr(cloud.persistence, 'device_id', lambda:'test-device')
    monkeypatch.setattr(cloud.persistence, 'device_label', lambda:'test browser')
    async def run():
        responses[:] = [{'t':'login_failed'}]
        assert not await cloud.push_save('uri', 'name', 'pw', {'_saved_at':2})
        assert not any(m['t']=='save' for m in sent)
        sent.clear()
        responses[:] = [{'t':'welcome', 'save':{'_saved_at':3}}]
        assert not await cloud.push_save('uri', 'name', 'pw', {'_saved_at':2})
        assert not any(m['t']=='save' for m in sent)
        sent.clear()
        responses[:] = [{'t':'welcome'}, {'t':'welcome'}, {'t':'saved','ok':False}]
        assert not await cloud.push_save('uri', 'name', 'pw', {'_saved_at':4})
        assert any(m['t']=='save' for m in sent)
        assert sent[0]['device'] == 'test-device'
    asyncio.run(run())


def test_raster_matches_terminal_pixels_and_reuses_rows():
    from tuipet.render import fill_buf, _paint_cells
    from tuipet.web.render import paint_cells
    from rich.console import Console
    buf = fill_buf(['10','01'], 4, 4)
    normal = _paint_cells(buf, 4, 2, '#000000', '#ffffff', None)
    browser = paint_cells(buf, 4, 2, '#000000', '#ffffff', None)
    again = paint_cells(buf, 4, 2, '#000000', '#ffffff', None)
    console = Console(width=4, color_system='truecolor')
    lines = console.render_lines(normal, console.options.update(width=4), pad=False)
    for y, line in enumerate(lines):
        actual = list(browser.lines[y])
        assert ''.join(s.text for s in actual) == ''.join(s.text for s in line)
        def cells(segments):
            return [(c, s.style.color, s.style.bgcolor) for s in segments for c in s.text]
        assert cells(actual) == cells(line)
        assert browser.lines[y] is again.lines[y]


def test_normal_app_driver_unchanged():
    from tuipet.app import TuiPetApp
    from textual.drivers.linux_driver import LinuxDriver
    assert TuiPetApp.get_driver_class(object.__new__(TuiPetApp)) is LinuxDriver


def test_web_build_version_cache_busting_and_reproducibility(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    import zipfile
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('build_web', root/'tools/build_web.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    lock = json.loads((root/'tools/web/vendor-lock.json').read_text(encoding='utf-8'))
    assert all(len(item['sha256']) == 64 for item in lock.values())
    assert 'textual-8.2.7-py3-none-any.whl' in lock
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    (tmp_path/'src/tuipet').mkdir(parents=True)
    (tmp_path/'src/tuipet/__init__.py').write_text('', encoding='utf-8')
    (tmp_path/'src/tuipet/data').mkdir()
    (tmp_path/'src/tuipet/data/eggs.json.gz').write_bytes((root/'src/tuipet/data/eggs.json.gz').read_bytes())
    (tmp_path/'tools/web').mkdir(parents=True)
    (tmp_path/'tools/web/loader.js').write_text('loader', encoding='utf-8')
    (tmp_path/'tools/web/index.html').write_text('@ASSETS@loader.js', encoding='utf-8')
    (tmp_path/'tools/web/vendor-lock.json').write_text('{}', encoding='utf-8')
    (tmp_path/'pyproject.toml').write_text('[project]\nversion="1.2.3"\n', encoding='utf-8')
    module.build()
    first = (tmp_path/'dist/web/manifest.json').read_bytes()
    manifest = json.loads(first)
    assert manifest['version'] == '1.2.3'
    assert manifest['display'] == 'fullscreen'
    assert manifest['start_url'] == './'
    assert manifest['theme_color'] == '#121212'   # the game's own screen colour (seamless page)
    assert (tmp_path/'dist/web/icon-192.png').read_bytes().startswith(b'\x89PNG')
    assert (tmp_path/'dist/web/icon-512.png').read_bytes().startswith(b'\x89PNG')
    with zipfile.ZipFile(tmp_path/'build/web-game.zip') as z:
        assert b'Version: 1.2.3' in z.read('tuipet-1.2.3.dist-info/METADATA')
    module.build()
    assert (tmp_path/'dist/web/manifest.json').read_bytes() == first
    (tmp_path/'src/tuipet/__init__.py').write_text('# changed', encoding='utf-8')
    module.build()
    changed = json.loads((tmp_path/'dist/web/manifest.json').read_text(encoding='utf-8'))
    assert changed['build'] != manifest['build']


def test_hidden_pauses_game_timers_without_replaying_beats(monkeypatch):
    from tuipet.web import entry
    calls = []
    timer = SimpleNamespace(pause=lambda:calls.append('pause'), reset=lambda:calls.append('resume'))
    app = SimpleNamespace(_frame_timer=timer, _life_timer=timer, _save_timer=timer,
                          autosave=lambda:calls.append('save'),
                          _flush_dms_on_quit=lambda:calls.append('dms'))
    async def flush(): calls.append('durable')
    monkeypatch.setattr(entry, 'app', app)
    monkeypatch.setattr(entry, 'hidden', False)
    monkeypatch.setattr(entry, 'durable_save', flush)
    async def run():
        await entry.visibility(True)
        assert entry.hidden
        assert calls == ['pause']*3 + ['save', 'dms', 'durable']
        await entry.visibility(False)
        assert not entry.hidden
        assert calls[-3:] == ['resume']*3
    asyncio.run(run())


def test_raster_only_writes_changed_scanlines(monkeypatch):
    from rich.console import Console
    from textual.geometry import Region, Spacing
    from tuipet.web.render import paint_cells, update_raster
    writes, dirty, refreshed = [], [], []
    widget = SimpleNamespace(
        content_region=Region(4, 5, 40, 12), screen=SimpleNamespace(is_current=True),
        gutter=Spacing(1, 1, 1, 1), size=SimpleNamespace(width=40),
        _styles_cache=SimpleNamespace(set_dirty=dirty.append),
        app=SimpleNamespace(console=Console(color_system='truecolor')),
        refresh=lambda *args:refreshed.append(args))
    monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(
        bridgeRaster=lambda *args:writes.append(args), bridgeRasterHide=lambda:None))
    monkeypatch.setitem(sys.modules, 'pyodide', SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'pyodide.ffi', SimpleNamespace(to_js=lambda value:value))
    buf = [[0]*40 for _ in range(24)]
    first = paint_cells(buf, 40, 12, '#000000', '#ffffff', None)
    assert update_raster(widget, first)
    assert len(refreshed) == 1
    assert update_raster(widget, first)
    assert len(writes) == 1
    writes.clear(); dirty.clear()
    buf[2][3] = 1
    assert update_raster(widget, paint_cells(buf, 40, 12, '#000000', '#ffffff', None))
    assert len(writes) == 1 and writes[0][:2] == (4, 5)
    assert writes[0][3] == [1]
    assert len(dirty) == 1
    assert not update_raster(widget, 'menu')
    assert widget._web_lines is None


def test_browser_update_buttons_never_start_threads(monkeypatch):
    from tuipet import optionsscreen
    from tuipet import web
    monkeypatch.setattr(web, 'is_browser', lambda:True)
    def forbidden(*args, **kwargs):
        raise AssertionError('browser attempted a thread')
    monkeypatch.setattr(optionsscreen.threading, 'Thread', forbidden)
    panel = object.__new__(optionsscreen.OptionsPanel)
    panel._check_updates()
    assert 'Reload' in panel.msg
    panel._install_update()
    assert 'Reload' in panel.msg


def test_browser_resize_reuses_terminal_warning(monkeypatch):
    from tuipet.web import entry
    from tuipet.appboot import terminal_size_warning
    messages, notices = [], []
    app = SimpleNamespace(post_message=messages.append,
                          notify=lambda text, **kw: notices.append((text, kw)))
    monkeypatch.setattr(entry, 'app', app)
    entry.browser_resize(60, 20)
    entry.browser_resize(60, 20)
    assert messages[0].size.width == 60
    assert notices == [(terminal_size_warning(60, 20), {'timeout': 2.5})]
    entry.browser_resize(80, 30)
    assert len(notices) == 1
