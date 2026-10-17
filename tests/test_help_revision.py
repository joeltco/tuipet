"""Help audit: corrected claims, stateful hints and physical display budgets."""
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import albumscreen, data_meta, lobbychat, optionsscreen, statusbox
from tuipet.helpscreen import HELP, HelpPanel
from tuipet.lobbyscreen import LobbyPanel
from tuipet.pet import Pet


def test_help_order_and_render_budget():
    assert [t for t, k in HELP if k == 2] == [
        'FIRST STEPS', 'PHONE / NAVIGATION', 'CARE', 'CONTROLS + ROAD',
        'GROW', 'ADVANCED', 'LEGACY', 'HOLIDAYS']
    assert HELP[8][0] == 'PHONE / NAVIGATION'
    assert any('hatches on its own' in t for t, _ in HELP[:8])
    assert len(HELP) <= 139
    pan = HelpPanel(Pet(num=100))
    for top in range(pan._max_top() + 1):
        pan.top = top
        rows = pan.text().plain.splitlines()
        assert len(rows) <= 12
        assert all(cell_len(r) <= 40 for r in rows)
    for t, _ in HELP:
        assert cell_len(t) <= 38
        assert Text.from_markup(t).plain == t
    assert Text.from_markup(pan.strip()).plain == '↑↓ scroll  PGUP/PGDN leap  ESC back'


@pytest.mark.parametrize('claim', [
    'Finds: ENTER, then time SPACE.', 'Your rival may answer a home bout;',
    'each try: +1 training, +1 Effort.', 'battles lock their own bar.',
    'Egg routes vary; some branches stop.', 'its road and care gates must fit.',
    'account, updates and home keys.', '? opens Help from the home view.',
])
def test_wrong_help_claims_replaced(claim):
    assert claim in '\n'.join(t for t, _ in HELP)


@pytest.mark.parametrize('n', range(5))
def test_area_milestones(n):
    assert data_meta.map_goal(n) == (
        f'Clear area {n + 1} ({6 * (n + 1)} maps), or fell {n + 1} raid '
        f'boss{"" if n == 0 else "es"}.')


@pytest.mark.parametrize(('num', 'egg'), [
    (489, 'Volcanic Beat'), (878, 'Infinite Tide'),
    (628, 'Blizzard Fang'), (779, 'Fairimon EX'),
])
def test_explicit_album_line(num, egg):
    assert albumscreen.route_hint(num) == f'raised on the {egg} Egg line'


def test_album_conservative_fallbacks(monkeypatch):
    from tuipet import data, lines
    monkeypatch.setattr(lines, 'load_lines', lambda: {})
    monkeypatch.setattr(data, 'load_requirements', lambda: {
        1: {'evol_item': 2}, 2: {'special': 'anything'}})
    monkeypatch.setattr(data, 'load_sprites', lambda: ({}, {3: {'field': 'NatureSpirits'}}))
    assert albumscreen.route_hint(1) == 'an evolution item reaches it'
    assert albumscreen.route_hint(2) == 'a special evolution reaches it'
    assert albumscreen.route_hint(3) == 'check X: Divergence for Field roads'


def test_options_web_update_and_home_keys(monkeypatch):
    from tuipet import web
    monkeypatch.setattr(web, 'is_browser', lambda: True)
    pan = optionsscreen.OptionsPanel(Pet(num=100), lambda: False, lambda: None)
    pan.cursor = optionsscreen._ROWS.index('update')
    assert 'Reload the page for web updates.' in pan.text().plain
    captured = []
    monkeypatch.setattr(statusbox, 'card', lambda app, title, rows: captured.extend(rows))
    statusbox.options(SimpleNamespace(pet=pan.pet, mode=pan))
    plain = ' '.join(Text.from_markup(r).plain for r in captured)
    assert 'Reload the page for web updates.' in plain
    assert 'ENTER check' not in plain and 'installs' not in plain
    monkeypatch.setattr(web, 'is_browser', lambda: False)
    assert 'Reload the page' not in pan.text().plain
    assert optionsscreen._DESC['keys'] == 'home shortcuts on one page'


def test_lobby_injury_and_stalled_strip():
    pet = Pet(num=100, name='Test', hunger=4, strength=4, energy=50, obedience=100,
              injured=True)
    pan = LobbyPanel(pet, on_connect=lambda *args: None)
    assert 'hurt!' in Text.from_markup(pan._care_cue()).plain
    pan.phase = 'ladder'
    pan._mq, pan._ladder_asked = 51, 0
    assert Text.from_markup(pan.strip()).plain == 'TAB retry · ESC back'
    assert 'ENTER send/act' in lobbychat.HINTS_OPEN


def test_dna_mash_hint(monkeypatch):
    from tuipet.dnascreen import DNAPanel
    from tuipet import evolution
    monkeypatch.setattr(evolution, 'divergence_roads', lambda p: {})
    monkeypatch.setattr(evolution, 'divergence_options', lambda p: [])
    pet = Pet(num=100)
    pan = DNAPanel(pet)
    widget = SimpleNamespace(update=lambda text: captured.append(text))
    app = SimpleNamespace(pet=pet, mode=pan, stats_w=widget)
    for phase in ('mash', 'home'):
        captured = []
        pan.phase = phase
        statusbox.dna(app)
        text = captured[0]
        assert ('Mash SPACE until time up.' in text) == (phase == 'mash')
        assert ('ESC steps back out' in text) == (phase != 'mash')


@pytest.mark.parametrize('essential', [
    'Web phone: tap the game to type.', 'ESC at sign-in plays locally.',
    'The egg hatches on its own (~60s).', 'energy + Effort; adds weight.',
    'In fights: SPACE locks the bar.', 'On the map list, H picks a hunt.',
    'Town rest restores lives/energy', 'Replay boss bits: once per real day.',
    'ENTER/F details; Y pays entry.', 'Three attempts per UTC day.',
    'forms, full DP and enough energy.', 'Buy at most one egg per real day.',
    'A spoiled mash returns half.', 'Tap keys during dying to try rescue.',
    'Menus pause care and growth too.',
])
def test_missing_essentials_stay_short_and_present(essential):
    assert essential in '\n'.join(t for t, _ in HELP)


def test_help_status_hint_and_noise(monkeypatch):
    captured = []
    monkeypatch.setattr(statusbox, 'card', lambda app, title, rows: captured.extend(rows))
    statusbox.help_(SimpleNamespace(sound=False, pet=Pet(num=100)))
    assert '[dim]↑↓ scroll  PGUP/PGDN leap[/]' in captured
    assert '[dim]ESC back[/]' in captured
    body = '\n'.join(t for t, _ in HELP)
    for stale in ('TIPS', 'whisper to death', 'every 3rd', 'sharpens aim',
                  'unique leader arms', 'Each egg has its own line'):
        assert stale not in body


def test_ladder_score_copy():
    pan = LobbyPanel(Pet(num=100), on_connect=lambda *args: None)
    pan.client = SimpleNamespace(ladder={'top': [], 'rank': 0, 'wins': 0})
    assert 'online wins set your ladder score' in pan._text_ladder().plain
