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

from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# (test_no_more_starvation_sickness left with the sickness system -- BASIC VPET 2026-07-17)




def test_an_effort_heal_survives_a_long_empty_spell():
    """H4 (gameplay audit 2026-07-19): _str_t kept accruing while the gauge
    sat EMPTY, so a heal after a long drought was decayed again on the very
    next tick -- and a fresh missed-day billed -- undoing it in one second.
    An empty gauge holds the timer; a refill starts a whole fresh interval."""
    p = Pet(num=-1, stage="Rookie", hunger=4, poop=0)
    p.world_seconds = 10 * 60.0                 # mid-day: awake
    p.strength = 0
    p._str_t = 9999.0                           # the drought's stale build-up
    p.tick(1.0)
    assert p._str_t == 0.0, "an empty gauge must hold the decay timer"
    p.strength = 4                              # the Vitamin's refill
    md0 = p.mistake_day
    p.tick(1.0)
    assert p.strength == 4, "the heal must survive the next tick"
    assert p.mistake_day == md0


def test_good_care_no_longer_mutes_the_happy_idles():
    """Gameplay polish #10 (2026-07-22): the under-drilled gate (effort<=2)
    muted BOTH idle families, so a well-kept pet played no ambient emote
    while a neglected one danced.  Joy plays at any effort now; the sulk
    stays an under-drilled tell."""
    from tuipet.pet import Pet

    def idled(strength, sick=False):
        p = Pet(num=100, stage="Champion", attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        p.hunger, p.energy, p.enthusiasm = 4, p.max_energy, 5
        p.strength, p.sick = strength, sick
        p.anim = "idle"
        assert p.current_mood() == ("Unhappy" if sick else "Happy")
        p._special_idle()
        return p.anim

    assert idled(4) in ("play", "happy")           # well-drilled joy PLAYS
    assert idled(4, sick=True) == "idle"           # a drilled pet doesn't sulk
    # the sulk is ALWAYS the tantrum now (the discouraged show, Joel
    # 2026-07-23): it wears the depressed gloom-cloud emote -- "angry"
    # is the same pose pair but stays the disturb grumble, emote-free
    assert idled(1, sick=True) == "tantrum"
