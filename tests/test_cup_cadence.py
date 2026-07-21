"""The real-calendar cadence layer (Joel 2026-07-17: "seasonal, daily,
weekly, holiday, etc").  Seasons pool the daily board, each real date fields
one any-hour FEATURED cup (weekends draw it from the top tier), and festival
days open every un-run slot."""
import datetime

import pytest

from tuipet import tournament
from tuipet.pet import Pet


WED = datetime.date(2026, 7, 15)          # a Summer weekday
SAT = datetime.date(2026, 7, 18)          # a Summer weekend
FEB = datetime.date(2026, 2, 4)           # a Winter weekday
ODAIBA = datetime.date(2026, 8, 1)        # the festival (a Saturday)


@pytest.fixture
def on_date(monkeypatch):
    def set_to(d):
        monkeypatch.setattr(tournament, "_today", lambda: d)
    return set_to


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 100000
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_real_calendar_reads_right(on_date):
    on_date(WED)
    assert tournament.real_season() == "Summer"
    assert not tournament.is_weekend() and tournament.holiday() is None
    on_date(SAT)
    assert tournament.is_weekend()
    on_date(FEB)
    assert tournament.real_season() == "Winter"
    on_date(ODAIBA)
    assert tournament.holiday() == "Odaiba Memorial Day"


def test_the_daily_board_is_the_seasons_pool(on_date):
    on_date(WED)
    p = _pet()
    for tid in tournament.schedule(p):
        if tid >= 0:
            assert tournament.trophy_by_id(tid)["season"] == "Summer"
    on_date(FEB)
    p2 = _pet()
    for tid in tournament.schedule(p2):
        if tid >= 0:
            assert tournament.trophy_by_id(tid)["season"] == "Winter"


def test_a_season_flip_rerolls_mid_gameday(on_date):
    on_date(WED)
    p = _pet()
    first = list(tournament.schedule(p))
    on_date(FEB)                                     # real date moved on
    second = list(tournament.schedule(p))
    assert {tournament.trophy_by_id(t)["season"] for t in second if t >= 0} == {"Winter"}
    assert first != second


def test_featured_is_deterministic_daily_and_seasonal(on_date):
    on_date(WED)
    p = _pet()
    a, b = tournament.featured_now(p), tournament.featured_now(p)
    assert a is not None and a["id"] == b["id"]      # one cup per date
    assert a["season"] == "Summer"
    on_date(FEB)
    c = tournament.featured_now(p)
    assert c["season"] == "Winter"


# (test_weekend_featured_draws_from_the_top_tier superseded by the cup
# ruling 2026-07-18: the headliner draws from the PET's bracket now --
# see test_weekend_featured_is_winnable_by_the_pet)


def test_featured_runs_once_per_real_day(on_date):
    on_date(WED)
    p = _pet()
    t = tournament.featured_now(p)
    assert tournament.eligibility_featured(p, t) is None
    tournament.Tournament(p, t, featured=True)       # entry spends the day slot
    assert p.featured_day == WED.toordinal()
    assert "featured" in tournament.eligibility_featured(p, t)
    # ...and it never burned an HOURLY slot
    assert not (p.fought_hours or [])
    on_date(datetime.date(2026, 7, 16))              # a new real day
    assert tournament.eligibility_featured(p, tournament.featured_now(p)) is None


def test_festival_opens_every_slot_once(on_date):
    on_date(ODAIBA)
    p = _pet()
    sched = tournament.schedule(p)
    hour = tournament._hour(p)
    slot = next(i for i, tid in enumerate(sched)
                if tid >= 0 and i != hour
                and tournament._eligibility_rest(p, tournament.trophy_by_id(tid)) is None)
    tr = tournament.trophy_by_id(sched[slot])
    assert tournament.eligibility_at(p, tr, slot) is None       # festival: open
    tournament.Tournament(p, tr, slot=slot)
    assert slot in p.fought_hours
    assert "run" in tournament.eligibility_at(p, tr, slot)      # once, ever


def test_ordinary_day_still_locks_to_the_hour(on_date):
    on_date(WED)
    p = _pet()
    sched = tournament.schedule(p)
    hour = tournament._hour(p)
    other = next(i for i, tid in enumerate(sched) if tid >= 0 and i != hour)
    tr = tournament.trophy_by_id(sched[other])
    err = tournament.eligibility_at(p, tr, other)
    assert err and "closed" in err


def test_weekend_featured_is_winnable_by_the_pet(monkeypatch):
    """Cup ruling 2026-07-18: the weekend headliner draws from the PET's own
    bracket or the open tier -- never a bracket the pet can only lose."""
    import datetime as dt
    from tuipet import tournament
    from tuipet.pet import Pet
    sat = dt.date(2026, 7, 18)                    # a real Saturday
    champ = Pet(num=100, stage="Champion", attribute="Vaccine")
    champ.world_seconds = 600.0
    t = tournament.featured_now(champ, today=sat)
    assert t is not None
    assert not t["age_limit"] or t["age_limit"] == "Champion"
    mega = Pet(num=200, stage="Mega", attribute="Vaccine")
    mega.world_seconds = 600.0
    t2 = tournament.featured_now(mega, today=sat)
    assert t2 is not None and not t2["age_limit"]  # a Mega gets the open field


def test_the_grand_chain_names_the_missing_season(monkeypatch):
    """Cup ruling 2026-07-18: a prelim wall from ANOTHER real season says so
    -- the year-long arc reads as a journey, not a mystery wall."""
    from tuipet import tournament
    from tuipet.pet import Pet
    monkeypatch.setattr(tournament, "real_season", lambda today=None: "Winter")
    p = Pet(num=100, stage="Mega", attribute="Vaccine", bits=99999)
    p.world_seconds = 600.0
    grand = tournament.trophy_by_id(248)           # Winter grand: prelim 170 (Fall)
    msg = tournament._eligibility_rest(p, grand)
    assert msg and "first" in msg and "Fall cup" in msg
