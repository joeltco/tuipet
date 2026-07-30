"""THE CARE AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown care audit next."

F1 (FIXED) — THE STARVATION CLOCK COULD NEVER FIRE.  `_starve_t`
accumulates dt, which is GAME-MINUTES, and was compared against
`12 * 3600` — a real-seconds shape asking for 43,200 of them, i.e. THIRTY
GAME-DAYS of unbroken starvation.  Measured, it reached 2,940 after three
game-days while the 20-mistake ladder was already at 13, so the death it
guards could not happen — on a field round 41 deliberately PERSISTED so
that quit-cycling couldn't dodge it.  The unit law's fourth instance, and
the warning for it sits twelve lines below the bug.

F2 (RULING, not fixed here) — the numbers behind it are pinned below so
the ruling starts from measurement: a full belly lasts ~5 GAME-DAYS, and
ordinary neglect kills at 3.5, so hunger cannot reach zero in a natural
life.  See CARE_AUDIT_2026_07_25.md §2.
"""
import pytest

from tuipet.pet import DAY_LENGTH, Pet
from tuipet.petbase import STARVE_DEATH_MIN


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.world_seconds = 8 * 60.0
    p.evo_blocked = True                  # isolate the body from the charts
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# ---- F1: the starvation clock ------------------------------------------

def test_the_starvation_clock_is_counted_in_the_bodys_own_minutes():
    """12 GAME-hours, the number its comment always claimed.  The old
    `12 * 3600` was 30 game-days: unreachable."""
    assert STARVE_DEATH_MIN == 12 * 60
    assert STARVE_DEATH_MIN < DAY_LENGTH          # inside a single game-day


def test_a_pet_held_at_an_empty_belly_actually_starves():
    p = _pet(hunger=0)
    died_at = None
    for i in range(int(DAY_LENGTH * 2)):
        p.tick(1.0)
        p.hunger = 0                              # hold it starving
        if p.dead:
            died_at = i
            break
    assert died_at is not None, "the starvation death still cannot fire"
    assert p.death_cause == "starvation"
    assert abs(died_at - STARVE_DEATH_MIN) <= 60  # ~12 game-hours


def test_a_belly_that_is_fed_resets_the_clock():
    p = _pet(hunger=0)
    for _ in range(300):
        p.tick(1.0)
        p.hunger = 0
    assert p._starve_t > 0
    p.hunger = 3                                  # a meal
    p.tick(1.0)
    assert p._starve_t == 0.0


def test_a_sleeping_pet_does_not_starve_in_its_sleep():
    """Awake-only, like the hunger call itself."""
    p = _pet(hunger=0)
    p.world_seconds = 23 * 60.0
    p._fall_asleep()
    before = getattr(p, "_starve_t", 0.0)
    for _ in range(200):
        p.tick(1.0)
        p.hunger = 0
        if not p.asleep:
            break
    assert getattr(p, "_starve_t", 0.0) == before


# ---- F2: the measurement the ruling needs ------------------------------

def test_a_full_belly_is_one_game_day():
    """RULED AND RETUNED (Joel 2026-07-25: "retune the hunger, do it").
    Was 225 game-min a lapse -- a heart every 1.2 game-days, a full belly
    every FIVE -- which is why hunger could never reach zero before
    something else killed the pet.  Now tied to the day itself: 4 hearts x
    8 lapses == DAY_MINUTES, so a heart is ~6 real minutes and a belly
    lasts one game-day, the device's own rhythm."""
    p = _pet()
    lapse = p._hunger_interval
    full_belly = 32 * lapse                       # 4 hearts x 8 lapses
    assert lapse == pytest.approx(45, abs=1)
    assert full_belly / DAY_LENGTH == pytest.approx(1.0, abs=0.05)


def test_a_pet_nobody_feeds_now_starves_as_it_should():
    """SUPERSEDED-IN-PLACE.  This pin used to assert the BROKEN world: that
    neglect killed by the mistake ladder while hearts remained, because the
    belly needed five game-days and the ladder only three and a half.  The
    retune inverted it, which is exactly what the pin existed to catch.
    Measured now: the belly empties at ~1.4 game-days and starvation takes
    the pet at ~1.9."""
    p = _pet()
    emptied_at = None
    for i in range(int(DAY_LENGTH * 8)):
        p.tick(1.0)
        if p.hunger == 0 and emptied_at is None:
            emptied_at = i / DAY_LENGTH
        if p.dead:
            break
    assert p.dead and p.death_cause == "starvation"
    assert emptied_at is not None and emptied_at < 2.0
    assert p.care_mistakes < 20, "the ladder should NOT be what got there first"


def test_the_attentive_player_is_not_punished_by_the_faster_clock():
    """The other half of the ruling: feeding becomes a rhythm (~3 meals a
    game-day), not a treadmill -- and a tended pet never sees an empty
    belly at all."""
    p = _pet()
    feeds = drills = 0
    for _ in range(int(DAY_LENGTH * 4)):
        p.tick(1.0)
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
            feeds += 1
        if p.strength <= 1 and not p.asleep and not p.can_train():
            # effort decays too (~2 game-days a heart) and its call books a
            # slip like hunger's -- an attentive player drills, so does this
            p.train_result(True)
            drills += 1
        if p.poop:
            p.clean()
        if p.sick:
            p.feed_pill()
        if p.discipline_call:
            p.scold()          # an ignored tantrum is a slip too (discipline B)
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
        assert p.hunger > 0 or p.asleep, "a tended pet went hungry"
    assert not p.dead and p.care_mistakes == 0
    assert 6 <= feeds <= 24, f"{feeds} meals in 4 game-days is not a rhythm"


# ---- the care loop's own invariants ------------------------------------

def test_an_attentive_player_keeps_a_spotless_pet():
    p = _pet()
    for _ in range(int(DAY_LENGTH * 2)):
        p.tick(1.0)
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
        if p.poop:
            p.clean()
        if p.sick:
            p.feed_pill()
        if p.injured:
            p.heal_bandage()
        if p.discipline_call:
            p.scold()          # an ignored tantrum is a slip too (discipline B)
            #                    -- and since 0.5.319 the mischief call runs at
            #                    canon's cadence, so "attentive" has to mean it
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
    assert not p.dead and p.care_mistakes == 0


@pytest.mark.parametrize("days", [1, 3])
def test_the_meters_never_leave_their_rails(days):
    p = _pet()
    for _ in range(int(DAY_LENGTH * days)):
        p.tick(1.0)
        assert 0 <= p.hunger <= 4
        assert 0 <= p.strength <= 4
        assert p.energy <= p.max_energy
        assert p.weight >= 1
        assert p.care_mistakes >= 0
        assert len(p.poop_sizes) == p.poop
        if p.dead:
            break


def test_every_care_mistake_has_exactly_one_source(monkeypatch):
    """The four doors that book a slip, each fired in isolation.

    Rolls are pinned (the house pattern): the body has RANDOM callers too
    -- a sickness roll, a discipline tantrum -- and either can book a
    second slip mid-wait.  That only ever showed in SUITE ORDER, where the
    RNG arrives in a different state, which is exactly why it is patched
    rather than seeded."""
    import tuipet.petbody as pb
    monkeypatch.setattr(pb.random, "random", lambda: 0.99)
    # an ignored hunger call.  ISOLATED: the body has other callers (the
    # effort gauge, a discipline tantrum), and with the retuned clock two
    # can mature in the same tick -- so quiet them and let hunger be the
    # only thing left to book a slip.
    p = _pet(hunger=0)
    p.auto_clean_until = p.world_seconds + 1e9   # no filth call: 4 piles/day now
    for _ in range(int(DAY_LENGTH)):
        p.strength = 4                        # no effort call
        p.discipline_call = False             # no tantrum
        p.tick(1.0)
        p.hunger = 0
        if p.care_mistakes:
            break
    assert p.care_mistakes == 1
    # filth left standing
    q = _pet(poop=4, poop_sizes=[1, 1, 1, 1])
    for _ in range(int(DAY_LENGTH)):
        q.tick(1.0)
        if q.care_mistakes:
            break
    assert q.care_mistakes >= 1
    # stuffing a full belly
    r = _pet(hunger=4)
    before = r.care_mistakes
    r.feed_meat()
    assert r.care_mistakes == before + 1


def test_the_death_ladder_holds_at_both_ends():
    p = _pet(care_mistakes=19)
    p.tick(1.0)
    assert not p.dead
    p.care_mistakes = 20
    p.tick(1.0)
    assert p.dead and p.death_cause == "neglect"
    q = _pet(stage="Ultimate", care_mistakes=5)
    q.stage_seconds = q.LATE_STAGE_WINDOW + 1
    q.tick(1.0)
    assert q.dead and q.death_cause == "frailty"


# ---- the sibling clocks, ruled 2026-07-25 ("retune the poop and effort
# clocks too") ------------------------------------------------------------

def test_all_three_body_clocks_are_tied_to_the_day():
    """Hunger, filth and effort now share one scale — the day itself — so
    none of them can drift out of it the way the belly had.  Roughly four
    meals, four piles and three drills a game-day."""
    p = _pet()
    assert 32 * p._hunger_interval == pytest.approx(DAY_LENGTH, rel=0.05)
    assert DAY_LENGTH / p._poop_interval == pytest.approx(4, abs=0.5)
    assert DAY_LENGTH / p._strength_interval == pytest.approx(3, abs=0.5)


def test_a_cared_for_pet_never_wastes_below_its_base_weight():
    """THE WEIGHT FLOOR LAW'S LAST SINK.  Pooping shed weight with no floor;
    invisible at a pile every 1.9 game-days, ruinous at four a day — at
    base 40 that is -16g of pooping against +3g of meals, so even a pet fed
    on the dot wasted to the hard clamp and wore the maximum condition
    penalty for life."""
    p = _pet()
    base = p._base_weight()
    lowest = base
    for _ in range(int(DAY_LENGTH * 4)):
        p.tick(1.0)
        lowest = min(lowest, p.weight)
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
        if p.poop:
            p.clean()
        if p.strength <= 1 and not p.asleep and not p.can_train():
            p.train_result(True)
        if p.sick:
            p.feed_pill()
        if p.discipline_call:
            p.scold()
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
    assert lowest >= base, f"a tended pet wasted to {lowest} from base {base}"


def test_starvation_alone_may_still_waste_a_pet_below_base():
    """The one deliberate exception: a body with nothing to burn."""
    p = _pet(hunger=0)
    base = p._base_weight()
    for _ in range(600):
        p.tick(1.0)
        p.hunger = 0
        if p.dead:
            break
    assert p.weight < base


@pytest.mark.parametrize("skip,should_live", [(0.0, True), (0.3, True),
                                              (0.6, True), (0.9, True),
                                              (1.0, False)])
def test_the_difficulty_curve_forgives_an_imperfect_player(skip, should_live):
    """The shape the retunes have to keep: someone who is PRESENT but
    sloppy keeps a healthy pet; only total abandonment kills.  (Measured at
    the retune: 90% of chores missed still survives six game-days with no
    care mistakes; never touching it at all dies of sickness in under a
    game-day.)"""
    import random
    random.seed(3)
    p = _pet()
    for _ in range(int(DAY_LENGTH * 6)):
        p.tick(1.0)
        if random.random() < skip:
            continue                       # the chore was missed
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
        if p.poop:
            p.clean()
        if p.strength <= 1 and not p.asleep and not p.can_train():
            p.train_result(True)
        if p.sick:
            p.feed_pill()
        if p.discipline_call:
            p.scold()
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
        if p.dead:
            break
    assert (not p.dead) == should_live
