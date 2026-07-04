"""Death/mortality math audit (2026-07): canon re-verification vs
PhysicalState.setLapsedLife / setTotalLifespan / saveFromDeath / sicken /
injure / fatigue / worsened* / hungerMistakePenalty / xEvolve /
calcXAntibodyLifeDec + config column 1.

Canon death is ONE trigger -- old age -- reached faster through the
LifeDec burn economy.  Verified: saveFromDeath (hunger 0, bonus -1,
lapsedLife = total - RevivalLifeInc 45000 on the /60 scale, then the
death evolution), the dying mash (HitsToSave 175 -> 30, a documented
clock adaptation), the postponeDie busy-state machinery (approximated by
tuipet's fx flow), and the death evolution (the evolution audit).

Fixed (canon divergences):
 * The BURN ECONOMY was mostly missing: SickLifeDec/InjuryLifeDec 10800
   per onset, WorseSick/WorseInjuryLifeDec 10800 per worsening (their
   omission notes are gone), FatigueLifeDec 21600 (+3600 geriatric), and
   the X-Program's one-time price (86400/nextInt(7), a 0 draw free) --
   all on the /60 game scale.
 * MistakeHungerLifeDec used a bespoke rescale (3600) instead of the
   series' /60 (360) -- the BadMed bug class again.
 * InstantDeathGracePeriod was unported: a burn can never kill inside
   the grace -- _burn_life clamps to age + 60.
 * The continuous per-second "extra" lifespan drip (sick 0.8 etc.) was
   INVENTED and is removed; the discrete caps (20/20/12h) stay as
   documented tuipet safety nets beneath the burns, their false
   canon-provenance docstring corrected."""
import random

from tuipet.pet import (Pet, SICK_LIFE_DEC, INJURY_LIFE_DEC, WORSE_MALADY_LIFE_DEC,
                        FATIGUE_LIFE_DEC, GERIATRIC_FATIGUE_LIFE_DEC,
                        HUNGER_MISTAKE_LIFE_DEC, INSTANT_DEATH_GRACE)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_every_malady_burns_life():
    p = _pet()
    l0 = p.lifespan
    p._sicken()
    assert p.lifespan == l0 - SICK_LIFE_DEC
    p._worsen_sick()
    assert p.lifespan == l0 - SICK_LIFE_DEC - WORSE_MALADY_LIFE_DEC
    q = _pet()
    l0 = q.lifespan
    q._injure()
    assert q.lifespan == l0 - INJURY_LIFE_DEC


def test_fatigue_burns_more_when_old():
    young = _pet()
    l0 = young.lifespan
    young._fatigue()
    assert young.lifespan == l0 - FATIGUE_LIFE_DEC
    old = _pet()
    old.age_seconds = old.lifespan - 100.0       # geriatric band
    l1 = old.lifespan
    old._fatigue()
    # the geriatric surcharge applies -- but never past the death grace
    assert old.lifespan == max(old.age_seconds + INSTANT_DEATH_GRACE,
                               l1 - FATIGUE_LIFE_DEC - GERIATRIC_FATIGUE_LIFE_DEC)


def test_hunger_mistakes_compound_by_total_count():
    p = _pet(care_mistakes=0, hunger=0, calories=-4)
    l0 = p.lifespan
    p._tick_hunger(600.0)                        # the first unanswered call
    assert p.care_mistakes == 1
    assert p.lifespan == l0 - HUNGER_MISTAKE_LIFE_DEC * 1
    p._hunger_call_t = 0.0                       # a fresh call (past the postpone)
    p._tick_hunger(600.0)                        # the second burns DOUBLE
    assert p.lifespan == l0 - HUNGER_MISTAKE_LIFE_DEC * 3


def test_a_burn_cannot_kill_inside_the_grace():
    p = _pet()
    p.age_seconds = p.lifespan - 30.0            # 30s from the end
    p._sicken()                                  # -180 would kill instantly
    assert p.lifespan == p.age_seconds + INSTANT_DEATH_GRACE
    assert not p.dead                            # the grace holds until the clock


def test_x_program_charges_life_once():
    random.seed(2)
    p = _pet()
    p.add_item("i:14")
    l0 = p.lifespan
    p.use_item("i:14")
    assert p.x_antibody == "Permanent"
    assert p.lifespan <= l0                      # the price (a 0 draw is free)
    p2 = _pet(x_antibody="Temporary")            # already marked: no charge
    p2.add_item("i:14")
    l2 = p2.lifespan
    random.seed(2)
    p2.use_item("i:14")
    assert p2.lifespan == l2


def test_save_from_death_leaves_the_revival_window():
    p = _pet()
    p.dead = True
    p.evol_bonus = 3
    p.save_from_death()
    assert not p.dead and p.hunger == 0 and p.evol_bonus == 2
    assert abs((p.lifespan - p.age_seconds) - 750.0) < 1e-6 or p.num != 100
