"""Canon-fidelity fixes from the SpriteAnim sweep (see ANIMATION_SPEC.md):
the happy/cheer pose pair, the net-zero sick shuffle, and the idle mood poses."""
from tuipet import anim, data


def test_happy_role_is_the_praise_pair_not_the_scold_pair():
    # DVPet cheer(true) bounces up=5/down=7; [6,4] was the cheer(false)/scold pair.
    # battlescreen.py already uses 5/7 for the win pose -- the ROLE must match it.
    assert data.ROLES["happy"] == [5, 7]


def test_sick_shuffle_is_net_zero():
    """The sick idle alternates the injured pair and sways 1px net-zero."""
    from tuipet.anim import sick_frame, SICK_PERIOD
    seen_idx = set()
    net = 0
    for f in range(SICK_PERIOD):
        idx, dx = sick_frame(f)
        seen_idx.add(idx)
        net += dx
    assert seen_idx == {10, 11}
    assert sum(dx for _, dx in (sick_frame(f) for f in range(SICK_PERIOD))) == 0



class _StubPet:
    def __init__(self, energy=10, sick=False, hunger=4, strength=4):
        self.energy, self.sick = energy, sick
        self.hunger, self.strength = hunger, strength


def test_mood_pose_reads_state():
    assert anim.mood_pose(_StubPet(energy=0)) in (10, 9, 2)          # spent -> weary
    assert anim.mood_pose(_StubPet(sick=True)) in (4, 6)             # unwell -> sour
    assert anim.mood_pose(_StubPet(hunger=0)) in (4, 6)              # starving -> sour
    assert anim.mood_pose(_StubPet()) is None                        # fine -> ordinary walk


def test_mood_pose_indices_are_valid_sprite_frames():
    # every pose mood_pose can return must be a real frame on the 11-frame strip
    for p in (10, 9, 2, 4, 6, 5):
        assert 0 <= p <= 10


def test_play_is_the_jump_pair_not_the_cheer_pair():
    # DVPet jumping()/playing() bounces poses 1<->5; cheer bounces 5<->7.  Play must
    # render its own hop, not reuse the cheer animation.
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
