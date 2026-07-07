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


def test_cleaning_builds_obedience_by_disposition():
    """Clean audit 2026-07-05: canon clean() adds CleanObedienceInc (1, sunny
    2, sour 0) alongside the mood lift -- tuipet was mood-only.  Cleaning an
    empty room earns nothing (canon gates on isFilth)."""
    from tuipet.pet import CLEAN_OBED_INC, CLEAN_MOOD_INC
    import csv, os
    cfg = {r[0]: r[1] for r in csv.reader(open(os.path.join(
        os.path.dirname(__file__), "..",
        "_extract/game/DVPetTest/jar/Model/config.csv"))) if r}
    assert int(cfg["CleanMoodInc"]) == CLEAN_MOOD_INC
    assert int(cfg["CleanObedienceInc"]) == CLEAN_OBED_INC[0]
    assert int(cfg["CleanObedienceIncHighDisposition"]) == CLEAN_OBED_INC[1]
    assert int(cfg["CleanObedienceIncLowDisposition"]) == CLEAN_OBED_INC[-1]
    # the raw config gains are disposition-shaded (1/2/0), but canon routes
    # them through setObedience whose nudge bends every CHANGE back by
    # -disposition -- so sunny +2 LANDS +1, and sour +0 is no change at all
    # (no change, no nudge).  The shipped flattening, pinned as-is
    # (obedience audit 2026-07-06).
    for dispo, landed in ((0, 1), (1, 1), (-1, 0)):
        p = _pet(disposition=dispo, poop=2, poop_sizes=[2, 2], obedience=10)
        msg = p.clean()
        assert "Cleaned 2" in msg and p.poop == 0
        assert p.obedience == 10 + landed
    p = _pet(obedience=10)                        # nothing to clean
    assert p.clean() == "Nothing to clean."
    assert p.obedience == 10


def test_heal_flows_and_the_double_dose_sours_the_taste():
    """Heal audit 2026-07-05: constants verified vs config (curedMoodBonus 75 /
    curedObedienceBonus 25 / Max lengths 10,12 / hours 60 / BadMedLifeDec 3600
    real-sec = 60 at the /60 clock scale).  New: a DOUBLE dose dings the Med
    food-rank (rankChangeSick +Forced) -- the pet grows to dislike medicine.
    The bandage-free heal is a documented delta (canon gates on OWNING the
    10b never-depleting Bandage; a broke pet must still be treatable)."""
    p = _pet(sick=True, obedience=100)
    p.compliance = True
    p.sick_length = 10.0
    msg = p.heal()                                # dose 1: treatment
    assert p.med_lapse > 0 and p.sick_length < 10.0
    r0 = p.food_ranks["Med"]
    p.sick = True
    p.compliance = True
    msg = p.heal()                                # dose 2: poison
    assert "double dose" in msg.lower()
    assert p.food_ranks["Med"] < r0               # it grows to dislike medicine
    q = _pet(injuries=1, obedience=100)
    q.compliance = True
    q.inj_length = 2.0
    msg = q.heal()                                # the bandage path
    assert q.bandage_lapse > 0
    assert "bandaged" in msg or "patched" in msg
    assert "already bandaged" in q._apply_bandage()   # one wrap at a time


def test_lights_wake_a_nap_unless_the_futon_holds_it():
    """Lights audit 2026-07-05: canon lightSwitch -- lights ON rouses a NAP
    (sick/injured pets bank +1 sleep pressure for the lost doze) UNLESS the
    Futon is active (!isFuton, effect_id 0 -- the exemption auto-care already
    honoured but the switch didn't); deep sleep ignores the switch entirely."""
    p = _pet(asleep=True, nap=True, lights=False, sick=True)
    s0 = p.sleep_lapse
    msg = p.toggle_lights()
    assert p.lights and not p.asleep              # the nap broke
    assert p.sleep_lapse == s0 + 1                # ...and the sick pet pays
    q = _pet(asleep=True, nap=True, lights=False, effect_id=0)   # Futon active
    msg = q.toggle_lights()
    assert q.lights and q.asleep and q.nap        # shielded: still dozing
    assert "futon" in msg.lower()
    r = _pet(asleep=True, nap=False, lights=False)               # DEEP sleep
    r.toggle_lights()
    assert r.asleep                               # the switch never wakes real sleep


# ---- care-mistake audit 2026-07-05 -------------------------------------------

def test_every_mistake_stings_the_mood():
    """incMistake: a Happy pet is knocked DOWN TO 100 (MistakeHappyMoodChange,
    absolute on the -300..300 scale); anyone else loses MistakeMoodDec(50).
    The counters used to tick silently."""
    from tuipet.pet import Pet, MISTAKE_HAPPY_MOOD, MISTAKE_MOOD_DEC
    assert (MISTAKE_HAPPY_MOOD, MISTAKE_MOOD_DEC) == (100, 50)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    p.mood = 280
    cm0, md0 = p.care_mistakes, p.mistake_day
    p._inc_mistake()
    assert p.mood <= 101                      # dropped TO ~100 (disposition nudge +-1)
    assert (p.care_mistakes, p.mistake_day) == (cm0 + 1, md0 + 1)
    p.mood = -10
    p._inc_mistake()
    assert p.mood <= -59                      # the -50 sting


def test_hunger_mistake_obedience_is_glutton_shaded():
    """hungerMistakePenalty: obedience +1 -- canon really REWARDS a plain pet's
    endured hunger -- but a glutton pays -1."""
    from tuipet.pet import Pet
    for glut, want in ((0, 1), (1, -1)):
        q = Pet(num=102, name="D", stage="Champion", attribute="Virus",
                obedience=100, glutton=glut)
        q.world_seconds = 12 * 60.0
        q.hunger = 0
        ob = q.obedience
        q._tick_hunger(600.0)
        assert q.obedience == ob + want


def test_a_fully_lit_night_costs_four_mistakes_and_one_obedience():
    """The whole-night integration: lit mistakes at 60 then every 120 lit
    minutes (~4 over a ver1 midnight-to-seven night); the obedience ding
    exactly once."""
    import random
    from tuipet.pet import Pet
    random.seed(7)
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=100)
    p.line_id = "ver1"
    p.world_seconds = 23 * 60.0 + 30
    cm0, ob0 = p.care_mistakes, p.obedience
    # stop shortly after the 7:00 wake: a longer awake tail crosses the
    # obedienceLapse cadence and would muddy the once-per-night ding pin
    for _ in range(8 * 60):
        p.tick(1.0)
        p.hunger = 4
        p.sick = False
    assert 3 <= p.care_mistakes - cm0 <= 5
    assert p.obedience - ob0 == -1


def test_jogress_and_cup_pokes_disturb_the_sleeper_too():
    """Joel 2026-07-06: feed/train/battle/dna grumble-wake a sleeper but
    jogress/cup answered a flat 'zzz' -- now every player poke runs the same
    disturb mechanic.  (The lobby's REMOTE invites stay pure: _session_gate
    short-circuits asleep before these gates.)"""
    from tuipet import jogress, tournament
    for gate in (jogress.can_jogress, tournament.can_enter):
        p = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
        p.world_seconds = 2 * 60.0
        p.asleep, p.lights = True, False
        p.dp = 4
        d0, m0 = p.disturb, p.mood
        msg = gate(p)
        assert msg and "grumbles" in msg, msg
        assert not p.asleep and p.disturb == d0 + 1 and p.mood < m0, gate


def test_neglect_never_opens_a_scold_window():
    """Canon sets _scold = true at exactly THREE sites -- refusals, travel
    refusal, the discipline tantrum.  The hunger/strength care mistakes cost
    mistakes + obedience, they never make the pet 'act up' (discipline audit
    2026-07-06: the invented windows leaked -10 obedience per miss and fed
    the refusal spiral -- the answer to 'why do digimon misbehave so much')."""
    p = _pet(hunger=0, obedience=50)
    p._hunger_call_t = 599.0
    p._tick_hunger(2.0)                              # the hunger mistake lands
    assert p.care_mistakes >= 1 and not p.scold_flag
    q = _pet(strength=0, obedience=50)
    q._str_call_t = 599.0
    q._tick_body(2.0)                                # the strength mistake lands
    assert q.care_mistakes >= 1 and not q.scold_flag


def test_a_standing_care_call_suppresses_the_tantrum(monkeypatch):
    """checkDisciplineCall gates on checkCall(): while a care light stands
    (hunger/strength empty) the pet is asking, not acting up."""
    import random as _r
    monkeypatch.setattr(_r, "randint", lambda a, b: 0)   # the roll always fires
    p = _pet(obedience=0, hunger=0, strength=2)
    p._check_discipline_call()
    assert not p.discipline_call                     # hungry: the call light rules
    p2 = _pet(obedience=0, hunger=4, strength=0)
    p2._check_discipline_call()
    assert not p2.discipline_call                    # effort-empty likewise
    p3 = _pet(obedience=0, hunger=4, strength=2)
    p3._check_discipline_call()
    assert p3.discipline_call                        # no call standing: it may tantrum


def test_tantrum_personality_mods_read_the_live_gauges(monkeypatch):
    """The +-target mods key on the LIVE hunger/strength gauges vs full-4
    (canon _hunger/_exercise), not drills-done-today; a peckish picky eater
    and a lazy low-effort pet both CALM the roll by 1 (target 15), a fretful
    one heats it to 19.  Probed by fixing the roll just around the base 16."""
    import random as _r

    def fires(roll, **kw):
        monkeypatch.setattr(_r, "randint", lambda a, b: roll)
        base = {"obedience": 0, "hunger": 4, "strength": 4}
        base.update(kw)
        q = _pet(**base)
        q._check_discipline_call()
        return q.discipline_call

    assert fires(15)                                          # base target 16
    assert not fires(16)
    assert fires(17, strength=2, restless=1)                  # +3 -> 19
    assert not fires(15, strength=2, restless=-1)             # -1 -> 15
    assert not fires(15, hunger=2, glutton=-1)                # -1 -> 15
    assert fires(17, hunger=2, glutton=1)                     # +3 -> 19
