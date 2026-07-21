"""Lifetime wins: the single source (pet.record_battle) feeding the win-gated
egg rules (Chibickmon 10 / V 25 / Slayerdra 30 / Sakumon 50 / Zuba 60).
The unlock-spread pass (2026-07-20) moved Hack to the cup axis and X3 to the
Mega axis, so they no longer ride wins (DORU carries the festival axis)."""
from tuipet.pet import Pet
from tuipet import egg, persistence


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


_ENEMY = {"num": 4, "name": "X", "stage": "Champion", "vaccine": 5,
          "data_power": 5, "virus": 5, "hp": 8, "bits": (0, 0)}


def test_every_recorded_win_counts_and_losses_do_not():
    p = _pet()
    p.record_battle(True, dict(_ENEMY))
    p.record_battle(False, None)
    p.record_battle(True, dict(_ENEMY))
    assert persistence.get_wins() == 2


def test_crossing_a_wins_gate_sets_the_announcement():
    """The nursery note fires exactly when a lifetime total crosses a rule's
    wins gate (50 = Sakumon), and stays quiet in between."""
    assert 50 in egg.wins_thresholds()
    p = _pet()
    for _ in range(49):
        persistence.wins_add(1)
    p.record_battle(True, dict(_ENEMY))              # win 50: Sakumon's gate
    assert "egg" in getattr(p, "egg_unlock_note", "")
    p.egg_unlock_note = ""
    p.record_battle(True, dict(_ENEMY))              # win 51: no gate, no note
    assert getattr(p, "egg_unlock_note", "") == ""


def test_mystery_eggs_are_gone():
    assert not hasattr(egg, "_WIN_EGGS")
    assert not hasattr(egg, "win_eggs")
    assert "???" not in {egg.hatch_name(i) for i in range(egg.count())}
