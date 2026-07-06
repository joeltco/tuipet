"""A dead pet can DO nothing — every home-screen care binding leads back to
the memorial; only quit and options stay live beside the grave.

Joel 2026-07-05: a dead mon could still ADVENTURE — action_adventure never
checked dead, and the per-action can_*() gates kept slipping one at a time
(feed had the dead leg, adventure/play/clean/heal/gift/lights didn't).  The
fix is ONE on_key chokepoint ahead of every global binding, and this test
walks the WHOLE bindings table so a new action can never ship ungated.
"""
import asyncio

from tuipet.app import TuiPetApp
from tuipet.pet import Pet


def _dead_pet():
    p = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    p.dead = True
    return p


def test_every_binding_leads_a_dead_pet_to_the_memorial():
    async def go():
        app = TuiPetApp(pet=_dead_pet())
        results = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")            # dismiss the title
            await pilot.pause()
            for key, action, _label in TuiPetApp.BINDINGS:
                if action in ("quit", "options"):
                    continue                       # the two keys that stay live
                app.mode = None                   # back to the dead home screen
                await pilot.press(key)
                await pilot.pause()
                results[action] = type(app.mode).__name__
            # options stays reachable beside the grave
            app.mode = None
            await pilot.press("g")
            await pilot.pause()
            results["_options_open"] = type(app.mode).__name__
        return results

    results = asyncio.run(go())
    opened = results.pop("_options_open")
    escaped = {a: m for a, m in results.items() if m != "DeathPanel"}
    assert not escaped, f"these actions escaped the grave: {escaped}"
    assert opened == "OptionsPanel", "options must stay live at the memorial"


def _egg_app():
    from tuipet.pet import Pet
    return TuiPetApp(pet=Pet.new_egg())


def test_every_binding_on_an_egg_opens_or_explains():
    """Egg-stage action audit (2026-07-05): pressing HABITAT with an egg
    CRASHED the app (num -1 has no roster sheet; grid.width(None)).  Walk the
    whole bindings table on an egg: every action must either open a browse
    panel or flash a reason -- no crashes, no silent dead keys (gift excepted:
    a no-gift ENTER is a no-op for every stage)."""
    async def go():
        app = _egg_app()
        flashes = []
        results = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause(0.3)
            await pilot.press("enter")            # past the title
            await pilot.pause(0.3)
            app.mode = None
            real_flash = app.flash
            app.flash = lambda m: (flashes.append(m), real_flash(m))
            for key, action, _label in TuiPetApp.BINDINGS:
                if action in ("quit", "options", "lobby", "gift"):
                    continue
                app.mode = None
                app.screen_w.fx = None
                flashes.clear()
                await pilot.press(key)
                await pilot.pause(0.05)
                results[action] = (type(app.mode).__name__ if app.mode else None,
                                   next((f for f in flashes if str(f).strip()), None))
        return results

    results = asyncio.run(go())
    dead = {a: r for a, r in results.items() if r[0] is None and r[1] is None}
    assert not dead, f"silent dead keys on an egg: {dead}"
    # the browse screens stay open per canon (enableMainMenu has no stage gate)
    for browse in ("shop", "inventory", "habitat", "digicore", "assist"):
        assert results[browse][0] is not None, f"{browse} should open for an egg"


def test_habitat_browser_renders_the_egg():
    """The direct crash pin: the preview scene draws the egg's shell art."""
    from tuipet.pet import Pet
    from tuipet.habitatscreen import HabitatPanel
    pan = HabitatPanel(Pet.new_egg())
    for _ in range(3):
        pan.text()                                # crashed before the fix
        pan.key("down")
    assert pan.text().plain.count("\n") == 11     # the 12-row scene renders


def test_training_panel_survives_a_direct_egg():
    """Egg-training audit (2026-07-06): can_train gates the ONE entry path
    ('It is still an egg.'), but TrainingPanel(egg).text() crashed on a raw
    [pet.num] sheet lookup -- the habitat-crash pattern.  Walk every drill
    phase with an egg so a future entry path can never ship a crash."""
    import random
    from tuipet.pet import Pet
    from tuipet.training import TrainingPanel
    random.seed(3)
    egg = Pet.new_egg()
    assert egg.can_train()                        # the gate itself still holds
    pan = TrainingPanel(egg)
    for k in ("", "down", "enter", "space", "space", "1", "space", "escape"):
        if k:
            pan.key(k)
        for _ in range(12):
            pan.anim()
        pan.text()                                # crashed before the fix


def test_battle_panel_survives_a_direct_egg():
    """Egg-battle audit (2026-07-06): can_battle gates the key, but the
    lobby PvP replay constructed BattlePanel with the pet directly and its
    raw [num] sheet lookup crashed on an egg -- walk every phase."""
    import random
    from tuipet.pet import Pet
    from tuipet.battlescreen import BattlePanel
    random.seed(3)
    egg = Pet.new_egg()
    assert egg.can_battle()
    pan = BattlePanel(egg)
    for k in ("", "enter", "1", "space", "space", "escape"):
        if k:
            pan.key(k)
        for _ in range(15):
            pan.anim()
        pan.text()                                # crashed before the fix


def test_no_raw_sprite_sheet_indexing_survives():
    """The egg-crash pattern was ALWAYS the same line: a raw
    `load_sprites()[1][num]` index with no entry for the egg's -1 (habitat,
    training, battle, adventure, transport -- five shipped instances).
    data.frames_for/bob_frame own safe access now; the raw index is BANNED
    outside data.py (egg sweep 2026-07-06)."""
    import glob, os
    root = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet")
    hits = []
    for fn in glob.glob(os.path.join(root, "*.py")):
        if fn.endswith("data.py"):
            continue
        for n, line in enumerate(open(fn), 1):
            if "load_sprites()[1][" in line:
                hits.append(f"{os.path.basename(fn)}:{n}")
    assert not hits, f"raw sheet indexing (egg-crash pattern): {hits}"


def test_remaining_panels_survive_a_direct_egg():
    """Direct-construct sweep with forced deep phases (the gates normally
    block these, but gates move): adventure travel, the transport ride, the
    DNA mash, the jogress fuse scene."""
    import random
    from tuipet.pet import Pet
    from tuipet.dnascreen import DNAPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.transportscreen import TransportPanel

    def egg():
        e = Pet.new_egg()
        e.world_seconds = 10 * 60.0
        return e

    random.seed(3)
    for pan, keys, ticks in (
            (AdventurePanel(egg()), ("enter", "space", "escape"), 30),
            (TransportPanel(egg(), "i:28"), ("space", "enter"), 20),
            (DNAPanel(egg()), ("space", "space"), 12),
            (JogressPanel(egg()), ("space",), 40)):
        if isinstance(pan, DNAPanel):
            pan.phase, pan.bet = "mash", 10
        if isinstance(pan, JogressPanel):
            pan.phase, pan.old_num, pan.partner_num = "fusing", -1, -1
            pan.fused = {"num": -1}
            pan.fuse_step = 0
        for k in ("",) + keys:
            if k:
                pan.key(k)
            for _ in range(ticks):
                pan.anim()
            pan.text()


def _dead():
    from tuipet.pet import Pet
    p = Pet(num=4, stage="Rookie", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    p.dead = True
    return p


def test_every_entry_gate_has_the_dead_leg():
    """Dead sweep (2026-07-06): jogress.can_jogress and tournament.can_enter
    had NO dead leg -- a full-DP corpse passed the jogress gate (which also
    drives the lobby invite auto-decline).  Every entry gate must rest."""
    from tuipet import jogress, tournament
    d = _dead()
    d.dp = 4
    for gate in (d.can_feed, d.can_train, d.can_battle, d.can_charge_dna,
                 lambda: jogress.can_jogress(d), lambda: tournament.can_enter(d)):
        assert "rests now" in (gate() or ""), gate


def test_offline_catchup_never_decays_a_corpse():
    """Loading a dead save after hours away starved/soiled the corpse and
    greeted 'Your pet needs care!' over the grave (dead sweep 2026-07-06)."""
    import time
    from tuipet import persistence, data
    d = _dead()
    d.name = data.load_sprites()[1][4]["name"]     # dex-true: no repair path
    save = persistence.to_save_dict(d)
    save["_saved_at"] = time.time() - 4 * 3600
    pet, msg = persistence.pet_from_save(save)
    assert pet.dead
    assert (pet.hunger, pet.poop, pet.care_mistakes, pet.mood) == (
        d.hunger, d.poop, d.care_mistakes, d.mood), "the departed do not decay"
    assert "needs care" not in msg


def test_every_panel_survives_a_direct_corpse():
    """The egg sweep's direct-construct pattern, dead edition: walk every
    panel with a dead pet (gates move; panels grow new callers)."""
    import random
    from tuipet.feedscreen import FeedPanel
    from tuipet.shopscreen import ShopPanel
    from tuipet.training import TrainingPanel
    from tuipet.battlescreen import BattlePanel
    from tuipet.dnascreen import DNAPanel
    from tuipet.jogressscreen import JogressPanel
    from tuipet.tournamentscreen import TournamentPanel
    from tuipet.townscreen import TownPanel
    from tuipet.adventurescreen import AdventurePanel
    from tuipet.transportscreen import TransportPanel
    from tuipet.habitatscreen import HabitatPanel
    from tuipet.digicorescreen import DigiCorePanel
    random.seed(3)
    walks = (
        (FeedPanel(_dead()), ("down", "enter", "escape"), 12),
        (ShopPanel(_dead()), ("right", "enter", "tab", "enter", "r"), 12),
        (TrainingPanel(_dead()), ("down", "enter", "space", "1", "escape"), 12),
        (BattlePanel(_dead()), ("enter", "1", "space", "escape"), 15),
        (DNAPanel(_dead()), ("space", "space"), 12),
        (JogressPanel(_dead()), ("space",), 40),
        (TournamentPanel(_dead()), ("down", "enter", "escape"), 12),
        (TownPanel(_dead(), 0), ("enter", "down", "enter", "escape"), 12),
        (AdventurePanel(_dead()), ("enter", "space", "escape"), 30),
        (TransportPanel(_dead(), "i:28"), ("space", "enter"), 20),
        (HabitatPanel(_dead()), ("down", "escape"), 12),
        (DigiCorePanel(_dead()), ("space", "right", "down", "enter", "escape"), 12),
    )
    for pan, keys, ticks in walks:
        if isinstance(pan, DNAPanel):
            pan.phase, pan.bet = "mash", 10
        for k in ("",) + keys:
            if k:
                pan.key(k)
            for _ in range(ticks):
                if hasattr(pan, "anim"):
                    pan.anim()
            pan.text()
