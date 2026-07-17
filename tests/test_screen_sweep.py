"""Deep render sweep: every screen path the unit tests never drew.

Coverage audit 2026-07 (after the bitmap_text NameError shipped): transport 17%,
tournament 21%, lobby 26%, town 29%, battlefx 31%, dna/jogress 42%, adventure/
battle 46%, training 59% -- their text()/anim() paths simply never ran.  Each
test here drives a REAL flow (seeded) and renders after every step.  Shallow on
purpose: the assertion is 'it draws in every phase'."""
import random

from tuipet.pet import Pet
from tuipet.net import LobbyState
from tuipet import lobbyscreen


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.bits = 9000
    p.sleep_limit = 9e9
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _step(pan, k=None, ticks=1):
    if k is not None:
        r = pan.key(k)
    else:
        r = None
    for _ in range(ticks):
        if hasattr(pan, "anim"):
            pan.anim()
    pan.text()
    return r


def test_tournament_panel_select_and_a_full_cup():
    from tuipet.tournamentscreen import TournamentPanel
    from tuipet import tournament
    random.seed(7)
    p = _pet()
    tournament.schedule(p)
    pan = TournamentPanel(p)
    _step(pan); _step(pan, "down"); _step(pan, "up")
    # walk the schedule and try to enter each cup; the first accepted entry
    # runs the bracket (fights render via the embedded battle sub)
    for _ in range(len(pan.sched) + 1):
        _step(pan, "enter")
        if pan.phase != "select":
            break
        _step(pan, "down")
    guard = 0
    while pan.phase != "select" and guard < 4000:
        guard += 1
        if getattr(pan, "sub", None) is not None:
            _step(pan, "space", ticks=2)         # skip strike volleys / advance fights
            _step(pan, "1")
            _step(pan, "enter")
        else:
            _step(pan, "enter", ticks=2)
    pan.text()


def test_jogress_panel_fuses():
    """The panel is the lobby's fusion cinematic now (the offline picker died
    with the home jogress, v0.2.348): construct at the fuse and walk the whole
    converge -> flash -> reveal."""
    from tuipet.jogressscreen import JogressPanel, FUSE_STEPS
    random.seed(11)
    p = _pet()
    pan = JogressPanel(p, p.num, 7, 4)
    guard = 0
    while pan.phase == "fusing" and guard < FUSE_STEPS + 5:
        guard += 1
        _step(pan)
    assert pan.phase == "fused"
    _step(pan, "enter")


def test_dna_panel_every_page():
    from tuipet.dnascreen import DNAPanel
    random.seed(5)
    p = _pet()
    for f in p.dna_owned:
        p.dna_owned[f] = 30
    from tuipet.dnascreen import _HOME
    pan = DNAPanel(p)
    for i in range(len(_HOME)):                  # open every home entry, render, back out
        pan.phase = "home"
        pan.home_i = i
        _step(pan, "enter", ticks=2)
        for k in ("down", "right", "1", "enter"):
            if pan.phase in ("mash",):
                break
            _step(pan, k)
        guard = 0
        while pan.phase in ("mash", "result") and guard < 300:
            guard += 1
            _step(pan, "space" if pan.phase == "mash" else "enter")
        _step(pan, "escape"); _step(pan, "escape")


def test_battle_panel_full_fight_and_forfeit():
    from tuipet.battlescreen import BattlePanel
    random.seed(2)
    p = _pet()
    pan = BattlePanel(p)
    guard = 0
    while pan.phase != "result" and guard < 3000:
        guard += 1
        if pan.phase == "menu":
            _step(pan, "1")
        elif pan.phase in ("anim", "strike"):
            _step(pan, "space", ticks=2)         # skip the volley, render each beat
        else:
            _step(pan, None, ticks=2)
    pan.text()
    _step(pan, "enter")
    # forfeit path (records the elimination)
    pan2 = BattlePanel(_pet())
    _step(pan2, None, ticks=8)
    _step(pan2, "escape", ticks=2)
    pan2.text()


def test_battle_surrender_ask_renders():
    from tuipet.battlescreen import BattlePanel
    random.seed(9)
    p = _pet(obedience=0, mood=-9000)            # a faltering pet asks to quit
    for attempt in range(30):
        pan = BattlePanel(p)
        guard = 0
        while pan.phase not in ("result",) and guard < 2000:
            guard += 1
            if pan.phase == "surrender_ask":
                pan.text()                       # THE page under audit
                _step(pan, "n")                  # fight on
            elif pan.phase == "menu":
                _step(pan, "1")
            else:
                _step(pan, "space", ticks=2)
        if guard < 2000:
            break


def test_training_all_four_drills():
    from tuipet.training import TrainingPanel
    random.seed(6)
    for drill in "1234":
        p = _pet()
        p.energy = p.max_energy
        pan = TrainingPanel(p)
        _step(pan)
        for arrow in ("up", "left", "right", "down"):
            _step(pan, arrow)                    # the cursor list renders every row
        _step(pan, drill)
        guard = 0
        while pan.phase != "done" and guard < 2000:
            guard += 1
            if pan.phase == "strike":
                _step(pan, "space", ticks=2)
            else:
                for k in ("space", "left", "right", "up", "down", "enter", "1"):
                    if pan.phase in ("done", "strike"):
                        break
                    _step(pan, k)
        pan.text()
        _step(pan, "enter")


def test_lobby_panel_every_phase_without_a_server():
    class _Stub:
        def __init__(self, state): self.state = state
        def respond(self, *a, **k): pass
        def relay(self, *a, **k): pass
        def update_pet(self, *a, **k): pass
        def chat(self, *a, **k): pass
        def invite(self, *a, **k): pass

    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.roster = [{"id": 1, "name": "joel", "pet": {}},
                {"id": 2, "name": "kai", "pet": {"name": "Agumon", "stage": "Champion", "num": 29}}]
    s.chat = [("kai", "yo"), ("", "kai joined")]
    p = _pet()
    pan = lobbyscreen.LobbyPanel(p, lambda n, pw, c: _Stub(s), name="joel", pw="x")
    _step(pan)
    _step(pan, "down"); _step(pan, "enter")                     # action menu renders
    pan.text()
    _step(pan, "escape")
    for ch in "hello":
        _step(pan, ch)
    _step(pan, "enter")                                         # chat send
    # inbound invite -> prompt -> accept -> jogress session phases
    s.inbox.append({"t": "invite", "from_id": 2, "from_name": "kai", "kind": "jogress"})
    _step(pan); pan.text()
    _step(pan, "y")                                             # waiting phase
    pan.text()
    pan._on_relay({"from_id": 2, "payload": {"kind": "jogress", "attr": "Vaccine", "num": 29, "name": "Agumon"}})
    pan.text()                                                  # result OR failed
    _step(pan, "escape"); _step(pan, "enter")
    if pan.phase != "lobby":
        pan._return_to_lobby()
    # battle session: host resolves a full round + the over screen
    pan._enter_session(2, "kai", "battle", host=True)
    pan.text()
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "t": "card",
                   "card": {"num": 29, "name": "Agumon", "stage": "Champion",
                            "vaccine": 5, "data_power": 5, "virus": 5, "hp": 8, "bits": (0, 0)}}})
    pan.text()
    guard = 0
    while pan.bphase not in ("over", None) and guard < 200:
        guard += 1
        if pan.bphase == "choose":
            _step(pan, "1")
            pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "t": "choice", "attr": "Virus"}})
        pan.text()
    pan.text()
    _step(pan, "enter")                                         # back to the lobby
    # abort / partner-left rendering
    pan._enter_session(2, "kai", "battle", host=True)
    pan._on_relay({"from_id": 2, "payload": {"kind": "battle", "abort": True}})
    pan.text()
    _step(pan, "enter")
    # login phase (AccountPanel typing)
    acct = lobbyscreen.AccountPanel(name="joel")
    acct.text()
    for k in ("tab", "s", "e", "c", "backspace", "space"):
        assert acct.key(k) is None                    # typing never closes the panel
        acct.text()
    acct.key("enter"); acct.text()                    # submit walks without crashing


def test_home_screen_paint_across_states():
    """Screen.paint (the DEFAULT idle view) was never rendered by a test --
    weather overlays, filth piles, sleep, dark room, the attention bubble."""
    import tuipet.app as app

    def S():
        s = app.Screen()                         # the REAL widget (unmounted)
        s.on_mount()                             # its attrs come from mount, not __init__
        s.update = lambda t: None                # ...and it never paints a terminal
        return s

    scenarios = [
        {},                                          # plain idle
        {"poop": 3, "poop_sizes": [2, 3, 1]},
        {"asleep": True, "lights": False},
        {"weather": "Raining"}, {"weather": "Snowing"}, {"weather": "Cloudy"},
        {"sick": True}, {"gift": "f:8"},
        {"world_seconds": 10.0},                     # night band
    ]
    for kw in scenarios:
        p = _pet(**kw)
        s = S()
        for i in range(12):
            s.frame_i = i
            s.paint(p)
    egg = Pet(num=-1, stage="Egg", attribute="None")
    egg.world_seconds = 600.0
    s = S()
    for i in range(6):
        s.frame_i = i
        s.paint(egg)


def test_jogress_panel_full_fuse():
    """A GENUINE roster fusion through the scene: a real jogress parent, a
    real partner sprite and the real fused form render every beat (the picker
    died with the home jogress, v0.2.348 -- the lobby resolves the match;
    this drives the cinematic it hands over)."""
    from tuipet.jogressscreen import JogressPanel, FUSE_STEPS
    from tuipet import data
    random.seed(4)
    _, by = data.load_sprites()
    reqs, evo = data.load_requirements(), data.load_evolutions()
    pair = next(((n, t) for n, r in by.items()
                 if not data.is_placeholder(n)
                 for t in evo.get(n, [])
                 if reqs.get(t, {}).get("special") in ("Jogress", "Fusion", "Mode")), None)
    if pair is None:
        import pytest
        pytest.skip("no jogress parents in the atlas")
    n, fused = pair
    p = Pet(num=n, stage=by[n]["stage"], attribute=by[n]["attribute"] or "Vaccine")
    p.world_seconds = 600.0
    pan = JogressPanel(p, n, n, fused)
    guard = 0
    while pan.phase == "fusing" and guard < FUSE_STEPS + 5:
        guard += 1
        _step(pan)
    assert pan.phase == "fused"
    pan.text()
    _step(pan, "enter")


def test_tournament_bracket_runs_when_eligible():
    from tuipet.tournamentscreen import TournamentPanel
    from tuipet import tournament
    random.seed(1)
    p = _pet()
    tournament.schedule(p)
    tr = tournament.open_now(p)
    assert tr is not None
    # dress for the door: satisfy exactly what eligibility() checks
    if tr.get("field_req"):
        p.field = tr["field_req"]
    if tr.get("attr_req"):
        p.attribute = tr["attr_req"]
    if tr.get("prelim"):
        p.trophies_won = {tr["prelim"]: p.season}
    p.fought_today = []
    err = tournament.eligibility(p, tr)
    assert not err, f"cup still not enterable: {err}"
    pan = TournamentPanel(p)
    pan.cursor = tournament._hour(p)
    _step(pan, "enter")
    assert pan.phase == "bracket"
    guard = 0
    while pan.phase != "select" and guard < 6000:
        guard += 1
        if getattr(pan, "sub", None) is not None:
            _step(pan, "space", ticks=2)
            _step(pan, "1")
            _step(pan, "enter")
        else:
            _step(pan, "enter", ticks=2)
    pan.text()


def test_shop_egg_tab_and_password_entry():
    from tuipet.shopscreen import ShopPanel
    p = _pet()
    pan = ShopPanel(p)
    for _ in range(8):                          # cycle to the egg tab
        from tuipet import shop as _shop
        if pan.tabs[pan.tab] == _shop.EGGS_CATEGORY:
            break
        _step(pan, "tab")
    from tuipet import shop as _shop
    if pan.tabs[pan.tab] == _shop.EGGS_CATEGORY:
        _step(pan, "down"); _step(pan, "enter")  # an egg buy attempt renders
    # (the shop's password door left with the old screen -- eggselect keeps
    # its own code entry, covered by test_eggselect_code_entry below)
    pan.text()


def test_eggselect_code_entry():
    from tuipet.eggselectscreen import EggSelectPanel
    pan = EggSelectPanel()
    _step(pan, "c")                              # secret-code mode
    for ch in "notacode":
        _step(pan, ch)
    _step(pan, "backspace")
    _step(pan, "enter")                          # bad code renders the rebuff
    _step(pan, "c"); _step(pan, "escape")
    pan.text()


def test_battlefx_across_varied_foes():
    """battlefx's effect branches key off each foe's attack conditions -- fight a
    spread of real enemies so the volley animations execute their variants."""
    from tuipet.battlescreen import BattlePanel
    from tuipet import battle as battle_mod
    random.seed(12)
    p = _pet()
    enemies = battle_mod.pick_enemy(p) and None  # warm the table
    from tuipet import data
    pool = [e for e in data.load_enemies() if e.get("stage") == "Champion"][:10]
    for e in pool:
        pan = BattlePanel(_pet(), enemy=dict(e))
        guard = 0
        while pan.phase != "result" and guard < 2500:
            guard += 1
            if pan.phase == "menu":
                _step(pan, str(1 + guard % 3))   # vary the attribute thrown
            else:
                _step(pan, "space", ticks=2)
        pan.text()


def test_battlefx_every_attack_effect_fires():
    """One fight per distinct attack effect in the atlas, played AS a species
    that carries it, throwing the attribute that carries it -- so checkEffect's
    branches (AttackUp/Counter/Leech/Heal/ForceOpp*/...) actually execute."""
    from tuipet.battlescreen import BattlePanel
    from tuipet import data
    random.seed(8)
    _, by = data.load_sprites()
    carriers = {}
    for n in by:
        if data.is_placeholder(n):
            continue
        for a in ("Vaccine", "Data", "Virus"):
            i = data.attack_info(n, a)
            if i["effect"] not in ("None", "") and i["effect"] not in carriers:
                carriers[i["effect"]] = (n, a)
    assert len(carriers) >= 10
    key = {"Vaccine": "1", "Data": "2", "Virus": "3"}
    for effect, (num, attr) in sorted(carriers.items()):
        p = Pet(num=num, stage=by[num]["stage"], attribute=by[num]["attribute"] or "Vaccine",
                obedience=500)
        p.world_seconds = 600.0
        p.sleep_limit = 9e9
        p.vaccine, p.data_power, p.virus = 40, 40, 40
        pan = BattlePanel(p, enemy={"num": 29, "name": "Agumon", "stage": by[num]["stage"],
                                    "vaccine": 6, "data_power": 6, "virus": 6,
                                    "hp": 10, "bits": (0, 0)})
        guard = 0
        while pan.phase != "result" and guard < 2500:
            guard += 1
            if pan.phase == "menu":
                _step(pan, key[attr])            # throw the effect-carrying move
            else:
                _step(pan, "space", ticks=2)
        pan.text()


def test_app_pilot_walks_every_binding():
    """The REAL Textual app, headless: every action binding opens and closes.
    This is the layer no panel test reaches -- action handlers, _open_mode /
    _close_mode, the HUD, on_frame ticking under a live screen."""
    import asyncio
    from tuipet.app import TuiPetApp

    async def scenario():
        p = _pet()
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause(0.3)                     # let on_frame/on_tick run
            walk = ("f", "escape", "p", "c", "h", "r", "k", "s", "s",
                    "e", "escape", "d", "escape", "v", "escape",
                    "i", "escape", "o", "escape", "g", "escape",
                    "t", "escape", "u", "escape", "x", "escape",
                    "j", "escape", "a", "escape", "l", "escape",
                    "n", "escape", "m", "enter",
                    "b", "escape", "escape")           # battle: forfeit out
            for k in walk:
                await pilot.press(k)
                await pilot.pause(0.04)
            await pilot.pause(0.3)                     # a few more life ticks

    asyncio.run(scenario())


def _ride_out(pan):
    """Skip the transport ride to the arrival hold and close it."""
    pan.anim()
    pan.key("space")
    return pan.key("enter")


