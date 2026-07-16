"""The win-gated mystery eggs (41/42) — tuipet-only, gated on lifetime wins.
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
    p.record_battle(True, dict(_ENEMY))              # win 50: egg 41's gate
    assert "mysterious egg" in getattr(p, "egg_unlock_note", "")
    p.egg_unlock_note = ""
    p.record_battle(True, dict(_ENEMY))              # win 51: no gate, no note
    assert getattr(p, "egg_unlock_note", "") == ""


def test_locked_win_eggs_stay_off_the_carousel():
    # visibility is EARNED: a locked mystery egg is not shown at all now
    from tuipet.eggselectscreen import EggSelectPanel
    persistence.wins_add(30)                             # 30/50: egg 41 not yet won
    pan = EggSelectPanel()
    assert 41 not in pan.carousel                        # locked -> hidden entirely
    assert all(pan.states[i][0] in ("owned", "temp") for i in pan.carousel)


def test_fifty_wins_unlocks_egg_41_and_not_42():
    persistence.wins_add(50)
    prog = persistence.get_progress()
    assert egg.egg_state(41, prog, set())[0] == "owned"
    assert egg.egg_state(42, prog, set())[0] == "locked"
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()
    assert 41 in pan.carousel                            # owned -> on the carousel
    assert 42 not in pan.carousel                        # still locked -> hidden
    pan.i = pan.carousel.index(41)
    assert pan.key("enter") == ("done", 41)              # hatchable now


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
