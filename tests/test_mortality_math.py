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

from tuipet.pet import (Pet, INSTANT_DEATH_GRACE)


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# (test_every_malady_burns_life left with the sickness system -- BASIC VPET 2026-07-17)


def test_a_burn_cannot_kill_inside_the_grace():
    p = _pet()
    p.age_seconds = p.lifespan - 30.0            # 30s from the end
    p._burn_life(180.0)                          # -180 would kill instantly
    #                                              (the sicken source left
    #                                              with the sickness system)
    assert p.lifespan == p.age_seconds + INSTANT_DEATH_GRACE
    assert not p.dead                            # the grace holds until the clock


def test_save_from_death_leaves_the_revival_window():
    # S1 ruling 2026-07-20: RevivalLifeInc RESTORES life -- an old-age death
    # walks out with the ~750s window, while a YOUNG rescue keeps the life it
    # had (the old unconditional jump burned it down to the window)
    p = _pet()
    p.dead = True
    p.evol_bonus = 3
    age0 = p.age_seconds
    p.save_from_death()
    assert not p.dead and p.hunger == 0 and p.evol_bonus == 2
    assert p.age_seconds == age0                 # young: nothing burned
    q = _pet()
    q.dead = True
    q.age_seconds = q.lifespan                   # died of old age
    q.save_from_death()
    assert abs((q.lifespan - q.age_seconds) - 750.0) < 1e-6 or q.num != 100


def test_the_care_bonus_carries_across_generations():
    """careBonusOnReset (death/rebirth audit 2026-07-06; unified onto the ONE
    bonus_seed channel, digimemory audit 2026-07-06): canon never zeroes the
    bonus at resetToEgg -- the ended life's full report card (final_care_grade)
    seeds what the next generation inherits, floored at zero."""
    from tuipet import persistence
    p = _pet(care_mistakes=0, mood=200, obedience=100, evol_bonus=2)
    persistence.bank_bonus_seed(p.final_care_grade())
    heir = Pet.new_egg(generation=2)
    heir.evol_bonus = persistence.take_bonus_seed()  # app._grant_digimemory's hand-off
    assert heir.evol_bonus == p.final_care_grade() > 2   # clean/Happy/obedient legs land
    fresh = Pet.new_egg(generation=1)
    assert fresh.evol_bonus == 0                     # a fresh game inherits nothing
    q = _pet(care_mistakes=6, mood=-50, obedience=10, evol_bonus=0)
    assert q.final_care_grade() == 0                 # a graded wreck floors at zero


def test_the_heir_inherits_the_device_bag():
    """Item/inventory audit 2026-07-06: canon's resetToEgg never touches bits,
    the bag, or the beaten-qualifier trophies -- the estate is device-lifetime.
    (The generation-1 StartingUses kit left with the staple props:
    strict-DSprite items, 2026-07-17 -- a fresh device starts empty, and an
    inherited bag sheds any dead furniture keys.)"""
    from tuipet import persistence
    p = _pet(bits=777, trophies=2)
    p.inventory = {"i:15": 1, "f:3": 4, "i:82": 40}
    p.trophies_won = {9: "Spring"}
    persistence.snapshot_prev_gen(p)
    heir = Pet.new_egg(generation=2)
    assert heir.bits == 777
    assert heir.inventory == {"i:15": 1, "f:3": 4}      # carries, minus dead keys
    assert heir.trophies == 2 and heir.trophies_won == {9: "Spring"}
    fresh = Pet.new_egg(generation=1)
    assert fresh.bits == 0
    assert fresh.inventory == {}
