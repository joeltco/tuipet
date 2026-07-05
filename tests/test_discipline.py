"""Praise/scold audit (2026-07-05): every discipline constant pinned to the
shipped config, plus the sleep semantics -- a sleeping pet is DISTURBED, not
served (documented adaptation; canon serves after disturb()), which is SAFE
because the discipline windows FREEZE during sleep (the asleep tick returns
before _tick_mood_discipline), so a misdeed survives the night scoldable."""
import csv
import os

from tuipet import pet as P
from tuipet.pet import Pet

_CFG = os.path.join(os.path.dirname(__file__), "..",
                    "_extract/game/DVPetTest/jar/Model/config.csv")


def test_all_discipline_constants_match_canon():
    cfg = {r[0]: r[1] for r in csv.reader(open(_CFG)) if r}
    pairs = [
        ("PraiseLowDispositionMoodInc", P.PRAISE_LOW_DISP_MOOD_INC),
        ("PraiseHighDispositionMoodInc", P.PRAISE_HIGH_DISP_MOOD_INC),
        ("PraiseNoncompliantObedienceDec", P.PRAISE_NONCOMPLIANT_OBED_DEC),
        ("PraiseScoldMoodInc", P.PRAISE_SCOLD_MOOD_INC),
        ("PraiseScoldEnthusiasmChange", P.PRAISE_SCOLD_ENTH),
        ("PraiseScoldObedienceDec", P.PRAISE_SCOLD_OBED_DEC),
        ("CorrectPraiseObedienceInc", P.CORRECT_PRAISE_OBED[0]),
        ("CorrectPraiseObedienceIncHighDisposition", P.CORRECT_PRAISE_OBED[1]),
        ("CorrectPraiseObedienceIncLowDisposition", P.CORRECT_PRAISE_OBED[-1]),
        ("ScoldObedienceInc", P.SCOLD_OBED_INC),
        ("ScoldHighObedienceMood", P.SCOLD_HIGH_OBED_MOOD),
        ("ScoldLowObedienceMoodDec", P.SCOLD_LOW_OBED_MOOD_DEC),
        ("ScoldHighObedienceMoodDec", P.SCOLD_HIGH_OBED_MOOD_DEC),
        ("ScoldPraiseMoodDec", P.SCOLD_PRAISE_MOOD_DEC),
        ("ScoldPraiseEnthusiasmDec", P.SCOLD_PRAISE_ENTH_DEC),
        ("ScoldPraiseObedienceInc", P.SCOLD_PRAISE_OBED[0]),
        ("ScoldPraiseObedienceIncHighDisposition", P.SCOLD_PRAISE_OBED[1]),
        ("ScoldPraiseObedienceIncLowDisposition", P.SCOLD_PRAISE_OBED[-1]),
        ("CorrectScoldEnthusiasmChange", P.CORRECT_SCOLD_ENTH),
        ("CorrectScoldObedienceInc", P.CORRECT_SCOLD_OBED[0]),
        ("CorrectScoldObedienceIncHighDisposition", P.CORRECT_SCOLD_OBED[1]),
        ("CorrectScoldObedienceIncLowDisposition", P.CORRECT_SCOLD_OBED[-1]),
        ("PraiseWindowMax", P.PRAISE_WINDOW_MAX),
        ("ScoldWindowMax", P.SCOLD_WINDOW_MAX),
    ]
    for name, ours in pairs:
        assert cfg.get(name) is not None, name
        assert float(cfg[name]) == float(ours), (name, cfg[name], ours)


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 12 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_well_timed_scold_corrects_and_mistimed_scold_is_unfair():
    p = _pet(obedience=10)
    p.scold_flag, p.scold_window = True, 0
    o0 = p.obedience
    msg = p.scold()
    assert "lesson" in msg and p.obedience > o0
    assert not p.scold_flag and p.compliance and not p.refused
    q = _pet(obedience=10)
    q.praise_flag = True                        # it did something GOOD
    msg = q.scold()
    assert "unfair" in msg and not q.praise_flag


def test_mispraise_spoils_a_misbehaving_pet():
    p = _pet(obedience=50)
    p.scold_flag = True
    o0 = p.obedience
    msg = p.praise()
    assert "spoiled" in msg
    assert p.obedience < o0 and not p.scold_flag


def test_sleeping_pet_is_disturbed_not_served_and_windows_freeze():
    p = _pet(obedience=10)
    p.scold_flag, p.scold_window = True, 0
    p.asleep, p.anim = True, "sleep"
    o0, d0 = p.obedience, p.disturb
    msg = p.scold()
    assert p.obedience == o0                    # the scold did NOT apply...
    assert p.disturb == d0 + 1 or "zzz" in msg  # ...the sleeper got disturbed
    for _ in range(120):                        # two window-minutes of sleep
        p.tick(1.0)
    assert p.scold_flag and p.scold_window == 0  # the window FROZE overnight


def test_nutrition_is_browsable_and_the_pills_are_reachable():
    """Joel 2026-07-05 ('isnt there a mineral or something, the pill food
    icon... we are missing that'): the nutrition ENGINE was complete (three
    tracks from the Proteins/Vitamins/Minerals food columns; good nutrition =
    faster recovery, fewer fatigues, softer life burn; the Vitamin pills grant
    the injury-protection buff via use_item -> feed_vitamin) but it only ever
    FLASHED BY in the eat readout.  It lives on the digicore CONDITION page now."""
    from tuipet import data
    from tuipet.digicorescreen import build_pages
    p = _pet(nutr_protein=20, nutr_mineral=17, nutr_vitamin=16)
    cond = dict(build_pages(p))["CONDITION"]
    row = dict(cond)["Nutrit."]
    assert row == "P20 M17 V16 ♥"                 # visible, with the good mark
    # the pills are obtainable and land the buff
    pool = {e["key"] for e in data.home_shop_pool()}
    assert {"f:5", "f:16", "f:19"} <= pool        # Vitamin / Vitamin G / Gold Pill
    p.compliance = True
    p.add_item("f:16")
    assert p.vitamin_lapse == 0
    p.use_item("f:16")
    assert p.vitamin_lapse > 0                    # feed_vitamin fired
    # minerals come from FOOD (peppers/bread/veg), pinned via the feed loader
    pep = next(f for f in data.load_foods() if f["key"] == "f:35")
    assert (pep.get("mineral") or 0) >= 10
