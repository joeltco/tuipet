"""Poop/body math audit (2026-07): canon re-verification vs
PhysicalState.moodLapse / checkDepressed / checkFilthMoodDec / the filth
sickness rolls / poopWaitMoodCheck / poop / bmLapse + config.csv column 1.

Verified matching: the poop relief/shed/size math, the bowel-gauge mapping,
the strength decay + strengthCall, the filth care-mistake grace/postpone,
nutrition decay, Happy -10 / Unhappy +5 lapse values, the discipline-call
rows, and the window machinery (audited previously).

Fixed (canon divergences):
 * moodLapse: the sick/injured/care-call FREEZE was missing, as were the
   personality drifts (glutton x hunger band; the restless term keeps
   DVPet's shipped compare-the-trait quirk verbatim), the very-unhappy
   +10 split at minMood/2, the neutral -5 band [5,150), the bad-weight
   -2, and it now runs ASLEEP (MinMoodAsleep only mutes rock bottom).
 * DEPRESSION IS A STICKY STATE (checkDepressed), not a mood threshold:
   entered by roll while Unhappy (10/1000 below -250, else 1/1000),
   exited by roll (100/1000 sad, 500/1000 recovered +33 obedience), and
   while down it drifts mood +50 / obedience -5 / spirit -1 an interval.
   The undepressed item clears the STATE.
 * Filth mood was flat and misattributed to poopWait: canon charges the
   SPECIES filth_mood x piles every 5 game-min; poopWaitMoodCheck nags
   the HELD gauge (a sleeper holding it in), -1/-2 per game-min.
 * The filth sickness roll was flat 2%: canon scales per pile vs a bound
   (x species multiplier; the 12000 real-min bound rides the /60 game
   scale) and adds the worse-sick path; the STARVATION sickness the old
   roll invented does not exist in canon and is gone."""
import random

from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_misery_freezes_the_mood_lapse():
    sickly = _pet(mood=200, sick=True, sick_length=9999.0)
    well = _pet(mood=200)
    random.seed(1)
    for _ in range(70):
        sickly.tick(1.0)
    random.seed(1)
    for _ in range(70):
        well.tick(1.0)
    assert well.mood < 200                     # Happy drains -10 a lapse
    assert sickly.mood >= well.mood            # ...but misery froze the drift


def test_bad_weight_drains_mood():
    fat = _pet(mood=100, weight=60)            # far past Healthy for base 20
    fit = _pet(mood=100, weight=20)
    random.seed(2)
    for _ in range(70):
        fat.tick(1.0)
    random.seed(2)
    for _ in range(70):
        fit.tick(1.0)
    assert fat.mood < fit.mood                 # BadWeightMoodLapseDec -2 per lapse


def test_depression_is_a_sticky_state():
    p = _pet(mood=-260)
    assert p.current_mood() == "Unhappy"       # a low mood alone is NOT depression
    p.depressed = True
    p.mood = 100
    assert p.current_mood() == "Depressed"     # ...and the state outlives the mood


def test_depression_enters_and_exits_by_roll():
    random.seed(4)
    entered = 0
    for _ in range(40):
        p = _pet(mood=-260)
        for _ in range(60 * 30):               # ~30 intervals of rolls
            p.tick(1.0)
            p.mood = min(p.mood, -260)         # hold it in the danger band
            if p.depressed:
                break
        entered += p.depressed
    assert entered >= 3                        # 10/1000 per interval bites eventually
    # while down: mood climbs, obedience pays
    p = _pet(mood=-260, obedience=100, depressed=True)
    random.seed(9)
    m0, o0 = p.mood, p.obedience
    for _ in range(60):
        p.tick(1.0)
        if not p.depressed:
            break
    assert p.depressed is False or p.obedience < o0 or p.mood > m0


def test_filth_mood_scales_with_the_pile_count(monkeypatch):
    one = _pet(mood=0, poop=1, poop_sizes=[2])
    four = _pet(mood=0, poop=4, poop_sizes=[2] * 4)
    random.seed(3)
    for _ in range(310):
        one.tick(1.0)
    random.seed(3)
    for _ in range(310):
        four.tick(1.0)
    assert four.mood < one.mood                # species filth_mood x piles


def test_no_more_starvation_sickness():
    random.seed(5)
    for _ in range(50):
        p = _pet(hunger=0, poop=0)
        p.tick(1.0)
        assert not p.sick                      # canon has no hunger==0 sick roll


def test_held_gauge_nags_a_sleeper(monkeypatch):
    random.seed(6)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)
    assert p.asleep
    p.lights = False
    p._poop_t = p._poop_interval * 1.2         # holding it in
    m0 = p.mood
    for _ in range(80):
        p.tick(1.0)
        if not p.asleep:
            break
    assert p.mood < m0                         # poopWaitMoodCheck: -1/-2 a game-min


