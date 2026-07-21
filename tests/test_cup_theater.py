"""CUP THEATER — the award ceremony + the visible NPC rounds (2026-07-21).

Pins the two beats that filled the cup's dead moments: after each of your
wins the field's other winners parade across the arena before the bracket
page lands, and the crown plays the podium ceremony before the tree and
the numbers.  Both lock input and play out (own-game law).
"""
from tuipet import data, tournament
from tuipet.tournamentscreen import (TournamentPanel, CEREMONY_T, NPC_T)
from tuipet.pet import Pet


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.strength = p.hunger = 4
    p._set_energy(p.max_energy)
    p.bits = 99999
    return p


class _Result:
    def __init__(self, won):
        self.won = won


class _Sub:
    """A finished match: its first key routes ('done', result) home."""
    def __init__(self, won):
        self._r = _Result(won)
    def key(self, _k):
        return ("done", self._r)
    def anim(self):
        pass
    def text(self):
        return ""
    def strip(self):
        return ""


def _in_bracket():
    p = _pet()
    pan = TournamentPanel(p)
    trophy = tournament.trophy_by_id(tournament.schedule(p)[tournament._hour(p)])
    pan.tourney = tournament.Tournament(p, trophy)
    pan.phase = "bracket"
    pan.tree_view = True
    return pan


def _win_match(pan):
    pan.sub = _Sub(True)
    pan.key("space")                           # routes the result through record


def test_a_quarterfinal_win_parades_the_advancing_field():
    pan = _in_bracket()
    _win_match(pan)
    assert pan._advance is not None
    nums = pan._advance["nums"]
    assert nums == pan.tourney.results_nums and len(nums) == 3   # 3 other winners
    assert "advances" in pan.strip()
    for _ in range(NPC_T * len(nums) - 1):
        pan.key("escape")                      # locked: no forfeit mid-show
        assert pan.tourney.over is False
        assert pan.text() is not None          # every crossing renders
        pan.anim()
    pan.anim()
    assert pan._advance is None and pan.tree_view   # the tree lands after


def test_the_crown_plays_the_ceremony_before_the_numbers():
    pan = _in_bracket()
    for _ in range(3):                         # QF, semi, final
        while pan._advance is not None:        # let the parades play
            pan.anim()
        _win_match(pan)
    assert pan.tourney.champion and pan._ceremony is not None
    assert "CHAMPION" in pan.strip()
    for _ in range(CEREMONY_T - 1):
        pan.key("escape")                      # locked: the show plays out
        assert pan._ceremony is not None
        txt = pan.text().plain
        assert "CHAMPION" in txt               # the podium page
        pan.anim()
    pan.anim()
    assert pan._ceremony is None and pan.tree_view   # then the crowned tree


def test_an_elimination_skips_the_theater():
    pan = _in_bracket()
    pan.sub = _Sub(False)
    pan.key("space")                           # the loss ends the cup
    assert pan.tourney.over and not pan.tourney.champion
    assert pan._advance is None and pan._ceremony is None
    assert pan.tree_view                       # straight to the tree, as before


def test_the_parade_walks_real_advancing_species():
    pan = _in_bracket()
    _win_match(pan)
    for num, name in zip(pan._advance["nums"], pan.tourney.results):
        rec = data.record_for(num)
        assert rec.get("name") == name         # the sprite IS the named winner


def test_space_stages_the_introductions_then_the_bell():
    """MATCH INTRODUCTIONS: SPACE on the faceoff page walks the challenger
    in from the right, your mon in from the left, holds the stare-down --
    input locked -- then the fight opens itself against that SAME opponent."""
    from tuipet.battlescreen import BattlePanel
    from tuipet.tournamentscreen import INTRO_OPP_T, INTRO_PET_T, INTRO_HOLD_T
    pan = _in_bracket()
    pan.tree_view = False                      # the faceoff page
    opp = pan.tourney.current_opponent()
    pan.key("space")
    assert pan._intro is not None and pan.sub is None   # the show, not the fight
    assert "introductions" in pan.strip()
    total = INTRO_OPP_T + INTRO_PET_T + INTRO_HOLD_T
    saw = set()
    for _ in range(total):
        pan.key("escape")                      # locked: no forfeit mid-entrance
        assert pan.tourney.over is False
        txt = pan.text().plain
        if "enters!" in txt:
            saw.add("opp")
        if "answers!" in txt:
            saw.add("pet")
        if "FIGHT!" in txt:
            saw.add("bell")
        pan.anim()
    assert saw == {"opp", "pet", "bell"}       # all three phases showed
    assert pan._intro is None
    assert isinstance(pan.sub, BattlePanel)    # the bell rang
    assert pan.sub._enemy is opp               # ...against the announced foe
