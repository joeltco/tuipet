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
