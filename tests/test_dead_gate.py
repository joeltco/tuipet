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
