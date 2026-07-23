"""The status-box sweep (Joel 2026-07-17: "for every action, every scene,
every menu, every part of the game, the status box needs to be redone").
Every mode paints a DELIBERATE card into the right-hand box -- the
bare-vitals fallback is for the home screen alone.  Driven through the
real app painters, not re-implementations."""


from tuipet.app import TuiPetApp, Stats
from tuipet.pet import Pet


class _FakeStats(Stats):
    def __init__(self):
        self.txt = ""
        self._sub = ""
    def update(self, t):
        self.txt = str(t)
    def paint(self, pet):
        self.txt = "VITALS"
    @property
    def border_subtitle(self):
        return self._sub
    @border_subtitle.setter
    def border_subtitle(self, v):
        self._sub = v


def _app(pet=None):
    p = pet or Pet(num=100, name="Rex", stage="Champion",
                   attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 2500
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = p
    app.stats_w = _FakeStats()
    app.sound = False
    return app


def _card(app, mode):
    app.mode = mode
    painter = app._status_painter()
    assert painter is not None, f"{type(mode).__name__} fell to bare vitals"
    painter()
    return app.stats_w.txt


def test_feed_card():
    from tuipet.feedscreen import FeedPanel
    app = _app()
    txt = _card(app, FeedPanel(app.pet))
    assert "Feed" in txt and "Hunger" in txt and "Meat" in txt
    app.mode.cursor = 1
    assert "Pill" in _card(app, app.mode)


def test_shop_and_bag_cards():
    from tuipet.shopscreen import ShopPanel
    app = _app()
    txt = _card(app, ShopPanel(app.pet))
    assert "Shop" in txt and "Price" in txt and "Bits" in txt
    bag = ShopPanel(app.pet, start_mode="bag")
    app.pet.add_item("energy_drink")
    txt = _card(app, bag)
    assert "Bag" in txt


def test_eggguide_card():
    from tuipet.eggguidescreen import EggGuidePanel
    app = _app()
    txt = _card(app, EggGuidePanel())
    assert "Digitama" in txt and "Hatches" in txt


def test_digicore_card():
    from tuipet.digicorescreen import DigiCorePanel
    app = _app()
    txt = _card(app, DigiCorePanel(app.pet))
    assert "DigiCore" in txt and "Page" in txt


def test_raid_card_offline():
    from tuipet.raidscreen import RaidPanel
    app = _app()
    pan = RaidPanel.__new__(RaidPanel)          # no relay in tests
    pan.pet, pan.sub = app.pet, None
    pan.client = type("C", (), {"raid": None})()
    txt = _card(app, pan)
    assert "Raid" in txt and "gate" in txt


def test_lobby_card_connecting():
    from tuipet.lobbyscreen import LobbyPanel
    app = _app()
    pan = LobbyPanel.__new__(LobbyPanel)
    pan.pet, pan.state, pan._last_name, pan.sub = app.pet, None, "joel", None
    txt = _card(app, pan)
    assert "Lobby" in txt and "connecting" in txt


def test_help_options_bug_cards():
    from tuipet.helpscreen import HelpPanel
    from tuipet.optionsscreen import OptionsPanel
    from tuipet.bugscreen import BugReportPanel
    app = _app()
    assert "tuipet" in _card(app, HelpPanel(app.pet))
    op = OptionsPanel.__new__(OptionsPanel)
    op.cursor, op.msg, op.sub = 0, "", None
    assert "Options" in _card(app, op)
    assert "Bug Report" in _card(app, BugReportPanel(app.pet))


def test_death_and_assist_cards():
    from tuipet.deathscreen import DeathPanel
    from tuipet.assistscreen import AssistPanel
    app = _app()
    app.pet.dead = True
    app.pet.death_cause = "a deadly fruit"
    dp = DeathPanel.__new__(DeathPanel)
    dp.sub = None
    txt = _card(app, dp)
    assert "In Memory" in txt and "deadly fruit" in txt
    app.pet.dead = False
    assert "Assistant" in _card(app, AssistPanel(app.pet))


def test_scenes_and_eggselect_still_covered():
    from tuipet.backgroundscreen import BackgroundPanel
    app = _app()
    assert "Scenes" in _card(app, BackgroundPanel(app.pet))


def test_eat_readout_charts_only_live_systems():
    """The feeding readout was REWRITTEN in the modularize pass (2026-07-17):
    the old card charted protein/mineral/vitamin bars from the nutrition
    system removed 2026-07-16 -- frozen numbers.  The live card: hunger,
    weight, effort, satiety.  (Fuel/calorie bar removed 2026-07-20 -- a
    DVPet-only mechanic feeding never touched.)"""
    from tuipet import statusbox
    app = _app()
    app.mode = None
    statusbox.eat(app)
    txt = app.stats_w.txt
    assert "feeding" in txt and "Hunger" in txt
    for dead in ("Fuel", "Protein", "Mineral", "Vitamin", "nourished"):
        assert dead not in txt, dead


def test_dna_card_bills_energy_not_dead_systems():
    """The DNA charge bill lies no more: spirit and mood are gone; applyDNA
    costs ENERGY (1/unit own Field, x2 off)."""
    from tuipet import statusbox
    from tuipet.dnascreen import DNAPanel
    app = _app()
    app.mode = DNAPanel(app.pet)
    statusbox.dna(app)
    txt = app.stats_w.txt
    assert "energy -" in txt
    assert "spirit" not in txt and "mood" not in txt


def test_every_painter_lives_in_statusbox():
    """The modularize law (Joel 2026-07-17): app.py holds only thin
    delegates -- no card body may creep back in."""
    import inspect
    import re
    from tuipet import app as app_mod
    src = inspect.getsource(app_mod)
    bodies = re.findall(r"def (_status_\w+)\(self.*?\):(.*?)(?=\n    def )", src, re.S)
    assert len(bodies) == 4                      # painter/eggselect/eat/card
    for name, body in bodies:
        assert "statusbox." in body, f"{name} grew a body outside statusbox"
        assert "stats_w.update" not in body or name == "_status_card" \
            or "statusbox" in body


def test_the_egg_carousel_card_names_the_egg():
    """Joel 2026-07-22: 'shouldnt the egg carousel screen show the name of
    the egg?' -- the browsed digitama had no label anywhere, so matching
    it to its egg-guide entry meant matching art by eye.  The card wears
    the egg's TITLE now; the hatch line still names the BABY only (the
    egg-must-not-promise-an-egg ruling is untouched)."""
    from tuipet import egg as egg_mod
    from tuipet.eggselectscreen import EggSelectPanel
    app = _app()
    pan = EggSelectPanel(app.pet)
    assert pan.n, "starters must populate the carousel"
    txt = _card(app, pan)
    idx = pan.carousel[pan.i]
    assert egg_mod.hatch_name(idx) in txt          # the egg's own name
    assert egg_mod.destined_name(idx) in txt       # the baby, unchanged
