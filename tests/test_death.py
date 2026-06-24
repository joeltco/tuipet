"""Care-mistake / neglect death triggers (Workstream A).

DVPet has discrete neglect deaths, not just a faster lifespan burn. tuipet's tick()
implements four:
  - care_mistakes >= 20  (MaxCareMistakes)   -> death   [per-form, resets on evolve]
  - injuries     >= 20   (MaxInjuries)       -> death   [per-form]
  - hunger == 0 for 12h continuous           -> death   [persists across evolutions]
  - age_seconds >= lifespan                  -> natural death

These guard the thresholds (a wrong one ruins a playthrough) and the safety rails:
eggs are immune, a dead pet stays frozen, and feeding resets the starvation clock.
A healthy pet is constructed (hunger full, no filth) so the only death is the one
under test. num=-1 keeps tick() deterministic and sprite-free.
"""
from tuipet.pet import Pet


def _healthy(stage="Rookie", **kw):
    return Pet(num=-1, stage=stage, hunger=4, poop=0, **kw)


def test_care_mistakes_20_is_fatal():
    p = _healthy(care_mistakes=20)
    p.tick(0.1)
    assert p.dead is True


def test_care_mistakes_19_is_survivable():
    p = _healthy(care_mistakes=19)
    p.tick(0.1)
    assert p.dead is False, "19 care mistakes must not kill (boundary is 20)"


def test_injuries_20_is_fatal():
    p = _healthy(injuries=20)
    p.tick(0.1)
    assert p.dead is True


def test_injuries_19_is_survivable():
    p = _healthy(injuries=19)
    p.tick(0.1)
    assert p.dead is False


def test_starvation_12h_is_fatal():
    p = _healthy()
    p.hunger = 0
    p._starve_t = 12 * 3600 - 1
    p.tick(2)                     # crosses the 12h continuous-starvation threshold
    assert p.dead is True


def test_starvation_clock_resets_when_fed():
    p = _healthy()
    p.hunger = 0
    p._starve_t = 12 * 3600 - 5
    p.hunger = 4                  # fed before the clock elapses
    p.tick(0.1)
    assert p.dead is False
    assert p._starve_t == 0.0, "feeding must reset the starvation timer"


def test_lifespan_expiry_is_fatal():
    p = _healthy()
    p.lifespan = 100.0
    p.age_seconds = 100.0
    p.tick(0.1)                   # age ticks past lifespan
    assert p.dead is True


def test_egg_is_immune_to_neglect_death():
    egg = Pet(num=-1, stage="Egg", care_mistakes=99, injuries=99)
    egg.hunger = 0
    egg._starve_t = 99 * 3600
    egg.tick(0.1)
    assert egg.dead is False, "an egg cannot die of neglect"


def test_dead_pet_stays_frozen():
    p = _healthy(care_mistakes=5)
    p.dead = True
    p.tick(10_000)
    assert p.dead is True
    assert p.care_mistakes == 5, "a dead pet's life-sim state must not advance"
