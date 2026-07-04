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
    for sel in ("up", "right", "left"):                   # vaccine / virus / data props:
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
    for sel, want in (("left", False), ("down", True), ("up", False)):
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
