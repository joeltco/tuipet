"""Regressions for section A of care audit 2026-10-14."""
import json
import random

import pytest

from tuipet import persistence
from tuipet.app import TuiPetApp
from tuipet.deathscreen import _age_str
from tuipet.disciplinescreen import DisciplinePanel
from tuipet.pet import Pet

from tuipet.petbase import LIGHTS_MISTAKE_SEC


def _pet(**kw):
    p = Pet(num=100, stage="Champion", obedience=100)
    p.world_seconds = 480
    p.evo_blocked = True
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    for k, v in kw.items():
        setattr(p, k, v)
    return p


@pytest.fixture(autouse=True)
def _quiet(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: .99)
    monkeypatch.setattr(random, "randrange", lambda n: n - 1)


def test_overfeed_keeps_weight_and_of_without_a_fourth_mistake_source():
    p = _pet(care_mistakes=4, pardon_lapse=0)
    before = p.weight
    p.feed_meat()
    assert (p.care_mistakes, p.overeat, p.weight) == (4, 1, before + 1)


@pytest.mark.parametrize("stage", ["Ultimate", "Mega"])
def test_rescue_steps_off_the_late_stage_fatal_trigger(stage, monkeypatch):
    monkeypatch.setattr('tuipet.evolution.death_targets', lambda p: [])
    p = _pet(stage=stage, stage_seconds=3000, care_mistakes=8, dead=True)
    p.save_from_death()
    assert p.care_mistakes == 4
    p.tick(1)
    assert not p.dead and p.saved_from_death == 1


CLOCKS = dict(_sleep_min=59., _nap_e=29., _nap_cycle=239., _to_nap_t=19.,
              _ac_cool=2., _obed_t=100., _lit_obed_hit=True, _interest_t=39.,
              _mood_rec_t=4., _rank_t=58.)


@pytest.mark.parametrize("key,value", CLOCKS.items())
def test_live_care_progress_survives_json_save(key, value):
    p = _pet()
    setattr(p, key, value)
    q, _ = persistence.pet_from_save(json.loads(json.dumps(persistence.to_save_dict(p))))
    assert q is not None and getattr(q, key, None) == value


def test_reload_does_not_lose_the_next_sleep_energy_payment():
    p = _pet(asleep=True, lights=False, energy=0)
    p._sleep_min = 59.
    q, _ = persistence.pet_from_save(json.loads(json.dumps(persistence.to_save_dict(p))))
    p.tick(1)
    q.tick(1)
    assert q.energy == p.energy and q.energy > 0


def test_reload_does_not_repeat_a_paid_assistant_visit():
    p = _pet(auto_care=True, bits=10000, hunger=0)
    p.tick(1)
    p.hunger = 0
    q, _ = persistence.pet_from_save(json.loads(json.dumps(persistence.to_save_dict(p))))
    p.tick(1)
    q.tick(1)
    assert (q.bits, q.hunger) == (p.bits, p.hunger)


def test_each_real_sleep_gets_its_own_lights_obedience_penalty():
    p = _pet()
    for _ in range(2):
        p._fall_asleep()
        p._lights_t = LIGHTS_MISTAKE_SEC - 30.0   # deep into the ten-minute grace
        p._tick_asleep(60)
        p._wake()
    assert p.obedience == 98


@pytest.mark.parametrize("needs", [dict(sick=True), dict(hunger=0), dict(strength=0)])
def test_hud_names_cleaning_before_a_filth_blocked_remedy(needs):
    p = _pet(poop=1, poop_sizes=[1], **needs)
    app = TuiPetApp(pet=p)
    assert '([b]C[/])' in app._need_message(p)


def test_empty_effort_and_insufficient_drill_energy_names_the_free_tonic():
    p = _pet(strength=0, energy=1)
    app = TuiPetApp(pet=p)
    assert '([b]F[/]' in app._need_message(p)
    p.feed_pill()
    assert p.strength == 1


def test_dark_frail_sleeper_is_not_told_to_train():
    p = _pet(stage='Mega', care_mistakes=3, asleep=True, lights=False, strength=0)
    msg = TuiPetApp(pet=p)._need_message(p)
    assert 'frail' in msg and 'train' not in msg


def test_legacy_feed_entry_forwards_assisted_serving():
    p = _pet(sick=True, hunger=0)
    p.feed(assisted=True)
    assert p.hunger == 1 and p.sick


def test_unset_praise_is_not_a_proud_moment_at_world_zero():
    p = _pet(world_seconds=0)
    panel = DisciplinePanel(p)
    assert 'all calm' in panel._state_line()
    before = p.obedience
    result = panel.key('enter')
    assert p.obedience == before and result[1][1] is None


@pytest.mark.parametrize("secs,shown", [(388800, '4d 12h'), (90000, '1d 1h'),
                                        (5400, '1h 30m'), (59 * 60, '59m')])
def test_memorial_reads_real_time(secs, shown):
    # age_seconds is REAL seconds (petbase.AGE_DAY = 86400): the 0.6.12
    # "game minutes" reading showed lifespans 60x too long -- reverted
    assert _age_str(secs) == shown


def test_evolution_does_not_orphan_the_existing_wounds_healing_clock():
    p = _pet(injured=True, inj_length=12)
    p.evolve_to(100)
    assert p.injured and p.inj_length == 12
    for _ in range(12):
        p.tick(1)
    assert not p.injured


def test_discipline_status_card_does_not_advertise_unset_praise():
    from types import SimpleNamespace
    from tuipet import statusbox
    card = SimpleNamespace(update=lambda text: captured.append(text))
    captured = []
    statusbox.discipline(SimpleNamespace(pet=_pet(world_seconds=0), stats_w=card))
    assert 'proud moment' not in captured[0]


def test_a_sick_or_hurt_sleeper_calls_in_the_dark():
    """Joel 2026-10-15 (care call #16 = A): death rolls run all night, so a
    sick or hurt pet asleep in the dark calls -- with a remedy that works."""
    p = _pet()
    p._fall_asleep()
    p.lights = False
    assert not p.needs_care()
    p.sick = True
    assert p.needs_care()
    app = TuiPetApp(pet=p)
    assert "([b]F[/]" in app._need_message(p)
    p.poop, p.poop_sizes = 1, [1]
    assert "([b]C[/])" in app._need_message(p)
    p.clean()
    assert not p.asleep                                   # C wakes it...
    p.clean()
    assert p.poop == 0                                    # ...C again cleans
    q = _pet()
    q._fall_asleep()
    q.lights = False
    q.injured = True
    assert q.needs_care() and "([b]H[/]" in TuiPetApp(pet=q)._need_message(q)
