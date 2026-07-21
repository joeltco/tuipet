"""Adventure rebuild — RUN SUMMARY on return (phase 16, 2026-07-20).

Pins the results card: a concluded run shows its take (outcome, bits, fights,
loot, lives) on the LCD, then a key rides the homecoming teleport.  A bare
turn-back with nothing to show skips straight to the teleport.
"""
from tuipet import adventure
from tuipet.adventure import ZONES
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


class _Win:
    won = True


def _panel_at_boss(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=ZONES[0])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            return pan
    raise AssertionError("boss never opened")


def test_a_concluded_run_shows_the_results_before_teleporting(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.adv.fights, pan.adv.wins, pan.adv.finds = 4, 4, 3
    pan.pet.bits = 0
    pan.sub = None
    pan._battle_done(_Win())
    from tuipet.adventurescreen import PULSE_T, PARADE_T
    for _ in range(PULSE_T + 3 * PARADE_T + 4):    # the zoneChange show plays first
        if pan._pulse is None and pan._parade is None:
            break
        pan.anim()
    assert pan._summary and pan._trans is None      # card first, not the teleport
    card = str(pan.text())
    assert "results" in card and "Conquered!" in pan.text().plain
    assert f"+{pan.adv.bits_earned}" in card        # the purse
    assert "5W/5" in card                            # 4 wilds + this boss, all won
    assert "Loot    3" in card                       # dug-up count
    # a key rides the teleport home
    pan.key("space")
    assert not pan._summary and pan._trans is not None


def test_the_results_count_fights_wins_and_finds(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=ZONES[0])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            break
    # a wild win + a dig
    pan._start_battle(pan.adv.zone["randoms"][0])
    pan.sub = None
    pan._battle_done(_Win())
    assert pan.adv.fights == 1 and pan.adv.wins == 1
    pan._find = pan.adv.zone["find_keys"][0]
    pan._dig()
    assert pan.adv.finds == 1


def test_a_bare_turn_back_skips_the_summary(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=ZONES[0])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            break
    # ESC at the very start: nothing fought, dug, or conquered -> no card
    pan.key("escape")
    assert not pan._summary and pan._trans is not None
