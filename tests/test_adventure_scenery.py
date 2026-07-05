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
    assert "mash SPACE" in pan.strip()          # the meter rides the strip
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


def test_investigate_ambush_startles_then_opens_the_battle():
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
    assert isinstance(pan.sub, BattlePanel)       # the ambush fight opened
    assert pan._scene is None


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
