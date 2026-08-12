"""The profile block travels with the cartridge.

GoingUnder, 2026-08-11: "save import device to device dosent import eggs
progress".  The cartridge moved save.json; every cross-generation milestone
the egg gates read lives in settings.json and never crossed the wire, so a
taken pet landed on the new device with its egg-unlock history at zero.

The headline gate below is that report, reproduced: earn progress on device A,
move the pet, read the eggs on device B.
"""
import pytest

from tuipet import persistence
from tuipet.pet import Pet


@pytest.fixture
def two_devices(tmp_path, monkeypatch):
    """Return switch(name) -- point persistence at 'phone' or 'laptop'.

    A device IS its save dir here, which is exactly what the bug is about:
    save.json travelled between them and settings.json did not.
    """
    dirs = {}
    for name in ("phone", "laptop"):
        d = tmp_path / name
        d.mkdir()
        dirs[name] = d

    def switch(name):
        d = dirs[name]
        monkeypatch.setattr(persistence, "SAVE_DIR", str(d))
        monkeypatch.setattr(persistence, "SAVE_PATH", str(d / "save.json"))
        monkeypatch.setattr(persistence, "SETTINGS_PATH", str(d / "settings.json"))
        monkeypatch.setattr(persistence, "_ALBUM_SEEN", set())

    switch("phone")
    return switch


def _a_pet():
    return Pet(num=-1, stage="Rookie")


# ---- the report -----------------------------------------------------------

def test_a_taken_pet_carries_its_egg_progress(two_devices):
    """GoingUnder's bug, end to end."""
    # the phone earned four eggs the long way
    for idx in (2, 5, 9, 14):
        persistence.egg_own(idx)
    assert persistence.get_eggs_owned() == {2, 5, 9, 14}

    # the cartridge moves: the phone's save is what the cloud hands the laptop
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    assert persistence.get_eggs_owned() == set()      # a fresh device, as it should be
    persistence.write_save_dict(wire)                 # <- the install funnel

    assert persistence.get_eggs_owned() == {2, 5, 9, 14}


def test_the_pet_still_arrives(two_devices):
    """The progress rider must not cost us the thing that already worked."""
    wire = persistence.to_save_dict(Pet(num=-1, stage="Rookie", strength=7))
    two_devices("laptop")
    persistence.write_save_dict(wire)
    pet, _ = persistence.load()
    assert pet is not None and pet.strength == 7


# ---- the merge rule -------------------------------------------------------

def test_the_move_never_costs_the_receiving_device_its_own_progress(two_devices):
    """Union, not replace: a take is not a way to LOSE what you earned here."""
    persistence.egg_own(2)
    persistence.egg_own(5)
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.egg_own(30)                           # earned on THIS device only
    persistence.write_save_dict(wire)

    assert persistence.get_eggs_owned() == {2, 5, 30}


def test_counters_take_the_better_of_the_two_never_the_sum(two_devices):
    """Both devices counted the same 40 wins; 40 is the answer, not 70."""
    persistence.wins_add(40)
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.wins_add(30)
    persistence.write_save_dict(wire)

    assert persistence.get_wins() == 40


def test_a_stale_fork_cannot_drag_a_counter_backwards(two_devices):
    persistence.wins_add(5)                           # the stale phone
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.wins_add(90)
    persistence.write_save_dict(wire)

    assert persistence.get_wins() == 90


def test_the_album_travels(two_devices):
    """The dex gates egg unlocks, so it is progress too (album_n rules)."""
    for num in (12, 34, 56):
        persistence.album_add(num)
    earned = persistence.get_album()
    assert earned                                     # the fixture really recorded
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.write_save_dict(wire)
    assert earned <= persistence.get_album()


def test_zone_bests_keep_the_higher_score(two_devices):
    persistence.zone_best_set(1, 900)
    persistence.zone_best_set(2, 100)
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.zone_best_set(1, 400)
    persistence.zone_best_set(2, 700)
    persistence.write_save_dict(wire)

    assert persistence.zone_bests() == {1: 900, 2: 700}


def test_a_one_shot_flag_survives_the_move(two_devices):
    persistence.note_xanti()
    wire = persistence.to_save_dict(_a_pet())

    two_devices("laptop")
    persistence.write_save_dict(wire)
    assert persistence.get_progress()["xanti_ever"] is True


# ---- what must NOT travel -------------------------------------------------

def test_the_one_slot_live_values_stay_device_local(two_devices):
    """last_gen / digimemory / bonus_seed / title_worn are current state, not
    earned history -- no merge of them is lose-nothing, so the fix leaves them
    alone deliberately.  Pinned so a later change to that call is a DECISION."""
    persistence.bank_digimemory({"num": 77})
    persistence.bank_bonus_seed(3)
    wire = persistence.to_save_dict(_a_pet())

    assert "digimemory" not in wire.get("progress", {})
    assert "bonus_seed" not in wire.get("progress", {})

    two_devices("laptop")
    persistence.write_save_dict(wire)
    assert persistence.peek_digimemory() is None


# ---- robustness -----------------------------------------------------------

@pytest.mark.parametrize("junk", [None, {}, [], "progress", 7,
                                  {"eggs_owned": "nope"},
                                  {"wins": "lots"},
                                  {"zone_bests": {"1": "high"}}])
def test_a_malformed_progress_block_never_costs_the_profile_its_history(
        two_devices, junk):
    two_devices("laptop")
    persistence.egg_own(11)
    persistence.wins_add(8)
    persistence.zone_best_set(1, 500)

    persistence.merge_progress(junk)

    assert persistence.get_eggs_owned() == {11}
    assert persistence.get_wins() == 8
    assert persistence.zone_bests() == {1: 500}


def test_an_empty_profile_adds_no_weight_to_the_wire(two_devices):
    """A brand-new player pushes exactly what they pushed before."""
    assert "progress" not in persistence.to_save_dict(_a_pet())


def test_the_rider_stays_far_under_the_wire_cap(two_devices):
    """The push is dropped whole if it crosses SAVE_WIRE_MAX, so a full album
    must not be what pushes a real save over."""
    import json
    from tuipet.net import SAVE_WIRE_MAX
    for num in range(1, 1500):
        persistence.album_add(num)
    for idx in range(40):
        persistence.egg_own(idx)
    persistence.wins_add(9999)
    assert len(json.dumps(persistence.to_save_dict(_a_pet()))) < SAVE_WIRE_MAX


def test_an_older_client_ignores_the_rider(two_devices):
    """pet_from_save keeps only Pet fields, so a client that never heard of
    'progress' still builds the pet -- no server change, no format break."""
    persistence.egg_own(4)
    wire = persistence.to_save_dict(_a_pet())
    assert "progress" in wire                     # the rider is really there
    pet, _ = persistence.pet_from_save(wire, strict=False)
    assert pet is not None
    assert not hasattr(pet, "progress")
