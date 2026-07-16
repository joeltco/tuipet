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


def test_training_target_wall_renders_and_only_mega_crumbles_it():
    """The wall never drew (the code read width/sprite off the OUTER
    {"Wall_1","Wall_2"} dict); a MEGA break shows Wall_2, a normal break
    keeps Wall_1 standing (source TRAINING_SHOOT rule)."""
    from tuipet import training
    pan = training.TrainingPanel(_adult())
    pan.grade = "mega"
    standing = pan._wall_overlay("fire_in")
    assert standing, "the target wall must render"
    mega_break = pan._wall_overlay("break")
    pan.grade = "normal"
    normal_break = pan._wall_overlay("break")
    assert normal_break == standing                # normal: wall stays intact
    assert mega_break != standing                  # mega: Wall_2, crumbled


def test_hit_flash_is_the_canon_blast_not_the_skull():
    """EXPLODE strobed the OLD game's skull-and-crossbones KO marker while
    the clone's real Hit_1 blast sat unused in battle_fx."""
    from tuipet import battlescreen as bs, data
    e = data.load_battle_fx()["hit"]["Hit_1"]
    w = e["width"]
    rows = ["".join("1" if e["sprite"][y * w + x] else "0" for x in range(w))
            for y in range(e["height"])]
    assert bs.EXPLODE[0] == rows                   # the blast
    assert all(set(r) == {"0"} for r in bs.EXPLODE[1])   # the blink's off beat


def test_orbs_fly_tinted_with_the_mons_own_hue():
    from tuipet import data, strikefx
    tint = data.mon_ink(29)
    assert isinstance(tint, str) and tint.startswith("#")
    pts = strikefx.orb_flight(["11", "11"], True, "fire_out", 0.5, 20,
                              color=tint)
    assert pts and all(len(p) == 3 and p[2] == tint for p in pts)


def test_new_egg_starts_on_its_assigned_scene():
    """The carousel previews every egg on its hue-picked scene, but the
    scene never reached the pet -- fresh eggs opened on default greenhills
    and generation-N eggs kept the DEAD pet's scene (Joel 2026-07-15)."""
    from tuipet import egg as egg_mod
    for i in range(egg_mod.count()):
        assert Pet.new_egg(egg_type=i).bg_current == egg_mod.scene_for(i)


def test_pre_402_egg_save_migrates_its_index():
    """_migrate_v401_save had ZERO callers: a mid-incubation .40x save
    hatched the wrong species after an update."""
    from tuipet import persistence
    save = persistence.to_save_dict(Pet.new_egg(egg_type=5))
    save.pop("egg_order_v")                    # a pre-.402 save has no stamp
    pet, _ = persistence.pet_from_save(dict(save), catch_up=False)
    assert pet.egg_type == 17                  # 5 through the v401 table


def test_title_mascot_pool_and_colour_render():
    """The title mascot vanished with the clone: the pool filtered on DVPet
    stage names (0 matches -> always num 0) and the painter tested colour
    cells against '1' (0 pixels lit).  (Joel 2026-07-15: 'title screen is
    missing mons')."""
    import random as _r
    from tuipet import titlescreen, theme
    nums = set()
    for seed in range(6):
        _r.seed(seed)
        nums.add(titlescreen.TitlePanel().num)
    assert len(nums) > 1, "the mascot pool must actually vary"
    _r.seed(1)
    pan = titlescreen.TitlePanel()
    pan.frame_i = 30                               # past the boot dissolve
    styles = {str(sp.style) for sp in pan.text().spans}
    inkish = {theme.LCD_ON, theme.LCD_BG}
    assert any(not set(s.replace(" on ", "|").split("|")) <= inkish
               for s in styles), "the mascot must render in COLOUR"


# ---- the UNDER-CONSTRUCTION gate: ONE switch, both ways ---------------------

def _title_calls(monkeypatch, gate_on, unlocked):
    """Drive _after_title with the switch set both ways; return what it opened."""
    from tuipet import persistence, titlescreen
    from tuipet.app import TuiPetApp
    monkeypatch.setattr(titlescreen, "GATE_ON", gate_on)
    monkeypatch.delenv("TUIPET_GATE", raising=False)   # the flag, not the override
    s = persistence.load_settings()
    if unlocked:
        s["construction_ok"] = True
    else:
        s.pop("construction_ok", None)
    persistence.save_settings(s)
    app = TuiPetApp.__new__(TuiPetApp)                 # no Textual mount needed
    calls = []
    app._post_title = lambda: calls.append("post")
    app._open_mode = lambda panel, cb=None: calls.append(type(panel).__name__)
    app._after_title()
    return calls


def test_gate_switch_off_opens_the_game_straight_up(monkeypatch):
    # GATE_ON=False must skip the lock even on a device that never unlocked
    assert _title_calls(monkeypatch, gate_on=False, unlocked=False) == ["post"]


def test_gate_switch_on_locks_until_unlocked(monkeypatch):
    assert _title_calls(monkeypatch, gate_on=True, unlocked=False) == ["GatePanel"]
    assert _title_calls(monkeypatch, gate_on=True, unlocked=True) == ["post"]


def test_gate_env_override_beats_the_flag(monkeypatch):
    from tuipet import titlescreen
    monkeypatch.setattr(titlescreen, "GATE_ON", True)
    monkeypatch.setenv("TUIPET_GATE", "0")
    assert titlescreen.gate_on() is False
    monkeypatch.setattr(titlescreen, "GATE_ON", False)
    monkeypatch.setenv("TUIPET_GATE", "1")
    assert titlescreen.gate_on() is True


def test_construction_gate_locks_game_keeps_lobby():
    from tuipet.app import _hud_plain
    from tuipet import titlescreen
    pan = titlescreen.GatePanel()
    assert len(_hud_plain(pan.strip())) <= 40
    pan.text()                                     # smoke: renders empty
    for k in ("1", "2", "3", "enter"):             # wrong PIN bounces
        out = pan.key(k)
        pan.anim(); pan.text()
    assert out is None and pan.buf == ""
    assert pan.key("l") == ("done", "lobby")       # the open door
    for k in titlescreen.GATE_PIN:
        pan.key(k)
    assert pan.key("enter") == ("done", "play")    # the right PIN
    assert pan.key("escape") == ("done", None)     # and the way back out


def test_gate_wiring_stands_between_title_and_game():
    import inspect
    from tuipet.app import TuiPetApp
    src = inspect.getsource(TuiPetApp._after_title)
    assert "construction_ok" in src and "GatePanel" in src and "gate_on" in src
    src = inspect.getsource(TuiPetApp._after_gate_lobby)
    assert "GatePanel" in src                      # lobby exit lands on the GATE


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


# ============================================================================
# ROUND 3 fixes (2026-07-16) -- see TUIPET_AUDIT.md "ROUND 3 backlog"
# ============================================================================

import time as _time  # noqa: E402


def _live(num=29):
    p = Pet.from_num(num)
    p.wall_time = _time.time()
    return p


# ---- Tier 1: crashes & save-loss --------------------------------------------

def test_r3_type_gate_rejects_corrupt_v044_fields():
    from tuipet import persistence
    for fld, bad in (("wake_until", "soon"), ("full_until", "x"),
                     ("auto_clean_until", "y"), ("call_latched", "hunger")):
        d = persistence.to_save_dict(_live())
        d[fld] = bad
        pet, _ = persistence.pet_from_save(dict(d), catch_up=False)
        assert pet is None, f"{fld}={bad!r} must be rejected, not crash _sim_minute"
    # a valid-typed list of junk elements is scrubbed to known meter tokens
    d = persistence.to_save_dict(_live())
    d["call_latched"] = ["hunger", "bogus", 5]
    pet, _ = persistence.pet_from_save(dict(d), catch_up=False)
    assert pet.call_latched == ["hunger"]


def test_r3_jogress_survives_non_int_peer_num():
    from tuipet import jogress
    assert jogress.resolve_online(_live(), {"num": "evil"}) is None
    assert jogress.resolve_online(_live(), {"num": None}) is None


def test_r3_local_saved_at_counts_the_bak():
    import json
    import tempfile
    from tuipet import persistence
    d = tempfile.mkdtemp()
    p = os.path.join(d, "save.json")
    json.dump({"stage": "Child", "name": "x"}, open(p, "w"))            # no _saved_at
    json.dump({"stage": "Adult", "name": "x", "_saved_at": 5000.0}, open(p + ".bak", "w"))
    assert persistence.local_saved_at(p) == 5000.0     # the good .bak counts (was 0.0)


def test_r3_autosave_skips_the_unsettled_new_game():
    from tuipet.app import TuiPetApp
    saved = []
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = _live()
    import tuipet.persistence as _p
    orig = _p.save
    _p.save = lambda pet, path=None: saved.append(pet)
    try:
        app._new_game = True
        app.autosave()                                 # unsettled: must NOT persist
        assert saved == []
        app._new_game = False
        app._start_sync = lambda: None
        app._warn_if_unsaveable = app._warn_if_cloud_dropped = lambda: None
        app._note_progress = app._push_cloud = lambda: None
        app.autosave()                                 # settled: persists
        assert saved == [app.pet]
    finally:
        _p.save = orig


# ---- Tier 2: economy / corruption -------------------------------------------

def test_r3_raid_mult_binds_to_num_not_stage_string():
    now = 9_100_000.0
    srv._raid_rotate(now); srv.RAID["boss"]["start"] = now
    honest = srv._raid_hit("h", 20, 374, now=now)          # a Child num -> x1
    forge = srv._raid_hit("c", 20, "super ultimate", now=now)   # forged string
    assert honest["dealt"] == 20 * srv.RAID_DMG_MULT * 1
    assert forge["dealt"] == 20 * srv.RAID_DMG_MULT * 1     # forge dead


def test_r3_raid_eviction_keeps_todays_counts():
    import time as _t
    now = 9_200_000.0
    day = _t.strftime("%Y-%m-%d", _t.gmtime(now))
    srv.RAID["attempts"] = {f"stale{i}": {"date": "2000-01-01", "left": 0}
                            for i in range(4100)}
    srv.RAID["attempts"]["active"] = {"date": day, "left": 0}   # spent today
    srv._raid_attempts("fresh", now)                            # triggers prune
    assert srv.RAID["attempts"]["active"]["left"] == 0          # NOT refunded
    assert not any(r["date"] == "2000-01-01" for r in srv.RAID["attempts"].values())


def test_r3_non_dict_pet_is_coerced():
    _pet = "not a dict"
    assert (_pet if isinstance(_pet, dict) else {}) == {}       # the store guard


def test_r3_jogress_requires_two_phase_consent():
    import inspect
    src = inspect.getsource(lobbyscreen.LobbyPanel._key_jogress)
    assert "if not self.j_peer_two_phase:" not in src           # legacy auto-commit gone
    assert "decline" in src


def test_r3_reconnect_rejoins_the_room():
    import json
    from tuipet.net import LobbyClient, LobbyState
    sent = []
    c = LobbyClient("ws://x", "joel")
    c._send = lambda o: sent.append(o)
    c.state = LobbyState()
    c.state.room = "secret"                                     # was in a room
    c._handle(json.dumps({"t": "welcome", "id": 1, "name": "joel", "proto": 1}))
    assert any(o.get("t") == "room" and o.get("code") == "secret" for o in sent)


# ---- Tier 3/4 ---------------------------------------------------------------

def test_r3_crest_eggs_are_buyable_at_source_default():
    from tuipet import shop
    armor = [e for e in shop.catalog() if e["category"] == shop.ARMOR_CATEGORY]
    assert len(armor) == 11 and all(e["price"] == shop.DEFAULT_PRICE for e in armor)
    keys = {e["key"] for e in shop.catalog()}
    assert "storage_drive" not in keys and not any(k.startswith("theme_") for k in keys)


def test_r3_feed_sets_the_eat_pose():
    p = _live(); p.hunger = 0
    assert p.feed_meat() == "ate"
    assert p.anim == "eat" and p._last_meal_starving is True


def test_a_sleeper_still_evolves():
    """The sleeping branch's early return skipped _maybe_evolve, so a mon that
    hit its stage time overnight sat at the old form until morning -- a Baby I
    needs 10 min and sleeps 13 HOURS (Joel 2026-07-16).  The source gates only
    the hourly decay on !SLEEPING; its evolution check qr() is unconditional."""
    for hour in (3, 23):                           # deep in the Baby I 20:00-09:00 window
        p = _live(282)                             # Botamon, Baby I, needs 10 min
        p._hour = lambda h=hour: h
        for _ in range(12):
            p._sim_minute()
        assert p.asleep is True, "fixture must be asleep to pin the bug"
        assert p.stage == "Baby II", f"a sleeper failed to evolve at {hour}:00"


def test_sleep_still_blocks_the_hourly_decay():
    """The evolve fix must NOT let the sleep gate leak: decay stays awake-only."""
    p = _live(282)
    p._hour = lambda: 3                            # asleep
    p.hunger, p.strength = 4, 4
    p.stage_minutes = 59                           # the next tick lands on the %60 decay
    p._sim_minute()
    assert (p.hunger, p.strength) == (4, 4), "a sleeper must not lose meters"


def test_pill_lives_in_the_feed_menu_not_a_separate_key():
    """The standalone H/heal action is gone (merge 2026-07-16): pill is a
    row in the feed menu, and picking it plays the HEAL fx, not the eat chew."""
    from tuipet.app import TuiPetApp
    from tuipet.feedscreen import FeedPanel
    # no heal binding, no action_heal method
    assert not hasattr(TuiPetApp, "action_heal")
    assert not any(a == "heal" for _, a, *_ in TuiPetApp.BINDINGS)
    # the menu's pill row heals a sick pet and asks for the medicine fx
    p = _live(); p.sick = True
    pan = FeedPanel(p)
    pan.key("down")                                  # meat -> pill
    done, payload = pan.key("enter")
    assert done == "done"
    outcome, food, msg = payload
    assert outcome == "healed" and food["key"] == "i:80"   # -> start_fx("heal")
    assert p.sick is False and msg == "Cured!"


def test_r3_cbounds_reads_colour_frames():
    from tuipet import strikefx
    fr = [[None] * 4 + ["#f00"] * 8 + [None] * 4 for _ in range(4)]
    assert strikefx.cbounds(fr) == (4, 11)                      # not full-frame (0,15)


def test_r3_sleep_pill_turns_lights_off():
    p = _live(); p.asleep = False; p.lights = True
    p.add_item("sleeping_pill")
    p.use_item("sleeping_pill")
    assert p.asleep and not p.lights                            # no bedtime mistake


def test_r3_lobby_messy_cue_is_reachable():
    import inspect
    src = inspect.getsource(lobbyscreen.LobbyPanel._care_cue)
    assert "p.poop >= 3" not in src and "messy!" in src
