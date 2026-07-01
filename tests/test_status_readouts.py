"""The mode-specific STATUS readouts (train / battle / feeding / card) must emit
VALID Rich markup and stay within the 26-col inner box, in EVERY theme.

These paint paths were the blind spot behind the v0.2.65-0.2.70 crash streak: unit
tests never rendered them through Rich, so a broken colour tag (empty `[]...[/]`)
shipped green and only blew up at launch. Here we bind the real methods onto a
lightweight stand-in and render them for real.
"""
import types

import pytest
from rich.text import Text
from rich.markup import render as render_markup

from tuipet import theme
from tuipet.app import TuiPetApp
from tuipet.pet import Pet

INNER_W = 26


class _App:
    """Carries the real _status_* methods with none of the Textual machinery."""
    def __init__(self, pet, mode=None):
        self.pet = pet
        self.mode = mode
        self.stats_w = types.SimpleNamespace(border_subtitle=None, update=self._cap)
        self._out = None

    def _cap(self, x):
        self._out = x


for _m in ("_status_training", "_status_battle", "_status_eat", "_status_card"):
    setattr(_App, _m, getattr(TuiPetApp, _m))


def _assert_ok(content):
    for ln in content.split("\n"):
        render_markup(ln)                                    # raises on a dangling tag
        assert len(Text.from_markup(ln).plain) <= INNER_W, f"{ln!r} overflows {INNER_W}"


def _pet():
    return Pet(num=-1, name="Wargreymonmon", stage="Super Ultimate", generation=7)


@pytest.mark.parametrize("th", theme._ORDER)
def test_eat_readout_markup(th):
    theme.apply(th)
    p = _pet()
    p.nutr_protein = p.nutr_mineral = p.nutr_vitamin = 24        # well-nourished branch
    a = _App(p)
    a._status_eat()
    _assert_ok(a._out)
    p.nutr_protein = 0                                          # varied-diet branch
    a._status_eat()
    _assert_ok(a._out)


@pytest.mark.parametrize("th", theme._ORDER)
@pytest.mark.parametrize("phase", ["done", "playing"])
def test_training_readout_markup(th, phase):
    theme.apply(th)
    tp = types.SimpleNamespace(phase=phase, full=(phase == "done"), success=True,
                               taps=7, timer=1.5, result="a solid drill")
    a = _App(_pet(), tp)
    a._status_training()
    _assert_ok(a._out)


@pytest.mark.parametrize("th", theme._ORDER)
@pytest.mark.parametrize("done", [False, True])
def test_battle_readout_markup(th, done):
    theme.apply(th)
    b = types.SimpleNamespace(pet_hp=120, enemy_hp=80, pet_max=120, enemy_max=200,
                              enemy={"name": "Machinedramon", "boss": True},
                              reward="Won 3 levels!")
    m = types.SimpleNamespace(battle=b, hud_php=120, hud_fhp=80, done_anim=done,
                              won=True, phase="menu", hud_note="choose an attack")
    a = _App(_pet(), m)
    a._status_battle()
    _assert_ok(a._out)


@pytest.mark.parametrize("th", theme._ORDER)
def test_card_readout_markup(th):
    theme.apply(th)
    a = _App(_pet())
    a._status_card("New Egg", ["[dim]1 of 5 available[/]", "", "Destined to hatch",
                               "  [b]Botamon[/]"])
    _assert_ok(a._out)
