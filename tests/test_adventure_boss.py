"""Adventure rebuild — the zone BOSS FIGHT (phase 5, 2026-07-20).

Pins the gate: reaching the end opens the zone's boss (not an instant win),
felling it conquers the zone, a survivable loss stands the pet at the gate to
retry (SPACE) or turn back (ESC), and 0 lives fails the run home.
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, MAX_LIVES
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _champ():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _boss_zone():
    return next(z for z in ZONES if z["bosses"])


def _reach_end(a):
    for _ in range(a.total + 2):
        r = a.travel()
        if isinstance(r, tuple) and r[0] == "boss":
            return r
    raise AssertionError("never reached the boss gate")


def _panel_at_boss(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)   # clean march to the gate
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_champ())
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            return pan
    raise AssertionError("boss fight never opened")


class _Win:
    won = True


class _Loss:
    won = False


# -- engine -------------------------------------------------------------------
def test_reaching_the_end_opens_the_boss_not_an_instant_win(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    r = _reach_end(a)
    assert r[1] is a.boss and r[1].get("boss")            # the zone's gate boss
    assert not a.done and a.loc == a.total                # crossing did NOT win


def test_felling_the_boss_conquers_the_zone(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    assert a.resolve_boss(True) == "won" and a.done


def test_a_survivable_boss_loss_retries_then_fails_at_zero(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    outs = [a.resolve_boss(False) for _ in range(MAX_LIVES)]
    assert outs == ["retry"] * (MAX_LIVES - 1) + ["failed"]
    assert a.failed and a.lives == 0 and not a.done


def test_fleeing_the_boss_turns_back_without_winning(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    assert a.resolve_boss(False, fled=True) == "fled"
    assert not a.done and not a.failed                     # neither win nor loss


# -- panel --------------------------------------------------------------------
def test_the_panel_opens_the_boss_on_its_biome(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    assert type(pan.sub).__name__ == "BattlePanel"
    assert pan.sub._enemy is pan.adv.boss and pan.sub._enemy.get("boss")
    assert pan.sub.scene == pan.adv.scene                  # fought on the zone biome
    assert not pan.travelling


def test_a_boss_win_teleports_home_conquered(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Win())
    assert pan.adv.done and "felled" in pan._home_msg
    assert pan._summary                           # the results card shows first
    pan.key("space")                              # dismiss -> rides the teleport home
    assert pan._trans is not None


def test_a_boss_loss_stands_at_the_gate_and_space_re_engages(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Loss())
    assert pan._at_gate and not pan._fighting_boss
    assert "fight" in pan.strip().lower()                  # the retry prompt
    pan.key("space")
    assert pan._fighting_boss and type(pan.sub).__name__ == "BattlePanel"


def test_the_gate_esc_turns_back_home(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Loss())                              # -> at the gate
    pan.key("escape")                                      # turn back -> results card
    assert pan._summary and "Turned back" in pan._home_msg
    pan.key("space")
    assert pan._trans is not None


def test_the_final_boss_loss_fails_the_run_home(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.adv.lives = 1
    pan.sub = None
    pan._battle_done(_Loss())
    assert pan.adv.failed and "Defeated" in pan._home_msg
    assert pan._summary                           # the results card shows first
    pan.key("space")
    assert pan._trans is not None
