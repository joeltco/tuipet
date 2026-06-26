"""Tournament eligibility, reward, and trophy persistence (Workstream A).

Cups (tournies.csv) are gated by season + field/attribute/age + a "won this season"
rule. Winning the 3-round bracket awards capped bits + the trophy and records it
both on the pet (trophies_won) and in cross-gen progress (persistence.tourney_add),
which is what unlocks the tournament eggs — so this closes the loop with the
egg-unlock work.

Eligibility tests monkeypatch data.load_tournies() with synthetic cups to isolate
the gating logic from whatever ships in the CSV. Season is controlled via
world_seconds (day 0 = Spring, day 1 = Summer, ...).

NOTE (latent, not exercised by shipped data): all 325 real trophies set
same_day_retry=True, so the won-status exclusion never fires in practice, and the
`reset_season and ws != season` re-entry branch is dead — `ws` stores the season
*name* at win time, which always equals the current season for a season-locked cup.
If a future data refresh sets same_day_retry=False on a reset_season cup, that
branch would wrongly keep it locked forever. Documented in TUIPET_AUDIT.md.
"""

from tuipet import data, tournament
from tuipet.tournament import Tournament, TOURNEY_BITS, TOURNEY_MAX_BITS
from tuipet.pet import Pet, DAY_LENGTH


def _trophy(id=1, season="Spring", field_req="", attr_req="", age_limit="",
            bit_mod=1.0, item=-1, food_id=-1, food_amt=0,
            reset_season=False, same_day_retry=True,
            enemy_stage="", enemy_attr="", enemy_elem="", enemy_field=""):
    return {"id": id, "sprite": 0, "season": season, "field_req": field_req,
            "attr_req": attr_req, "age_limit": age_limit, "bit_mod": bit_mod,
            "item": item, "food_id": food_id, "food_amt": food_amt,
            "reset_season": reset_season, "same_day_retry": same_day_retry,
            "enemy_stage": enemy_stage, "enemy_attr": enemy_attr,
            "enemy_elem": enemy_elem, "enemy_field": enemy_field}


def _patch(monkeypatch, trophies):
    monkeypatch.setattr(data, "load_tournies", lambda: trophies)


def _pet(stage="Rookie", season_day=0, **kw):
    return Pet(num=-1, stage=stage, world_seconds=season_day * DAY_LENGTH, **kw)


# ---- eligibility -----------------------------------------------------------

def test_too_young_stages_cannot_enter(monkeypatch):
    _patch(monkeypatch, [_trophy()])
    for st in ("Egg", "Fresh", "InTraining"):
        p = _pet(stage=st)
        assert tournament.available(p) == []
        assert "young" in tournament.can_enter(p).lower()


def test_asleep_blocks_entry(monkeypatch):
    _patch(monkeypatch, [_trophy()])
    p = _pet("Rookie")
    p.asleep = True
    assert "asleep" in tournament.can_enter(p)


def test_season_filter(monkeypatch):
    _patch(monkeypatch, [_trophy(id=1, season="Spring"), _trophy(id=2, season="Summer")])
    spring = _pet("Rookie", season_day=0)
    assert spring.season == "Spring"
    ids = [t["id"] for t in tournament.available(spring)]
    assert ids == [1]


def test_field_restriction(monkeypatch):
    _patch(monkeypatch, [_trophy(field_req="Metal Empire")])
    blocked = _pet("Rookie"); blocked.field = "Nature Spirits"
    assert tournament.available(blocked) == []
    ok = _pet("Rookie"); ok.field = "Metal Empire"
    assert len(tournament.available(ok)) == 1


def test_attribute_restriction(monkeypatch):
    _patch(monkeypatch, [_trophy(attr_req="Virus")])
    blocked = _pet("Rookie", attribute="Vaccine")
    assert tournament.available(blocked) == []
    ok = _pet("Rookie", attribute="Virus")
    assert len(tournament.available(ok)) == 1


def test_age_limit(monkeypatch):
    _patch(monkeypatch, [_trophy(age_limit="Champion")])
    assert tournament.available(_pet("Rookie")) == []
    assert len(tournament.available(_pet("Champion"))) == 1


def test_same_day_retry_allows_reentry(monkeypatch):
    _patch(monkeypatch, [_trophy(id=5, same_day_retry=True)])
    p = _pet("Rookie")
    p.trophies_won = {5: "Spring"}            # already won this season
    assert len(tournament.available(p)) == 1, "same_day_retry cups stay enterable"


def test_won_blocks_without_retry(monkeypatch):
    _patch(monkeypatch, [_trophy(id=5, same_day_retry=False, reset_season=False)])
    p = _pet("Rookie")
    p.trophies_won = {5: "Spring"}
    assert tournament.available(p) == [], "a won, no-retry cup is excluded this season"


# ---- reward + persistence --------------------------------------------------

def test_champion_reward_and_trophy_persistence(monkeypatch):
    from tuipet import persistence
    t = _trophy(id=7, bit_mod=1.0)
    p = _pet("Rookie")
    bits0 = p.bits
    tm = Tournament(p, t)
    for _ in range(3):
        assert not tm.over
        tm.record(True)
    assert tm.over and tm.champion
    assert tm.reward_bits == min(TOURNEY_MAX_BITS, int(TOURNEY_BITS["Rookie"] * 1.0))
    assert p.bits == bits0 + tm.reward_bits
    assert p.trophies == 1
    assert p.trophies_won.get(7) == p.season
    assert 7 in persistence.get_progress()["tourneys"], "trophy must feed egg-unlock progress"


def test_bits_are_capped(monkeypatch):
    t = _trophy(id=8, bit_mod=10.0)        # 125 * 10 = 1250, capped to 225
    p = _pet("Rookie")
    tm = Tournament(p, t)
    for _ in range(3):
        tm.record(True)
    assert tm.reward_bits == TOURNEY_MAX_BITS


def test_loss_eliminates(monkeypatch):
    t = _trophy(id=9)
    p = _pet("Rookie")
    tm = Tournament(p, t)
    tm.record(True)               # win round 1
    tm.record(False)              # lose round 2
    assert tm.over and not tm.champion
    assert p.trophies == 0
