"""THE CUP AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown cup audit next."

F1 — THE CUP'S SHOW PAGES OVERFLOWED THE LCD.  Every one of them stacked
a title bar ABOVE a full 12-row arena and up to three caption rows BELOW
it: 16 rows into a 12-row box.  The bottom four were clipped off screen,
so the arena lost its own floor row and the cup lost its NARRATION --
"vs <foe>  your ★N", "<foe> enters!", "<winner> advances", "the trophy is
yours", and the faceoff's "SPACE fight  ESC leave", the only line telling
you how to start the match.  Verified in the live app, not just in a
string: the LCD widget's content region is 12 rows and the panel handed
it 16.

The fix is the family law the raid page got in v0.5.183 and the battle
panel always had: THE LCD IS PURE SCENE.  The words moved to the two
surfaces that were always visible -- the strip narrates, the card carries
the foe.

The rest of the audit found the cup sound, and those measurements are
pinned here too so they stay true.
"""
import random

import pytest

from tuipet import grid, statusbox, tournament as T
from tuipet.pet import Pet
from tuipet.tournamentscreen import TournamentPanel

LCD_ROWS, LCD_COLS = grid.ROWS, grid.COLS      # the box the app gives a panel


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.stage_trainings, p.total_trainings = 900, 9000
    p.battles, p.wins, p.saved_hit_type = 200, 180, "mega"
    p.bits, p.world_seconds = 100_000, 3 * 86400.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


class _Stats:
    def __init__(self):
        self.text = ""
        self.border_subtitle = ""

    def update(self, t):
        self.text = t


class _App:
    def __init__(self, pet, mode):
        self.pet, self.mode, self.stats_w = pet, mode, _Stats()


def _entered(seed=5):
    random.seed(seed)
    p = _pet()
    pan = TournamentPanel(p)
    pan.tourney = T.Tournament(p, T.trophy_by_id(T.schedule(p)[0]))
    return p, pan


def _rows(pan):
    txt = pan.text()
    plain = txt.plain if hasattr(txt, "plain") else str(txt)
    return plain.split("\n")


# ---- F1: every page fits the box ---------------------------------------

CUP_PAGES = {
    "select": lambda pan: setattr(pan, "phase", "select"),
    "tree": lambda pan: setattr(pan, "tree_view", True),
    "faceoff": lambda pan: setattr(pan, "tree_view", False),
    "intro": lambda pan: setattr(pan, "_intro", {"t": 1}),
    "advance": lambda pan: setattr(pan, "_advance", {"t": 1, "nums": [120]}),
    "ceremony": lambda pan: setattr(pan, "_ceremony", {"t": 1}),
}


@pytest.mark.parametrize("page", sorted(CUP_PAGES))
def test_every_cup_page_fits_the_LCD(page):
    _p, pan = _entered()
    pan.tree_view = False
    if page == "advance":
        pan.tourney.results = ["SandYanmamon"]
        pan.tourney.results_nums = [120]
    CUP_PAGES[page](pan)
    rows = _rows(pan)
    assert len(rows) <= LCD_ROWS, (
        f"{page}: {len(rows)} rows into a {LCD_ROWS}-row LCD — "
        f"clipped: {rows[LCD_ROWS:]}")
    assert max(len(r) for r in rows) <= LCD_COLS, f"{page}: too wide"


@pytest.mark.parametrize("page", ["intro", "advance", "ceremony"])
def test_the_show_pages_are_PURE_SCENE(page):
    """The family law (raid page v0.5.183, and the battle panel always):
    a fight screen is scene and nothing else, so the arena's floor is on
    screen and the entrance does not jump a row when the bout opens."""
    _p, pan = _entered()
    pan.tree_view = False
    if page == "advance":
        pan.tourney.results, pan.tourney.results_nums = ["Yanmamon"], [120]
    CUP_PAGES[page](pan)
    assert len(_rows(pan)) == LCD_ROWS


def test_the_narration_that_was_clipped_now_rides_the_strip():
    _p, pan = _entered()
    pan.tree_view = False
    pan._intro = {"t": 1}
    pan.text()                                   # the frame sets the caption
    assert pan._say and pan._say in pan.strip()  # "<foe> enters!"
    pan._intro = None
    pan._advance = {"t": 1, "nums": [120]}
    pan.tourney.results, pan.tourney.results_nums = ["Yanmamon"], [120]
    pan.text()
    assert "advances" in pan.strip()
    pan._advance = None
    pan._ceremony = {"t": 1}
    pan.text()
    assert "trophy" in pan.strip().lower()


def test_the_card_names_the_foe_the_LCD_no_longer_can():
    p, pan = _entered()
    pan.tree_view = False
    app = _App(p, pan)
    statusbox.painter_for(pan)(app)
    opp = pan.tourney.current_opponent()
    assert opp["name"][:12] in app.stats_w.text
    assert "Match" in app.stats_w.text and "★" in app.stats_w.text


# ---- what the audit measured and found SOUND ---------------------------

def test_the_bracket_survives_a_whole_cup():
    """8 entrants, YOU exactly once, three rounds to the title."""
    for seed in range(20):
        random.seed(600 + seed)
        p = _pet()
        t = T.Tournament(p, T.trophy_by_id(T.schedule(p)[seed % 24]))
        assert len(t.bracket) == 8 and t.bracket.count("YOU") == 1
        rounds = 0
        while not t.over and rounds < 8:
            assert isinstance(t.current_opponent(), dict)
            t.record(True)
            rounds += 1
            if not t.over:
                assert t.bracket.count("YOU") == 1
        assert rounds == 3 and t.champion


def test_the_stake_is_charged_and_the_payout_ladder_holds():
    """The bit-sink design: a QF exit eats the stake, a semi pays a third,
    a final half, the title the whole purse."""
    p = _pet()
    trophy = T.trophy_by_id(T.schedule(p)[3])
    fee = T.entry_fee(p, trophy)
    before = p.bits
    t = T.Tournament(p, trophy)
    assert before - p.bits == fee > 0            # the stake leaves at entry
    t.record(False)
    assert t.reward_bits == 0                    # a quarterfinal exit pays nothing
    for exits, share in ((1, 3), (2, 2)):
        q = _pet()
        t2 = T.Tournament(q, trophy)
        for _ in range(exits):
            t2.record(True)
        purse = t2._calc_bits()
        t2.record(False)
        assert t2.reward_bits == purse // share
    r = _pet()
    t3 = T.Tournament(r, trophy)
    for _ in range(3):
        t3.record(True)
    assert t3.champion and t3.reward_bits >= t3._calc_bits()
    assert r.trophies == 1


def test_the_egg_gate_cups_are_the_ones_the_board_names():
    """The guide says "Win Summer Open #147"; the gate keys on trophy 146.
    The label is 1-based ("#0 reads like a bug"), so those are the same cup
    -- pinned because an off-by-one here sends a tamer to win the WRONG
    tournament for an egg that never unlocks."""
    from tuipet import data
    rules = data.load_egg_unlock()
    for egg_i, tid, name in ((12, 146, "Summer Open #147"),
                             (32, 187, "Fall Open #188")):
        assert rules[egg_i]["tourney"] == tid
        assert T.trophy_label(T.trophy_by_id(tid)) == name


def test_the_year_always_has_a_featured_cup():
    import datetime
    p = _pet()
    for d in range(0, 365, 7):
        day = datetime.date(2026, 1, 1) + datetime.timedelta(days=d)
        assert T.featured_now(p, today=day) is not None
    sched = T.schedule(p)
    assert len(sched) == 24
    assert all(T.trophy_by_id(t) is not None for t in sched)


def test_a_pet_that_falls_mid_bracket_is_not_crowned():
    p = _pet()
    t = T.Tournament(p, T.trophy_by_id(T.schedule(p)[0]))
    t.record(True)
    p.dead = True
    t.record(True)
    assert t.over and not t.champion and p.trophies == 0


def test_one_space_from_the_tree_starts_the_show():
    """Dead-stop fix (Joel 2026-07-25 "i have to press space in order for
    the animation sequence to start? i thought the thing froze, there was
    nothing on screen"): SPACE on the bracket tree launches the walk-in on
    the SAME press.  The old flow parked on the empty faceoff arena --
    render_scene([]) with only a strip hint -- until a second space."""
    p, pan = _entered()
    pan.phase = "bracket"
    pan.tree_view = True
    pan.key("space")
    assert pan._intro is not None                # the introductions are RUNNING
    assert not pan.tree_view


def test_B_never_lands_on_the_empty_faceoff_mid_cup():
    """B is the bracket key: while the cup runs it always SHOWS the tree
    (the old toggle flipped tree->empty-arena, the same frozen blank);
    once the cup is over it still toggles tree <-> result."""
    p, pan = _entered()
    pan.phase = "bracket"
    pan.tree_view = True
    pan.key("b")
    assert pan.tree_view                         # pinned to the tree mid-cup
    pan.tourney.over = True
    pan.key("b")
    assert not pan.tree_view                     # over: toggle to the result...
    pan.key("b")
    assert pan.tree_view                         # ...and back


def test_a_pet_drained_or_hurt_mid_cup_withdraws_before_the_next_round():
    """Battle call #22 = A (Joel 2026-10-15): the body is checked EVERY round,
    not just at entry."""
    for state in ({"energy": 0}, {"injured": True}):
        p, pan = _entered()
        pan.tree_view = True
        for k, v in state.items():
            setattr(p, k, v)
        pan._start_intro()                       # "fight on" walks in here
        assert pan.sub is None and pan._intro is None
        assert pan.tourney.over and not pan.tourney.champion
        assert "Withdrawn" in pan.tourney.last
    p, pan = _entered()                          # a fit pet still walks in
    pan._start_intro()
    assert pan._intro is not None and not pan.tourney.over
