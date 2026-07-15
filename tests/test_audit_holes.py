"""Pins for the 2026-07-15 OPEN-HOLES audit fixes (TUIPET_AUDIT.md).

Each test names the hole it closes.  The crash-class pins render the actual
markup (pytest never renders Rich markup on its own -- the MarkupError class
only fires at parse time)."""
import asyncio
import os
import sys

from rich.text import Text

from tuipet import lobbyscreen
from tuipet.pet import Pet

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import server as srv  # noqa: E402


class _Stub:
    def __init__(self, state): self.state = state
    def respond(self, *a, **k): pass
    def relay(self, *a, **k): pass
    def update_pet(self, *a, **k): pass


def _lobby(state):
    return lobbyscreen.LobbyPanel(Pet(num=100, stage="Adult",
                                      attribute="Vaccine"),
                                  lambda n, pw, c: _Stub(state),
                                  name="joel", pw="x")


# ---- crash: a bracketed PEER name reached msg_w.update() unescaped ----------

def test_unread_strip_survives_bracket_peer_names():
    from tuipet.net import LobbyState
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    pan = _lobby(s)
    s.unread.add("[/]e[red]vil")               # a hostile account name
    strip = pan.strip()
    Text.from_markup(strip)                    # the exact parse msg_w.update() does


def test_need_message_survives_bracket_pet_names():
    from tuipet.app import TuiPetApp
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    p.name = "[/]e[vil"                        # peer cards can carry pet names too
    p.sick = True
    Text.from_markup(TuiPetApp._need_message(None, p))


# ---- crash: wire-supplied junk killed the server connection -----------------

def test_store_save_survives_junk_saved_at(tmp_path, monkeypatch):
    monkeypatch.setattr(srv, "SAVES_PATH", str(tmp_path / "saves.json"))
    monkeypatch.setattr(srv, "SAVES", {})
    save = {"stage": "Child", "name": "x", "_saved_at": "lol"}
    assert asyncio.run(srv._store_save("k", save)) is True   # was a TypeError

    # a poisoned far-future stamp must not lock the account's cloud save
    poison = {"stage": "Child", "name": "x", "_saved_at": 9e99}
    assert asyncio.run(srv._store_save("k2", poison)) is True
    honest = {"stage": "Adult", "name": "x", "_saved_at": 2e9}
    assert asyncio.run(srv._store_save("k2", honest)) is True
    assert srv.SAVES["k2"]["stage"] == "Adult"


def test_peer_lookup_survives_unhashable_to():
    assert srv._peer([]) is None               # pm/invite/relay {"to": []}
    assert srv._peer({"a": 1}) is None
    assert srv._peer(None) is None


def test_raid_hit_survives_junk_damage():
    now = 5_000_000.0
    srv._raid_rotate(now)
    srv.RAID["boss"]["start"] = now
    r = srv._raid_hit("joel", "abc", "Adult", now=now)       # was a ValueError
    assert r["ok"] and r["dealt"] == 0


# ---- feature-dead: 0/991 per-species attack sprites ever fired --------------

def test_every_species_attack_sprite_resolves():
    """The sheet keys are Attack_N; the bare str(n) lookup matched nothing,
    so the v0.4.2 headline volley silently fell back to generic orbs for
    ALL 991 species."""
    from tuipet import data
    sprites, _ = data.load_sprites()
    dead = [r["name"] for r in sprites
            if data._attack_shape(r.get("attack_sprite", 0)) is None]
    assert dead == []


# ---- feature-dead: 4 reverse-sorted jogress keys were unreachable -----------

def test_jogress_keys_are_all_sorted_and_exveemon_pairs_fuse():
    from tuipet import data
    pairs = data.load_jogress_pairs()
    for k in pairs:
        a, _, b = k.partition("|")
        assert not b or a <= b, f"unsorted key survived the loader: {k}"
    key = "database/Adult/ExVeemon.json|database/Adult/Stingmon.json"
    assert pairs.get(key) == "database/Perfect/Dinobeemon.json"


# ---- feature-dead: the monthly ladder never credited a single win -----------

def test_battle_over_files_ladder_report_from_both_sides():
    """The loser's agreeing report is what lands a credit -- filing only on
    won meant no bout was EVER confirmed; and the report must lead with the
    ACCOUNT name (the server doesn't know pet names)."""
    from tuipet.net import LobbyState
    filed = []
    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    pan = _lobby(s)
    pan.client = _Stub(s)
    pan.client.ladder_report = lambda won, opp: filed.append((won, opp))
    pan.partner = (2, "mika")                       # account name off the roster
    pan.opp_card = {"name": "Agumon"}               # PET name: must NOT lead
    pan.is_host = True
    pan.battle = {"seq": [], "host_hp": 0, "guest_hp": 5, "i": 0}   # we LOST
    pan._battle_over()
    assert filed == [(False, "mika")]


def test_server_ladder_credits_on_matching_halves():
    now = 6_000_000.0
    srv._ladder_report("joel", True, "mika", now=now)       # winner's claim
    assert srv.LADDER["seasons"] == {}                       # not credited alone
    srv._ladder_report("mika", False, "joel", now=now + 5)   # loser agrees
    season = srv.LADDER["seasons"][srv._season_key(now)]
    assert season == {"joel": 1}


# ---- economy: use_item consumed on EVERY refusal ----------------------------

def _adult():
    p = Pet(num=100, stage="Adult", attribute="Vaccine")
    p.wall_time = __import__("time").time()
    return p


def test_refusals_keep_the_item():
    p = _adult()
    p.hunger = p.hunger_max
    p.add_item("best_fruit")
    assert "Refused" in p.use_item("best_fruit")
    assert p.inventory.get("best_fruit") == 1                # NOT burned

    p.add_item("revive_floppy")
    assert "No one needs reviving" in p.use_item("revive_floppy")
    assert p.inventory.get("revive_floppy") == 1             # 2500b, kept

    p.add_item("care_mistake_eraser")
    assert "No mistakes" in p.use_item("care_mistake_eraser")
    assert p.inventory.get("care_mistake_eraser") == 1

    p.add_item("x_antibody")
    out = p.use_item("x_antibody")                           # Adult 100 has no _X
    if "Nothing stirs" in out:
        assert p.inventory.get("x_antibody") == 1


def test_items_are_life_state_guarded():
    p = Pet.new_egg(egg_type=1)                              # an EGG
    p.add_item("training_pack")
    assert p.use_item("training_pack") == ""
    assert p.inventory.get("training_pack") == 1             # kept
    assert p.trainings_cur_stage == 0                        # gate NOT pre-cleared

    d = _adult()
    d._die("test")
    d.add_item("time_gear")
    assert d.use_item("time_gear") == ""
    assert d.inventory.get("time_gear") == 1
    assert d.item_evolve("egg_of_courage") is None           # no corpse evolution
    d.add_item("revive_floppy")
    assert "LIVES" in d.use_item("revive_floppy")            # the one dead-legal item
    assert not d.dead and "revive_floppy" not in d.inventory


def test_super_carrot_trims_ten():
    p = _adult()
    p.weight = 25
    p.add_item("super_carrot")
    p.use_item("super_carrot")
    assert p.weight == 15 and "super_carrot" not in p.inventory
    p.weight = 1
    p.add_item("super_carrot")
    assert isinstance(p.use_item("super_carrot"), str)
    assert p.inventory.get("super_carrot") == 1              # refused at the floor


def test_shop_shelves_only_working_goods():
    from tuipet import shop
    keys = {e["key"] for e in shop.catalog()}
    assert "storage_drive" not in keys
    assert not any(k.startswith("theme_") for k in keys)
    assert "super_carrot" in keys                            # wired, so on sale


# ---- life-sim: sleep disturbs, the alarm, stale clocks ----------------------

def _sleeper():
    p = _adult()
    p.asleep = True
    return p


def test_feeding_a_sleeper_is_a_disturb():
    p = _sleeper()
    p.hunger = 2
    assert p.feed_meat() == "ate"                            # not refused
    assert not p.asleep and p.care_mistakes == 1
    assert p.wake_until > p.wall_time                        # grumpy 5-30min


def test_item_on_a_sleeper_disturbs_then_applies():
    p = _sleeper()
    p.energy = 1
    p.add_item("energy_drink")
    assert "Energy" in p.use_item("energy_drink")
    assert not p.asleep and p.care_mistakes == 1


def test_alarm_wakes_without_mistake_and_without_free_energy():
    p = _sleeper()
    p.energy = 1
    p.add_item("alarm_clock")
    assert "Rise" in p.use_item("alarm_clock")
    assert not p.asleep and p.care_mistakes == 0             # mistake-FREE
    assert p.energy == 1                                     # no free refill
    assert "alarm_clock" not in p.inventory                  # spent
    # and it HOLDS: an in-window minute must not re-sleep it (the old alarm
    # re-slept the NEXT minute and charged a second bedtime mistake)
    p._hour = lambda: 23                                     # deep in Adult's window
    p.lights = True
    p._sim_minute()
    assert not p.asleep and p.care_mistakes == 0


def test_alarm_on_awake_pet_is_refunded():
    p = _adult()
    p.add_item("alarm_clock")
    assert "awake" in p.use_item("alarm_clock")
    assert p.inventory.get("alarm_clock") == 1


def test_hatch_and_revive_reset_the_clock():
    import time as _t
    egg = Pet.new_egg(egg_type=1)
    egg.wall_time = _t.time() - 2 * 86400                    # egg from 2 days ago
    egg._hatch_into_fresh()
    egg.tick(0.1)
    assert egg.stage == "Baby I"                             # not Perfect-in-a-frame
    assert egg.total_minutes <= 1

    q = _adult()
    q.wall_time = _t.time() - 3 * 86400
    q._die("test")
    q.revive()
    q.tick(0.1)
    assert not q.dead and not q.sick                         # no replayed death


def test_call_latch_is_per_meter():
    import random as _r
    _r.seed(1)
    p = _adult()
    p._hour = lambda: 12                                     # noon: awake for sure
    p.lights = True
    p.asleep = False
    p.hunger = 0
    from tuipet.pet import CALL_MINUTES
    for _ in range(CALL_MINUTES):
        p._sim_minute()
        p.poop = 0
        p.sick = False
    assert p.care_mistakes == 1 and "hunger" in p.call_latched
    p.strength = 0                                           # a SECOND meter empties
    for _ in range(CALL_MINUTES):
        p._sim_minute()
        p.poop = 0
        p.sick = False
    assert p.care_mistakes == 2                              # it rang and cost too


def test_pre_402_egg_save_migrates_its_index():
    """_migrate_v401_save had ZERO callers: a mid-incubation .40x save
    hatched the wrong species after an update."""
    from tuipet import persistence
    save = persistence.to_save_dict(Pet.new_egg(egg_type=5))
    save.pop("egg_order_v")                    # a pre-.402 save has no stamp
    pet, _ = persistence.pet_from_save(dict(save), catch_up=False)
    assert pet.egg_type == 17                  # 5 through the v401 table


# ---- PvP: the card clamp derives stage from the species record --------------

def test_login_throttle_and_registration_cap():
    srv._login_bucket.clear()
    srv._reg_bucket.clear()
    now = 7_000_000.0
    for _ in range(srv.LOGIN_PER_WINDOW):
        assert srv._login_allowed("1.2.3.4", now=now)
    assert not srv._login_allowed("1.2.3.4", now=now)        # the CPU-DoS door
    assert srv._login_allowed("5.6.7.8", now=now)            # other IPs unaffected
    assert srv._login_allowed("1.2.3.4", now=now + 61)       # window rolls over

    for _ in range(srv.REG_PER_DAY):
        assert srv._registration_allowed("1.2.3.4", now=now)
    assert not srv._registration_allowed("1.2.3.4", now=now)


def test_account_names_cannot_impersonate_or_carry_markup():
    assert srv._clean_name("📢 dev") == "dev"                # no announce cosplay
    out = srv._clean_name("[/]evil[b]")
    assert "[" not in out and "]" not in out                 # no live Rich markup


def test_raid_attempt_day_is_utc():
    now = 8_000_000.0
    srv.RAID["attempts"].clear()
    rec = srv._raid_attempts("joel", now=now)
    import time as _t
    assert rec["date"] == _t.strftime("%Y-%m-%d", _t.gmtime(now))


def test_welcome_proto_reaches_the_state_and_stale_pages_say_so():
    import json as _j
    from tuipet.net import LobbyClient, LobbyState
    c = LobbyClient("ws://x", "joel")
    c._handle(_j.dumps({"t": "welcome", "id": 1, "name": "joel", "proto": 1}))
    assert c.state.server_proto == 1

    s = LobbyState()
    s.connected = True
    s.me_id, s.me_name = 1, "joel"
    s.server_proto = 0                                       # a pre-handshake relay
    pan = _lobby(s)
    pan.client = _Stub(s)
    assert "older than this" in pan._text_ladder().plain
    assert "older than this" in pan._text_raid().plain


def test_clamp_card_kills_the_stage_forge():
    from tuipet.lobbyscreen import _clamp_card
    forged = {"num": 100, "stage": "Special", "attribute": "Virus",
              "battles": 10, "wins": 10}
    from tuipet import data
    rec = data.record_for(100)
    out = _clamp_card(forged)
    assert out["stage"] == rec["stage"]                      # the record wins
    assert out["attribute"] == rec["attribute"]
    unknown = {"num": 999999, "stage": "Special"}
    assert _clamp_card(unknown)["stage"] != "Special"        # no 14.5 by claim
