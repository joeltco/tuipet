"""Hunger system vs DVPet PhysicalState: awake-gated neglect, starvation weight
loss, the hunger-mistake penalty, and the glutton decay coefficient."""
from tuipet.pet import (Pet, CALORIE_LIMIT, HUNGER_MISTAKE_LIFE_DEC,
                        STARVE_WEIGHT_DEC)


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _drain_one_lapse(p):
    """Force the calorie buffer to bottom on the next lapse tick."""
    p.calories = -CALORIE_LIMIT + 1
    p._cal_t = p._hunger_interval          # due now
    p.tick(1.0)


def test_sleeping_pet_never_racks_hunger_mistakes():
    # DVPet hungerCall(): alive && !asleep && hunger<=0 -- no overnight mistakes
    p = _pet(hunger=0, asleep=True, anim="sleep")
    m0, w0 = p.care_mistakes, p.lifespan
    _drain_one_lapse(p)
    assert p.care_mistakes == m0
    assert p.lifespan == w0


def test_awake_hunger_neglect_is_a_mistake_with_teeth():
    p = _pet(hunger=0, asleep=False)
    m0, l0, o0 = p.care_mistakes, p.lifespan, p.obedience
    _drain_one_lapse(p)
    assert p.care_mistakes == m0 + 1
    assert p.lifespan < l0                      # MistakeHungerLifeDec x mistakes
    assert p.obedience == o0 + 1                # HungerMistakeObedienceChange


def test_starving_sheds_weight_each_lapse():
    p = _pet(hunger=0, weight=20)
    _drain_one_lapse(p)
    assert p.weight <= 20 - STARVE_WEIGHT_DEC + 1   # starvation weight loss applied
    assert p.weight < 20


def test_glutton_gets_hungry_faster():
    glut = _pet(glutton=1)
    picky = _pet(glutton=-1)
    normal = _pet(glutton=0)
    assert glut._hunger_interval < normal._hunger_interval < picky._hunger_interval


def test_starve_death_timer_pauses_while_asleep():
    p = _pet(hunger=0, asleep=True, anim="sleep")
    p._starve_t = 11.9 * 3600
    p.tick(1.0)
    assert not p.dead and p._starve_t == 11.9 * 3600   # frozen overnight
    p.asleep = False
    for _ in range(400):
        p.tick(1.0)
        if p.dead:
            break
    assert p.dead                                       # resumes awake
