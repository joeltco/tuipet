"""The authentic DM20 wall-mash training (see training.py / AUTHENTIC_REBUILD.md):
your Digimon attacks a brick wall; MASH the button to smash it. >= MASH_TARGET hits
in the window destroys the wall -> full success (+1 Effort, a training credit toward
evolution); a partial showing still lands some hits; too few -> it fails.
"""
from tuipet import training as T
from tuipet.pet import Pet


def _panel(**kw):
    # high energy / normal weight so the gain under test is deterministic
    p = Pet(num=1, stage="Child", strength=0, obedience=0, trainings=0,
            energy=24, max_energy=24, weight=20, **kw)
    return p, T.TrainingPanel(p)


def _mash(panel, n):
    for _ in range(n):
        panel.key(" ")


def test_starts_in_play_no_drill_menu():
    _, panel = _panel()
    assert panel.phase == "play"          # single game: straight into the mash, no drill picker
    assert panel.taps == 0


def test_full_smash_succeeds_and_builds_effort():
    pet, panel = _panel()
    _mash(panel, T.MASH_TARGET)           # >= 13 hits destroys the wall...
    assert panel.phase == "done"          # ...and ends the drill early
    assert panel.full and panel.success
    assert pet.strength == 1              # +1 Effort
    assert pet.trainings == 1             # a training credit toward evolution


def test_timeout_with_too_few_hits_fails():
    pet, panel = _panel()
    _mash(panel, 3)                       # below MASH_PARTIAL
    while panel.phase == "play":
        panel.anim()                      # let the window run out
    assert panel.phase == "done"
    assert not panel.success and not panel.full
    assert pet.strength == 0 and pet.trainings == 0   # a failed drill builds nothing


def test_partial_lands_some_hits_short_of_a_full_break():
    pet, panel = _panel()
    _mash(panel, T.MASH_PARTIAL)          # enough to count, not enough to smash it
    while panel.phase == "play":
        panel.anim()
    assert panel.success and not panel.full
    assert pet.strength == 1 and pet.trainings == 1


def test_wall_crumbles_as_you_mash():
    # the rendered wall has fewer bricks the more you hit it (visual feedback is real)
    full = len(T._wall_overlay(0))
    half = len(T._wall_overlay(T.MASH_TARGET // 2))
    gone = len(T._wall_overlay(T.MASH_TARGET))
    assert full > half > gone == 0


def test_done_key_closes_with_the_result():
    pet, panel = _panel()
    _mash(panel, T.MASH_TARGET)
    assert panel.phase == "done"
    assert panel.key(" ") == ("done", panel.result)   # closing returns the outcome message
