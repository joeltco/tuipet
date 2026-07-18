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
    assert "feat." in _ok(tp.strip(), "cup:select")
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


def test_the_remaining_screens_strips_fit_too():
    """The 8 panels the sweep above missed (tidy sweep 2026-07-18) — every
    strip in the app now holds the 40-col never-marquee budget."""
    from tuipet.training import TrainingPanel
    from tuipet.digicorescreen import DigiCorePanel
    from tuipet.eggguidescreen import EggGuidePanel
    from tuipet.backgroundscreen import BackgroundPanel
    from tuipet.raidscreen import RaidPanel
    from tuipet.deathscreen import DeathPanel
    from tuipet.titlescreen import TitlePanel
    from tuipet.accountscreen import AccountPanel

    p = _pet()
    assert "strike" in _ok(TrainingPanel(p).strip(), "training")
    assert "gaze" in _ok(DigiCorePanel(p).strip(), "digicore")
    guide = EggGuidePanel(p)
    assert "browse" in _ok(guide.strip(), "eggguide:list")
    guide.detail = True
    assert "back" in _ok(guide.strip(), "eggguide:detail")
    _ok(BackgroundPanel(p).strip(), "scenes")
    raid = RaidPanel(p, lambda name, pw, card: object())
    assert "raid" in _ok(raid.strip(), "raid")
    assert "egg" in _ok(DeathPanel(p).strip(), "death")
    title = TitlePanel()
    title.frame_i = 999                       # past the power-on hush
    assert "ENTER" in _ok(title.strip(), "title")
    assert "switch" in _ok(AccountPanel().strip(), "account")


def test_the_egg_tease_marquees_instead_of_clipping():
    """menu.footer clips at 38 cols; the unlock tease is DATA (eggUnlock
    descs run to 45 cols) so it rides footer_note and scrolls through whole
    within one TEASE_BEAT leg (tidy sweep 2026-07-18: 32/46 hints used to
    clip mid-word, losing the actual instruction)."""
    from tuipet import data
    from tuipet.eggselectscreen import EggSelectPanel, TEASE_BEAT

    descs = [r["desc"] for r in data.load_egg_unlock().values() if r.get("desc")]
    worst = max(descs, key=len)
    tail = worst.split()[-1]
    pan = EggSelectPanel()
    pan.hint, pan.locked, pan.msg = worst, 22, ""
    frames = []
    for f in range(TEASE_BEAT, 2 * TEASE_BEAT):        # one tease leg
        pan.frame_i = f
        frames.append(pan.text().plain.rstrip("\n").split("\n")[-1])
    assert any(tail in line for line in frames), f"tease tail {tail!r} never shown"


def test_options_strip_covers_menu_and_confirm():
    from tuipet.optionsscreen import OptionsPanel
    p = _pet()
    op = OptionsPanel(p, lambda: True, lambda: None)
    assert "pick" in _ok(op.strip(), "options")
    op.confirm = True
    assert "erase" in _ok(op.strip(), "options:confirm")


def test_battle_strip_follows_the_fight():
    """0.5 phases (2026-07-17): intro -> ready (the timing bar) -> anim
    (clean) -> result."""
    from tuipet.battlescreen import BattlePanel
    from tuipet import data
    _, by = data.load_sprites()
    foe = next(n for n, r in by.items()
               if r["stage"] == "Champion" and not data.is_placeholder(n))
    bp = BattlePanel(_pet(), enemy={"num": foe, "name": by[foe]["name"],
                                    "stage": "Champion"})
    assert "skip" in _ok(bp.strip(), "battle:intro")
    bp.phase = "ready"
    assert "lock" in _ok(bp.strip(), "battle:ready")
    bp.phase = "anim"
    assert bp.strip() == ""                    # the round plays clean
    bp.phase = "result"


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
