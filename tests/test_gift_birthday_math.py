"""Gift/birthday math audit (2026-07): canon re-verification vs
PhysicalState.checkGiftCall / checkGift / getGift / setTimeToAge /
getMajorMood / getMajority / checkMoodRecord, Consumable.getCanGift,
ClockTic.giftEnd + config column 1.

THE SECOND FULLY-CLEAN AUDIT: zero divergences.  Verified verbatim --
the gift roll (cap - obedience + (maxMood - mood) x 0.5 + 70, one-in-N),
its gates (57-min cadence; grown, awake, HAPPY -- now the sticky state),
the pool (getCanGift IS a per-consumable GiftChance% roll, then a uniform
pick -- what looked like a boolean column is canon's own randomChance),
giftEnd (home gift cheers; the adventure carried-home find praises),
the birthday (AgeUp 1440; majority mood with getMajority's strict-max
tie -> None -> normal; slips 0/1 gates; bonus +-1 with the zero floor;
lifespan +-21600 real-sec on the /60 game scale; Cupcake 55 / Candy 7 /
Cookie 54; the slate wipe), and the 5-min mood sampling that feeds it.
Noted: canon's gift roll would THROW on a negative chance (a maxed pet);
tuipet's guard yields the same no-gift outcome.  The unhappy time-rank
decay in checkMoodRecord stays with the unported rank system."""
import random

from tuipet.pet import Pet, MOOD_RECORD_MIN, DAY_LENGTH


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_gift_roll_narrows_with_care(monkeypatch):
    # isolate the ROLL: the pool's own per-item GiftChance rolls (canonical)
    # otherwise add empty-pool noise
    monkeypatch.setattr(Pet, "_pick_gift", lambda self: "f:8")
    spoiled = _pet(mood=300, obedience=90)     # chance = 100-90+0+70 = 80
    neglected = _pet(mood=150, obedience=0)    # chance = 100-0+75+70 = 245
    def gifts(p, seed):
        random.seed(seed)
        n = 0
        for _ in range(2000):
            p.gift = ""
            p.gift_t = 10**9                   # force a roll every call
            p._check_gift_call(1.0)
            n += bool(p.gift)
        return n
    s_, n_ = gifts(spoiled, 1), gifts(neglected, 1)
    assert s_ > n_                             # ~1/80 vs ~1/245
    assert 10 <= s_ <= 60 and n_ <= 20


def test_gift_needs_a_genuinely_happy_grown_pet():
    p = _pet(mood=300)
    p.depressed = True                         # the sticky state vetoes Happy
    p.gift_t = 10**9
    p._check_gift_call(1.0)
    assert p.gift == ""
    baby = Pet(num=1, stage="Fresh", attribute="Vaccine", obedience=500)
    baby.world_seconds = 600.0
    baby.mood = 300
    baby.gift_t = 10**9
    baby._check_gift_call(1.0)
    assert baby.gift == ""


def test_good_birthday_needs_happy_majority_and_zero_slips():
    p = _pet()
    p.daily_mood = {"Happy": 10, "Neutral": 2, "Unhappy": 0, "Depressed": 0}
    p.mistake_day = 0
    b0, l0 = p.evol_bonus, p.lifespan
    p._birthday()
    assert p.evol_bonus == b0 + 1 and p.lifespan == l0 + 360.0
    assert p.inventory.get("f:55", 0) == 1                     # the Cupcake
    assert p.mistake_day == 0 and sum(p.daily_mood.values()) == 0   # the slate wipes


def test_one_slip_spoils_the_good_day():
    p = _pet()
    p.daily_mood = {"Happy": 10, "Neutral": 0, "Unhappy": 0, "Depressed": 0}
    p.mistake_day = 1                          # MaxMissedDayForBonusInc = 0
    b0 = p.evol_bonus
    p._birthday()
    assert p.evol_bonus == b0                  # no bonus...
    assert p.inventory.get("f:54", 0) == 1     # ...just the normal Cookie


def test_bad_birthday_and_the_bonus_floor():
    p = _pet(evol_bonus=0)
    p.daily_mood = {"Happy": 0, "Neutral": 1, "Unhappy": 8, "Depressed": 0}
    p.mistake_day = 3
    l0 = p.lifespan
    p._birthday()
    assert p.evol_bonus == 0                   # the floor: never negative
    assert p.lifespan == l0 - 360.0
    assert p.inventory.get("f:7", 0) == 1      # the consolation Candy


def test_a_mood_tie_is_a_normal_birthday():
    p = _pet()
    p.daily_mood = {"Happy": 5, "Neutral": 0, "Unhappy": 5, "Depressed": 0}
    p.mistake_day = 0
    b0 = p.evol_bonus
    p._birthday()
    assert p.evol_bonus == b0                  # getMajority tie -> None -> normal
    assert p.inventory.get("f:54", 0) == 1


def test_mood_samples_every_five_game_minutes():
    random.seed(4)
    p = _pet(mood=200)
    for _ in range(int(MOOD_RECORD_MIN * 60 * 3.5)):
        p.tick(1.0)
    assert sum(p.daily_mood.values()) >= 3     # ~one sample per 5 game-min


def test_gifts_are_found_at_home_only(monkeypatch):
    """checkGiftCall gates on _isHome (play/gift audit 2026-07-06): on the
    road there are no presents -- and the roll resumes at homecoming."""
    monkeypatch.setattr(Pet, "_pick_gift", lambda self: "f:8")
    monkeypatch.setattr(random, "randrange", lambda n: 0)   # the roll always hits
    p = _pet(mood=300, obedience=90)
    p.away = True
    p.gift_t = 10**9
    p._check_gift_call(1.0)
    assert p.gift == ""                        # adventuring: no visitor
    p.away = False
    p.gift_t = 10**9
    p._check_gift_call(1.0)
    assert p.gift == "f:8"                     # home again: the present lands
