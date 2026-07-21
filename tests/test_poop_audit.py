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
from tuipet.pet import (POOP_INC_WEIGHT_FACTOR,
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


def test_the_self_toilet_is_gone_the_floor_always_takes_it():
    """(The toilet chain left with the staple props: strict-DSprite items,
    2026-07-17.)  Even a bag stuffed with old furniture keys changes nothing:
    the gauge rollover always drops a pile on the floor."""
    p = _pet()
    p.obedience, p.stage = 500, "Rookie"
    p.inventory["i:82"] = 1                     # a stale key, not a fixture
    assert not hasattr(p, "_toilet_for_poop")
    before = p.poop
    p._poop_t = p._poop_interval
    p._tick_body(0.0)
    assert p.poop == before + 1                 # the floor it is


def test_sick_diarrhea_is_compressed_not_machine_gun():
    """SickLapsePenaltyBM rides the x5 count compression (2026-07-15): a full
    max-length illness hurries roughly one-to-two extra poops out of an awake
    pet -- not canon-proportional's nine in five real minutes."""
    from tuipet.pet import (MAX_SICK_LENGTH, SICK_LAPSE_MIN,
                            SICK_LAPSE_PENALTY_BM)
    p = _pet()
    p.sick, p.sick_length = True, float(MAX_SICK_LENGTH * SICK_LAPSE_MIN)
    per_lapse = p._poop_interval * SICK_LAPSE_PENALTY_BM \
        / (p._phys().get("poop_limit", 64) * 5)
    spell_total = per_lapse * MAX_SICK_LENGTH
    assert 1.0 <= spell_total / p._poop_interval <= 2.0, \
        "a max illness should hurry ~1-2 poops, not a stream"
