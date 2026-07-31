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


def test_filth_never_books_a_care_mistake():
    """Bug report 2026-07-31 (Joel, v0.5.329): "mon is getting a care mistake
    after 4 poops, not 1... correct?"  NO -- and not after 4 either.  The
    LINES_SPEC §5 / Pen20 ruling is that mistakes are unanswered CALL LIGHTS
    only; filth keeps its teeth through the sickness roll and the mood drain,
    and past the grace it opens a SCOLD WINDOW (`_open_scold` sets
    scold_window and deliberately does NOT raise discipline_call, so the
    ignored-call penalty cannot reach it).  Pinned: days pegged at poop 4,
    with every other call answered, book ZERO."""
    import os
    import sys
    import tempfile
    os.environ.setdefault("TUIPET_SAVE_DIR", tempfile.mkdtemp())
    sys.path.insert(0, "src")
    from tuipet.pet import Pet
    p = Pet(num=399, name="Omni", stage="Mega", attribute="Vaccine",
            obedience=500)
    p.world_seconds = 10 * 60.0
    p.sleep_limit = 9e9                       # never sleeps -> no lights neglect
    opened = 0
    for _ in range(6000):                     # ~4.2 game-days
        p.hunger, p.strength = 4, 4           # the hunger + effort calls: ANSWERED
        p.discipline_call = False             # the random tantrum: never open
        p.poop = max(p.poop, 4)               # held filthy, past FILTH_LIMIT = 3
        before = p.scold_window
        p.tick(1.0)
        if p.scold_window > before:
            opened += 1
    assert opened > 0, "the mess must still make it ACT UP"
    assert p.care_mistakes == 0, (
        f"filth booked {p.care_mistakes} care mistakes -- it must book none")


def test_every_care_mistake_names_itself():
    """The real defect behind that report: a care mistake was SILENT.  The
    counter moved on the card, the mood took its sting, and nothing said WHICH
    call was missed -- on a Mega, where the fifth slip turns lethal.  Every
    source stamps a reason, and each fits the 40-cell HUD line."""
    import inspect
    import os
    import re
    import sys
    import tempfile
    os.environ.setdefault("TUIPET_SAVE_DIR", tempfile.mkdtemp())
    sys.path.insert(0, "src")
    from rich.cells import cell_len
    from tuipet import petbody, petcare
    from tuipet.pet import Pet
    src = inspect.getsource(petbody) + inspect.getsource(petcare)
    calls = re.findall(r"_inc_mistake\((.*?)\)", src)
    assert len(calls) >= 5, calls
    for arg in calls:
        if arg.startswith("self"):            # the definition's own signature
            continue
        assert arg.startswith('"') and len(arg) > 2, f"unnamed mistake: {arg!r}"
        why = arg.strip('"')
        line = f"✗ Care mistake — {why}"
        assert cell_len(line) <= 40, f"{cell_len(line)} cells: {line!r}"
    # ...and the stamp actually lands on the pet
    p = Pet(num=399, name="Omni", stage="Mega", attribute="Vaccine")
    p.world_seconds = 600.0
    p._inc_mistake("left hungry too long")
    assert p.mistake_reason == "left hungry too long"
    assert p.care_mistakes == 1


def test_the_first_slip_of_a_session_still_flashes():
    """The latch bug the smoke launch caught and no test would have: reading
    the edge as `getattr(self, "_cm_seen", cm)` seeds the latch on the very
    tick that books the slip, so the FIRST care mistake after launch was
    swallowed.  The edge is captured BEFORE pet.tick() now."""
    import inspect
    import re
    from tuipet import app as app_mod
    src = inspect.getsource(app_mod.TuiPetApp.on_tick)
    assert "cm0 = self.pet.care_mistakes" in src
    # ...and it is read before the tick that can move it
    assert src.index("cm0 = self.pet.care_mistakes") < src.index("self.pet.tick(1.0)")
    assert src.index("self.pet.tick(1.0)") < src.index("if p.care_mistakes > cm0")
    assert not re.search(r"_cm_seen\s*=", src)      # no lazy latch, ever again
