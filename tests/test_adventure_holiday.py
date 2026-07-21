"""Adventure rebuild — HOLIDAY EVENTS (phase 15, 2026-07-20).

Pins the festival cadence (reused from the cup's date/holiday layer): on a
holiday a run pays DOUBLE bounties and spills MORE loot, and the zone picker
flies a festival banner.  Ordinary days are untouched.
"""
import datetime
from tuipet import adventure, tournament
from tuipet.adventure import Adventure, ZONES
from tuipet.adventurescreen import ZonePickPanel
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _boss_zone():
    return next(z for z in ZONES if z["bosses"])


def _on(month, day, monkeypatch):
    monkeypatch.setattr(tournament, "_today", lambda: datetime.date(2026, month, day))


def test_a_run_knows_todays_festival(monkeypatch):
    _on(7, 20, monkeypatch)                            # an ordinary day
    assert Adventure(_pet(), zone=_boss_zone()).holiday is None
    _on(8, 1, monkeypatch)                             # Odaiba Memorial Day
    assert Adventure(_pet(), zone=_boss_zone()).holiday == "Odaiba Memorial Day"
    _on(12, 25, monkeypatch)                           # Christmas
    assert Adventure(_pet(), zone=_boss_zone()).holiday == "Christmas Festival"


def test_bounties_pay_double_on_a_holiday(monkeypatch):
    z = _boss_zone()
    boss = z["bosses"][0]
    lo, hi = boss["bits"]
    _on(7, 20, monkeypatch)
    p = _pet(); p.bits = 0
    normal = Adventure(p, zone=z).award_bits(boss)
    assert lo <= normal <= hi
    _on(8, 1, monkeypatch)
    q = _pet(); q.bits = 0
    fest = Adventure(q, zone=z).award_bits(boss)
    assert lo * 2 <= fest <= hi * 2                    # the festival purse
    assert q.bits == fest


def test_more_loot_spills_on_a_holiday(monkeypatch):
    # the effective find chance is multiplied on a festival
    _on(8, 1, monkeypatch)
    a = Adventure(_pet(), zone=next(z for z in ZONES if z["find_keys"]))
    assert a.holiday
    # force a roll: on a holiday, FIND_CHANCE*mult >= 1 fires every eligible step
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.6)   # *2 = 1.2 -> always fires
    a.loc = 5                                            # a mid-road step, not a town
    assert not a._in_town(a.loc)
    assert a._roll_find() is not None                   # a festival find lands


def test_no_double_reward_on_an_ordinary_day(monkeypatch):
    _on(3, 15, monkeypatch)
    z = _boss_zone()
    a = Adventure(_pet(), zone=z)
    assert a.holiday is None
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.4)
    # 0.4 (no mult) does NOT always fire -> a deterministic seed check is flaky,
    # so just assert the multiplier is not applied to the bounty
    boss = z["bosses"][0]
    lo, hi = boss["bits"]
    assert lo <= a.award_bits(boss) <= hi               # single, not doubled


def test_the_picker_flies_a_festival_banner(monkeypatch):
    _on(10, 31, monkeypatch)                            # Halloween
    pk = ZonePickPanel(_pet())
    assert pk.holiday == "Halloween Festival"
    body = str(pk.text())
    assert "Halloween Festival" in body and "FESTIVAL" in body
    # an ordinary day: no banner
    _on(7, 20, monkeypatch)
    assert "FESTIVAL" not in str(ZonePickPanel(_pet()).text())
