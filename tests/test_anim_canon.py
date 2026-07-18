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
    """LIVE-signal stub (idle-pose audit 2026-07-18: mood/enthusiasm were
    frozen meters; the pose reads energy + the derived word + condition)."""

    def __init__(self, energy=10, word="Neutral", cond=1):
        self.energy, self._word, self._cond = energy, word, cond

    def current_mood(self):
        return self._word

    def condition(self):
        return self._cond


def test_mood_pose_reads_live_state():
    assert anim.mood_pose(_StubPet(energy=0)) in (10, 9, 2)          # spent -> weary
    assert anim.mood_pose(_StubPet(word="Unhappy")) in (4, 6)        # sick/starving -> sour
    assert anim.mood_pose(_StubPet(cond=3)) == 5                     # well-kept -> bright
    assert anim.mood_pose(_StubPet()) is None                        # ordinary -> walk pose


def test_bright_is_earned_not_frozen():
    """The frozen-meter bug: mood sat at its hatch value (100) forever, so
    the bright pose fired for every pet.  Now it demands condition 3 -- a
    REAL pet fresh out of care neglect must read neutral, not bright."""
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    p.mood = 100                              # the frozen hatch value
    p.hunger, p.strength, p.energy = 1, 0, 3  # visibly under-kept
    assert anim.mood_pose(p) is None or anim.mood_pose(p) in (4, 6)
    p.hunger = p.strength = 4
    p.energy = p.max_energy
    assert anim.mood_pose(p) == 5             # NOW it beams


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
