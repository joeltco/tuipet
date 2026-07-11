"""Adventure restyle (2026-07-04): the journey lives on the standard 12-row
arena with the zone's canonical per-step scenery (zones.csv BackgroundsAndRange)
-- the old flat 7-row strip looked nothing like the rest of the game."""
import random

from tuipet import data
from tuipet.pet import Pet
from tuipet.adventurescreen import AdventurePanel, ROWS


def _pet():
    random.seed(3)
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    for _ in range(2):
        p.stage_seconds = 9e8
        p._maybe_evolve()
    p.world_seconds = 12 * 60.0
    return p


def test_adventure_uses_the_standard_arena():
    assert ROWS == 12                      # the ONE locked LCD, like every screen


def test_zone_scenery_parses_and_covers_the_walk():
    zones = data.load_maps()[0]["zones"]   # map 1 (index 0 = the first real map row)
    z = zones[0]
    assert z["bgs"], "zone 1-1 lost its BackgroundsAndRange spans"
    los = [b[0] for b in z["bgs"]]
    assert los[0] == 0 and los == sorted(los)
    for _, _, hid in z["bgs"]:
        assert hid in data.load_habitats(), hid   # every span names a real habitat


def test_backdrop_changes_along_the_journey():
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the arrival fade
    a = pan.adv
    a.location = int(a.total_steps * 0.02)
    early = pan.text().markup              # markup, not plain: the arena is colour
    a.location = int(a.total_steps * 0.55)
    late = pan.text().markup
    assert early != late                   # the world moved with the pet


def test_towns_carry_their_canonical_backdrop():
    towns = data.load_towns()
    assert towns[0]["bg_habitat"] == 13        # towns.csv TownBackgroundID
    assert towns[0]["bg_habitat"] in data.load_habitats()


def test_town_lobby_is_a_scene_and_arrival_shows_the_town():
    from tuipet.townscreen import TownPanel
    p = _pet()
    pan = TownPanel(p, 0)
    lobby = pan.text()
    # box-clip repin 2026-07-04: the lobby fills the PHYSICAL LCD exactly
    # (12 rows); the errand picker rides the strip under it
    assert len(lobby.plain.split("\n")) == 12
    assert "Food" in pan.strip() and "Leave" in pan.strip()
    pan.key("enter")                           # into the food shop: menu grammar returns
    assert len(pan.text().plain.split("\n")) <= 12
    # the pages carry in-LCD menus AND pop the hint line (convention v0.2.399;
    # the silent box was the audit 2026-07-13 gap -- the home shop hinted here)
    assert "pick" in pan.strip() and "buy" in pan.strip()
    # adventure: stepping INSIDE the town's span swaps to the town backdrop
    ap = AdventurePanel(_pet())
    ap._trans = None                           # settled past the teleport
    a = ap.adv
    a.location = 4250                          # town 0 spans 4201-4300 in zone 1-1
    in_town = ap.text().markup
    a.location = 4350                          # same zone-bg span, just past the gates
    from tuipet.adventurescreen import FADE_T
    for _ in range(FADE_T + 1):                # let the cross-fade settle (v0.2.233)
        ap.text()
        ap.anim()
    outside = ap.text().markup
    assert in_town != outside


def test_tournament_scenes_use_the_standard_arena():
    from tuipet.tournamentscreen import FIGHT_ROWS
    assert FIGHT_ROWS == 12                    # was a squat 8-row band


def test_town_cup_interstitial_is_a_scene():
    from tuipet.townscreen import TownPanel
    from tuipet import tournament as tmod
    p = _pet()
    pan = TownPanel(p, 0)
    tr = next((t for t in (tmod.trophy_by_id(i) for i in range(40)) if t), None)
    assert tr is not None
    pan.tourney = tmod.Tournament(p, tr)
    assert len(pan.text().plain.split("\n")) == 12   # the faceoff fills the LCD
    assert "fight" in pan.strip()                     # controls ride the strip


def test_jogress_scenes_use_the_standard_arena():
    from tuipet import jogressscreen
    assert (jogressscreen.ROWS, jogressscreen.FUSE_ROWS) == (12, 12)


def test_dna_mash_is_a_staged_scene():
    from tuipet.dnascreen import DNAPanel
    p = _pet()
    pan = DNAPanel(p)
    pan.phase, pan.bet, pan.mash_f, pan.hits = "mash", 10, 20, 14
    idle = pan.text()
    assert len(idle.plain.split("\n")) == 12   # the arena fills the LCD
    assert "SPACE" in pan.strip()               # the meter rides the strip
    pan.key("space")                           # markup, not plain: sprites are colour
    assert pan.text().markup != idle.markup    # a press visibly moves the pet


def test_memorial_rests_in_the_home_scenery():
    from tuipet import deathscreen
    from tuipet.deathscreen import DeathPanel
    assert deathscreen.ROWS == 12
    p = _pet()
    p.dead = True
    pan = DeathPanel(p)
    assert len(pan.text().plain.split("\n")) == 12   # the grave fills the LCD
    assert "R.I.P." in pan.strip()                    # the epitaph rides the strip


# ---- adventure animation audit (2026-07-04): canon walk/discover/investigate ----

def test_travel_walk_steps_on_the_walk_beat():
    """The journey walk flips poses on WALK_BEAT (idleWalk cadence), not every
    0.1s tick -- the 10Hz flutter class the battle audit retired."""
    from tuipet.adventurescreen import WALK_BEAT
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the arrival fade
    pan.travelling = True
    def markup_at(f):
        pan.frame_i = f
        return pan.text().markup                  # arena = markup, never .plain
    assert markup_at(1) == markup_at(WALK_BEAT - 1)          # same beat, same pose
    assert markup_at(1) != markup_at(WALK_BEAT + 1)          # next beat steps


def test_discover_call_is_the_attention_bounce():
    """Canon DiscoverCall = attention(5,7): the pet bounces its cheer poses
    while the investigate prompt waits (it used to keep idling, text-only)."""
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the arrival fade
    pan.travelling = False
    pan.discovering = True
    pan.frame_i = 1
    call = pan.text().markup
    pan.frame_i = 7
    assert pan.text().markup != call              # 5 <-> 7 flip on the 6-tick beat
    pan.discovering = False
    pan.frame_i = 1
    assert pan.text().markup != call              # the bounce is not the idle stand


def test_investigate_plays_the_left_walk_and_seals_the_reveal():
    """Canon investigateLeft: walk LEFT, suspense dots, THEN the reveal -- the
    result message must not leak into the note before the reveal beat."""
    from tuipet.adventurescreen import INV_REVEAL_T, INV_END_T
    random.seed(1)
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the teleport
    pan.adv.location = pan.adv.total_steps // 2
    pan.discovering = True
    for seed in range(120):
        random.seed(seed)
        pan.key("enter")                          # resolves + starts the playbook
        if pan._scene is not None and pan._scene["kind"] == "item":
            break
        pan._scene, pan.discovering = None, True
    assert pan._scene and pan._scene["kind"] == "item" and pan._scene["icon"]
    sealed = pan._scene["msg"]
    assert "dug up" in sealed
    # box-clip repin 2026-07-04: the journey note rides the STRIP now
    for _ in range(INV_REVEAL_T - 2):
        assert sealed not in pan.strip()          # sealed until the reveal beat
        pan.anim()
    while pan._scene is not None:
        pan.anim()
        assert pan._scene is None or pan._scene["t"] <= INV_END_T
    assert sealed in pan.strip()                  # revealed
    assert pan.travelling                         # back on the road


def test_investigate_ambush_startles_then_opens_the_battle():
    from tuipet.adventurescreen import INV_REVEAL_T
    from tuipet.battlescreen import BattlePanel
    random.seed(1)
    pan = AdventurePanel(_pet())
    pan._trans = None                             # past the arrival fade
    pan.adv.location = pan.adv.total_steps // 2
    for seed in range(120):
        random.seed(seed)
        pan.discovering = True
        pan.key("enter")
        if pan._scene is not None and pan._scene["kind"] == "enemy":
            break
        pan._scene = None
    assert pan._scene and pan._scene["kind"] == "enemy"
    pan.key("space")                              # skip straight to the reveal
    assert pan._scene["t"] == INV_REVEAL_T - 1
    for _ in range(8):
        pan.anim()
    assert isinstance(pan.sub, BattlePanel)       # the ambush fight opened
    assert pan._scene is None


def test_habitat_change_cross_fades_not_snaps():
    """Canon BackgroundAnim.animateBack (2026-07-04): crossing into a new
    backdrop span fades old-over-new at -0.05 opacity/frame (20 ticks); the
    scenery used to SNAP mid-stride."""
    from tuipet.adventurescreen import FADE_T
    random.seed(7)
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the teleport
    a = pan.adv
    spans = a.zone.get("bgs", [])
    assert len(spans) >= 2
    pan.travelling = False
    a.location = spans[0][0]
    pan.text()                                   # settle on the first backdrop
    a.location = spans[1][0] + 1                 # stride across the boundary
    frames = []
    for _ in range(FADE_T + 3):
        frames.append(pan.text().markup)
        pan.anim()
    assert len(set(frames)) >= FADE_T - 2        # a smooth blend, not a snap
    assert frames[-1] == frames[-2]              # ...that settles on the new world


# ---- the adventure feel arc (Joel 2026-07-07: "adventure felt different in
# dvpet") -- Battle_Flash alert, battleWait escape, zoneChange pulse, pacing ----

def _mon(pan):
    """A wild card shaped like an enemies.csv row."""
    return {"num": 29, "name": "Kunemon", "stage": "Rookie",
            "attribute": "Virus", "hp": 5, "penalty": 200,
            "vaccine": 2, "data_power": 2, "virus": 2}


def test_encounter_opens_the_fight_directly():
    """Battles get NO transition and NO overlay -- the fight's own intro IS
    the battle screen (Joel 2026-07-07: the .359 Battle_Flash card is dead;
    no battleStart cards in the atlas either)."""
    from tuipet.battlescreen import BattlePanel
    from tuipet.adventurescreen import TRAVEL_TICKS
    assert "battleStart" not in data.load_backgrounds()
    pan = AdventurePanel(_pet())
    pan._trans = None
    pan.travelling = True
    pan.adv.travel = lambda: ("encounter", _mon(pan))
    for _ in range(TRAVEL_TICKS):
        pan.anim()
    assert isinstance(pan.sub, BattlePanel)
    assert pan._pending == (False, _mon(pan)) and not pan.travelling


def test_adventure_opens_with_the_teleport_leave_then_arrive():
    """The REAL habitat transition (Joel 2026-07-07, third strike): canon
    Teleport_Leave plays over the HOME habitat -- the striped curtain flashes
    at t3/t15/t21 (disappear=strongHit), swallows the pet at t23, shrinks to
    a sliver (shrink=attackHit) and departs off the top (attack) -- then the
    world swaps and Teleport_Arrive drops the sliver back in, expands it, and
    teleportAppear flickers the pet in on the ROAD.  Travel is held the whole
    way and begins only at endAnim."""
    from tuipet.adventurescreen import (TELE_LEAVE_SNDS, TELE_ARRIVE_SNDS)
    pan = AdventurePanel(_pet())
    assert pan._trans == {"dir": "in", "phase": "leave", "t": 0}
    assert not pan.travelling                     # canon holds until endAnim
    home = pan.text().markup                      # the pet standing at home
    snds, frames = [], {home}
    while pan._trans is not None and pan._trans["phase"] == "leave":
        pan.anim()
        frames.add(pan.text().markup)
        if getattr(pan, "sfx", None):
            snds.append(pan.sfx)
            pan.sfx = None
        assert pan.key("f") is None and pan.sub is None   # the anim owns the keys
    assert snds == [TELE_LEAVE_SNDS[k] for k in sorted(TELE_LEAVE_SNDS)]
    assert pan._trans == {"dir": "in", "phase": "arrive", "t": 0}
    while pan._trans is not None:
        pan.anim()
        frames.add(pan.text().markup)
        if getattr(pan, "sfx", None):
            snds.append(pan.sfx)
            pan.sfx = None
    assert snds[5:] == [TELE_ARRIVE_SNDS[k] for k in sorted(TELE_ARRIVE_SNDS)]
    assert len(frames) > 10                       # flashes/shrink/flicker all render
    assert pan.travelling                         # landed: the walk begins


def test_going_home_teleports_out_then_auto_closes():
    """ESC plays the same teleport the other way: leave on the road, the
    world swaps home at the phase boundary (away drops, home climate), the
    arrive flicker plays in the habitat, then the panel asks the app to
    close it (auto_close) -- canon teleportArrive toggles isHome at frame 0
    and teleportAppear ends with endAnim."""
    from tuipet.adventurescreen import TELE_LEAVE_T, TELE_ARRIVE_T
    pan = AdventurePanel(_pet())
    p = pan.pet
    pan._trans = None                            # settled on the road
    pan.travelling = True
    assert pan.key("escape") is None             # no instant close: the anim runs
    assert pan._trans == {"dir": "out", "phase": "leave", "t": 0}
    assert not pan.travelling
    assert pan.key("f") is None and pan.sub is None   # the anim owns the keys
    for _ in range(TELE_LEAVE_T):
        assert p.away                            # not home until the world swap
        pan.anim()
    assert not p.away                            # teleportArrive: home again
    assert p.habitat == p.home_habitat
    assert pan._trans["phase"] == "arrive"
    for _ in range(TELE_ARRIVE_T):
        pan.anim()
    assert pan._trans is None
    assert pan.auto_close == ("done", None)      # the app closes the panel


def test_out_of_life_plays_the_retreat_town_fade():
    """Canon Enum.State.Retreat_Town (SpriteAnim.retreatToTown): running out
    of adventure life fades the world to black over the dejected pet, the
    town reset waits under it, and the road resumes when it lifts."""
    from tuipet.adventurescreen import RETREAT_T
    pan = AdventurePanel(_pet())
    pan._trans = None
    a = pan.adv
    a.life = 1
    a.location = a.stride * 3
    a._lose_life("Lost...", 0)                   # the model side retreats
    assert a.retreated and a.life == 3           # toClosestTown + the refill
    assert a.location <= a.stride * 3            # never forward of the fall
    a.retreated = False                          # the view pops the flag
    pan._retreat = {"t": 0}                      # ...and plays the fade
    pan.travelling = False
    frames = set()
    while pan._retreat is not None:
        assert pan.key("f") is None and pan.sub is None
        pan.anim()
        frames.add(pan.text().markup)
        assert pan._retreat is None or pan._retreat["t"] <= RETREAT_T
    assert len(frames) > 5                       # the black steps down and back up
    assert pan.travelling                        # regrouped: the road resumes


def test_zone_clear_plays_the_pulse_transition():
    """Canon SpriteAnim.zoneChange: four zonePulse beats (interval*5/15/25/35)
    before the road resumes -- the zone used to advance with no beat at all."""
    from tuipet.adventurescreen import PULSE_T, PULSE_ON, TRAVEL_TICKS
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the teleport
    a = pan.adv
    a.travel = lambda: ("zone", None)
    pan.travelling = True
    for _ in range(TRAVEL_TICKS):
        pan.anim()
    assert pan._pulse is not None and not pan.travelling
    assert pan.key("space") is None and pan._pulse is not None   # not skippable
    lit, dark = None, None
    while pan._pulse is not None:
        t = pan._pulse["t"]
        m = pan.text().markup
        if any(on <= t < off for on, off in PULSE_ON):
            lit = m
        elif t < PULSE_ON[0][0]:
            dark = m
        pan.anim()
        assert pan._pulse is None or pan._pulse["t"] <= PULSE_T
    assert lit and dark and lit != dark          # the light actually pulses
    assert pan.travelling                        # then the road resumes


def test_travel_paces_one_stride_per_second():
    """The compression's pacing knob (TRAVEL_TICKS): one auto-stride per 1s of
    0.1s ticks -- at the old 3 ticks the whole zone crossed in ~12s and zone
    1's twelve scenes strobed ~1/s."""
    from tuipet.adventurescreen import TRAVEL_TICKS
    assert TRAVEL_TICKS == 10
    pan = AdventurePanel(_pet())
    pan._trans = None                             # settled past the teleport
    pan.travelling = True
    moved = []
    pan.adv.travel = lambda: moved.append(1)
    for _ in range(TRAVEL_TICKS - 1):
        pan.anim()
    assert not moved                             # not yet
    pan.anim()
    assert len(moved) == 1                       # the stride lands on the beat


# ---- road care beats (Joel 2026-07-07: "make sure action animations like
# praise and scold work ... and adventure mode") ----

def _road(travelling=True):
    p = _pet()
    p.world_seconds = 12 * 60.0
    p.obedience = 1000                            # no refusal noise in the beats
    p.compliance = True
    pan = AdventurePanel(p)
    pan._trans = None                             # settled past the teleport
    pan.travelling = travelling
    return pan, p


def test_road_praise_plays_the_cheer_beat_and_resumes_travel():
    """A landed praise mirrors the home cheer fx on the arena (poses 5/7 with
    the happy emote on up-beats), holds travel while it plays, then the road
    resumes -- the key used to act text-only."""
    from tuipet.adventurescreen import CARE_T
    pan, p = _road()
    p.praise_flag = True                          # a well-timed praise
    pan.key("r")
    assert p.anim == "happy"
    assert pan._care == {"kind": "cheer", "good": True, "t": 0, "resume": True}
    assert not pan.travelling                     # the beat holds the walk
    up = pan.text().markup                        # up-beat pose + emote
    for _ in range(6):
        pan.anim()
    assert pan.text().markup != up                # the bounce actually bounces
    assert pan._care is not None                  # the beat is still playing
    while pan._care is not None:
        pan.anim()
        assert pan._care is None or pan._care["t"] <= CARE_T
    assert pan.travelling                         # back on the road


def test_road_bad_scold_slumps_and_care_keys_lock():
    """Mis-scolding an innocent plays the Bad_Scold slump (10/9); a second
    care press during the beat is swallowed (the home fx guard)."""
    pan, p = _road(travelling=False)
    p.praise_flag = True                          # it did nothing wrong
    pan.key("k")
    assert p.anim == "sad"
    assert pan._care and pan._care["kind"] == "jeer" and not pan._care["good"]
    assert pan._care["resume"] is False
    msg = pan.adv.last
    pan.key("r")                                  # locked while the beat plays
    assert pan.adv.last == msg and pan._care["kind"] == "jeer"
    lights0 = p.lights
    pan.key("s")                                  # every care key locks
    assert p.lights == lights0
    while pan._care is not None:
        pan.anim()
    assert not pan.travelling                     # resume honours the held walk


def test_road_heal_bandages_then_chains_the_cheer():
    """Canon bandage(): hurt pose + the i:80 strip, then cheer(true) chains --
    exactly the home heal fx, on the road."""
    from tuipet.adventurescreen import HEAL_T
    pan, p = _road(travelling=False)
    p.injury = True
    p.inj_length = 4
    pan.key("h")
    assert p.anim == "heal"
    assert pan._care and pan._care["kind"] == "heal"
    frame = pan.text().markup                     # the bandage beat renders
    for _ in range(HEAL_T):
        pan.anim()
    assert pan._care and pan._care["kind"] == "cheer"   # the chain
    assert pan.text().markup != frame
    while pan._care is not None:
        pan.anim()


def test_road_care_beat_sounds_are_canon_scripted():
    """cheer stings happy@1, jeer angry@6, heal click@8/13 confirm@18 (the
    home fx snds tables)."""
    pan, p = _road(travelling=False)
    p.scold_flag = True                           # a deserved scold
    pan.key("k")
    assert pan._care["kind"] == "jeer" and pan._care["good"]
    heard = {}
    while pan._care is not None:
        t = pan._care["t"]
        pan.sfx = None
        pan.anim()
        if pan.sfx:
            heard[t] = pan.sfx
    assert heard == {6: "angry"}
