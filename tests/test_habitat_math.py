"""Habitat/temperature math audit (2026-07): canon re-verification vs
PhysicalState.checkEnergyIncFromPerfectConditions / setEnergy /
setCurrentHabitat / getMajorHabitat, Habitat.java + config column 1.
(The drift, day bands, weather params and ideal-band mood shipped with the
sleep/weather audit; the affinity fatigue/sick-length mods with training
and medicine.)

Verified matching: the perfect-conditions energy save (base 10 shrunk by
weather -2 / mood -1 / temp -1 / nutrition -2 / compat -1 each, grown by
incompat +2/+1; nextInt(range)==1 pays the point back; gated on the
FAVOURITE hour and a genuine DROP), habitat buy/move (price + unlock +
move-in with a fresh climate roll), the species IdealTemp bands, and
majorHabitat's most-lived-in record (the evolution audit's consumer).

Fixed (canon divergence):
 * MinEnergyLifePenalty (3600 -> 60) was unported -- and unreachable: the
   old clamp ran before the floor could be detected.  Bottoming out at
   -maxEnergy now burns life per hit, through the graced _burn_life."""
import random

from tuipet.pet import Pet, MIN_ENERGY_LIFE_PENALTY


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_bottoming_out_burns_life():
    # injured: canon setEnergy skips the fatigue trigger (and its own life
    # burn -- pinned in test_mood_system), isolating the floor penalty
    p = _pet(energy=-23, max_energy=24, inj_length=5.0)
    l0 = p.lifespan
    p._set_energy(p.energy - 5)                   # raw -28 < -24: the floor
    assert p.energy == -24
    assert p.lifespan == l0 - MIN_ENERGY_LIFE_PENALTY
    p._set_energy(p.energy - 1)                   # pinned at the floor: burns AGAIN
    assert p.lifespan == l0 - 2 * MIN_ENERGY_LIFE_PENALTY


def test_ordinary_drains_never_burn():
    p = _pet(energy=10)
    l0 = p.lifespan
    p._set_energy(3)
    assert p.lifespan == l0


def test_perfect_conditions_can_save_the_point():
    hits = 0
    random.seed(1)
    for _ in range(400):
        p = _pet(energy=10, mood=300)
        p.time_pref = {k: 0 for k in p.time_pref}
        p.time_pref[p.day_phase] = 50             # NOW is its favourite hour
        p.temp = sum(p.ideal_temp) / 2
        p.nutr_protein = p.nutr_mineral = p.nutr_vitamin = 50
        p._set_energy(9)
        hits += p.energy == 10                    # the drop bounced back
    assert 15 <= hits <= 160                      # ~1/(10-2-1-1-2 +compat) per drop


def test_wrong_hour_never_saves():
    random.seed(2)
    for _ in range(120):
        p = _pet(energy=10, mood=300)
        p.time_pref = {k: 0 for k in p.time_pref}   # no favourite hour at all
        p._set_energy(9)
        assert p.energy == 9


def test_buying_a_home_moves_you_in_with_fresh_weather():
    p = _pet(bits=99999)
    from tuipet import data
    target = next(h for h in data.load_habitats().values()
                  if h["id"] not in p.habitats and h["price"] > 0)
    msg = p.buy_habitat(target["id"])
    assert "moved in" in msg.lower() or "Bought" in msg
    assert p.habitat == target["id"] and target["id"] in p.habitats
    assert p._weather_day == -1                   # setCurrentHabitat's fresh roll
