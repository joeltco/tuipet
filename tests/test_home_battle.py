"""The home BATTLE action (Joel 2026-07-23: "should we add battles
action into the system? like dm20 does it?" -> "yeah lets do it").

A first-class action-bar bout: tier-matched rival (battle.pick_enemy,
same stage bracket -- no punching down for free egg-gate wins), a REAL
record (wins/exp/KO6/log/+2 trainings, exactly like a road wild), and
NO purse -- adventure stays the earning game.  Energy is the pacer:
can_battle's >= 10 entry gate, -5 per bout, ~3 per full tank.
"""
import random

from tuipet.app import TuiPetApp, keys_markup
from tuipet.battle import Battle, pick_enemy
from tuipet.battlescreen import BattlePanel
from tuipet.pet import Pet


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    return p


def test_battle_rides_the_action_bar():
    assert ("m", "battle", "Battle") in TuiPetApp.BINDINGS
    assert "battle" in keys_markup()


def test_the_rival_is_tier_matched():
    """pick_enemy draws from the pet's own stage bracket -- a Mega can
    never farm Rookie wins for the egg gates."""
    p = _pet()
    random.seed(7)
    assert all(pick_enemy(p)["stage"] == "Champion" for _ in range(40))


def test_a_home_bout_records_real_but_pays_no_purse():
    p = _pet()
    p._set_energy(p.max_energy)
    bits0, battles0, tr0 = p.bits, p.battles, p.stage_trainings
    e0 = p.energy
    random.seed(3)
    b = Battle(p)                          # enemy=None -> pick_enemy
    while b.play_round() is not None:
        pass
    assert b.over
    assert p.battles == battles0 + 1       # a REAL recorded bout...
    assert p.stage_trainings == tr0 + 2    # ...that trains like any local fight
    assert p.bits == bits0                 # ...and pays NOTHING
    assert p.energy == e0 - 5              # the energy pacer's bill


def test_the_home_panel_keeps_the_home_scene():
    """BattlePanel(pet) with no enemy is the home bout: tier-matched pick,
    NOT the arena backdrop (that is the cup/pvp dress)."""
    p = _pet()
    random.seed(5)
    pan = BattlePanel(p)
    assert not pan.arena and not pan.wild
    assert pan._pick["stage"] == "Champion"


def test_the_home_bout_wears_the_battle_card():
    """painter_for must resolve a TOP-LEVEL BattlePanel to the battle
    card -- the home bout is the first top-level use of the panel."""
    from tuipet import statusbox
    fn = statusbox.painter_for(BattlePanel(_pet()))
    assert fn is statusbox.battle


def test_the_gate_is_can_battle():
    """The action refuses through the ONE gate: a drained pet never
    starts a bout (and the -5 bill can therefore never strand it,
    the energy floor law's spend side)."""
    p = _pet()
    p._set_energy(5)
    assert "drained" in p.can_battle()
