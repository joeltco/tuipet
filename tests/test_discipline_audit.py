"""Discipline/praise-scold audit vs the decompile (2026-07-15).

The system was near-verbatim already: praise()/scold() branch-for-branch
(mis-praise spoils, mis-scold is unfair, the correct answers' disposition
tables, the noncompliant praise dec, scoldDisciplineCall LAST with its
compliance override), the window machine (1-min aging, overflow at
MaxPraiseWindow 3 with the fail penalties, the PraiseWindowMax 2 timing
gates), compliance spending opening the praise window, the tantrum's raise
gate (near-bedtime/obedience suppressions) and both endings (placated -10/+5
vs ignored -25 + missed day on the x60 response-window family), the standing-
call mood drain, and the adventure find's ReturnItem praise.

Two divergences fixed and pinned here:
* canon has NO direct battle-win praise -- wins only open the window through
  SPENT COMPLIANCE; the old unconditional _open_praise let defiant wins farm
  praise windows.
* canon's tourneyEnd opens the praise window for an ELIMINATED pet
  (setIsWon(0) -> setPraise(true)) -- the consolation was missing.
"""
from tuipet.pet import Pet
from tuipet.tournament import Tournament


def _pet(**kw):
    kw.setdefault("obedience", 500)
    return Pet(num=100, stage="Champion", attribute="Vaccine", **kw)


def test_defiant_win_earns_no_praise_window():
    """Canon: a battle win opens the praise window only via spent compliance."""
    p = _pet()
    p.free_style = True
    p.compliance = False
    p.praise_flag = False
    p.record_battle(True, {"bits": (1, 1)}, free_style=True)
    assert not p.praise_flag, "no compliance spent -> no praise window (canon)"


def test_compliant_win_still_opens_praise():
    p = _pet()
    p.compliance = True                    # a fair scold restored it
    p.praise_flag = False
    p.record_battle(True, {"bits": (1, 1)}, free_style=True)
    assert p.praise_flag, "spent compliance opens the window (setCompliance)"


def test_tournament_elimination_opens_the_consolation_window():
    """tourneyEnd: setIsWon(0) -> setPraise(true) -- it fought and lost;
    console it.  The champion path has no such window."""
    p = _pet()
    p.praise_flag = False
    tm = Tournament.__new__(Tournament)
    tm.pet, tm.over, tm.round = p, False, 0
    tm.trophy = {"same_day_retry": True, "id": "_aud", "bit_mod": 1.0}
    tm.entrants = []
    tm.record(False)
    assert p.praise_flag, "an eliminated pet leaves praise-able (canon)"
