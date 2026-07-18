"""Poop/filth canon audit pins (2026-07-06) vs DVPet PhysicalState.

Mostly verified sound from prior arcs (poop bodies/sizes, the toilet chain,
filth mood + its own sick-bound formula, the held-gauge nag, clean).  Found:
addFilth's OVERFLOW rule was missing (a full room upgrades the first pile
smaller than the new mess; ours silently dropped it), and canon's poopCall
is PROVABLY DEAD in the shipped config (the filth array holds 6 piles,
MistakeFilthLimit is 7 -- countFilth can never reach it), so the 50/50
begging-gauge mistake rolls ported last arc keyed on a branch that never
runs; removed.  The pile cap stays Joel's 4 (real-toy match)."""
import random

from tuipet.pet import Pet, POOP_MAX_PILES


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_a_full_room_upgrades_the_first_smaller_pile():
    p = _pet(poop=POOP_MAX_PILES, poop_sizes=[1, 1, 2, 3])
    p._add_filth(3)
    assert p.poop == POOP_MAX_PILES                  # never past the cap
    assert p.poop_sizes == [3, 1, 2, 3]              # the first smaller pile grew

def test_a_full_room_of_bigger_messes_absorbs_a_small_one():
    p = _pet(poop=POOP_MAX_PILES, poop_sizes=[2, 3, 4, 2])
    p._add_filth(1)
    assert p.poop_sizes == [2, 3, 4, 2]              # nothing smaller: it vanishes

def test_below_the_cap_piles_stack_normally():
    p = _pet(poop=1, poop_sizes=[2])
    p._add_filth(3)
    assert p.poop == 2 and p.poop_sizes == [2, 3]

def test_the_dead_poop_call_mistake_branch_is_gone(monkeypatch):
    """poopCall never fires in shipped canon (6-slot array vs a 7 threshold):
    a mistake with an urgent GAUGE but a clean floor rolls NO sickness."""
    monkeypatch.setattr(random, "randrange", lambda n: 0)      # every roll would hit
    p = _pet(poop=0, mood=0)
    p._poop_t = p._poop_interval * 0.95                        # gauge begging
    p._inc_mistake()
    assert not p.sick                                          # no filth, no rolls

def test_the_bad_vitamin_lurch_still_drops_a_pile_through_the_helper():
    p = _pet(poop=0, poop_sizes=[])
    p._start_poop()
    assert p.poop == 1 and len(p.poop_sizes) == 1
