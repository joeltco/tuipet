"""Care-mistake / neglect death triggers (Workstream A).

DVPet has discrete neglect deaths, not just a faster lifespan burn. tuipet's tick()
implements four:
  - care_mistakes >= 20  (MaxCareMistakes)   -> death   [per-form, resets on evolve]
  - injuries     >= 20   (MaxInjuries)       -> death   [per-form]
  - hunger == 0 for 12h continuous           -> death   [persists across evolutions]
  - age_seconds >= lifespan                  -> natural death

These guard the thresholds (a wrong one ruins a playthrough) and the safety rails:
eggs are immune, a dead pet stays frozen, and feeding resets the starvation clock.
A healthy pet is constructed (hunger full, no filth) so the only death is the one
under test. num=-1 keeps tick() deterministic and sprite-free.
"""
from tuipet.pet import Pet


def _healthy(stage="Rookie", **kw):
    # world starts at mid-day: hour 0 is NIGHT under the canon daylight bands,
    # and a sleeping pet freezes its starvation/care clocks
    kw.setdefault("world_seconds", 10 * 60.0)
    return Pet(num=-1, stage=stage, hunger=4, poop=0, **kw)


def test_care_mistakes_20_is_fatal():
    p = _healthy(care_mistakes=20)
    p.tick(0.1)
    assert p.dead is True


def test_care_mistakes_19_is_survivable():
    p = _healthy(care_mistakes=19)
    p.tick(0.1)
    assert p.dead is False, "19 care mistakes must not kill (boundary is 20)"


def test_injuries_19_is_survivable():
    p = _healthy(injuries=19)
    p.tick(0.1)
    assert p.dead is False


def test_starvation_12h_is_fatal():
    p = _healthy()
    p.hunger = 0
    p._starve_t = 12 * 3600 - 1
    p.tick(2)                     # crosses the 12h continuous-starvation threshold
    assert p.dead is True


def test_starvation_clock_resets_when_fed():
    p = _healthy()
    p.hunger = 0
    p._starve_t = 12 * 3600 - 5
    p.hunger = 4                  # fed before the clock elapses
    p.tick(0.1)
    assert p.dead is False
    assert p._starve_t == 0.0, "feeding must reset the starvation timer"


def test_the_hazard_roll_is_fatal(monkeypatch):
    # the DSprite roll (2026-07-22): mistakes bracket + age bracket, one roll
    import tuipet.petbody as body
    monkeypatch.setattr(body.random, "random", lambda: 0.0)
    p = _healthy(care_mistakes=5)
    p.tick(0.1)
    assert p.dead is True and p.death_cause == "neglect"
    q = _healthy()
    q.age_seconds = 26 * 86400.0
    q.tick(0.1)
    assert q.dead is True and q.death_cause == "old age"


def test_egg_is_immune_to_neglect_death():
    egg = Pet(num=-1, stage="Egg", care_mistakes=99, injuries=99)
    egg.hunger = 0
    egg._starve_t = 99 * 3600
    egg.tick(0.1)
    assert egg.dead is False, "an egg cannot die of neglect"


def test_dead_pet_stays_frozen():
    p = _healthy(care_mistakes=5)
    p.dead = True
    p.tick(10_000)
    assert p.dead is True
    assert p.care_mistakes == 5, "a dead pet's life-sim state must not advance"


# ---- saveFromDeath (the death evolution) -------------------------------------

def test_save_from_death_restores_life_and_costs_bonus():
    p = _healthy(stage="Champion")
    p.num = 100                                       # Gatomon (no Death target expected)
    p.evol_bonus = 2
    p.age_seconds = 10000.0
    p.dead = True
    p.save_from_death()
    assert not p.dead
    assert p.saved_from_death == 1
    assert p.hunger == 0                              # alive, but starving
    assert p.evol_bonus == 1                          # BonusChangeAfterSavedFromDeath
    assert p.age_seconds == 10000.0                   # no life math: the clone's revive


def test_death_evolution_fires_when_a_dark_form_accepts():
    from tuipet import data
    # find any form with a Death-special evolution target
    src = next(n for n, targets in data.load_evolutions().items()
               if any(data.load_requirements().get(t, {}).get("special") == "Death"
                      for t in targets))
    _, by = data.load_sprites()
    p = _healthy(stage=by[src]["stage"])
    p.num, p.attribute = src, by[src]["attribute"]
    p.evol_bonus = 100000                             # deterministic gate pass
    p.wins = p.battles = 50
    p.vaccine = p.data_power = p.virus = 500
    p.dead = True
    old = p.save_from_death()
    assert old == src and p.num != src                # the dark rebirth
    assert data.load_requirements()[p.num]["special"] == "Death"


def test_unsaved_counters_step_off_the_trigger_line():
    p = _healthy(stage="Champion")
    p.num = 100
    p.care_mistakes = 20
    p.dead = True
    p.save_from_death()
    assert p.care_mistakes == 19                      # off the continuous check
    p.tick(1.0)
    assert not p.dead


# ---- death-animations audit 2026-07-05 ---------------------------------------

def test_memorial_grave_beat_absorbs_the_save_mash():
    """Canon deading(): 20 ticks of just the grave (dieLoop -> error, x2)
    before the memorial takes input -- without it the frantic save-mash
    overshoots INTO the memorial, where 'n' starts a new egg unread."""
    from tuipet.deathscreen import DeathPanel
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", dead=True)
    p.world_seconds = 12 * 60.0
    pan = DeathPanel(p, hold=20)
    assert pan.sfx == "error"                     # the first dieLoop sting
    pan.sfx = None
    assert pan.key("n") is None                   # mash absorbed: no new egg
    assert pan.key("enter") is None
    assert pan.strip() == "…"                     # just the grave, no key hints
    stings = []
    for _ in range(25):                           # drain sfx like the app does
        pan.anim()
        if pan.sfx:
            stings.append(pan.sfx)
            pan.sfx = None
    assert stings == ["error"]                    # the second loop, exactly once
    assert "N new egg" in pan.strip()
    assert pan.key("n") == ("done", "new")        # alive again after the beat
    pan2 = DeathPanel(p)                          # no-hold constructions (tests,
    assert pan2.sfx is None                       # startup) are untouched
    assert pan2.key("escape") == ("done", None)


def test_revive_bar_rises_with_each_rescue():
    """dying(): numHits > HitsToSave x (savedFromDeath + 1) -- every rescue
    doubles down on the next one's mash bar."""
    from tuipet.pet import HITS_TO_SAVE
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 12 * 60.0
    assert p.saved_from_death == 0
    bar0 = HITS_TO_SAVE * (p.saved_from_death + 1)
    p.dead = True
    p.save_from_death()
    assert not p.dead and p.saved_from_death == 1
    bar1 = HITS_TO_SAVE * (p.saved_from_death + 1)
    assert bar1 == 2 * bar0                       # the second rescue costs double


def test_poison_mushroom_dies_like_every_other_death():
    """C3 (gameplay audit 2026-07-19): _deadly hand-set dead=True from the
    paused bag panel -- asleep/hatching stayed set and the app's was_dead
    tick edge never saw the between-ticks death (no dying beat, no mash
    window, no banking).  It routes through _die now."""
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus",
            hunger=4, poop=0, world_seconds=10 * 60.0)
    p.asleep = True
    p.add_item("poison_mushroom")
    p.use_item("poison_mushroom")
    assert p.dead and p.death_cause == "a poison mushroom"
    assert not p.asleep and not p.hatching


def test_a_between_ticks_death_still_gets_the_dying_beat():
    """The app pairs with C3 by checking STATE, not a was_dead edge: a dead,
    un-ceremonied pet with no dying fx in flight starts the beat on the
    next tick, wherever the death landed."""
    import asyncio
    from tuipet import data
    from tuipet.app import TuiPetApp
    _, by = data.load_sprites()
    num = next((n for n, r in by.items()
                if r["stage"] == "Rookie" and not data.is_placeholder(n)), None)
    if num is None:
        import pytest
        pytest.skip("sprite assets not installed")
    pet = Pet.from_num(num)
    pet.hunger = 4
    pet.energy = 24
    pet.world_seconds = 10 * 60.0

    async def go():
        app = TuiPetApp(pet=pet)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")            # dismiss title -> main view
            await pilot.pause()
            pet.inventory["poison_mushroom"] = 1
            pet.use_item("poison_mushroom")        # between ticks: sim paused
            assert pet.dead
            app.on_tick()
            return app._dying_fx, (app.screen_w.fx or {}).get("kind")

    dying, kind = asyncio.run(go())
    assert dying and kind == "dying"
