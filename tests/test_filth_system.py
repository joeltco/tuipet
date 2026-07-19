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


# ---- the startPoop state-machine block (restored 2026-07-19) ----------------
# Joel's live bug report: "mon is doing a weird pose while walking, and it
# poops during feeding... make sure you audit that sequnce, make sure nothing
# can get glitchy. ie pooping".  Canon DVPet blocks startPoop while the anim
# state machine is busy and bills PostponePoopMoodChange -1; the 07-15 audit
# had dropped the hold "by architecture".  Restored: a busy pet (care anim
# playing, or the app's _fx_busy window) HOLDS the squat -- gauge keeps
# accruing, mood pays -1 once per hold -- and releases when idle.

def _ripe(**kw):
    p = _pet(**kw)
    p._poop_t = p._poop_interval + 1.0     # gauge past the threshold
    return p

def test_a_feeding_pet_holds_the_squat():
    p = _ripe()
    p._set_anim("eat", 1.4)
    p._tick_body(1.0)
    assert p.poop == 0                     # no pile lands mid-meal
    assert p.anim == "eat"                 # the meal was never interrupted

def test_the_fx_window_holds_it_too():
    """The visible fx outlives the anim ttl -- the app marks the window."""
    p = _ripe()
    p._fx_busy = True                      # app.on_tick's per-tick proxy
    p._tick_body(1.0)
    assert p.poop == 0

def test_the_hold_is_one_episode_not_a_drumbeat():
    """PostponePoopMoodChange bills via _set_mood -- a no-op today (the
    mood meter left with BASIC VPET; canon write-sites stay as inert
    citations) -- but the EPISODE latch must still arm exactly once."""
    p = _ripe()
    p._set_anim("eat", 9.0)
    p._tick_body(1.0)
    assert p._poop_held is True            # the hold latched...
    p._tick_body(1.0)
    assert p.poop == 0                     # ...and keeps holding, no pile

def test_release_lands_the_pile_when_idle_again():
    p = _ripe()
    p._set_anim("eat", 1.4)
    p._tick_body(1.0)
    assert p.poop == 0
    p.anim, p._fx_busy = "idle", False     # the action ended
    p._tick_body(1.0)
    assert p.poop == 1                     # the held squat goes
    assert p.anim == "poop"
    p._set_anim("eat", 1.4)                # a NEW hold re-arms the latch
    p._poop_t = p._poop_interval + 1.0
    p._tick_body(1.0)
    assert p._poop_held is True and p.poop == 1   # held again, no second pile

def test_an_idle_pet_still_goes_on_schedule():
    p = _ripe()
    assert p.anim in ("idle", "walk")
    p._tick_body(1.0)
    assert p.poop == 1
