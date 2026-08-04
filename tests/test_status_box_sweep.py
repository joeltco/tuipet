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
    pan.pet, pan.state, pan._last_name = app.pet, None, "joel"
    pan.bshow = None      # `sub` is DERIVED from bshow (see LobbyPanel.sub)
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


def test_every_embedded_fight_shows_the_battle_card():
    """Modularize (Joel 2026-07-22: 'why are adventure battles and cup
    battles different?? the status box in cup shows so much more'):
    painter_for walks sub chains, so ANY host's embedded fight gets THE
    battle card — the cup's, the road wild's, the town cup's two layers
    deep, the raid volley's.  One fight, one card."""
    from tuipet import adventure
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.battlescreen import BattlePanel
    from tuipet.townscreen import TownPanel
    app = _app()

    road = AdventurePanel(app.pet, zone=adventure.ZONES[0])
    road._trans = None
    road.travelling = True
    road.sub = BattlePanel(app.pet, {"num": 100}, wild=True)
    txt = _card(app, road)
    assert "battle" in txt and "You " in txt and "Foe " in txt

    town = TownPanel(app.pet, town_id=0)
    town.cursor = 3                              # Town Cup
    town.key("enter")                            # mounts the TournamentPanel
    if town.sub is not None:                     # (affordability permitting)
        town.sub.sub = BattlePanel(app.pet, {"num": 100})
        txt = _card(app, town)
        assert "battle" in txt and "You " in txt   # two layers deep, same card


def test_the_shop_eggs_tab_buys_through_the_single_source():
    """Shops-look-the-same: the tab's ENTER runs shop.town_egg_buy — the
    exact path the old market panel now delegates to."""
    from tuipet import persistence, shop
    from tuipet.shopscreen import ShopPanel
    app = _app()
    app.pet.bits = 5000
    pan = ShopPanel(app.pet, town_id=1, start_tab="Eggs")
    rows = pan._rows()
    idx = next(e["egg_idx"] for e in rows if not e["owned"])
    pan.cursor = next(i for i, e in enumerate(rows) if e["egg_idx"] == idx)
    pan.key("enter")
    assert idx in persistence.get_eggs_owned()
    assert app.pet.bits == 5000 - shop.egg_price(idx)
    pan.key("enter")                             # again: refuses, no double bill
    assert app.pet.bits == 5000 - shop.egg_price(idx)
    assert pan.text()                            # and the tab renders


def test_the_road_wears_its_own_card():
    """Joel's named order 2026-07-30 ("yeah give the road its own card"): the
    walk had NO painter at all, so a forty-leg run showed the HOME vitals --
    the same card as standing in the yard -- while every number the road
    generates (legs, lives, bits, fights, loot, the chain) lived only in the
    end-of-run results card or one-at-a-time on the 40-cell strip."""
    import re
    from rich.cells import cell_len
    from tuipet import adventure
    from tuipet.adventurescreen import AdventurePanel
    app = _app()
    road = AdventurePanel(app.pet, zone=adventure.ZONES[0])
    road._trans = None
    road.travelling = True
    road.adv.loc, road.adv.lives = 17, 2
    road.adv.bits_earned, road.adv.fights, road.adv.wins = 240, 4, 3
    road.adv.finds, road.adv.streak = 2, 3
    txt = _card(app, road)
    assert "road" in txt and "Rex" in txt
    assert "17/40" in txt                       # the live march position
    assert "+240b" in txt and "3W/4" in txt and "Loot   2" in txt
    assert "×3" in txt                          # the live chain
    assert "SPACE hurry" in txt                 # ...and the FULL key set at once,
    #                                             which the rotating strip cannot show
    # the gate arm names the boss where the road gauge was
    road._at_gate = True
    gate_txt = _card(app, road)
    assert "Gate" in gate_txt and road.adv.boss_name[:8] in gate_txt
    road._at_gate = False
    # a TOWN visit is still ON the run: the unregistered TownPanel must not
    # drop the card back to bare vitals (painter_for walks .sub, then falls
    # back to the host) -- but its SHOP tab still wins, two layers deep
    from tuipet.townscreen import TownPanel
    road.sub = TownPanel(app.pet, town_id=0)
    assert "road" in _card(app, road)

    # the box budget, worst case (26x16): longest name, 3-digit energy, a
    # 5-digit purse, 99s across the ledger and a held transport
    app.pet.name = "Wwwwwwwwwwwwwwww"
    app.pet.energy = 125
    app.pet.inventory["town_transport"] = 1
    wide = AdventurePanel(app.pet, zone=adventure.ZONES[-1])
    wide._trans, wide.travelling = None, True
    wide.adv.loc, wide.adv.bits_earned = 39, 99999
    wide.adv.fights = wide.adv.wins = wide.adv.finds = wide.adv.streak = 99
    for gate in (False, True):
        wide._at_gate = gate
        rows = _card(app, wide).split("\n")
        assert len(rows) <= 16, f"gate={gate}: {len(rows)} rows"
        for r in rows:
            plain = re.sub(r"\[/?[^\[\]]*\]", "", r)
            assert cell_len(plain) <= 26, f"gate={gate}: {plain!r}"
    assert "T warp" in _card(app, wide)          # the out only shows when held


def test_the_road_card_names_the_wound_line_and_the_gate_verdict():
    """ROAD ITEM AUDIT 2026-07-31 (Joel: "do 1 and 3").

    Two things the road never said out loud, both now on the card:
     * the WOUND LINE -- `record_battle` calls a body "bad" under
       BATTLE_MIN_ENERGY and rolls injury at 10% a bout instead of 0.3%.
       Measured: 391/400 runs cross it by the median leg 19.
     * the GATE VERDICT -- `battle_condition(check_energy=False)` is what
       refuses the boss AND makes every wayside wild slip away, and it was
       only ever spoken after forty legs of walking.  Same call the road
       itself makes, so the card cannot drift from the gate."""
    import re
    from rich.cells import cell_len
    from tuipet import adventure
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.petbase import BATTLE_MIN_ENERGY
    app = _app()
    road = AdventurePanel(app.pet, zone=adventure.ZONES[0])
    road._trans, road.travelling = None, True

    plain = lambda t: re.sub(r"\[/?[^\[\]]*\]", "", t)
    app.pet._set_energy(BATTLE_MIN_ENERGY + 5)
    txt = plain(_card(app, road))
    assert f"Energy {BATTLE_MIN_ENERGY + 5}" in txt and "wounds easy" not in txt
    app.pet._set_energy(BATTLE_MIN_ENERGY - 1)
    assert "wounds easy" in plain(_card(app, road))    # the line, named

    # the gate's OWN words, the moment they are true
    for state, attr, val in (("hurt", "injured", True), ("sick", "sick", True),
                             ("hungry", "hunger", 0), ("Clean", "poop", 2)):
        fresh = _app()
        fresh.pet._set_energy(4)
        setattr(fresh.pet, attr, val)
        pan = AdventurePanel(fresh.pet, zone=adventure.ZONES[0])
        pan._trans, pan.travelling = None, True
        want = fresh.pet.battle_condition(check_energy=False)
        assert want is not None, state
        txt = plain(_card(fresh, pan))
        assert want in txt, f"{state}: card does not carry {want!r}"
        rows = _card(fresh, pan).split("\n")
        assert len(rows) <= 16
        for r in rows:
            assert cell_len(re.sub(r"\[/?[^\[\]]*\]", "", r)) <= 26, r
    # a well pet gets NO verdict row (the card must not invent a worry)
    clean = _app()
    clean.pet._set_energy(20)
    pan = AdventurePanel(clean.pet, zone=adventure.ZONES[0])
    pan._trans, pan.travelling = None, True
    assert clean.pet.battle_condition(check_energy=False) is None
    assert "fight." not in plain(_card(clean, pan))


def test_every_card_fits_the_box_in_cells():
    """⭐THE UNIVERSAL BUDGET SWEEP (card audit 2026-08-04, Joel: "lets do an
    audit on ALL status cards").

    The box is 26x16.  Individual cards had individual budget pins, and the
    gaps between them are where the clipping lived: this audit found the DNA
    card at 28 cells -- `Field    Virus Buster  (own)` -- and 7 of the 10 DNA
    fields overflowed the same way whenever the card showed the pet's OWN
    field, which is the commonest case there is.  Textual wrapped the tail
    onto the box's invisible next row.

    ⛔This drives EVERY registered painter through the REAL dispatcher, so a
    new card cannot ship without a budget check, and an old one cannot drift
    into overflow silently.  Cells, never len() -- THE CELL LAW."""
    from rich.cells import cell_len
    from rich.text import Text
    from tuipet import adventure, data, statusbox
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.battlescreen import BattlePanel
    from tuipet.dnascreen import DNAPanel
    from tuipet.feedscreen import FeedPanel
    from tuipet.shopscreen import ShopPanel

    def _sweep(tag, app):
        txt = app.stats_w.txt
        rows = Text.from_markup(txt).plain.split("\n")   # raises on bad markup
        assert len(rows) <= 16, f"{tag}: {len(rows)} rows overflow the card"
        for r in rows:
            assert cell_len(r) <= 26, f"{tag}: {cell_len(r)} cells |{r}|"

    # the three fixed cards, in their worst states
    for tag, lines in (
        ("home", statusbox.home_lines(_app().pet)),
        ("home/loaded", statusbox.home_lines(
            _app(Pet(num=399, name="Wwwwwwwwwwwwwwwwwwwwww", stage="Mega",
                     attribute="Vaccine")).pet)),
        ("egg", statusbox.egg_lines(Pet(num=-1, name="", stage="Egg"))),
    ):
        fake = _FakeStats()
        fake.txt = "\n".join(lines)
        _sweep(tag, type("A", (), {"stats_w": fake})())

    # every DNA field -- the case this audit caught
    for fld in data.DNA_FIELDS:
        app = _app()
        app.pet.field = fld
        _sweep(f"dna[{fld}]", _card_app(app, DNAPanel(app.pet)))

    # the panels, driven through painter_for
    app = _app()
    road = AdventurePanel(app.pet, zone=adventure.ZONES[0])
    road._trans, road.travelling = None, True
    for tag, mode in (
        ("feed", FeedPanel(app.pet)),
        ("shop", ShopPanel(app.pet)),
        ("bag", ShopPanel(app.pet, start_mode="bag")),
        ("road", road),
        ("battle", BattlePanel(app.pet, {"num": 100, "name": "MetalGreymon"},
                               wild=True)),
    ):
        _sweep(tag, _card_app(_app(), mode))


def _card_app(app, mode):
    """Paint `mode`'s card into `app` through the real dispatcher."""
    from tuipet import statusbox
    app.mode = mode
    painter = statusbox.painter_for(mode)
    assert painter is not None, f"{type(mode).__name__} fell to bare vitals"
    painter(app)
    return app


def test_the_album_and_hall_wear_their_own_cards():
    """⭐Joel's named order 2026-08-04 ("build the album and hall cards"), off
    the all-cards audit that found both falling through to BARE VITALS -- you
    opened the bestiary or the lineage book and the box on the right was still
    reading out your pet's hunger.  Two screens he had asked for (2026-07-21
    and 2026-07-26) had never had a card at all.

    Each shows what a BOOK has and a scoreboard doesn't: where you are in it,
    and the entry under the cursor."""
    import re
    from rich.cells import cell_len
    from tuipet.albumscreen import AlbumPanel
    from tuipet.hallscreen import HallPanel
    plain = lambda t: re.sub(r"\[/?[^\[\]]*\]", "", t)

    app = _app()
    # ---- the ALBUM: progress, and the browsed form -------------------------
    ap = AlbumPanel(app.pet)
    ap.seen = set(ap.roster[:37])
    txt = plain(_card(app, ap))
    assert "Album" in txt
    assert f"37 of {ap.n} forms" in txt              # LIVE off the panel's own data
    assert "Found" in txt
    rec_name = _rec_name(ap.roster[0])
    assert rec_name in txt, "a DISCOVERED form must wear its name"
    # ...and an undiscovered one stays masked, but carries its ROUTE
    ap.i = next(i for i, n in enumerate(ap.roster) if n not in ap.seen)
    txt = plain(_card(app, ap))
    assert "???" in txt, "an undiscovered form must stay masked"
    from tuipet.albumscreen import route_hint
    hint = route_hint(ap.roster[ap.i])
    assert hint.split()[0] in txt, "the route must reach the card"

    # ---- the HALL: the line, and the elder ---------------------------------
    hp = HallPanel(app.pet)
    hp.elders = [
        {"gen": 3, "name": "Wwwwwwwwwwwwwwwwwwwwwwww", "stage": "Mega",
         "age": 3 * 86400 + 7000, "cups": 12, "dead": True, "num": 399,
         "cause": "a really quite long and wordy demise", "wins": 74},
        {"gen": 2, "name": "Agumon", "stage": "Rookie", "age": 6000,
         "cups": 0, "dead": False, "num": 100, "wins": 3},
    ]
    hp.n = len(hp.elders)
    txt = plain(_card(app, hp))
    assert "2 elders" in txt and "gen 3" in txt      # the LINE
    assert "3d01h" in txt and "74W" in txt and "12" in txt   # the ELDER
    assert "†" in txt, "a fallen elder must be marked"
    hp.i = 1
    txt = plain(_card(app, hp))
    assert "Agumon" in txt and "†" not in txt        # a RETIRED elder is not

    # an empty lineage says so instead of crashing or lying
    empty = HallPanel(app.pet)
    empty.elders, empty.n = [], 0
    assert "no elders yet" in plain(_card(app, empty))

    # both fit the box in every state above
    for mode in (ap, hp, empty):
        rows = _card(app, mode).split("\n")
        assert len(rows) <= 16
        for r in rows:
            assert cell_len(plain(r)) <= 26, r


def _rec_name(num):
    from tuipet import data
    return data.record_for(num).get("name", "?")


def test_the_zone_picker_wears_its_own_card():
    """⭐Joel 2026-08-04 ("do the zone picker one too") -- the last of the
    three the all-cards audit found on bare vitals.

    The panel's LIST already carries the name, the conquered mark and the
    standing best, so the card does NOT repeat them (a screen shows a fact
    once).  It carries what the list cannot: the gate boss, the road's length,
    whether there is a town on it, and the DEVICE'S VERDICT ON THE BODY --
    from the same `battle_condition(check_energy=False)` the gate itself will
    ask.  The road card learned that: a refusal that only speaks after forty
    legs speaks too late."""
    import re
    from rich.cells import cell_len
    from tuipet import adventure
    from tuipet.adventurescreen import ZonePickPanel
    plain = lambda t: re.sub(r"\[/?[^\[\]]*\]", "", t)
    app = _app()
    app.pet.hunger = app.pet.strength = 4

    m = ZonePickPanel(app.pet)
    zi = m.indices[m.cursor]
    z = adventure.ZONES[zi]
    txt = plain(_card(app, m))
    assert (z.get("bosses") or [{}])[0].get("name", "?") in txt   # the GATE
    assert f"{z['steps']} legs" in txt                            # the LENGTH
    assert "town" in txt                                          # the REST stop
    assert "Energy" in txt

    # the body's verdict reaches the card, verbatim, before the walk
    for attr, val in (("injured", True), ("sick", True), ("hunger", 0),
                      ("poop", 2)):
        q = _app()
        q.pet.hunger = q.pet.strength = 4
        setattr(q.pet, attr, val)
        want = q.pet.battle_condition(check_energy=False)
        assert want, attr
        assert want in plain(_card(q, ZonePickPanel(q.pet))), attr

    # ⛔the title must never restate the Gate row: `_zone_display` shortens a
    # long zone name to its BOSS, which is right on the home card and a
    # duplicate here.  Swept over all 26 zones, worst case included.
    for zi in range(len(adventure.ZONES)):
        mm = ZonePickPanel(app.pet)
        mm.indices, mm.cursor = [zi], 0
        rows = [plain(r) for r in _card(app, mm).split("\n")]
        gate = next(r for r in rows if r.startswith("Gate")).replace("Gate", "").strip()
        assert rows[0] != gate, f"zone {zi}: title restates the gate ({gate!r})"
        assert len(rows) <= 16
        for r in rows:
            assert cell_len(r) <= 26, f"zone {zi}: {r!r}"

    # no roads open yet says so, instead of an empty frame
    empty = ZonePickPanel(app.pet)
    empty.indices = []
    assert "no roads open" in plain(_card(app, empty))
