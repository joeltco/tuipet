"""Approved Batch A: ink, account geometry, and the real terminal shell."""
import asyncio

import pytest
from rich.cells import cell_len
from rich.console import Console
from rich.style import Style

from tuipet import theme
from tuipet.accountscreen import AccountPanel, CloudWaitPanel
from tuipet.app import TuiPetApp, Stats
from tuipet.pet import Pet
from tuipet.tournamentscreen import TournamentPanel


def test_cup_terms_have_lcd_body_ink():
    p = Pet(num=100, stage="Champion")
    panel = TournamentPanel(p)
    panel.key("enter")
    assert panel.detail is not None
    text = panel.text()
    console = Console(color_system="truecolor")
    body = [segment for segment in console.render(text)
            if segment.text.strip() and "Y PAY" not in segment.text]
    assert any(segment.style == Style.parse(theme.INK) for segment in body)
    # Every payment paragraph has ink, including wrapped and scrolled lines.
    for offset in (0, 3, 99):
        panel.detail_scroll = offset
        text = panel.text()
        for line in text.split("\n")[1:-1]:
            if line.plain.strip():
                assert all(seg.style.color == Style.parse(theme.INK).color
                           for seg in console.render(line) if seg.text.strip())


@pytest.mark.parametrize("name", ["", "audit", "界" * 24])
def test_account_header_fields_and_budget(name):
    panel = AccountPanel(name=name)
    panel.pw_buf = "secret" * 11
    for field in ("name", "pw"):
        panel.field = field
        text = panel.text()
        lines = text.plain.splitlines()
        assert lines[0].startswith("ACCOUNT") and lines[0].endswith("SIGN IN")
        assert lines[1] == "─" * 38
        assert lines[2] == ""
        assert lines[3][2:12] == "Name      "
        assert lines[4][2:12] == "Password  "
        assert len(lines) == 12
        assert max(map(cell_len, lines)) <= 40
        selected = text.split("\n")[3 if field == "name" else 4]
        assert selected.get_style_at_offset(Console(), 0) == Style.parse(theme.SEL)
        assert cell_len(selected.plain) == 38
    assert "secret" not in panel.text().plain
    panel.note = "long rejection " * 30
    assert len(panel.text().plain.splitlines()) <= 12
    assert CloudWaitPanel(name).text().plain.startswith("ACCOUNT")


def test_shell_semantics_reach_terminal_widget_without_changing_lcd():
    original = theme.current()
    try:
        for name in theme.names():
            theme.apply(name)
            stats = Stats()
            stats.update(f"[{theme.COIN}]coins[/] [{theme.POS}]positive[/]")
            text = stats.render()
            segments = list(Console(color_system="truecolor").render(text))
            expected = theme.shell_colors(theme.THEMES[name])
            assert next(s for s in segments if s.text == "coins").style.color.triplet.hex == expected['coin']
            assert next(s for s in segments if s.text == "positive").style.color.triplet.hex == expected['pos']
            assert Style.parse(theme.INK).color.triplet.hex == theme.THEMES[name]['on']
            assert theme.KEY == "cyan"
    finally:
        theme.apply(original)


def test_panel_hides_rail_and_recenters_real_terminal():
    async def run():
        app = TuiPetApp(pet=Pet(num=100, stage="Champion"))
        async with app.run_test(size=(80, 24)) as pilot:
            for timer in (app._frame_timer, app._life_timer, app._save_timer):
                timer.pause()
            app.mode = None
            app.repaint()
            await pilot.pause()
            assert app.keys_w.display
            home_region = app.query_one("#wrap").region
            app._open_mode(AccountPanel(name="audit"))
            await pilot.pause()
            # Joel 2026-10-17 reverted the hiding: the rail stays and dims in panels
            assert app.keys_w.display and app.keys_w.styles.opacity == 0.4
            assert app.query_one("#wrap").region == home_region     # layout no longer jumps
            assert app.screen_w.content_region.size == (40, 12)
            assert app.screen_w.render().plain.startswith("ACCOUNT")
            app._close_mode(None)
            await pilot.pause()
            assert app.keys_w.display and app.keys_w.styles.opacity == 1.0
    asyncio.run(run())


def test_raster_resyncs_unchanged_pixels_after_layout(monkeypatch):
    import sys
    from types import SimpleNamespace
    from textual.geometry import Region
    from tuipet.web.render import Raster, update_raster, sync_raster

    calls = []
    monkeypatch.setitem(sys.modules, 'js', SimpleNamespace(
        bridgeRaster=lambda *args: calls.append(args), bridgeRasterHide=lambda: None))
    monkeypatch.setitem(sys.modules, 'pyodide.ffi', SimpleNamespace(to_js=lambda x: x))
    widget = SimpleNamespace(content_region=Region(4, 2, 40, 12),
                             screen=SimpleNamespace(is_current=True),
                             refresh=lambda *args: None,
                             gutter=SimpleNamespace(left=0, top=0),
                             _styles_cache=SimpleNamespace(set_dirty=lambda _: None))
    frame = Raster([object() for _ in range(12)], [[('#000000', '#ffffff')] * 40] * 12)
    update_raster(widget, frame)
    assert len(calls) == 1
    update_raster(widget, frame)
    assert len(calls) == 1
    widget.content_region = Region(4, 5, 40, 12)
    sync_raster(widget)
    assert calls[-1][:2] == (4, 5)
    assert calls[-1][3] == list(range(12))
    update_raster(widget, AccountPanel().text())
    sync_raster(widget)
    assert widget._web_raster is None


def test_phone_fit_uses_24_rows_and_centers_xterm():
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to execute the shipped browser fitter')
    source = (Path(__file__).resolve().parents[1] / 'tools/web/loader.js').read_text(encoding='utf-8')
    fitter = source[source.index('function fitTerminal()'):source.index('function changeZoom')]
    script = '''
let fitting=false, zoom=1, coarse=true, innerWidth=844, innerHeight=390;
const screen={style:{}}, box={clientWidth:844,clientHeight:314};
const document={querySelector:s=>s==='#screen'?screen:box};
const window={}, xkeys={style:{}}, xkeysHeight=()=>76;
const matchMedia=()=>({matches:coarse});
const term={options:{fontSize:16},element:{style:{}},
 _core:{_renderService:{dimensions:{css:{get cell(){return {width:term.options.fontSize*.6,height:term.options.fontSize*1.2};}}}}},
 resize(c,r){this.cols=c;this.rows=r;}};
const lastRaster=null;
''' + fitter + '''
fitTerminal();
if(term.rows!==24 || term.cols!==80 || term.element.style.margin!=='0 auto') throw Error('phone fit');
if(parseFloat(term.element.style.width)>844) throw Error('overflow');
coarse=false; box.clientWidth=1100; box.clientHeight=800;
fitTerminal();
if(term.rows!==30 || term.cols!==80) throw Error('desktop fit');
'''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True)
