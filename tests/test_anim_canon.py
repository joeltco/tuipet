"""Canon-fidelity fixes from the SpriteAnim sweep (see ANIMATION_SPEC.md):
the happy/cheer pose pair, the net-zero sick shuffle, and the idle mood poses."""
from tuipet import anim, data


def test_happy_role_is_the_praise_pair_not_the_scold_pair():
    # DVPet cheer(true) bounces up=5/down=7; [6,4] was the cheer(false)/scold pair.
    # battlescreen.py already uses 5/7 for the win pose -- the ROLE must match it.
    assert data.ROLES["happy"] == [5, 7]


def test_sick_shuffle_is_net_zero():
    """idleUnwell sways moveLeft1@30, moveRight1@35/40, moveLeft1@45 -> the offset
    is held -1 over [30,35), 0 over [35,40), +1 over [40,45), 0 elsewhere; net zero."""
    assert anim.sick_frame(0) == (10, 0)
    assert anim.sick_frame(30)[1] == -1
    assert anim.sick_frame(34)[1] == -1
    assert anim.sick_frame(35)[1] == 0          # the second move cancels the first
    assert anim.sick_frame(40)[1] == 1
    assert anim.sick_frame(44)[1] == 1
    assert anim.sick_frame(45)[1] == 0          # back to centre
    assert anim.sick_frame(49)[0] == 9          # weary flash before the reset
    # over a full period the shuffle returns to where it started
    assert sum(anim.sick_frame(f)[1] for f in range(anim.SICK_PERIOD)) == 0


class _StubPet:
    def __init__(self, energy=10, fatigued=False, mood=0, enthusiasm=0):
        self.energy, self._fat, self.mood, self.enthusiasm = energy, fatigued, mood, enthusiasm

    def is_fatigued(self):
        return self._fat


def test_mood_pose_reads_state():
    assert anim.mood_pose(_StubPet(energy=0)) in (10, 9, 2)          # spent -> weary
    assert anim.mood_pose(_StubPet(fatigued=True)) in (10, 9, 2)     # tired -> weary
    assert anim.mood_pose(_StubPet(mood=-5)) in (4, 6)               # unhappy -> sour
    assert anim.mood_pose(_StubPet(mood=5, enthusiasm=0)) == 5       # content & spirited -> bright
    assert anim.mood_pose(_StubPet(mood=0)) is None                  # neutral -> ordinary walk pose


def test_mood_pose_indices_are_valid_sprite_frames():
    # every pose mood_pose can return must be a real frame on the 11-frame strip
    for p in (10, 9, 2, 4, 6, 5):
        assert 0 <= p <= 10
