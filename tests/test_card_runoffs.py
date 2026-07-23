"""STATUS-CARD run-off sweep (Joel 2026-07-23: "all status cards need to
be audited. i see text run off in quite a few").

The card interior is 26 cols x 16 rows (#stats: width 30 - border 2 -
padding 2).  A line wider than 26 wraps inside the box and shoves the
card's tail off the bottom -- the same failure family as the LCD menu
run-offs (tools/menu_sheet.py), which never covered the card column.

This sweep drives EVERY painter through its deep states with worst-case
data (14-char pet names, 8-digit bits, long species/boss/cup names) and
measures the PLAIN width of every rendered line.  Fit-fixes ship
pre-clipped at the source (the family law) -- never rely on the widget
to crop.
"""
import pytest
from rich.text import Text

from tuipet import statusbox
from tuipet.pet import Pet

CARD_W = 26          # #stats interior: width 30 - round border 2 - padding 2
CARD_H = 16


class _W:
    def __init__(self):
        self.txt = ""
        self.border_subtitle = ""

    def update(self, t):
        self.txt = t


class _App:
    sound = True                      # the options painter reads it

    def __init__(self, pet, mode=None):
        self.pet = pet
        self.mode = mode
        self.stats_w = _W()


def _worst_pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    p.name = "Maximilianmon"          # the 14-char name budget, fully spent
    p.bits = 99_999_999
    p.world_seconds = 600.0
    p.trophies = 12
    p.wins, p.battles = 999, 4321
    p.weight = 199
    p.care_mistakes = 19
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _measure(txt):
    """[(row, width, plain)] for every over-wide line."""
    out = []
    for i, l in enumerate(txt.split("\n")):
        p = Text.from_markup(l).plain
        if len(p) > CARD_W:
            out.append((i, len(p), p))
    return out


def _paint(pan, pet=None):
    app = _App(pet or _worst_pet(), pan)
    fn = statusbox.painter_for(pan)
    assert fn is not None, f"{type(pan).__name__}: no painter"
    fn(app)
    return app.stats_w.txt


# ---- the state factories ----------------------------------------------------

def _battle(phase):
    from tuipet.battlescreen import BattlePanel
    p = _worst_pet()
    pan = BattlePanel(p, {"num": 100, "name": "Metalgarurumon X"})
    if phase in ("result-won", "result-lost"):
        pan._start_fight("normal")
        while pan.battle.play_round() is not None:
            pass
        pan._enter_result()
        pan.won = phase == "result-won"
    elif phase == "ready":
        pan.phase = "ready"
        pan.hud_note = "Set your timing!  (weight on base, full belly & drills win fights)"
    return pan, p


def _raid_panel(**view_kw):
    import time
    from tuipet.raidscreen import RaidPanel
    pan = RaidPanel.__new__(RaidPanel)
    pan.pet = _worst_pet()
    pan.sub = None
    view = {"now": time.time(), "attempts": 3,
            "you": [999, 99_000_000],
            "top": [["Wxyzabcdefghijk", 99_000_000]],
            "boss": {"num": 214, "name": "Omnimon Merciful Mode",
                     "hp": 5_400_000, "max_hp": 5_500_000,
                     "start": 0, "end": time.time() + 86400 * 6},
            "award": None}
    view.update(view_kw)
    pan.client = type("C", (), {"raid": view})()
    return pan, pan.pet


def _dna(phase):
    from tuipet.dnascreen import DNAPanel
    p = _worst_pet()
    pan = DNAPanel(p)
    pan.phase = phase
    pan.last = ("The resonance splashed DeepSaver's neighbors on both sides "
                "of the wheel!")
    return pan, p


STATES = {}


def state(name):
    def deco(fn):
        STATES[name] = fn
        return fn
    return deco


state("home-vitals")(lambda: (None, _worst_pet()))
state("home-sick-poop")(lambda: (None, _worst_pet(sick=True, poop=4)))


@state("egg")
def _egg():
    return None, Pet(num=-1, stage="Egg")


@state("grave")
def _grave():
    p = _worst_pet()
    p.dead = True
    p.death_cause = "a poisonous deadly fruit"
    return None, p


@state("feed")
def _feed():
    from tuipet.feedscreen import FeedPanel
    p = _worst_pet()
    return FeedPanel(p), p


@state("eat")
def _eat():
    p = _worst_pet()
    app = _App(p, None)
    statusbox.eat(app)
    return ("raw", app.stats_w.txt)


state("battle-fresh")(lambda: _battle("fresh"))
state("battle-ready")(lambda: _battle("ready"))
state("battle-won")(lambda: _battle("result-won"))
state("battle-lost")(lambda: _battle("result-lost"))


@state("raid-volley-card")
def _raid_volley():
    from tuipet.battlescreen import BattlePanel
    pan, p = _raid_panel()
    enemy = {"num": 214, "name": "Omnimon Merciful Mode", "boss": True,
             "pool": (5_400_000, 5_500_000)}
    pan.sub = BattlePanel(p, enemy, raid=True)
    return pan, p


state("raid-standing")(lambda: _raid_panel())
state("raid-award")(lambda: _raid_panel(award={"id": "9", "boss": "Omnimon MM"}))
state("raid-incoming")(lambda: _raid_panel(
    boss={"num": 214, "name": "Omnimon Merciful Mode", "hp": 0,
          "max_hp": 5_500_000, "start": 9e12, "end": 9e12}))


@state("cup-select")
def _cup_select():
    from tuipet.tournamentscreen import TournamentPanel
    p = _worst_pet()
    pan = TournamentPanel.__new__(TournamentPanel)
    pan.pet, pan.tourney, pan.sub = p, None, None
    return pan, p


@state("cup-bracket")
def _cup_bracket():
    import random
    from tuipet import tournament
    from tuipet.tournamentscreen import TournamentPanel
    random.seed(3)
    p = _worst_pet()
    from tuipet import data
    troph = dict(data.load_tournies()[0], bit_mod=1.5)
    pan = TournamentPanel.__new__(TournamentPanel)
    pan.pet, pan.sub = p, None
    pan.tourney = tournament.Tournament(p, troph)
    return pan, p


@state("cup-champion")
def _cup_champion():
    pan, p = _cup_bracket()
    pan.tourney.over = pan.tourney.champion = True
    pan.tourney.reward_bits = 99999
    return pan, p


@state("cup-eliminated")
def _cup_out():
    pan, p = _cup_bracket()
    pan.tourney.over, pan.tourney.champion = True, False
    return pan, p


for ph in ("home", "charge", "stats", "bet", "mash", "result", "roads"):
    state(f"dna-{ph}")(lambda ph=ph: _dna(ph))


@state("training")
def _training():
    from tuipet.training import TrainingPanel
    p = _worst_pet()
    return TrainingPanel(p), p


@state("lobby-connecting")
def _lobby():
    from tuipet.lobbyscreen import LobbyPanel
    p = _worst_pet()
    pan = LobbyPanel.__new__(LobbyPanel)
    pan.pet, pan.state, pan._last_name, pan.sub = p, None, "joel", None
    return pan, p


@state("death-etch")
def _death():
    from tuipet.deathscreen import DeathPanel
    p = _worst_pet()
    p.dead = True
    mem = {"name": "Maximilianmon", "vaccine": 9, "data": 9, "virus": 9}
    return DeathPanel(p, new_mem=mem, hold=0), p


@state("assist")
def _assist():
    from tuipet.assistscreen import AssistPanel
    p = _worst_pet()
    return AssistPanel(p), p


@state("eggselect")
def _eggselect():
    from tuipet.eggselectscreen import EggSelectPanel
    p = _worst_pet()
    return EggSelectPanel(p), p


@state("eggguide")
def _eggguide():
    from tuipet.eggguidescreen import EggGuidePanel
    return EggGuidePanel(), _worst_pet()


@state("digicore")
def _digicore():
    from tuipet.digicorescreen import DigiCorePanel
    p = _worst_pet()
    return DigiCorePanel(p), p


@state("scenes")
def _scenes():
    from tuipet.backgroundscreen import BackgroundPanel
    p = _worst_pet()
    return BackgroundPanel(p), p


@state("shop")
def _shop():
    from tuipet.shopscreen import ShopPanel
    p = _worst_pet()
    return ShopPanel(p), p


@state("bag")
def _bag():
    from tuipet.shopscreen import ShopPanel
    p = _worst_pet()
    p.add_item("energy_drink")
    return ShopPanel(p, start_mode="bag"), p


@state("town-eggs")
def _town_eggs():
    from tuipet.shopscreen import ShopPanel
    p = _worst_pet()
    return ShopPanel(p, town_id=0, start_tab="Eggs"), p


@state("help")
def _help():
    from tuipet.helpscreen import HelpPanel
    p = _worst_pet()
    return HelpPanel(p), p


@state("options")
def _options():
    from tuipet.optionsscreen import OptionsPanel
    op = OptionsPanel.__new__(OptionsPanel)
    op.cursor, op.msg, op.sub = 0, "", None
    return op, _worst_pet()


@state("bug")
def _bug():
    from tuipet.bugscreen import BugReportPanel
    p = _worst_pet()
    return BugReportPanel(p), p


@state("title")
def _title():
    from tuipet.titlescreen import TitlePanel
    return TitlePanel(), _worst_pet()


# ---- the sweep --------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(STATES))
def test_no_card_line_runs_off(name):
    built = STATES[name]()
    if built[0] == "raw":                    # a direct stats_w text
        txt = built[1]
    elif built[0] is None:                   # home vitals family
        lines = (statusbox.grave_lines(built[1]) if built[1].dead
                 else statusbox.egg_lines(built[1]) if built[1].num == -1
                 else statusbox.home_lines(built[1]))
        txt = "\n".join(lines)
    else:
        txt = _paint(built[0], built[1])
    bad = _measure(txt)
    assert not bad, f"{name}: " + "; ".join(
        f"row {i} = {n} cols |{p}|" for i, n, p in bad)
    rows = txt.count("\n") + 1
    assert rows <= CARD_H, f"{name}: {rows} rows > {CARD_H}"
