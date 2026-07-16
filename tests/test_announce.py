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
    p = Pet(num=-1, stage="Child", name="Pico", hunger=4, energy=10)
    app = TuiPetApp(pet=p)                         # __init__ only; no mount needed
    assert app._need_message(p) == ""             # no need -> nothing to announce
    p.hunger = 0
    assert "hungry" in app._need_message(p)
    p.sick = True
    assert "sick" in app._need_message(p)         # sick outranks hunger
    p.sick = False
    p.hunger = 4
    p.poop = 2
    assert "cleaning" in app._need_message(p)
    p.poop = 0
    p.strength = 0
    assert "strength" in app._need_message(p)
    # the pet's name appears in the announcement
    p.hunger = 0
    assert "Pico" in app._need_message(p)


def _hungry_rookie():
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["stage"] == "Child" and not data.is_placeholder(n)), None)
    if num is None:
        return None
    p = Pet.from_num(num)
    p.name = "Pico"
    p.hunger = 0          # hungry
    p.call_on = True      # the empty-meter call is ringing
    p.energy = 24         # awake, not exhausted
    p._hour = lambda: 12  # noon, pinned: run at 21:00+ and the Child's REAL
    #                       bedtime opened mid-test -- lights-on-asleep is a
    #                       second legit care need that nags forever (the
    #                       suite was time-of-day flaky; caught 2026-07-15)
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


def test_alarm_beeps_on_onset_then_nags_every_90s():
    """The alarm's SOUND half (sound/notification audit 2026-07-06): canon's
    `call` cue plays with the care-call animation -- ours rings once on the
    need's ONSET, nags every ~90s while it stands, and stops when it is met."""
    pet = _hungry_rookie()
    if pet is None:
        import pytest
        pytest.skip("sprite assets not installed")
    persistence.set_account("Tester", "x")
    pet._sicken = lambda *a, **k: None

    #                                    need would legitimately ring a fresh onset)

    async def go():
        app = TuiPetApp(pet=pet)
        rings = []
        app.beep = lambda name=None, bell=True: rings.append(name)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            rings.clear()                          # ignore any title-flow blips
            app.on_tick()                          # onset
            onset = rings.count("alarm")
            for _ in range(60):                    # inside the nag window: silent
                app.on_tick()
            mid = rings.count("alarm")
            for _ in range(40):                    # ...the ~90s nag lands
                app.on_tick()
            nagged = rings.count("alarm")
            pet.hunger = 4                          # fed
            for _ in range(120):
                pet.strength = 4                    # keep the OTHER meter topped:
                app.on_tick()                       # per-meter calls (audit
            done = rings.count("alarm")             # 2026-07-15) rightly ring for it
            return onset, mid, nagged, done

    onset, mid, nagged, done = asyncio.run(go())
    assert onset == 1                              # one ring at onset
    assert mid == 1                                # silent inside the window
    assert nagged == 2                             # the 90s nag repeats once
    assert done == 2                               # a met need stops the nagging


def test_the_lights_call_is_the_one_asleep_alarm():
    """Canon lightsCall fires ASLEEP (alive && asleep && lights) -- the one
    call a sleeper raises; awake calls include the effort gauge (strengthCall,
    which used to empty silently).  Sleep-screens audit 2026-07-06."""
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    p._hour = lambda: 23                          # bedtime, deterministic
    p.hunger, p.strength = 4, 2
    p.asleep, p.lights = True, True
    assert p.needs_attention()                   # a lit sleeper calls
    p.lights = False
    assert not p.needs_attention()               # dark: it sleeps in peace
    # awake at noon with an empty meter: the 20-minute call rings
    p._hour = lambda: 12
    p.asleep = False
    p.strength = 0
    p._sim_minute()
    assert p.call_on and p.needs_attention()     # the empty-meter call
    p.strength = 2
    p._sim_minute()
    assert not p.needs_attention()


