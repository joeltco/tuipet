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
    assert pan.strip() == ""                   # pages carry their own in-LCD chrome
    # adventure: stepping INSIDE the town's span swaps to the town backdrop
    ap = AdventurePanel(_pet())
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


def test_investigate_ambush_startles_then_flashes_the_alert():
    """Canon onDiscoverEnemy -> checkWildEncounter: an ambush ALERTS through
    the same Battle_Flash as any wild -- it used to open the fight unannounced
    (adventure feel arc 2026-07-07)."""
    from tuipet.adventurescreen import INV_REVEAL_T
    from tuipet.battlescreen import BattlePanel
    random.seed(1)
    pan = AdventurePanel(_pet())
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
    assert pan._flash is not None                 # the ambush alerts first
    assert pan._scene is None and pan.sub is None
    pan.key("space")                              # engage
    assert isinstance(pan.sub, BattlePanel)


def test_habitat_change_cross_fades_not_snaps():
    """Canon BackgroundAnim.animateBack (2026-07-04): crossing into a new
    backdrop span fades old-over-new at -0.05 opacity/frame (20 ticks); the
    scenery used to SNAP mid-stride."""
    from tuipet.adventurescreen import FADE_T
    random.seed(7)
    pan = AdventurePanel(_pet())
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


def test_flash_cards_ride_the_background_atlas():
    """The REAL battleStart/battleStartFlash rips (jar resources) live in the
    atlas as full-window cards -- never drawn, extracted."""
    bgs = data.load_backgrounds()
    for card in ("battleStart", "battleStartFlash"):
        assert card in bgs and len(bgs[card][0]) == 24    # 40x24 window card


def test_encounter_alerts_before_the_fight():
    """Canon checkWildEncounter: a wild trigger stops travel and FLASHES the
    alert (Battle_Flash); the fight opens on the player's press -- it used to
    open unannounced."""
    from tuipet.battlescreen import BattlePanel
    from tuipet.adventurescreen import TRAVEL_TICKS, FLASH_ALT_T
    pan = AdventurePanel(_pet())
    pan.travelling = True
    pan.adv.travel = lambda: ("encounter", _mon(pan))
    for _ in range(TRAVEL_TICKS):
        pan.anim()
    assert pan._flash is not None and pan.sub is None
    assert not pan.travelling
    a = pan.text().markup                        # the card alternates its flash
    for _ in range(FLASH_ALT_T):
        pan.anim()
    assert pan.text().markup != a
    assert "SPACE fight" in pan.strip()
    pan.key("f")                                 # care keys are locked out
    assert pan.sub is None
    pan.key("enter")                             # engage
    assert isinstance(pan.sub, BattlePanel) and pan._pending == (False, _mon(pan))


def test_ignored_flash_escapes_with_the_knockback():
    """WorldMap.battleWait: BattleWait(720 fires ~= 514 ticks) unanswered ->
    the foe escapes, lossPenalty knocks the pet back, travel stays stopped
    (canon lossPenalty zeroes travelSpeed)."""
    from tuipet.adventurescreen import FLASH_WAIT_T
    pan = AdventurePanel(_pet())
    pan.adv.location = 5000
    pan._flash = {"t": 0, "boss": False, "enemy": _mon(pan)}
    pan.travelling = False
    for _ in range(FLASH_WAIT_T + 1):
        pan.anim()
    assert pan._flash is None and pan.sub is None
    assert pan.adv.location == 4800              # Penalty 200 steps back
    assert not pan.travelling
    assert "left" in pan.adv.last


def test_ignored_boss_flash_rearms_the_gate():
    """A boss alert waited out knocks back past the gate so the boss re-arms
    (flee's re-arm clamp) -- the gate can never be skipped by waiting."""
    from tuipet.adventurescreen import FLASH_WAIT_T
    pan = AdventurePanel(_pet())
    boss = dict(_mon(pan), location=6000, penalty=0)
    pan.adv.location = 6000
    pan._flash = {"t": 0, "boss": True, "enemy": boss}
    for _ in range(FLASH_WAIT_T + 1):
        pan.anim()
    assert pan.adv.location < 6000               # behind the gate again


def test_zone_clear_plays_the_pulse_transition():
    """Canon SpriteAnim.zoneChange: four zonePulse beats (interval*5/15/25/35)
    before the road resumes -- the zone used to advance with no beat at all."""
    from tuipet.adventurescreen import PULSE_T, PULSE_ON, TRAVEL_TICKS
    pan = AdventurePanel(_pet())
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
    assert pan.anim() or True
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
