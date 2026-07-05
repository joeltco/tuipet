"""Tournament vs DVPet Tournament.java: the hourly schedule, isEligible gates,
the 8-entrant dex bracket, and the calcBits purse (sum over the field, with
partial payouts for a semi/final elimination).

Eligibility tests monkeypatch data.load_tournies() with synthetic cups to
isolate the gating logic from whatever ships in the CSV.  Season is controlled
via world_seconds (day 0 = Spring, day 1 = Summer, ...).
"""
import random

from tuipet import data, tournament
from tuipet.tournament import (Tournament, TOURNEY_BITS, TOURNEY_MAX_BITS,
                               TOURNEY_AGES, HOME_LIMIT)
from tuipet.pet import Pet, DAY_LENGTH


def _trophy(id=1, season="Spring", field_req="", attr_req="", age_limit="",
            bit_mod=1.0, item=-1, food_id=-1, food_amt=0, prelim=0,
            reset_season=False, same_day_retry=True,
            enemy_stage="", enemy_attr="", enemy_elem="", enemy_field=""):
    return {"id": id, "sprite": 0, "season": season, "field_req": field_req,
            "attr_req": attr_req, "age_limit": age_limit, "bit_mod": bit_mod,
            "item": item, "food_id": food_id, "food_amt": food_amt, "prelim": prelim,
            "reset_season": reset_season, "same_day_retry": same_day_retry,
            "enemy_stage": enemy_stage, "enemy_attr": enemy_attr,
            "enemy_elem": enemy_elem, "enemy_field": enemy_field}


def _patch(monkeypatch, trophies):
    monkeypatch.setattr(data, "load_tournies", lambda: trophies)


def _pet(stage="Rookie", season_day=0, **kw):
    p = Pet(num=-1, stage=stage, world_seconds=season_day * DAY_LENGTH, **kw)
    p.age_seconds = 1 * DAY_LENGTH             # a 1-day-old: inside every age tier
    return p


# ---- the schedule -----------------------------------------------------------

def test_schedule_is_24_hourly_slots_no_dupes():
    p = _pet("Rookie")
    sched = tournament.schedule(p)
    assert len(sched) == HOME_LIMIT == 24
    real = [t for t in sched if t >= 0]
    assert len(real) == len(set(real))          # picks remove from the bucket
    assert all(tournament.trophy_by_id(t)["season"] == p.season for t in real)


def test_schedule_rerolls_each_game_day():
    p = _pet("Rookie")
    s1 = list(tournament.schedule(p))
    p.fought_today = [s1[0]]
    p.world_seconds += DAY_LENGTH               # dailyChange
    s2 = tournament.schedule(p)
    assert p.fought_today == []                 # foughtTrophiesToday cleared
    assert len(s2) == 24


def test_only_the_current_hour_is_open():
    p = _pet("Rookie")
    p.world_seconds = 5 * (DAY_LENGTH / 24)     # 05:00
    tr = tournament.open_now(p)
    assert tr is not None
    assert tr["id"] == tournament.schedule(p)[5]


# ---- isEligible -------------------------------------------------------------

def test_too_young_and_asleep_gates(monkeypatch):
    _patch(monkeypatch, [_trophy()])
    for st in ("Egg", "Fresh", "InTraining"):
        assert "young" in tournament.can_enter(Pet(num=-1, stage=st)).lower()
    p = _pet("Rookie")
    p.asleep = True
    assert "asleep" in tournament.can_enter(p)


def test_field_and_attribute_restrictions():
    p = _pet("Rookie", attribute="Vaccine")
    p.field = "Nature Spirits"
    assert tournament.eligibility(p, _trophy(field_req="Metal Empire"))
    assert tournament.eligibility(p, _trophy(attr_req="Virus"))
    assert tournament.eligibility(p, _trophy(field_req="Nature Spirits")) is None
    assert tournament.eligibility(p, _trophy(attr_req="Vaccine")) is None


def test_tier_gate_blocks_the_overgrown():
    # STAGE is the tier truth (2026-07-04: the pacing rebuild broke age-days --
    # a compressed-clock Champion pub-stomped Rookie cups as a "1.4-day-old")
    rook = _pet("Rookie")
    rook.age_seconds = (TOURNEY_AGES["Rookie"] + 1) * DAY_LENGTH   # age is irrelevant now
    assert tournament.eligibility(rook, _trophy(age_limit="Rookie")) is None
    champ = _pet("Champion")
    assert "old" in tournament.eligibility(champ, _trophy(age_limit="Rookie")).lower()
    assert tournament.eligibility(champ, _trophy(age_limit="Champion")) is None
    assert tournament.eligibility(champ, _trophy(age_limit="Ultimate")) is None


def test_fought_today_blocks_unless_same_day_retry():
    p = _pet("Rookie")
    p.fought_today = [5]
    assert tournament.eligibility(p, _trophy(id=5, same_day_retry=False))
    assert tournament.eligibility(p, _trophy(id=5, same_day_retry=True)) is None


def test_prelim_chain(monkeypatch):
    q = _trophy(id=3)
    _patch(monkeypatch, [q, _trophy(id=4, prelim=3)])
    p = _pet("Rookie")
    assert "first" in tournament.eligibility(p, _trophy(id=4, prelim=3))
    p.trophies_won = {3: p.season}              # qualifier beaten
    assert tournament.eligibility(p, _trophy(id=4, prelim=3)) is None


def test_prelim_qualification_never_expires(monkeypatch):
    """seasonBeat is set once and never reset -- every cup in tournies.csv
    has ResetWonOnSeasonChange=FALSE.  The grand chain crosses seasons
    (Spring 14 -> Summer 92 -> Fall 170 -> Winter 248), so a beaten-THIS-
    season check would lock those qualifiers forever (audit 2026-07)."""
    _patch(monkeypatch, [_trophy(id=3), _trophy(id=4, prelim=3)])
    p = _pet("Rookie")
    for past in ("Spring", "Summer", "Fall", "Winter"):
        p.trophies_won = {3: past}              # beaten in ANY season, ever
        assert tournament.eligibility(p, _trophy(id=4, prelim=3)) is None


def test_cross_season_grand_chain_is_reachable():
    """The real data: cups 92/170/248 must accept a prelim beaten in the
    prior season (their prelims live in a different season by design)."""
    from tuipet import data
    by = {t["id"]: t for t in data.load_tournies()}
    for qid, pid in ((92, 14), (170, 92), (248, 170)):
        assert by[qid]["season"] != by[pid]["season"]   # the data really crosses
        p = _pet("Rookie")
        p.field = by[qid].get("field_req") or p.field
        p.attribute = by[qid].get("attr_req") or p.attribute
        p.trophies_won = {pid: by[pid]["season"]}
        r = tournament.eligibility(p, by[qid])
        assert r is None or "first" not in r            # never blocked on the prelim


# ---- the bracket ------------------------------------------------------------

def test_bracket_is_player_plus_seven_dex_entrants():
    random.seed(4)
    p = _pet("Rookie")
    tm = Tournament(p, _trophy())
    assert len(tm.bracket) == 8 and tm.bracket.count("YOU") == 1
    for e in tm.entrants:
        assert e["stage"] == "Rookie"           # stage_by_age(1d) = Rookie tier
        assert e["bits"] == (0, 0)              # the cup pays via calcBits
        total = e["vaccine"] + e["data_power"] + e["virus"]
        assert 50 <= total <= 150               # TourneyRandomRookiePower band


def test_purse_is_the_sum_over_the_field():
    random.seed(4)
    p = _pet("Rookie")
    tm = Tournament(p, _trophy(bit_mod=1.0))
    assert tm._calc_bits() == 7 * TOURNEY_BITS["Rookie"]    # 875, NOT capped at 225
    for _ in range(3):
        tm.record(True)
    assert tm.over and tm.champion and tm.reward_bits == 875
    assert p.trophies == 1


def test_partial_payouts_on_elimination():
    random.seed(4)
    p = _pet("Rookie")
    purse = 7 * TOURNEY_BITS["Rookie"]
    tm = Tournament(p, _trophy())
    tm.record(False)                            # out in the quarterfinal
    assert tm.over and tm.reward_bits == 0
    tm2 = Tournament(p, _trophy())
    tm2.record(True); tm2.record(False)         # out in the semi
    assert tm2.reward_bits == purse // 3
    tm3 = Tournament(p, _trophy())
    tm3.record(True); tm3.record(True); tm3.record(False)   # out in the final
    assert tm3.reward_bits == purse // 2


def test_mega_entrants_pay_max_bits_past_mega_age():
    random.seed(4)
    p = _pet("Mega")
    p.age_seconds = (TOURNEY_AGES["Mega"] + 1) * DAY_LENGTH
    tm = Tournament(p, _trophy(enemy_stage="Mega"))
    assert tm._calc_bits() == 7 * TOURNEY_MAX_BITS


def test_npc_rounds_shrink_the_bracket():
    random.seed(4)
    p = _pet("Rookie")
    tm = Tournament(p, _trophy())
    tm.record(True)
    assert len(tm.bracket) == 4 and "YOU" in tm.bracket
    tm.record(True)
    assert len(tm.bracket) == 2 and "YOU" in tm.bracket


def test_champion_feeds_egg_unlock_progress():
    from tuipet import persistence
    random.seed(4)
    p = _pet("Rookie")
    tm = Tournament(p, _trophy(id=7))
    for _ in range(3):
        tm.record(True)
    assert p.trophies_won.get(7) == p.season
    assert 7 in persistence.get_progress()["tourneys"]


# ---- the tournament alarm (CurrentTime.setSeconds / onTourneyAlarm) ----------

def test_alarm_rings_at_the_cup_hour():
    p = _pet("Rookie")
    p.world_seconds = 8.9 * (DAY_LENGTH / 24)   # just before 09:00
    sched = tournament.schedule(p)
    p.tourney_alarm = sched[9]                  # alarm the 09:00 cup
    p.tick(0.2 * (DAY_LENGTH / 24))             # cross the hour line
    assert p.tourney_alert is True
    assert p.tourney_alarm == -1                # setTourneyAlarm(-1) on ring


def test_alarm_only_rings_on_its_own_hour():
    p = _pet("Rookie")
    p.world_seconds = 3.9 * (DAY_LENGTH / 24)
    sched = tournament.schedule(p)
    p.tourney_alarm = sched[9]
    p.tick(0.2 * (DAY_LENGTH / 24))             # 04:00, not the alarm hour
    assert p.tourney_alert is False and p.tourney_alarm == sched[9]


def test_ring_expires_next_hour_and_daily_reset_clears():
    p = _pet("Rookie")
    tournament.schedule(p)
    p.tourney_alert = True
    p.world_seconds = 9.99 * (DAY_LENGTH / 24)
    p.tick(0.02 * (DAY_LENGTH / 24))            # hour rolls -> stale ring clears
    assert p.tourney_alert is False
    p.tourney_alarm = 42
    p.world_seconds += DAY_LENGTH               # dailyChange
    tournament.schedule(p)
    assert p.tourney_alarm == -1


def test_bracket_tree_records_every_round():
    random.seed(4)
    p = _pet("Rookie")
    tm = Tournament(p, _trophy())
    assert [len(r) for r in tm.tree] == [8]
    tm.record(True)
    assert [len(r) for r in tm.tree] == [8, 4]
    tm.record(True)
    assert [len(r) for r in tm.tree] == [8, 4, 2]
    tm.record(True)
    assert [len(r) for r in tm.tree] == [8, 4, 2, 1] and tm.tree[3] == ["YOU"]


def test_bracket_page_renders_and_toggles():
    from tuipet.tournamentscreen import TournamentPanel
    random.seed(4)
    p = _pet("Rookie")
    p.name = "Rookling"
    pan = TournamentPanel(p)
    pan.tourney = Tournament(p, _trophy())
    pan.phase, pan.tree_view = "bracket", True
    txt = pan.text().plain
    assert "BRACKET" in txt and "Rookling" in txt   # the field of eight, you included
    pan.key("space")                                # onward to the faceoff
    assert not pan.tree_view
    pan.key("b")                                    # B recalls the tree any time
    assert pan.tree_view
