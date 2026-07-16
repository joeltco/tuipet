"""The STATUS box budget: #stats is physically 26x16 content (CSS 30x18
border-box).  Every painter must fit -- the status-box audit 2026-07-04 found
the DNA card 28 wide (its hint line wrapped mid-box) and raw-minutes ages
('4325m40s').  Same lesson as the LCD box-clip: pixels aren't the box."""
import re
import random

from tuipet.pet import Pet

CARD_W, CARD_H = 26, 16


def _vis(line):
    return len(re.sub(r"\[/?[^\[\]]*\]", "", line))


from tuipet.app import Stats


class _FakeStats(Stats):
    """A Stats with the Textual plumbing stubbed out (never mounted)."""
    def __init__(self): self.txt = ""
    def update(self, t): self.txt = str(t)
    @property
    def border_subtitle(self): return ""
    @border_subtitle.setter
    def border_subtitle(self, v): pass


def _fits(fake, tag):
    lines = fake.txt.split("\n")
    assert len(lines) <= CARD_H, f"{tag}: {len(lines)} lines overflow the card"
    w = max(_vis(l) for l in lines)
    assert w <= CARD_W, f"{tag}: {w} cols overflow the card"


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.age_seconds = 3 * 86400 + 7000       # an older pet: worst-case widths
    p.bits = 99999
    p.dp = 3
    p.poop = 2
    p.sick = True
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_main_egg_and_grave_cards_fit_and_read_compact_ages():
    fake = _FakeStats()
    p = _pet()
    Stats.paint(fake, p)
    _fits(fake, "main")
    assert "3d01h" in fake.txt                  # compact age, not 4436m40s
    assert "◆3" in fake.txt                     # the DP meter rides the Power line
    Stats.paint(fake, Pet.new_egg(egg_type=1))
    _fits(fake, "egg")
    dead = _pet(dead=True)
    Stats.paint(fake, dead)
    _fits(fake, "grave")
    assert "Lived    3d01h" in fake.txt


def test_every_mode_painter_fits_the_card():
    random.seed(5)
    from tuipet.app import TuiPetApp
    from tuipet import (adventurescreen, townscreen, training, battlescreen,
                        dnascreen, tournamentscreen)
    from tuipet import tournament as tmod
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = _pet()
    fake = app.stats_w = _FakeStats()
    p = app.pet

    app.mode = adventurescreen.AdventurePanel(p)
    app._status_adventure(); _fits(fake, "adventure")
    app.mode.sub = townscreen.TownPanel(p, 0)
    app._status_adventure(); _fits(fake, "town")
    app.mode = training.TrainingPanel(p)
    app._status_training(); _fits(fake, "train menu")
    app.mode.key("enter")
    app._status_training(); _fits(fake, "train drill")
    # EVERY drill's play card, not just the default -- v0.2.417 shipped a
    # card that still read the retired turret fields and CRASHED the moment
    # the data drill opened (Joel's phone report 2026-07-13): the harness
    # had only ever painted the HP card
    p.obedience = 900
    for gi, gk in ((1, "vaccine"), (2, "data"), (3, "virus")):
        app.mode = training.TrainingPanel(p)
        app.mode.gi = gi
        app.mode.key("enter")
        assert app.mode.phase == "play", f"{gk}: refused, card unprobed"
        app._status_training(); _fits(fake, f"train {gk}")
        if gk == "data":                                # the versus card counts
            assert "Round" in fake.txt and "Past" in fake.txt
    app.mode.gi = 2                                     # data, mid-volley
    app.mode._reset(); app.mode._start_game()
    app.mode.key("up")
    app._status_training(); _fits(fake, "train data volley")
    app.mode = battlescreen.BattlePanel(p)
    app._status_battle(); _fits(fake, "battle")
    from tuipet import habitatscreen
    app.mode = habitatscreen.HabitatPanel(p)
    app.mode.msg = "x" * 50                       # a long action message wraps
    app._status_habitat(); _fits(fake, "habitat")
    app.mode = dnascreen.DNAPanel(p)
    app._status_dna(); _fits(fake, "dna")
    app.mode = tournamentscreen.TournamentPanel(p)
    app._status_tournament(); _fits(fake, "cup select")
    tr = next((t for t in (tmod.trophy_by_id(i) for i in range(40)) if t), None)
    app.mode.tourney = tmod.Tournament(p, tr)
    app._status_tournament(); _fits(fake, "cup live")


def test_the_untested_consumer_cards_paint_and_fit():
    """Every OTHER app.py status-card branch a live session can reach -- the
    v0.2.417 crash shipped because the harness only painted each painter in
    ONE state (test audit 2026-07-13): the eat card, the battle result card,
    the town cup-bout card, the adventure mid-encounter card, the training
    done card and the HP card mid-drill were all attribute-drift blind."""
    random.seed(7)
    from tuipet.app import TuiPetApp
    from tuipet import adventurescreen, townscreen, training, battlescreen
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = _pet()
    fake = app.stats_w = _FakeStats()
    p = app.pet

    app._status_eat(); _fits(fake, "eat")                # painted every eat fx

    app.mode = battlescreen.BattlePanel(p)               # the result card
    app.mode.done_anim, app.mode.won = True, True
    app.mode.battle.reward = "Won 100b and a Digimental of Courage"
    app._status_battle(); _fits(fake, "battle result")
    assert "VICTORY" in fake.txt

    town = townscreen.TownPanel(p, 0)                    # the cup-bout card
    town.sub = battlescreen.BattlePanel(p)
    app._status_town(town); _fits(fake, "town bout")
    assert "vs" in fake.txt

    app.mode = adventurescreen.AdventurePanel(p)         # mid-encounter card
    app.mode.sub = battlescreen.BattlePanel(p)
    app._status_adventure(); _fits(fake, "adventure battle")

    app.mode = training.TrainingPanel(p)                 # the done card
    app.mode.phase, app.mode.success = "done", True
    app.mode.result = "Perfect! Effort up! HP +1!"
    app._status_training(); _fits(fake, "train done")
    assert "drill complete" in fake.txt

    p.obedience = 900
    app.mode = training.TrainingPanel(p)                 # HP card mid-drill
    app.mode.key("enter")
    assert app.mode.phase == "play"
    app.mode.rep, app.mode.rounds_won = 2, 1             # the dots arithmetic
    app._status_training(); _fits(fake, "train hp mid")
