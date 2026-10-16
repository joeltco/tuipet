"""Approved first-minute copy/UI fixes; no game clocks change."""
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import statusbox
from tuipet.accountscreen import AccountPanel, FIRST_RUN_NOTE
from tuipet.app import TuiPetApp
from tuipet.eggselectscreen import EggSelectPanel
from tuipet.helpscreen import HelpPanel, HELP
from tuipet.pet import Pet
from tuipet.training import TrainingPanel, VERDICT_T


def plain(markup):
    return Text.from_markup(markup).plain


def test_account_explains_creation_and_local_play_in_lcd():
    panel = AccountPanel(note=FIRST_RUN_NOTE)
    text = panel.text().plain
    assert 'Choose a name and password' in text
    assert 'create an account' in text
    assert 'play locally' in text
    assert 'continue' in plain(panel.strip())
    assert cell_len(plain(panel.strip())) <= 40
    assert len(text.splitlines()) <= 12
    assert all(cell_len(line) <= 40 for line in text.splitlines())


@pytest.mark.parametrize('action', ['can_battle', 'can_adventure'])
def test_age_gate_names_stage_and_growth_page(action):
    pet = Pet(num=0, stage='Fresh')
    message = getattr(pet, action)()
    assert 'In-Training' in message
    assert 'D: CORE' in message and 'growth' in message
    assert cell_len(plain(message)) <= 40
    pet.stage = 'InTraining'
    pet.hunger, pet.energy, pet.poop = 4, pet.max_energy, 0
    assert getattr(pet, action)() is None


def test_first_help_view_teaches_the_home_stats_before_holidays():
    panel = HelpPanel(Pet(num=0))
    text = panel.text().plain
    for phrase in ('FIRST STEPS', 'filled Hunger circles = fed',
                   'Fresh = stage', 'None = no attribute', 'DP diamonds',
                   'Vaccine/Data/Virus', 'Quest: next road map', 'D CORE',
                   'In-Training'):
        assert phrase in text
    assert 'HOLIDAYS' not in text
    assert [t for t, _ in HELP].index('FIRST STEPS') < [t for t, _ in HELP].index('HOLIDAYS')
    assert len(text.splitlines()) <= 12
    assert all(cell_len(line) <= 40 for line in text.splitlines())


class Widget:
    def __init__(self):
        self.styles = SimpleNamespace(opacity=1.0)
        self.border_subtitle = ''
        self.rendered = ''

    def update(self, text):
        self.rendered = text

    def paint(self, pet):
        pass


def test_panel_and_egg_subordinate_rail_then_home_restores_it():
    app = SimpleNamespace(pet=Pet(num=0, stage='Fresh'), mode=AccountPanel(),
                          keys_w=Widget(), screen_w=Widget(), stats_w=Widget(),
                          _center=lambda t: t, _mode_strip=lambda: None,
                          _status_painter=lambda: None)
    TuiPetApp.repaint(app)
    assert app.keys_w.styles.opacity == 0.4
    assert 'TUIPET ACCOUNT' in app.screen_w.rendered.plain
    app.mode = None
    app.pet.stage = 'Egg'
    TuiPetApp.repaint(app)
    assert app.keys_w.styles.opacity == 0.4
    app.pet.stage = 'Fresh'
    TuiPetApp.repaint(app)
    assert app.keys_w.styles.opacity == 1.0


def test_training_result_prominently_offers_existing_skip():
    pet = Pet(num=100, stage='Champion')
    panel = TrainingPanel(pet)
    panel.key('space')
    app = SimpleNamespace(pet=pet, mode=panel, stats_w=Widget())
    statusbox.training(app)
    assert '[b]SPACE to skip[/]' in app.stats_w.rendered
    assert 'SPACE to skip' in plain(app.stats_w.rendered)
    assert VERDICT_T == 14
    assert panel.i == 0
    panel.i = 3
    panel.key('space')
    panel.anim()
    assert panel.auto_close == ('done', panel.result)


def test_start_egg_label_and_wait_care_tips():
    assert 'start egg' in plain(EggSelectPanel().strip())
    text = plain('\n'.join(statusbox.egg_lines(Pet.new_egg())))
    for phrase in ('hatches on its own', '? help', 'F feed on hatch',
                   'C clean', 'O night lights'):
        assert phrase in text
    assert 'cosy' not in text
