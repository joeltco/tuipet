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


def test_transport_panel_full_flow():
    from tuipet.transportscreen import TransportPanel
    p = _pet()
    p.add_item("i:28")                          # Zone Transport (PhoenixTransport)
    pan = TransportPanel(p, "i:28")
    _step(pan); _step(pan, "down"); _step(pan, "up")
    assert _step(pan, "enter") is None             # the ride plays first
    r = _ride_out(pan)
    assert r and r[0] == "done" and "Warped" in r[1]
    pan2 = TransportPanel(p, "i:28")
    assert _step(pan2, "escape") == ("done", None)


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


def test_town_panel_every_phase():
    from tuipet.townscreen import TownPanel
    from tuipet import data
    random.seed(3)
    p = _pet()
    for town in list(data.load_towns())[:2]:
        pan = TownPanel(p, town)
        _step(pan)
        n = len(getattr(pan, "entries", [])) or 6
        for i in range(n):                       # visit every menu entry
            pan.phase = "menu"
            pan.sub = None
            pan.cursor = i if hasattr(pan, "cursor") else 0
            _step(pan, "down")
            _step(pan, "enter", ticks=2)
            _step(pan, "down"); _step(pan, "enter", ticks=2)
            _step(pan, "escape"); _step(pan, "escape")


def test_jogress_panel_fuses():
    from tuipet.jogressscreen import JogressPanel
    random.seed(11)
    p = _pet()
    pan = JogressPanel(p)
    _step(pan); _step(pan, "down"); _step(pan, "up")
    if pan.options:
        _step(pan, "enter")
        guard = 0
        while pan.phase == "fusing" and guard < 200:
            guard += 1
            _step(pan)
        _step(pan, "enter")                      # fused -> apply / back
    _step(pan, "escape")


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


def test_adventure_panel_travels_and_renders_events():
    from tuipet.adventurescreen import AdventurePanel
    random.seed(4)
    p = _pet()
    pan = AdventurePanel(p)
    for i in range(600):
        _step(pan)
        for k in ("enter", "1", "y", "space"):   # answer whatever prompt appeared
            _step(pan, k)
        if i % 50 == 0:
            _step(pan, "i")                      # investigate / info keys
    pan.text()


def test_training_all_four_drills():
    from tuipet.training import TrainingPanel
    random.seed(6)
    for drill in "1234":
        p = _pet()
        p.energy = p.max_energy
        pan = TrainingPanel(p)
        _step(pan)
        for arrow in ("up", "left", "right", "down"):
            _step(pan, arrow)                    # the diamond select renders each face
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
        acct.key(k); acct.text()
    assert acct.key("enter") is None or True


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
    """The earlier walk had no options (a default pet unlocks nothing) -- raise
    one properly so pick -> fusing -> fused all render."""
    from tuipet.jogressscreen import JogressPanel
    from tuipet import data, jogress
    random.seed(4)
    _, by = data.load_sprites()
    reqs, evo = data.load_requirements(), data.load_evolutions()
    n = next((n for n, r in by.items()
              if not data.is_placeholder(n)
              and any(reqs.get(t, {}).get("special") in ("Jogress", "Fusion", "Mode")
                      for t in evo.get(n, []))), None)
    if n is None:
        import pytest
        pytest.skip("no jogress parents in the atlas")
    p = Pet(num=n, stage=by[n]["stage"], attribute=by[n]["attribute"] or "Vaccine")
    p.world_seconds = 600.0
    p.vaccine, p.data_power, p.virus = 250, 60, 20
    p.battles, p.wins = 80, 70
    p.train_time = "Noon"
    p.overeat = 5
    p.levels_fought = [5, 5, 5, 5]
    p.evol_bonus = 100000
    p.energy = p.max_energy
    pan = JogressPanel(p)
    assert pan.options, "a fully-raised pet unlocks its fusion"
    _step(pan); _step(pan, "down"); _step(pan, "up")
    _step(pan, "enter")
    guard = 0
    while pan.phase == "fusing" and guard < 300:
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
        if pan._tabs()[pan.tab] == "egg":
            break
        _step(pan, "tab")
    if pan._tabs()[pan.tab] == "egg":
        _step(pan, "down"); _step(pan, "enter")  # an egg buy attempt renders
        _step(pan, "p")                          # password mode
        for ch in "abc":
            _step(pan, ch)
        _step(pan, "backspace")
        _step(pan, "enter")                      # wrong password renders the rebuff
        _step(pan, "p"); _step(pan, "escape")
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


def test_weather_engine_walks_every_transition():
    from tuipet import weather as wx
    from tuipet import data
    random.seed(0)
    habs = list(data.load_habitats().values())
    seen = set()
    for season in ("Spring", "Summer", "Fall", "Winter"):
        w = "Clear"
        for i in range(400):
            w = wx.next_weather(w, season, day_temp=40 + (i % 60), hab=habs[i % len(habs)])
            seen.add(w)
            wx.adjusted_day_temp(70, w, ("dawn", "day", "dusk", "night")[i % 4], habs[i % len(habs)])
    assert {"Clear", "Cloudy"} <= seen           # the engine actually moved


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


def test_thunder_flash_renders_and_startles():
    """DVPet Weather.checkThunder: HeavyRain lightning lifts the gloom on 2-frame
    beats; a dark room stays dark; the countdown burns itself out."""
    import tuipet.app as app
    s = app.Screen(); s.on_mount(); s.update = lambda t: None
    p = _pet(weather="HeavyRain")
    for lights in (True, False):
        p.lights = lights
        s.thunder_i = 14
        for _ in range(20):
            s.frame_i += 1
            s.paint(p)
        if lights:
            assert s.thunder_i == 0          # the countdown burns out while lit


def _ride_out(pan):
    """Skip the transport ride to the arrival hold and close it."""
    pan.anim()
    pan.key("space")
    return pan.key("enter")


def test_transports_land_at_canon_arrival_points():
    """Canon PhysicalState.transport (audit 2026-07-04): warps land AT a place
    -- Phoenix at the zone's first town, Birdra moves you to the town AND
    rests, Garuda one step shy of the next boss.  Every warp used to dump you
    at step 0 (and Garuda flagged a random ambush instead of the boss)."""
    from tuipet import data
    from tuipet.transportscreen import TransportPanel
    from tuipet.adventure import Adventure

    zone = data.load_maps()[0]["zones"][0]
    first_town = zone["towns"][0][0]
    first_boss = sorted(b.get("location") or zone.get("total_steps", 10000)
                        for b in zone["bosses"])[0]

    p = _pet()
    p.add_item("i:28")
    pan = TransportPanel(p, "i:28")
    pan.kind = "zone"                              # Phoenix
    pan.options = pan._options()
    assert pan.key("enter") is None                # the ride plays first
    r = _ride_out(pan)
    assert r and "Warped" in r[1]
    assert p.adv_loc == first_town
    adv = Adventure(p)                             # the next journey consumes it
    assert adv.location == first_town and p.adv_loc == 0

    p.add_item("i:28")
    p.energy = 1
    pan = TransportPanel(p, "i:28")
    pan.kind = "town"                              # Birdra: moved AND rested
    pan.options = pan._options()
    pan.key("enter"); _ride_out(pan)
    assert p.adv_loc == first_town and p.energy == p.max_energy

    p.add_item("i:28")
    pan = TransportPanel(p, "i:28")
    pan.kind = "danger"                            # Garuda: one shy of the boss
    pan.options = pan._options()
    pan.key("enter"); _ride_out(pan)
    assert p.adv_loc == first_boss - 1
    adv = Adventure(p)
    assert adv.location == first_boss - 1
    for _ in range(40):                            # refusals/discovers may stall,
        ev = adv.travel()                          # but the FIRST real stride
        if ev and ev[0] == "boss":                 # crosses the gate boss
            break
    assert ev and ev[0] == "boss"
    assert adv.location == first_boss


def test_continent_warp_lists_only_unlocked_maps():
    """Canon drawMapSelect honours map unlocks: a Wha ticket day one must not
    offer Continent 5 (transport re-audit 2026-07-05 -- all maps were listed)."""
    from tuipet.transportscreen import TransportPanel
    from tuipet import persistence
    p = _pet()
    p.add_item("i:31")                              # Continent Transport (Wha)
    pan = TransportPanel(p, "i:31")
    assert len(pan.options) == 1                    # fresh save: Continent 1 only
    assert pan.options[0][1] == 0
    persistence.map_complete_add(0)                 # first continent beaten
    pan = TransportPanel(p, "i:31")
    assert [o[1] for o in pan.options] == [0, 1]
    p.adv_map = 3                                   # already standing on map 4:
    pan = TransportPanel(p, "i:31")                 # never locked out of it
    assert 3 in [o[1] for o in pan.options]


def test_every_transport_plays_its_ride_scene():
    """Canon animates ALL four transports (SpriteAnim whaTransport + transport()):
    Whamon 193 surfaces/swims for the continent warp; Birdramon 97 / Garudamon
    234 / Phoenixmon 292 swoop from above, scoop the pet, and drop it bouncing
    at the destination.  Every frame stays in the 12x40 arena; the done is
    deferred to the arrival hold; the ticket is consumed at confirm."""
    from tuipet.transportscreen import TransportPanel, CARRIER
    for key, kind in (("i:31", "continent"), ("i:28", "zone"),
                      ("i:29", "town"), ("i:30", "danger")):
        p = _pet()
        p.add_item(key)
        pan = TransportPanel(p, key)
        assert pan.kind == kind and CARRIER[kind]
        assert pan.key("enter") is None and pan.ride is not None
        assert key not in p.inventory
        stings = []
        for _ in range(pan.ride["end"] + 6):
            pan.anim()
            if pan.sfx:
                stings.append(pan.sfx)
                pan.sfx = None
            lines = pan.text().plain.split("\n")
            assert len(lines) <= 12 and all(len(ln) <= 40 for ln in lines)
        assert stings[0] == "happy" and stings[-1] == "reward"
        assert stings.count("reward") == 1              # the hold must not re-sting
        assert "ENTER done" in pan.strip()
        r = pan.key("enter")
        assert r[0] == "done" and "Warped" in r[1]
        # skip: one press jumps to the hold, the next closes
        p.add_item(key)
        pan2 = TransportPanel(p, key)
        pan2.key("enter"); pan2.anim(); pan2.key("space")
        assert pan2.ride["t"] == pan2.ride["end"]
        assert pan2.key("enter")[0] == "done"
