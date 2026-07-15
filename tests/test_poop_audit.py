"""Poop/filth audit vs the decompile (2026-07-15) — VERDICT: MATCHES.

The sweep found no mechanical divergence: poop() (relief mood, the
floor(baseWeight x 0.1) weight shed capped at 4, sizes 3/1/2 by base weight,
the backlog upgrade + extra shed + gauge zero, the carried remainder),
addFilth's full-room upgrade, startPoop's asleep 2x desperate hold, the
toilet-training arc (1 InTraining use, obedience >= 50, Rookie+ auto,
Toilet-before-Potty), checkFilthSick's species-scaled bound, the species
filth mood, obedienceLapse billing the mess, poopWaitMoodCheck, sickPenalty's
racing bowels, and the bad-med/bad-vitamin lurches all match canon (or its
documented tuipet adaptations: the 4-pile cap, the retired poopCall mistake
-- data-dead in canon anyway at limit 7 vs array 6 -- and the acting-up
scold in its place).  These pins lock the audited invariants that had none.

The one live canon constant with no tuipet counterpart is
PostponePoopMoodChange (-1): canon's anim-state machine can BLOCK a poop and
charge mood per blocked minute; tuipet has no blocking state (the pile drops
the tick the gauge crosses), so the postpone path cannot exist.
"""
from tuipet.pet import (OBEDIENCE_FILTH_SCALE, POOP_INC_WEIGHT_FACTOR,
                        POOP_INC_WEIGHT_FACTOR_SMALL, POOP_MAX_PILES, Pet)


def _pet(**kw):
    kw.setdefault("obedience", 500)
    return Pet(num=-1, stage="Rookie", **kw)


def test_pile_size_follows_base_weight(monkeypatch):
    """poop(): baseWeight >= 40 drops a 3, <= 15 a 1, else a 2."""
    p = _pet()
    for bw, size in ((POOP_INC_WEIGHT_FACTOR, 3), (POOP_INC_WEIGHT_FACTOR_SMALL, 1),
                     (POOP_INC_WEIGHT_FACTOR_SMALL + 1, 2)):
        monkeypatch.setattr(Pet, "_base_weight", lambda self, b=bw: b)
        assert p._poop_size() == size


def test_full_room_upgrades_a_smaller_pile():
    """addFilth with every slot taken: a bigger arrival REPLACES the first
    smaller pile (canon's second loop), never a fifth slot."""
    p = _pet()
    p.poop, p.poop_sizes = POOP_MAX_PILES, [1, 2, 1, 2]
    p._add_filth(3)
    assert p.poop == POOP_MAX_PILES
    assert p.poop_sizes == [3, 2, 1, 2]
    p._add_filth(1)                             # nothing smaller than a 1: no change
    assert p.poop_sizes == [3, 2, 1, 2]


def test_filth_mood_bills_per_pile_at_the_cadence():
    """checkFilthMoodDec: species FilthLapseMoodChange x countFilth every
    FilthMoodDecMin."""
    p = _pet(mood=0)
    p.poop, p.poop_sizes = 3, [2, 2, 2]
    fm = p._phys().get("filth_mood", -1)
    p._filth_mood_t = 0.0
    p._filth_sick_t = 0.0
    p._filth_effects(5.0)                       # FILTH_MOOD_DEC_MIN
    assert p.mood == fm * 3


def test_obedience_lapse_bills_the_mess():
    """checkObedienceDec: each lapse dec also charges ObedienceChangeFilthScale
    x piles while the room is dirty."""
    p = _pet(obedience=100)
    p.poop, p.poop_sizes = 2, [2, 2]
    p._obed_lapse_t = 10e9                      # force the lapse this tick
    from tuipet.pet import OBEDIENCE_LAPSE_DEC
    before = p.obedience
    p.tick(0.5)                                 # one awake tick runs the lapse
    expected = before - OBEDIENCE_LAPSE_DEC + OBEDIENCE_FILTH_SCALE * 2
    assert abs(p.obedience - expected) <= 2     # other 0.5s drifts are tiny


def test_filth_acting_up_is_a_scold_not_a_mistake():
    """LINES_SPEC §5 (kept by the audit): no real device counts filth as a
    care mistake -- past the grace the pet ACTS UP (scold window) and the
    call is postponed, mistakes untouched."""
    p = Pet(num=100, stage="Champion", obedience=500)   # _open_scold skips num=-1
    p.poop, p.poop_sizes = 3, [2, 2, 2]
    before = p.care_mistakes
    p._filth_t = 1800.0
    p.tick(0.5)
    assert p.scold_flag and p.care_mistakes == before
    assert p._filth_t < 0                       # postponed, not re-armed


def test_toilet_priority_home_before_portable():
    p = _pet()
    p.toilet_trained, p.obedience, p.stage = 1, 500, "Rookie"
    p.inventory["i:82"] = 1
    p.inventory["i:83"] = 1
    assert p._toilet_for_poop() == "i:82"       # the home Toilet flushes first
    p.inventory["i:82"] = 0
    assert p._toilet_for_poop() == "i:83"
    p.inventory["i:83"] = 0
    assert p._toilet_for_poop() is None         # unstocked: the floor it is
