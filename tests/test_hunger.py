"""Hunger system vs DVPet PhysicalState: awake-gated neglect, starvation weight
loss, the hunger-mistake penalty, and the glutton decay coefficient."""
from tuipet.pet import (Pet, CALORIE_LIMIT, STARVE_WEIGHT_DEC)


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
    m0 = p.care_mistakes
    _drain_one_lapse(p)
    assert p.care_mistakes == m0


def test_awake_hunger_neglect_is_a_mistake_with_teeth():
    # LINES_SPEC §5: the mistake is the unanswered CALL (10 min, one per call,
    # postponed after) -- no longer repeating every calorie cycle while starving
    p = _pet(hunger=0, asleep=False)
    m0 = p.care_mistakes
    p._tick_hunger(599.0)
    assert p.care_mistakes == m0                # inside the call window: no mistake yet
    p._tick_hunger(1.0)
    assert p.care_mistakes == m0 + 1
    # (the MistakeHungerLifeDec burn left with the lifespan clock -- the
    # mistake itself now raises the DSprite hazard bracket)
    # (the obedience change left with the discipline system)
    p._tick_hunger(600.0)
    assert p.care_mistakes == m0 + 1            # postponed: one mistake per call


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
    p.sleep_lapse, p.sleep_limit = 0.0, 9e9            # hold the pressure clock: stays awake
    for _ in range(400):
        p.tick(1.0)
        if p.dead:
            break
    assert p.dead                                       # resumes awake
