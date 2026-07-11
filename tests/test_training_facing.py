"""Training-target facing audit (2026-07): every drill target faces the right
way in every phase, per the decompile.

Canon: the HP dummy is a creature stand-in -- drawHPTraining places it left
with drawNumMirror(bag, TRUE), and drawNum preserves _isMirror so the taunt
stays flipped.  The punching bag and the cannon are PROPS swapped in via
setAltIcon, which never flips: the bag (and punchingBagBroken in
aftermathDefault) keeps its sheet facing, and the cannon's barrel faces
right off the sheet -- toward the pet -- in aftermathGreen's done view.

tuipet had the dummy RAW in the pick round and the props MIRRORED in the
strike volley + done scene (faceoff's creature default)."""
from tuipet.pet import Pet
from tuipet import training, strikefx, grid


def _panel(sel):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=1000)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    p.check_refused = lambda **kw: False
    tp = training.TrainingPanel(p)
    tp.key(sel)
    tp.key("enter")
    return tp


def test_target_mirror_matches_canon_per_drill():
    assert _panel("down")._target_mirror() is True        # hp dummy: drawNumMirror(.., true)
    assert _panel("left")._target_mirror() is True        # data sparring partner: creature stand-in
    for sel in ("up", "right"):                           # vaccine / virus props:
        assert _panel(sel)._target_mirror() is False      # setAltIcon never flips


def test_place_combatant_prop_keeps_sheet_facing():
    rows = ["1100", "1000"]                               # asymmetric probe
    (pl, mouth) = strikefx.place_combatant(False, rows, mirror=False)
    assert pl[0][2] is False and pl[0][0] == rows         # native facing kept
    assert mouth == pl[0][1] + 2                          # mouth = content right edge
    (pl_m, _) = strikefx.place_combatant(False, rows)     # creature default unchanged
    assert pl_m[0][2] is True


def test_hp_pick_round_shows_the_dummy_mirrored(monkeypatch):
    tp = _panel("down")
    seen = {}
    real = training.render_scene
    def spy(placements, *a, **kw):
        seen["placements"] = placements
        return real(placements, *a, **kw)
    monkeypatch.setattr(training, "render_scene", spy)
    tp.text()
    (rows, x, mirror) = seen["placements"][0]
    assert mirror is True                                 # the dummy faces the picker


def test_done_scene_props_face_the_pet(monkeypatch):
    real = grid.faceoff
    for sel, want in (("left", True), ("down", True), ("up", False)):
        tp = _panel(sel)
        tp._finish(3, 60, {"left": "Data", "down": None, "up": "Vaccine"}[sel]
                   or ("Vaccine", "Data", "Virus")[tp.hp_target],
                   {"left": "data", "down": "hp", "up": "vaccine"}[sel])
        tp.phase = "done"                                 # jump volleys straight to the reveal
        seen = {}
        monkeypatch.setattr(training.grid, "faceoff",
                            lambda l, r, left_mirror=True, **kw:
                            seen.update(m=left_mirror) or real(l, r, left_mirror=left_mirror, **kw))
        tp.text()
        assert seen["m"] is want, f"{sel}: done-scene target mirror {seen['m']} != canon {want}"


def test_strike_volley_target_facing(monkeypatch):
    real = strikefx.place_combatant
    for sel, want in (("up", False), ("down", True)):     # bag native / dummy mirrored
        tp = _panel(sel)
        if sel == "up":
            tp.timer = 0
            tp.taps = 99
            tp.anim()                                     # eval -> strike phase
        else:
            tp._hp_resolve(True)
            while tp.phase == "play":
                tp.anim()
        assert tp.phase == "strike"
        seen = {}
        def spy(faces_left, rows, xshift=0, mirror=True):
            if not faces_left:
                seen["m"] = mirror
            return real(faces_left, rows, xshift, mirror)
        monkeypatch.setattr(training.strikefx, "place_combatant", spy)
        for _ in range(80):                               # walk the volley through fire_in/break
            tp.anim()
            tp.text()
            if tp.phase == "done":
                break
        assert seen.get("m") is want, f"{sel}: volley target mirror {seen.get('m')} != canon {want}"


def test_vaccine_scene_shows_the_punch():
    """Polish 2026-07-04: the vaccine drill is a STAGED scene (bag left, pet
    right), and a tap visibly changes the arena -- the old drill rendered an
    identical static bag no matter how hard you mashed."""
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "vaccine")
    pan._start_game()
    idle = pan.text().markup               # .plain strips the arena (all "▀" cells --
    pan.key("space")                        # sprites live in the COLORS, audit 2026-07-04)
    punch = pan.text().markup
    assert punch != idle
    assert pan._strike_t > 0 and pan._strike_pose == 6


def test_hp_pick_round_shows_the_reacting_pet():
    """Restage 2026-07-04: canon drawHPTraining has the char on-screen reacting
    to every guess -- the reaction pose must be VISIBLE, not a hidden state."""
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "hp")
    pan._start_game()
    idle = pan.text().markup                   # markup, not plain: the arena is colour
    pan._strike_pose, pan._strike_t = 6, 4     # the right-pick reaction, target unchanged
    assert pan.text().markup != idle           # ...and it shows on the arena


def test_data_pick_act_is_the_faceoff():
    """Canon versus training: the PICK act stages the sparring partner (the
    square-marked dummy, mirrored to face the mon) and the bobbing mon as a
    faceoff -- both on stage, waiting on UP/DOWN."""
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "data")
    pan._start_game()
    assert not pan.fired                       # the pick act
    pan.frame_i = 0
    a = pan.text().markup
    pan.frame_i = 2                            # bob pose 1 -- the mon is alive on stage
    b = pan.text().markup
    assert a != b, "the bobbing mon must be visible during the PICK act"



def _data_panel():
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "data")
    pan._start_game()
    return pan


def test_hp_stage_takes_turns_and_the_mon_reacts():
    """The HP drill is time-multiplexed now (window LAW 2026-07-11): the REEL
    act shows dummy + target/pick with the mon offstage; every SPACE cuts to
    the REACTION act, where the mon plays its 6/9 pose beside the dummy.
    (The old always-on-stage idle bob died with the bezel-leaking layout.)"""
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "hp")
    pan._start_game()
    pan._strike_t = 0                          # the reel act: mon offstage, icons up
    reel = pan.text().markup
    pan._strike_t = 4                          # the reaction act: the mon on stage
    pan._strike_pose = 6
    right = pan.text().markup
    assert right != reel, "reel and reaction are different stages"
    pan._strike_pose = 9
    assert pan.text().markup != right, "the 6/9 reaction poses must differ"


def test_data_round_tells_ride_the_next_pick():
    """One reaction language across the drills: a shot that gets PAST wears the
    hit tell (pose 6) into the next pick act; a blocked one wears the miss tell
    (pose 9) -- same as the HP drill's right/wrong picks."""
    pan = _data_panel()
    pan.key("down" if pan.tt_shield[0] else "up")      # past
    while pan.fired:
        pan.anim()
    assert (pan._strike_pose, pan._strike_t > 0) == (6, True)
    pan2 = _data_panel()
    pan2.key("up" if pan2.tt_shield[0] else "down")    # blocked
    while pan2.fired:
        pan2.anim()
    assert (pan2._strike_pose, pan2._strike_t > 0) == (9, True)



def test_data_fire_out_wears_the_attack_pose(monkeypatch):
    """The mon's own view of its shot: the fire_out beat stages the mon alone
    in the battle's ATTACK pose, its real orb leaving along the picked lane."""
    from tuipet import training
    pan = _data_panel()
    idle = pan.text().markup
    pan.key("up")
    assert pan.tt_tl[pan.tt_i]["m"] == "fire_out"
    assert pan.text().markup != idle           # a different stage entirely



def test_punch_hit_banner_takes_over_the_window(monkeypatch):
    """Joel 2026-07-12: the Hit!! banner is a FULL-WINDOW 32x16 banner,
    staged like the battle start banner -- on the strike beat the scene
    YIELDS (no bag, no pet) and the 2x-upscaled banner owns the window;
    between taps the bag/pet scene is back and the banner is gone."""
    from tuipet import training, grid
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    seen = {}
    real = training.render_scene

    def spy(placements, *a, **kw):
        seen["placements"] = list(placements)
        seen["overlay"] = list(kw.get("overlay") or [])
        return real(placements, *a, **kw)

    monkeypatch.setattr(training, "render_scene", spy)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "vaccine")
    pan._start_game()
    pan._strike_t = 0
    pan.text()
    assert seen["placements"], "between taps: the bag is on stage"
    idle_ov = set(seen["overlay"])
    pan._strike_t = 3
    pan._strike_pose = 6
    pan.text()
    assert not seen["placements"], "strike beat: the scene yields"
    ov = seen["overlay"]
    assert ov and set(ov) != idle_ov
    assert all(grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
               for x, y in ov)
    w = max(x for x, _ in ov) - min(x for x, _ in ov) + 1
    h = max(y for _, y in ov) - min(y for _, y in ov) + 1
    assert (w, h) == (26, 10), (w, h)          # the 2x banner fills the band
def test_hit_banner_is_the_native_4x_decode():
    """trainHit.png is the ONE training asset authored at 4x -- the blanket
    3x extraction mushed it to 17x6 (Joel 2026-07-12: 'out of resolution').
    The vendored sprite is the exact 13x5 native decode; a blanket
    re-extraction at F=3 would regress it."""
    from tuipet import data
    hit = data.load_effects()["train_hit"][0]
    assert (max(len(r) for r in hit), len(hit)) == (13, 5)
    assert sum(r.count("1") for r in hit) == 30
def test_hit_explosion_is_the_sourced_32x16_full_window_flash(monkeypatch):
    """Joel 2026-07-12: the orb-impact explosion is a 32x16 banner-class
    flash, like the battle start banner.  It was: commit 852e663 sourced
    hit_explosion from DMU at 32x16 -- the invented-art revert (3d7a6af)
    put back WRONG 30x18/22x12 frames for this one key, undersized AND
    clipped (18 > the 16px band).  Pin the sourced frames and that both
    collision paths strobe them alone, filling the window exactly."""
    from tuipet import training, grid
    from tuipet.training import TrainingPanel, GAMES, EXPLODE_FRAMES, _EXPLODE
    from tuipet.pet import Pet
    assert [(max(len(r) for r in f), len(f)) for f in _EXPLODE] \
        == [(32, 16), (32, 16)]
    seen = {}
    real = training.render_scene

    def spy(placements, *a, **kw):
        seen["placements"] = list(placements)
        seen["overlay"] = list(kw.get("overlay") or [])
        return real(placements, *a, **kw)

    monkeypatch.setattr(training, "render_scene", spy)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True

    def full_window():
        xs = [x for x, _ in seen["overlay"]]
        ys = [y for _, y in seen["overlay"]]
        return (min(xs), max(xs), min(ys), max(ys)) \
            == (grid.X0, grid.X1 - 1, grid.TOP, grid.FLOOR - 1)

    pan = TrainingPanel(p)                       # data drill: a shot gets PAST
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "data")
    pan._start_game()
    pan.key("down" if pan.tt_shield[0] else "up")
    pan.tt_i = next(i for i, fr in enumerate(pan.tt_tl) if fr["m"] == "hit")
    pan.text()
    assert full_window()
    pan2 = TrainingPanel(p)                      # strike volley 'hit' beat
    pan2.gi = next(i for i, g in enumerate(GAMES) if g[0] == "hp")
    pan2._start_game()
    pan2.success = True
    pan2._build_strike()
    pan2.phase = "strike"
    pan2.si = next(i for i, fr in enumerate(pan2.strike_tl)
                   if fr.get("m") == "hit")
    pan2.text()
    assert not seen["placements"] and full_window()

def test_data_stage_never_covers_the_mon(monkeypatch):
    """Canon rebuild 2026-07-13 (Joel: "mons face is gettimg cut off by
    shield"): the versus staging can NEVER cover the mon -- the shield lives
    on the PARTNER's side, and the mon's acts (pick faceoff, fire_out) put
    nothing in front of it.  Pin: in every mon-bearing act, no overlay ink
    within the mon's cell half (x20..35) except the mon/orb the act stages,
    and the shield only ever appears in the partner's view."""
    from tuipet import training, grid
    from tuipet.training import TrainingPanel, GAMES
    from tuipet.pet import Pet
    seen = {}
    real = training.render_scene

    def spy(placements, *a, **kw):
        seen["placements"] = list(placements)
        seen["overlay"] = list(kw.get("overlay") or [])
        return real(placements, *a, **kw)

    monkeypatch.setattr(training, "render_scene", spy)
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.compliance = True
    pan = TrainingPanel(p)
    pan.gi = next(i for i, g in enumerate(GAMES) if g[0] == "data")
    pan._start_game()
    pan.text()                                  # PICK: pure faceoff, no overlay props at all
    assert seen["placements"] and not seen["overlay"], \
        "the pick act is a clean faceoff -- nothing overlays the mon"
    pan.key("up")                               # fire HIGH
    pan.text()                                  # FIRE_OUT: the mon + its own orb, nothing else
    assert seen["placements"], "the mon holds the stage on fire_out"
    orb_ink = seen["overlay"]
    assert orb_ink and all(y <= grid.TOP + 8 for _, y in orb_ink), \
        "only the orb rides the fire_out overlay, in the picked (HIGH) lane"
    pan.tt_i = next(i for i, fr in enumerate(pan.tt_tl) if fr["m"] == "fire_in")
    pan.text()                                  # FIRE_IN: partner's view -- the mon is OFFSTAGE
    assert not seen["placements"], "the mon is offstage while the shield shows"
    shield_zone = [pt for pt in seen["overlay"] if pt[0] <= grid.X0 + 15]
    assert shield_zone, "partner + shield hold the left"
