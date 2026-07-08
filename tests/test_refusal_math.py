"""Refusal/discipline math audit (2026-07): canon re-verification vs
PhysicalState.checkRefused / getObedienceFactors / refused(Item) /
refuseAttack / checkSurrender / praise / scold / setPraiseWindow /
setScoldWindow + config.csv column 1.

Verified matching: every obedience/refusal/surrender/travel constant
(caps, coefficients, all 20+ surrender factors), the food branch
(fav bypass incl. the hunger<=full edge, sick-only unwell, med/hunger/
personality mods + moodMod), the attribute branch (+20 dispirited-fav
grace), the battle/activity dispositional branches (all canon type=null
call sites pass isBattle=true), refuseAttack (no compliance gate --
matches canon), the surrender two-pass shape and its aftermath/reject
effects, praise/scold branch structure (setScoldWindow(0)'s side effect
clears the flag, so tuipet's one-shots were already right), and the
discipline-call rows.  ForceUse is data-empty in the corpus (noted).

Fixed (canon divergences):
 * getObedienceFactors' `_exercise` divisor is the EFFORT GAUGE
   (strength hearts), not drills-done-today.
 * Items rolled the FOOD refusal formula: no hunger/disliked-food terms
   apply to items, and the BOREDOM term was missing (itemInterest x
   RefuseInterestModCoefficient -15 when the item bores).
 * WeakConsumableCoefficient was unported: a COMPLIANT pet cannot refuse
   an item but takes it grudgingly at 0.1 strength (Inherit + healing
   items exempt, like applyItem's Recover carve-out).
 * Window EXPIRY had no effects: an unpraised good deed now costs mood
   -10 / obedience +3 (disposition-shaded); an unanswered scold window
   means it GOT AWAY WITH IT -- mood +10, obedience -10, refusal
   forgiven."""
import random

from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_obedience_energy_term_divides_by_the_effort_gauge():
    a = _pet(strength=4, exercise_today=0)
    b = _pet(strength=1, exercise_today=9)
    # same energy: the effort gauge divides the term -- strength shrinks it,
    # and drills-done-today (the OLD divisor) must not matter at all
    assert a._obedience_factors()[2] < b._obedience_factors()[2]
    c = _pet(strength=1, exercise_today=0)
    assert abs(b._obedience_factors()[2] - c._obedience_factors()[2]) < 1e-9


def test_items_refuse_by_boredom_not_hunger():
    toy = {"key": "i:0", "interest_change": 1}
    random.seed(1)
    bored = _pet(obedience=60, item_interest=5)
    n_b = sum(bool(bored.check_refused(item=dict(toy))) for _ in range(400))
    random.seed(1)
    keen = _pet(obedience=60, item_interest=0)
    n_k = sum(bool(keen.check_refused(item=dict(toy))) for _ in range(400))
    assert n_b > n_k                           # boredom (-15 x interest) raises refusals
    # hunger never enters the item branch: identical rolls, identical outcomes
    random.seed(2)
    r1 = [_pet(obedience=60, hunger=0).check_refused(item={"key": "i:0"}) for _ in range(200)]
    random.seed(2)
    r2 = [_pet(obedience=60, hunger=4).check_refused(item={"key": "i:0"}) for _ in range(200)]
    assert r1 == r2


def test_compliant_pet_takes_items_weakly():
    """A compliant pet cannot refuse an item but takes it at 0.1 strength --
    the Hedonism toy's +300 mood lands as +30 (end-to-end through use_item)."""
    willing = _pet(compliance=False, mood=0)
    willing.add_item("i:1")
    willing.use_item("i:1")
    grudging = _pet(compliance=True, mood=0)
    grudging.add_item("i:1")
    grudging.use_item("i:1")
    assert grudging.mood < willing.mood
    assert grudging.mood <= willing.mood * 0.2 + 20   # ~0.1x, allowing personality shading
    assert not grudging.compliance                     # check_compliant spent the one-shot


def test_unpraised_window_expires_with_a_sulk():
    p = _pet(mood=0, obedience=100)
    p._open_praise()
    for _ in range(200):                       # ride the mood-lapse cadence past the window
        p.tick(1.0)
        if not p.praise_flag:
            break
    assert not p.praise_flag
    # +3 sulk at the window's expiry, -2 from the obedienceLapse the ride
    # crosses at 120 (obedience audit 2026-07-06)
    assert p.obedience == 101


def test_unanswered_scold_window_means_it_got_away():
    p = _pet(mood=0, obedience=100)
    p._open_scold()
    p.refused = True
    for _ in range(200):
        p.tick(1.0)
        if not p.scold_flag:
            break
    assert not p.scold_flag
    assert p.obedience <= 90                   # ScoldFailObediencePenalty -10
    assert p.refused is False                  # the refusal is forgiven unscolded


def test_correct_discipline_still_one_shots():
    p = _pet()
    p._open_scold()
    msg = p.scold()
    assert "lesson" in msg and p.compliance and not p.scold_flag
    p._open_praise()
    msg = p.praise()
    assert "pride" in msg and not p.praise_flag
