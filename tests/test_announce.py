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
    p = Pet(num=-1, stage="Rookie", name="Pico", hunger=4, energy=10,
            world_seconds=10 * 60.0)                    # mid-day: awake, calls announce
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
    # (the misbehaving announcement left with the discipline system)
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
    p.world_seconds = 10 * 60.0   # mid-day under the canon daylight bands -> stays awake
    return p


def test_hud_announces_yields_and_clears():
    pet = _hungry_rookie()
    if pet is None:
        import pytest
        pytest.skip("sprite assets not installed")
    persistence.set_account("Tester", "x")
    pet._sicken = lambda *a, **k: None   # deterministic: sick is the only need that
    # outranks hunger, so block random illness and the announced need stays "hungry"

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
    pet.obedience = 100                # exempt from discipline tantrums (a second
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
                app.on_tick()
            done = rings.count("alarm")
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
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=140)
    p.world_seconds = 10 * 60.0
    p.hunger, p.strength = 4, 2
    p.asleep, p.lights = True, True
    assert p.needs_attention()                   # a lit sleeper calls
    p.lights = False
    assert not p.needs_attention()               # dark: it sleeps in peace
    p.asleep = False
    p.strength = 0
    assert p.needs_attention()                   # strengthCall: effort empty
    p.strength = 2
    assert not p.needs_attention()


def test_frailty_warning_announces_before_the_elder_death():
    """Joel 2026-07-13 (MetalGreymon died of frailty with 8 unseen mistakes):
    an Ultimate/Mega at 3+ care mistakes warns in the message box, counting
    the slips left before the 5-mistake elder death."""
    from tuipet.pet import Pet
    import tuipet.app as appmod
    app = appmod.TuiPetApp.__new__(appmod.TuiPetApp)
    p = Pet(num=220, stage="Ultimate", obedience=500)
    p.world_seconds = 10 * 60.0
    p.care_mistakes = 2
    assert not p.is_frail()
    assert "frail" not in appmod.TuiPetApp._need_message(app, p)
    p.care_mistakes = 3
    assert p.is_frail()
    msg = appmod.TuiPetApp._need_message(app, p)
    assert "frail" in msg and "2 more slips" in msg
    p.care_mistakes = 4
    assert "1 more slip" in appmod.TuiPetApp._need_message(app, p)
    p.stage = "Champion"                      # only elders are frail
    assert not p.is_frail()


def test_frail_badge_rides_the_hud_deco():
    from tuipet.pet import Pet
    from tuipet.app import _care_deco
    p = Pet(num=220, stage="Ultimate", obedience=500)
    p.world_seconds = 10 * 60.0
    p.care_mistakes = 3
    assert any("frail" in d for d in _care_deco(p))
    p.care_mistakes = 0
    assert not any("frail" in d for d in _care_deco(p))


# --- gameplay polish #7 / #9 / #11 (2026-07-22) ------------------------------

def _quiet_champion():
    """No needs, awake, mid-day: the idle HUD slot is free."""
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.hunger, p.energy = 4, 24
    p.world_seconds = 10 * 60.0
    p._sicken = lambda *a, **k: None
    return p


def test_a_lone_pile_gets_the_quiet_tidy_nudge():
    """The care ALARM deliberately waits for 3 piles; a lone pile sat
    visible and un-asked-about for ~135 min.  The idle slot now answers
    -- text only, the 3-pile alarm keeps the escalation."""
    import asyncio
    from tuipet.app import TuiPetApp
    p = _quiet_champion()
    p.poop = 1

    async def go():
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            app.beeps = []
            app.beep = lambda name=None, bell=True: app.beeps.append(name)
            app.on_tick()
            nudged = str(app.msg_w.render())
            beeped = list(app.beeps)
            p.poop = 0                         # cleaned: the nudge clears
            app.on_tick()
            app.on_tick()
            cleared = str(app.msg_w.render())
            p.poop = 3                         # the real alarm outranks it
            app.on_tick()
            alarmed = str(app.msg_w.render())
            return nudged, beeped, cleared, alarmed

    nudged, beeped, cleared, alarmed = asyncio.run(go())
    assert "to clean" in nudged
    assert "alarm" not in beeped               # the nudge itself is silent
    assert "to clean" not in cleared
    assert "needs cleaning" in alarmed         # the 3-pile call is unchanged


def test_frailty_beeps_once_at_onset():
    """The one lethal care state was the only silent one.  Onset alarm
    only -- no key clears frailty, so no 90s re-nag."""
    import asyncio
    from tuipet.app import TuiPetApp
    p = _quiet_champion()
    p.stage = "Ultimate"

    async def go():
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            app.beeps = []
            app.beep = lambda name=None, bell=True: app.beeps.append(name)
            app.on_tick()
            before = app.beeps.count("alarm")
            p.care_mistakes = 3                # frailty begins
            app.on_tick()
            onset = app.beeps.count("alarm")
            for _ in range(120):               # two nag-windows later…
                app.on_tick()
            later = app.beeps.count("alarm")
            return before, onset, later

    before, onset, later = asyncio.run(go())
    assert before == 0 and onset == 1
    assert later == 1                          # …still just the one


def test_the_morning_tier_reaches_the_hud():
    """The wake roll can move mood a full tier with nothing but a 1.6s
    pose (petbody._wake).  The note now flashes; a DISTURBED wake keeps
    reporting the disturbance instead."""
    import asyncio
    from tuipet import petbody
    from tuipet.app import TuiPetApp

    # unit half: the roll writes the note, the disturb path clears it
    p = _quiet_champion()
    p.asleep, p.lights = True, False
    real = petbody.random.randrange
    petbody.random.randrange = lambda n: 0     # force BadMorning
    try:
        p._wake()
    finally:
        petbody.random.randrange = real
    assert "wrong side" in p.wake_note

    q = _quiet_champion()
    q.asleep, q.lights, q.energy = True, False, 1
    q._disturbed()
    assert getattr(q, "wake_note", "") == ""   # the grumble is the story

    # app half: the note flashes once and is consumed
    z = _quiet_champion()

    async def go():
        app = TuiPetApp(pet=z)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            z.wake_note = "Pico woke up beaming!"
            app.on_tick()
            shown = str(app.msg_w.render())
            return shown, z.wake_note

    shown, left = asyncio.run(go())
    assert "beaming" in shown and left == ""
