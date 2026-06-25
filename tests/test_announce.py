"""The HUD care-need announcement (the alarm's on-screen half).

When the pet has an unmet need (hungry/sick/dirty/exhausted/misbehaving) the box
under the LCD announces it, in sync with the alarm beep. It yields to a fresh
action flash for a few seconds, then re-asserts, and clears once the need is met.
Persistence is sandboxed by the autouse isolate_save fixture.
"""
import asyncio

from tuipet import persistence, data
from tuipet.pet import Pet
from tuipet.app import TuiPetApp


def test_need_message_priority_and_text():
    p = Pet(num=-1, stage="Rookie", name="Pico", hunger=4, energy=10)
    app = TuiPetApp(pet=p)                         # __init__ only; no mount needed
    assert app._need_message(p) == ""             # no need -> nothing to announce
    p.hunger = 0
    assert "hungry" in app._need_message(p)
    p.sick = True
    assert "sick" in app._need_message(p)         # sick outranks hunger
    p.sick = False
    p.hunger = 4
    p.poop = 4
    assert "cleaning" in app._need_message(p)
    p.poop = 0
    p.energy = 0
    assert "exhausted" in app._need_message(p)
    p.energy = 10
    p.scold_flag = True
    assert "misbehaving" in app._need_message(p)
    # the pet's name appears in the announcement
    p.hunger = 0
    assert "Pico" in app._need_message(p)


def _hungry_rookie():
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["stage"] == "Rookie" and not data.is_placeholder(n)), None)
    if num is None:
        return None
    p = Pet.from_num(num)
    p.name = "Pico"
    p.hunger = 0          # hungry
    p.energy = 24         # awake, not exhausted
    p.world_seconds = 0   # daytime -> stays awake
    return p


def test_hud_announces_yields_and_clears():
    pet = _hungry_rookie()
    if pet is None:
        import pytest
        pytest.skip("sprite assets not installed")
    persistence.set_account("Tester", "x")

    async def go():
        app = TuiPetApp(pet=pet)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")            # dismiss title -> main view
            await pilot.pause()
            assert app.mode is None

            app.on_tick()                          # need announced
            announced = str(app.msg_w.render())

            app.flash("FRESH-ACTION")              # a fresh action result holds
            app.on_tick()
            held = str(app.msg_w.render())

            for _ in range(app.FLASH_HOLD + 1):    # ...then the need re-asserts
                app.on_tick()
            reasserted = str(app.msg_w.render())

            pet.hunger = 4                          # fed: the need is now met
            app.on_tick()
            cleared = str(app.msg_w.render())
            return announced, held, reasserted, cleared

    announced, held, reasserted, cleared = asyncio.run(go())
    assert "hungry" in announced
    assert "FRESH-ACTION" in held, "a fresh flash must hold over the care-need"
    assert "hungry" in reasserted, "the need re-asserts after the flash hold"
    assert "hungry" not in cleared and cleared.strip() == "", "met need clears the box"
