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
    app.mode = battlescreen.BattlePanel(p)
    app._status_battle(); _fits(fake, "battle")
    app.mode = dnascreen.DNAPanel(p)
    app._status_dna(); _fits(fake, "dna")
    app.mode = tournamentscreen.TournamentPanel(p)
    app._status_tournament(); _fits(fake, "cup select")
    tr = next((t for t in (tmod.trophy_by_id(i) for i in range(40)) if t), None)
    app.mode.tourney = tmod.Tournament(p, tr)
    app._status_tournament(); _fits(fake, "cup live")
