"""Final sweep 2026-10-14: catalog edge states and shipped guidance."""
from pathlib import Path

import pytest

from tuipet import digicore
from tuipet.pet import Pet
from tuipet.petbase import MAX_OBEDIENCE, WEIGHT_LIMIT_MULTIPLE, _Refused


@pytest.mark.parametrize("key", ["ai_supplement", "bitter_herbs"])
def test_nonmeal_snacks_keep_doses_at_full_gauges(key):
    p = Pet(num=100, stage="Champion")
    p.strength, p.obedience = 4, MAX_OBEDIENCE
    p.inventory = {key: 1}
    assert isinstance(p.use_item(key), _Refused)
    assert p.inventory[key] == 1


def test_help_explains_the_gcell_dial():
    from tuipet.helpscreen import HELP
    text = "\n".join(row for row, _kind in HELP)
    assert "G-Cells" in text
    assert "472" in text


def test_notice_agrees_with_package_assets():
    notice = (Path(__file__).parents[1] / "NOTICE").read_text(encoding="utf-8")
    assert "ships no game assets" not in notice


def test_title_and_keys_exit_without_stuck_state():
    from tuipet.titlescreen import TitlePanel
    from tuipet.optionsscreen import KeysPanel
    title = TitlePanel.__new__(TitlePanel)
    assert title.key("q") == ("quit", None)
    assert title.key("enter") == ("done", None)
    keys = KeysPanel([(str(i), "action", "label") for i in range(30)])
    for _ in range(10):
        keys.key("pagedown")
    assert keys.top == 30 - keys.VISIBLE
    assert keys.key("escape") == ("done", None)


def test_theme_preview_cancel_and_commit_persist():
    from tuipet import theme
    from tuipet.themescreen import ThemePanel
    original = theme.current()
    try:
        theme.save_choice(original)
        panel = ThemePanel()
        panel.key("down")
        chosen = theme.current()
        assert chosen != original and theme.load_choice() == original
        panel.key("escape")
        assert theme.current() == theme.load_choice() == original
        panel = ThemePanel()
        panel.key("down")
        panel.key("enter")
        assert theme.current() == theme.load_choice() == chosen
    finally:
        theme.apply(original)


def test_sound_and_option_switches_reload():
    from tuipet import persistence, sound
    from tuipet.appboot import _load_sound, _save_sound
    from tuipet.optionsscreen import OptionsPanel, _ROWS
    _save_sound(False)
    assert not _load_sound()
    _save_sound(True)
    assert _load_sound()
    assert sound.set_volume(70) == sound._load_volume() == 70
    panel = OptionsPanel(Pet(num=100, stage="Champion"), lambda: True, lambda: None)
    panel.cursor = _ROWS.index("cloud")
    before = persistence.get_cloud_sync()
    panel.key("enter")
    assert persistence.get_cloud_sync() == (not before)
    panel.cursor = _ROWS.index("update")
    before = persistence.get_auto_update()
    panel.key("a")
    assert persistence.get_auto_update() == (not before)
    panel._updated = True
    assert panel.key("enter") == ("done", ("restart",))


@pytest.mark.parametrize("key", ["slim_drink", "ball", "trampoline", "dumbbell"])
def test_saturated_training_items_keep_the_dose(key):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.weight = max(1, p._base_weight() - round(p._base_weight() * WEIGHT_LIMIT_MULTIPLE))
    p.strength, p.stage_trainings = 4, 999
    p.inventory = {key: 2}
    before = (p.weight, p.strength, p.stage_trainings)
    out = p.use_item(key)
    assert isinstance(out, _Refused), (key, out, before)
    assert p.inventory[key] == 2
    assert (p.weight, p.strength, p.stage_trainings) == before


def test_grow_capsule_uses_burning_godzillas_real_window():
    p = Pet(num=1644, stage="Mega", line_id="godzilla")
    p.stage_seconds = 100
    p.inventory = {"grow_capsule": 2}
    duration = p._evolve_after()
    assert duration == p.LATE_STAGE_WINDOW == digicore.growth_clock(p)
    out = p.use_item("grow_capsule")
    assert not isinstance(out, _Refused)
    assert p.stage_seconds == 100 + duration / 4
    assert p.inventory["grow_capsule"] == 1
    assert isinstance(p.use_item("grow_capsule"), _Refused)


def test_grow_capsule_keeps_terminal_mega_untimed():
    p = Pet(num=1650, stage="Mega", line_id="godzilla")
    p.inventory = {"grow_capsule": 1}
    assert p._evolve_after() == p.STAGE_DURATION["Mega"]
    assert isinstance(p.use_item("grow_capsule"), _Refused)
    assert p.inventory["grow_capsule"] == 1 and p.stage_seconds == 0


def test_trampoline_still_lands_when_effort_has_room():
    p = Pet(num=100, stage="Champion")
    p._set_weight(1)
    p.strength = 3
    p.inventory = {"trampoline": 1}
    assert not isinstance(p.use_item("trampoline"), _Refused)
    assert p.strength == 4 and not p.inventory.get("trampoline", 0)


@pytest.mark.parametrize("claim", ["controls", "play", "assets"])
def test_readme_matches_shipped_controls_play_and_assets(claim):
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    if claim == "controls":
        assert "SPACE works wherever ENTER does" not in readme
        assert "most screens" in readme
    elif claim == "play":
        assert "couch time buys energy" not in readme
        assert "couch time builds DP" in readme
    else:
        assert "repository ships none of them" not in readme
        assert "bundled assets" in readme
