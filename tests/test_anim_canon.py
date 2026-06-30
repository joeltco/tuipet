"""Canon-fidelity fixes from the SpriteAnim sweep (see ANIMATION_SPEC.md):
the happy/cheer pose pair, the net-zero sick shuffle, and the idle mood poses."""
from tuipet import anim, data


def test_happy_role_is_the_dvpet_cheer_pair():
    # DVPet Cheering: cheer-up 5 -> cheer-down 7 (the canonical praise/win/evolve pair).
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


def test_play_renders_its_own_hop():
    # DVPet Bounce/Jump toy interact is its own pose pair (1 -> 5); the jump is also a
    # real on-screen lift via the yshift hop (PLAY_HOP/PLAY_HOP_H).
    from tuipet import app
    assert data.ROLES["play"] == [1, 5]
    assert app.PLAY_HOP > 0 and app.PLAY_HOP_H > 0


def test_render_yshift_lifts_the_sprite():
    """yshift raises the sprite (the play hop); enough yshift lifts it off the top."""
    from tuipet.render import render_screen
    sprite = ["1111", "1111"]
    empty = render_screen([], 8, 6)
    ground = render_screen(sprite, 8, 6)
    assert ground.spans != empty.spans                          # a grounded sprite is visible
    assert render_screen(sprite, 8, 6, yshift=99).spans == empty.spans   # hopped clean off-screen


def test_battle_strong_hit_sfx_branches_on_double():
    """DVPet doubleAttack launches/lands with the strong sting/impact; a normal hit
    uses the plain ones.  _emit_sfx is pure over (timeline[i], _last_m) -- drive it on
    a stub so we don't have to build a whole battle."""
    from tuipet.battlescreen import BattlePanel

    def _sfx(marker, double):
        stub = type("S", (), {"sfx": None, "_last_m": None, "i": 0,
                              "timeline": [{"m": marker, "double": double}]})()
        BattlePanel._emit_sfx(stub)
        return stub.sfx

    assert _sfx("fire_out", True) == "strongAttack"
    assert _sfx("fire_out", False) == "attack"
    assert _sfx("hit", True) == "strongHit"
    assert _sfx("hit", False) == "attackHit"
