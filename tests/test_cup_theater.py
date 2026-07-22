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


def _finish_match(pan, won):
    pan.sub = _Sub(won)
    pan.key("space")


def test_a_real_elimination_crowns_a_rival_a_forfeit_does_not():
    """THE RIVAL: the mon that beats you in a fought match becomes the
    standing grudge; walking out of the bracket names nobody."""
    pan = _in_bracket()
    opp = pan.tourney.current_opponent()
    _finish_match(pan, won=False)              # a real loss
    assert pan.pet.rival_num == opp["num"]
    assert pan.pet.rival_name == opp["name"]
    pan2 = _in_bracket()                       # a fresh cup, fresh pet
    pan2.pet.rival_num, pan2.pet.rival_name = -1, ""
    pan2.key("escape")                         # forfeit from the tree
    assert pan2.pet.rival_num == -1            # no fight, no grudge


def test_the_rival_reseeds_marked_and_announced():
    p = _pet()
    trophy = tournament.trophy_by_id(tournament.schedule(p)[tournament._hour(p)])
    probe = tournament.Tournament(p, trophy)   # learn the bracket's tier
    tier_num = probe.entrants[0]["num"]
    rec = data.record_for(tier_num)
    p.rival_num, p.rival_name = tier_num, rec["name"]
    t = tournament.Tournament(p, trophy)
    assert t.rival_in
    rivals = [e for e in t.entrants if e.get("rival")]
    assert len(rivals) == 1 and rivals[0]["num"] == tier_num
    assert "your rival" in t.last              # announced at the gate
    pan = TournamentPanel(p)
    pan.tourney, pan.phase, pan.tree_view = t, "bracket", True
    assert "!" + rec["name"][:9] in pan.text().plain[:400]   # the grudge mark


def test_a_mismatched_tier_keeps_the_rival_out():
    p = _pet()
    trophy = tournament.trophy_by_id(tournament.schedule(p)[tournament._hour(p)])
    from tuipet.data import load_sprites
    _, by_num = load_sprites()
    probe = tournament.Tournament(p, trophy)
    tier_stage = data.record_for(probe.entrants[0]["num"])["stage"]
    other = next(n for n, r in by_num.items()
                 if r["stage"] not in ("Egg", "Fresh", "InTraining", tier_stage)
                 and not data.is_placeholder(n))
    p.rival_num, p.rival_name = other, by_num[other]["name"]
    t = tournament.Tournament(p, trophy)
    assert not t.rival_in                      # the wall holds
    assert not any(e.get("rival") for e in t.entrants)


def test_revenge_settles_the_grudge():
    p = _pet()
    trophy = tournament.trophy_by_id(tournament.schedule(p)[tournament._hour(p)])
    probe = tournament.Tournament(p, trophy)
    tier_num = probe.entrants[0]["num"]
    p.rival_num = tier_num
    p.rival_name = data.record_for(tier_num)["name"]
    pan = TournamentPanel(p)
    pan.tourney = tournament.Tournament(p, trophy)
    pan.phase = "bracket"
    # stand the rival across from YOU
    t = pan.tourney
    yi = t.bracket.index("YOU")
    ri = next(i for i, e in enumerate(t.bracket)
              if e != "YOU" and e.get("rival"))
    pair = yi + 1 if yi % 2 == 0 else yi - 1
    t.bracket[ri], t.bracket[pair] = t.bracket[pair], t.bracket[ri]
    assert t.current_opponent().get("rival")
    _finish_match(pan, won=True)               # the revenge bout
    assert p.rival_num == -1 and p.rival_name == ""
    assert "REVENGE" in t.last
