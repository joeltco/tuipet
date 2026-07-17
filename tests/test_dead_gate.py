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


def test_every_panel_survives_a_direct_sleeper():
    """Asleep sweep (2026-07-06): the sleeper edition of the direct-construct
    walk.  Poking a sleeper is a SYSTEM (the disturb mechanic: grumble-wake,
    mood hit, disturb count) -- these walks assert the panels merely render."""
    import random
    from tuipet.pet import Pet
    from tuipet.feedscreen import FeedPanel
    from tuipet.shopscreen import ShopPanel
    from tuipet.training import TrainingPanel
    from tuipet.battlescreen import BattlePanel
    from tuipet.habitatscreen import HabitatPanel
    from tuipet.digicorescreen import DigiCorePanel

    def sleeper():
        p = Pet(num=4, name="Rex", stage="Rookie", attribute="Vaccine")
        p.world_seconds = 2 * 60.0
        p.asleep, p.lights = True, False
        return p

    random.seed(3)
    for pan, keys in ((FeedPanel(sleeper()), ("down", "enter", "escape")),
                      (ShopPanel(sleeper()), ("right", "enter", "tab", "r")),
                      (TrainingPanel(sleeper()), ("down", "enter", "space", "escape")),
                      (BattlePanel(sleeper()), ("enter", "1", "space", "escape")),
                      (HabitatPanel(sleeper()), ("down", "escape")),
                      (DigiCorePanel(sleeper()), ("space", "right", "enter", "escape"))):
        for k in ("",) + keys:
            if k:
                pan.key(k)
            for _ in range(15):
                if hasattr(pan, "anim"):
                    pan.anim()
            pan.text()


def test_hatching_state_contracts():
    """Hatching sweep (2026-07-06): the ONE clean sweep -- no bugs found,
    so pin the load-bearing contracts.  `hatching` serializes but `_hatch_t`
    does not: a mid-crack save must SELF-HEAL on load (the timer restarts at
    3.0 and the egg still becomes a Fresh); offline catch-up must not decay
    it; every gate holds mid-crack; lights can't cancel the crack; death
    does (pet._die clears hatching)."""
    import time
    from tuipet.pet import Pet
    from tuipet import persistence

    e = Pet.new_egg()
    e.name = "Digitama"
    e.world_seconds = 10 * 60.0
    e.stage_seconds = e.EGG_DURATION + 1.0
    e.tick(1.0)                                   # the tick arms the crack
    assert e.hatching and getattr(e, "_hatch_t", 0) == 3.0
    e.advance_hatch(1.0)                          # mid-crack

    save = persistence.to_save_dict(e)
    assert save.get("hatching") is True and "_hatch_t" not in save
    save["_saved_at"] = time.time() - 3600        # an hour away, mid-crack
    pet, msg = persistence.pet_from_save(save)
    assert pet.hatching and pet.stage == "Egg"
    assert "needs care" not in (msg or "")        # eggs skip offline decay
    assert pet.can_feed() == "It is still an egg."
    assert pet.toggle_lights() == "It is still an egg." and pet.hatching
    hatched = False
    for _ in range(35):                           # the restarted 3s timer completes
        hatched = pet.advance_hatch(0.1)
        if hatched:
            break
    assert hatched and pet.stage == "Fresh" and pet.num >= 0
    d = Pet.new_egg()
    d.hatching = True
    d._die("test")
    assert not d.hatching                         # death cancels the crack


def test_mid_strobe_contracts():
    """Evolution mid-strobe audit (2026-07-06): the strobe is PRESENTATION
    over an already-evolved pet.  Pin the load-bearers: EVERY binding locks
    while an animation plays (canon disableMainMenu; Joel: "lock the browse
    menus during animations like canon" -- only q stays live); a mid-strobe
    save round-trips clean; the strobe resolves into the chained cheer;
    death REPLACES the ceremony with the dying flow (correct priority)."""
    import asyncio
    from tuipet import data, persistence
    from tuipet.pet import Pet
    from tuipet.app import TuiPetApp

    async def go():
        rec = data.load_sprites()[1][4]
        p = Pet(num=4, name=rec["name"], stage=rec["stage"], attribute="Vaccine")
        p.world_seconds = 10 * 60.0
        app = TuiPetApp(pet=p)
        out = {}
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause(0.3)
            await pilot.press("enter")
            await pilot.pause(0.2)
            app.mode = None
            app.screen_w.start_fx("evolve", old_num=4)
            await pilot.pause(0.2)
            persistence.save(app.pet)                    # mid-strobe save
            pet2, msg = persistence.load()
            out["save"] = (pet2.num, msg)
            opened = []
            for key, action, _label in TuiPetApp.BINDINGS:
                if action == "quit":
                    continue                              # q stays live
                await pilot.press(key)
                await pilot.pause(0.03)
                if app.mode is not None:
                    opened.append(action)
                    app.mode = None
            out["opened"] = opened                       # canon lock: nothing opens
            for _ in range(90):
                await pilot.pause(0.1)
                fx = app.screen_w.fx
                if fx is None or fx["kind"] != "evolve":
                    break
            out["resolved"] = app.screen_w.fx["kind"] if app.screen_w.fx else None
            # death interrupts a fresh ceremony
            app.screen_w.start_fx("evolve", old_num=4)
            app.pet.care_mistakes = 20                   # the neglect cap
            await pilot.pause(1.5)                       # one on_tick fires
            fx = app.screen_w.fx
            out["death"] = fx["kind"] if fx else None
        return out

    out = asyncio.run(go())
    assert out["save"] == (4, ""), out["save"]           # clean round-trip, no repair
    assert out["opened"] == [], f"menus escaped the anim lock: {out['opened']}"
    assert out["resolved"] == "cheer", out["resolved"]   # evolFinish -> the chained cheer
    assert out["death"] == "dying", out["death"]         # death outranks the ceremony
