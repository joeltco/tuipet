"""The message-box hint overhaul (Joel 2026-07-10): every sub-screen pops its
key hints in the #msg box via strip() -- one menu.hints() convention, and every
line holds still (plain text <= 40 cols, the never-marquee budget)."""
from tuipet.app import _hud_plain
from tuipet.pet import Pet
from tuipet import menu


def _pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500, bits=500)
    p.world_seconds = 12 * 60.0
    return p


def _ok(s, where):
    assert isinstance(s, str), where
    assert len(_hud_plain(s)) <= 40, f"{where}: {len(_hud_plain(s))} cols {s!r}"
    return s


def test_hints_helper_convention():
    s = menu.hints(("ENTER", "go"), ("ESC", "back"))
    assert s == "[b]ENTER[/][dim] go[/] [dim]·[/] [b]ESC[/][dim] back[/]"
    assert _hud_plain(s) == "ENTER go · ESC back"


def test_every_screen_strip_fits_and_speaks():
    from tuipet.shopscreen import ShopPanel
    from tuipet.eggselectscreen import EggSelectPanel
    from tuipet.tournamentscreen import TournamentPanel
    from tuipet.optionsscreen import KeysPanel
    from tuipet.feedscreen import FeedPanel
    from tuipet.assistscreen import AssistPanel
    from tuipet.themescreen import ThemePanel
    from tuipet.bugscreen import BugReportPanel
    from tuipet.helpscreen import HelpPanel
    from tuipet.dnascreen import DNAPanel

    p = _pet()
    for mode in ("shop", "bag"):
        assert "ENTER" in _ok(ShopPanel(p, mode).strip(), f"shop:{mode}")
    egg = EggSelectPanel()
    assert "pick" in _ok(egg.strip(), "eggselect")
    tp = TournamentPanel(p)
    assert "enter cup" in _ok(tp.strip(), "cup:select")
    tp.phase = "bracket"
    assert "bracket" in _ok(tp.strip(), "cup:bracket")
    assert "scroll" in _ok(KeysPanel([("f", "feed", "Feed")]).strip(), "keys")
    _ok(FeedPanel(p).strip(), "feed")
    assert "helper" in _ok(AssistPanel(p).strip(), "assist")
    assert "preview" in _ok(ThemePanel().strip(), "theme")
    assert "dev" in _ok(BugReportPanel(p).strip(), "bug")
    _ok(HelpPanel(p).strip(), "help")
    dna = DNAPanel(p)
    for ph in ("home", "charge", "stats", "reqs", "roads", "bet"):
        dna.phase = ph
        _ok(dna.strip(), f"dna:{ph}")
    dna.phase = "mash"
    assert "SPACE" in _ok(dna.strip(), "dna:mash")


def test_options_strip_covers_menu_and_confirm():
    from tuipet.optionsscreen import OptionsPanel
    p = _pet()
    op = OptionsPanel(p, lambda: True, lambda: None)
    assert "pick" in _ok(op.strip(), "options")
    op.confirm = True
    assert "erase" in _ok(op.strip(), "options:confirm")


def test_battle_strip_follows_the_fight():
    from tuipet.battlescreen import BattlePanel
    from tuipet import data
    _, by = data.load_sprites()
    foe = next(n for n, r in by.items()
               if r["stage"] == "Champion" and not data.is_placeholder(n))
    bp = BattlePanel(_pet(), enemy={"num": foe, "name": by[foe]["name"],
                                    "stage": "Champion", "vaccine": 30,
                                    "data_power": 30, "virus": 30, "hp": 10})
    assert "skip" in _ok(bp.strip(), "battle:intro")
    bp.phase = "menu"
    assert "attack" in _ok(bp.strip(), "battle:menu")
    bp.phase = "surrender_ask"
    assert "allow" in _ok(bp.strip(), "battle:surrender")
    bp.phase = "anim"
    assert bp.strip() == ""                    # the round plays clean
    bp.phase = "result"
    assert "done" in _ok(bp.strip(), "battle:result")


def test_lobby_strip_is_fully_contextual():
    from tuipet.net import LobbyState
    from tuipet import lobbyscreen

    class _Stub:
        def __init__(self, state): self.state = state
        def respond(self, *a, **k): pass
        def relay(self, *a, **k): pass
        def update_pet(self, *a, **k): pass

    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}, "live": True},
                {"id": 2, "name": "mika", "pet": {}, "live": True}]
    pan = lobbyscreen.LobbyPanel(_pet(), lambda n, pw, c: _Stub(s),
                                 name="joel", pw="x")
    assert "fold" in _ok(pan.strip(), "lobby:open")
    pan.rost_hidden = True
    assert "players" in _ok(pan.strip(), "lobby:folded")
    pan.rost_hidden = False
    s.unread.add("mika")                       # a fresh ✉ pops its nudge first
    assert "✉ mika" in _ok(pan.strip(), "lobby:unread")
    s.unread.clear()
    pan.action_for = (2, "mika", True)
    assert "battle" in _ok(pan.strip(), "lobby:action")
    pan.action_for = (2, "mika", False)
    assert "ping" in _ok(pan.strip(), "lobby:ghost")
    pan.action_for = None
    pan.pm_to = (2, "mika")
    assert "send" in _ok(pan.strip(), "lobby:pm")
    pan.pm_to = None
    pan.invite_prompt = {"from_id": 2, "from_name": "mika", "kind": "battle"}
    assert "accept" in _ok(pan.strip(), "lobby:invite")
    pan.invite_prompt = None
    pan.phase = "dm"
    assert "saved" in _ok(pan.strip(), "lobby:dm")
    pan.phase = "login"
    assert "TAB" in _ok(pan.strip(), "lobby:login")
