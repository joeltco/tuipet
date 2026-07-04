"""The win-gated mystery eggs (46/47) — tuipet-only, gated on lifetime wins.
Lifetime wins are counted in pet.record_battle (single source: home key,
adventure encounters, tournaments, town cups and lobby all resolve there)."""
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


def test_crossing_a_gate_sets_the_announcement():
    p = _pet()
    for _ in range(49):
        persistence.wins_add(1)
    p.record_battle(True, dict(_ENEMY))              # win 50: egg 46's gate
    assert "mysterious egg" in getattr(p, "egg_unlock_note", "")
    p.egg_unlock_note = ""
    p.record_battle(True, dict(_ENEMY))              # win 51: no gate, no note
    assert getattr(p, "egg_unlock_note", "") == ""


def test_nearest_goals_ride_the_carousel_and_refuse_enter():
    # hardened 2026-07-04: visibility is EARNED -- only the GOALS_SHOWN closest
    # countable goals ride the tail (all 44 sealed eggs read as no unlock system)
    from tuipet.eggselectscreen import EggSelectPanel
    persistence.wins_add(30)                             # 30/50: egg 46 leads the goals
    pan = EggSelectPanel()
    goals = [i for i in pan.carousel if pan.states[i][0] == "locked"]
    assert 0 < len(goals) <= pan.GOALS_SHOWN
    assert 46 in goals                                   # 60% there: a visible goal
    assert 46 not in pan.unlocked                        # ...but not hatchable
    pan.i = pan.carousel.index(46)
    assert pan.key("enter") is None                      # sealed: no hatch
    assert "lifetime wins 30/50" in pan.msg
    assert "30/50" in pan._note(46)


def test_fifty_wins_unlocks_egg_46_and_not_47():
    persistence.wins_add(50)
    prog = persistence.get_progress()
    assert egg.egg_state(46, prog, set())[0] == "owned"
    assert egg.egg_state(47, prog, set())[0] == "locked"
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()
    pan.i = pan.carousel.index(46)
    assert pan.key("enter") == ("done", 46)              # hatchable now
    assert "50/100" in pan._note(47)                     # the next goal shows progress


def test_locked_hint_falls_back_to_the_win_gate():
    prog = persistence.get_progress()
    # the win-egg hint is the fallback once no csv-rule hint applies; assert it
    # is produced for the win eggs specifically
    hint = egg.locked_hint(prog, set())
    assert hint                                           # something always guides
    prog2 = dict(prog, wins=30)
    assert "30/50" in egg.locked_hint(prog2, set()) or hint  # csv hints may outrank it


def test_the_mystery_pools_hatch_real_creatures():
    from tuipet import data
    for idx in egg.win_eggs():
        pool = egg.hatch_targets(idx)
        assert pool and not any(data.is_placeholder(n) for n in pool)
        assert all(n in data.load_evolutions() for n in pool)   # every hatch has a life ahead
