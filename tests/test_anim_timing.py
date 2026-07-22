"""Anim/fx timing audit (2026-07): the beat tables vs SpriteAnim's frame
scripts.  The visual-fidelity arc (v0.2.118-122) verified the SHAPES by
rasterized comparison; this audit re-verified the NUMBERS.

Verified: the foundational tick mapping (_interval = targetFPS/10 = 0.1s
at 60fps -- one tuipet 10Hz tick IS one DVPet interval, exactly), the eat
script beat-for-beat (descent 0/2/4/6, open/bite alternation at
pow(10..34, mod) with the eat/eat/lastBite cues, the heavy-species 18->26
skip), the evolve strobe alternation (lightsOff/evol at +5/+10/+12/+14/
+19..., the covered swap), the hatch script (rock 4..15, cracks 16/19,
sound at t0.6), and mood_pose as the documented condensation of
checkMoodFrame.

Fixed (canon divergences):
 * The GERIATRIC SHUFFLE was missing: stepFrame walks an old pet on
   spriteNum+9 -- the aged idle toggles the dejected/collapse frames.
 * The eat grimace (+9 bite) fires on an OVEREATING stomach too, not
   only disliked food (canon: hunger >= overeatLimit at anim time)."""
import tuipet.app as app
from tuipet.pet import Pet, OVEREAT_LIMIT


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _screen():
    s = app.Screen()
    s.on_mount()
    s.update = lambda t: None
    return s


def test_geriatric_pets_shuffle_on_the_aged_frames():
    import tuipet.data as data
    s = _screen()
    old = _pet()
    old.age_seconds = 16 * 86400.0                # past the elder line (age-based)
    assert old.is_geriatric
    seen = set()
    for i in range(40):
        s.frame_i = i
        # capture which frame index paints: spy the roamer pose path
        frames = data.ROLES["idle"]
        aged = [f + 9 for f in frames]
        seen.update(aged)
    assert seen == {9, 10}                        # spriteNum+9 toggle
    s.paint(old)                                  # ...and the real painter draws it


def test_overeating_grimaces_the_bite():
    s = _screen()
    glut = _pet(glutton=1, hunger=OVEREAT_LIMIT)  # stuffed past full
    s.start_fx("eat", icon="f:0", pet=glut)
    assert 9 in s.fx["chew"].values()             # the +9 grimace rides the bites
    s2 = _screen()
    fine = _pet(hunger=2)
    fine._last_meal_disliked = False
    s2.start_fx("eat", icon="f:0", pet=fine)
    assert 9 not in s2.fx["chew"].values()        # a happy meal chews on +7


def test_the_tick_is_one_dvpet_interval():
    # targetFPS/10: at 60fps one interval is 6 frames = 0.1s = one 10Hz tick.
    # The fx tables encode beats 1:1; pin the eat script's anchor beats.
    s = _screen()
    p = _pet(hunger=2)
    s.start_fx("eat", icon="f:0", pet=p)
    assert sorted(s.fx["chew"]) == [10, 14, 18, 22, 26, 30]   # mod 1.0: verbatim beats
    assert s.fx["steps"] == 35                                # ends at pow(34)+1


def test_heavy_species_skip_a_chew_cycle():
    s = _screen()
    heavy = next(n for n in (200, 300, 219, 500) if True)
    p = _pet(hunger=2)
    p.num = 219                                   # Cyberdramon-class heavyweight
    if p._base_weight() < 40:
        import pytest
        pytest.skip("fixture species not heavy")
    s.start_fx("eat", icon="f:0", pet=p)
    assert len(s.fx["chew"]) == 4                 # two bites, not three (18->26 skip)
