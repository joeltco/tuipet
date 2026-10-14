"""Adventure audit 2026-10-14: road state and displayed payout contracts."""
import pytest

from tuipet import adventure
from tuipet.adventurescreen import AdventurePanel, ZonePickPanel
from tuipet.pet import Pet


def _road():
    panel = AdventurePanel(Pet(num=100, stage="Champion", obedience=500),
                           zone=adventure.MAPS[0])
    panel._trans = None
    panel.travelling = True
    return panel


@pytest.mark.parametrize("refusal", [None, "Too hurt to fight."])
def test_gate_item_menu_names_selected_item_and_use_key(refusal):
    panel = _road()
    panel.travelling = False
    panel._at_gate = True
    panel._gate_refusal = refusal
    panel.adv.loc = panel.adv.total
    panel.adv.lives = 1
    panel.pet.energy = 0
    panel.pet.inventory = {"life_recovery": 1, "rest_kit": 1}
    panel.key("t")
    assert "Life Recovery" in panel.strip()
    assert "ENTER use" in panel.strip()
    panel.key("down")
    assert "Rest Kit" in panel.strip()
    panel.key("enter")
    assert panel.pet.energy == panel.pet.max_energy // 2
    assert panel.pet.inventory.get("rest_kit", 0) == 0
    assert panel.adv.lives == 1


def test_festival_picker_still_discloses_claimed_boss_bounty():
    from tuipet import shop
    pet = Pet(num=100, stage="Champion")
    pet.adv_progress = 1
    pet.road_bounty = {"day": shop._today_ordinal(), "0": 1}
    panel = ZonePickPanel(pet)
    panel.cursor = 0
    panel.holiday = "Halloween"
    assert "bounty claimed today" in panel.text().plain
    assert "FESTIVAL" in panel.text().plain


def test_unfit_wild_slip_breaks_win_chain_without_bout_or_life():
    panel = _road()
    panel.adv.chain(True)
    panel.adv.chain(True)
    panel.pet.injured = True
    panel._start_battle(panel.adv.zone["randoms"][0])
    assert panel.adv.streak == 0
    assert panel.adv.best_streak == 2
    assert panel.adv.fights == panel.pet.battles == 0
    assert panel.adv.lives == adventure.MAX_LIVES
    assert panel.sub is None and panel.travelling


def test_hurry_cannot_march_sleeping_traveller(monkeypatch):
    panel = _road()
    panel.pet.asleep = True
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0)
    before = panel.adv.loc, panel._wx, panel._travel_t
    panel.key("space")
    assert (panel.adv.loc, panel._wx, panel._travel_t) == before
    panel.key("escape")
    assert panel._trans is not None
