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


def test_no_more_starvation_sickness():
    random.seed(5)
    for _ in range(50):
        p = _pet(hunger=0, poop=0)
        p.tick(1.0)
        assert not p.sick                      # canon has no hunger==0 sick roll


