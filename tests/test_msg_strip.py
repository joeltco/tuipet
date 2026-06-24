"""The message strip clears when a sub-screen opens (Workstream C / QoL).

Closing a screen flashes its farewell into the #msg strip; opening the next screen
used to leave that there, so e.g. "Pick a home." lingered on the Cup screen. Now
_open_mode clears the strip (each sub-screen carries its own note inside the LCD).
Driven through a real Textual pilot. Persistence is sandboxed by the autouse
isolate_save fixture; an account is preset so the first-launch panel is skipped.
"""
import asyncio

from tuipet import persistence, data
from tuipet.pet import Pet
from tuipet.app import TuiPetApp


def _rookie():
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["stage"] == "Rookie" and not data.is_placeholder(n)), None)
    return Pet.from_num(num) if num is not None else None


def test_opening_a_mode_clears_the_message_strip():
    pet = _rookie()
    if pet is None:
        import pytest
        pytest.skip("sprite assets not installed")
    persistence.set_account("Tester", "x")        # skip the first-launch account panel

    async def go():
        app = TuiPetApp(pet=pet)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")            # dismiss title -> main view
            await pilot.pause()
            app.flash("STALE-MESSAGE")
            assert "STALE-MESSAGE" in str(app.msg_w.render())
            app.action_habitat()                  # open a sub-screen
            await pilot.pause()
            return str(app.msg_w.render())

    cleared = asyncio.run(go())
    assert "STALE-MESSAGE" not in cleared, "a stale flash must not survive into a sub-screen"
