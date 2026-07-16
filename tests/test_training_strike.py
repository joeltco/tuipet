"""The DVPet training strike sequence (ANIMATION_SPEC.md §6): after the skill drill
the pet fires at the punching bag (or green target), it flashes, then breaks on
success / the pet recoils on a fail -- attackDefault -> hitAnim -> aftermathDefault.
Reuses the projectile + impact-flash art already in effects.json.gz and battle's
strong-vs-normal attack/hit sounds."""
from tuipet import training as T, data
from tuipet.pet import Pet


def _panel(game="vaccine"):
    p = Pet(num=1, stage="Rookie", vaccine=5, data_power=5, virus=5)
    p.obedience = 500            # out-roll checkRefused: these tests exercise the drills
    panel = T.TrainingPanel(p)
    panel.gi = {"hp": 0, "vaccine": 1, "data": 2, "virus": 3}[game]
    return panel


def test_finish_launches_the_strike_then_reveals_result():
    panel = _panel()
    panel._finish(2, 30, "Vaccine", "vaccine")
    assert panel.phase == "strike"          # not straight to "done"
    assert panel.si == 0 and panel.strike_tl   # a battle-style volley timeline is built
    assert panel.result                     # the outcome is decided, just not shown yet
    assert panel.flash == ""                # ...held until the strike lands
    # drive the volley to completion -> the score is revealed
    for _ in range(len(panel.strike_tl) + 2):
        panel.anim()
    assert panel.phase == "done"
    assert panel.result in panel.flash      # score revealed when the strike completes


def test_strike_sfx_timing_and_strength():
    def sfx_seq(hits):
        panel = _panel()
        panel._finish(hits, 30, "Vaccine", "vaccine")
        seq = []
        while panel.phase == "strike":
            panel.sfx = None
            panel.anim()
            if panel.sfx:
                seq.append(panel.sfx)
        return seq

    strong = sfx_seq(3)
    assert strong[0] == "strongAttack"      # launch sting (full success), then...
    assert "strongHit" in strong            # ...the strong impact on the target
    good = sfx_seq(2)
    assert good[0] == "attack"
    assert "attackHit" in good
    miss = sfx_seq(0)
    assert miss[0] == "attack"              # the pet still fires...
    assert "cancel" in miss                 # ...but the orb whiffs (no hit -> miss thud)


def test_strike_renders_every_drill_and_can_skip():
    for game in ("hp", "vaccine", "data", "virus"):
        for hits in (3, 2, 0):
            panel = _panel(game)
            panel._finish(hits, 30, None if game == "hp" else "Vaccine", game)
            steps_seen = 0
            while panel.phase == "strike" and steps_seen < 80:
                assert panel.text() is not None            # composes without error every frame
                panel.anim()
                steps_seen += 1
            assert panel.phase == "done"
    # a key during the volley skips to the end (like the battle screen)
    panel = _panel("vaccine")
    panel._finish(2, 30, "Vaccine", "vaccine")
    assert panel.key("space") is None
    panel.anim()
    assert panel.phase == "done"


def test_strike_opponent_art_exists():
    e = data.load_effects()
    for k in ("punching_bag", "punching_bag_broken", "train_green", "attack", "flash"):
        assert k in e and e[k], f"missing strike asset: {k}"


# ---- DVPet-faithful drill mechanics (the rebuild) --------------------------

def test_hp_drill_matches_the_dummy_attribute():
    """HP = read the dummy's attribute, pick the matching icon; first to 2 wins -> Effort
    (DVPet drawHPTraining: loop while round < 3 AND roundsWon < 2)."""
    panel = _panel("hp")
    panel._start_game()
    assert panel.phase == "play"
    for _ in range(T.HP_ROUNDS):                       # match correctly every round
        if panel.phase != "play":
            break
        panel.hp_pick = panel.hp_target               # read the dummy -> pick the match
        panel.key("space")
    # two correct matches ends it immediately (early-exit at _hpTrainingRoundsWon), a full success.
    assert panel.rounds_won == T.HP_ROUNDS_WON
    assert panel.success and panel._strong
    # HP now fires the SAME battle volley as vaccine/virus before revealing the score
    assert panel.phase == "strike"
    for _ in range(len(panel.strike_tl) + 2):
        panel.anim()
    assert panel.phase == "done"


def test_hp_timeout_counts_as_wrong():
    panel = _panel("hp")
    panel._start_game()
    for _ in range(T.HP_ROUNDS * (max(T.HP_ROUND_LEN) + 1)):
        if panel.phase != "play":
            break
        panel.anim()                                   # never guess -> every round times out
    assert panel.rounds_won == 0 and not panel.success


def test_data_drill_is_the_dm20_versus_training():
    """The REAL DM20 tag training (humulos manual): "you choose to fire a high
    shot or a low shot.  If your shot gets past your partner's shield, you
    succeed.  You need to succeed 3 out of the 5 rounds."  Fire opposite the
    chart's shield -> past; into it -> blocked; 3 of 5 passes the session.
    (Replaces the fan-made turret duel -- Joel 2026-07-13: "i dont think this
    system is canon at all", and it wasn't.)"""
    def play(win_rounds):
        panel = _panel("data")
        panel._start_game()
        for r in range(T.DATA_ROUNDS):
            shield_up = panel.tt_shield[r]
            want_past = r in win_rounds
            panel.key("down" if shield_up == want_past else "up")
            assert panel.fired
            for _ in range(len(panel.tt_tl) + 1):      # the round volley plays out
                panel.anim()
        return panel
    panel = play({0, 1, 2})                            # 3 of 5 -> success
    assert panel.phase == "done" and panel.tt_past == 3 and panel.success
    panel = play({0, 4})                               # 2 of 5 -> fail
    assert panel.phase == "done" and panel.tt_past == 2 and not panel.success


def test_data_chart_is_the_manual_verbatim():
    """The manual's repeating cheat chart, ported exactly: "pressing the
    buttons according to the chart below will let you win tag training every
    time" -- rows ABABB/BBAAB/BAABB/ABBAA/BABAB/ABABA, A=HIGH (tuipet's one
    documented adaptation), sessions cycling by data_trainings (VERSUS sessions
    alone -- other drills between sessions must not shift the printed pattern,
    audit 2026-07-13)."""
    assert T.DATA_WIN_CHART == ("ABABB", "BBAAB", "BAABB", "ABBAA", "BABAB", "ABABA")
    for session in range(8):                           # ...and it REPEATS past row 6
        panel = _panel("data")
        panel.pet.data_trainings = session
        panel.pet.stage_trainings = session * 7 + 3    # noise: other drills played too
        panel.key("enter")
        row = T.DATA_WIN_CHART[session % 6]
        for c in row:                                  # play the printed winning buttons
            panel.key("up" if c == "A" else "down")
            assert not panel.blocked, f"session {session}: the cheat chart must win"
            for _ in range(len(panel.tt_tl) + 1):
                panel.anim()
        assert panel.tt_past == T.DATA_ROUNDS and panel.success


def test_data_round_volley_beats():
    """Each round is a mini battle volley: fire_out -> fire_in -> hit strobe
    (past) or blocked tableau; the pick act waits on the player (turn-based)."""
    panel = _panel("data")
    panel._start_game()
    for _ in range(20):
        panel.anim()                                   # the pick act never advances itself
    assert not panel.fired and panel.tt_round == 0
    shield_up = panel.tt_shield[0]
    panel.key("down" if shield_up else "up")           # fire PAST
    ms = []
    while panel.fired:
        ms.append(panel.tt_tl[panel.tt_i]["m"])
        panel.anim()
    assert "fire_out" in ms and "fire_in" in ms and "hit" in ms and "block" not in ms
    assert panel.tt_round == 1 and panel.tt_past == 1
    panel.key("up" if panel.tt_shield[1] else "down")  # fire INTO the shield
    ms = []
    while panel.fired:
        ms.append(panel.tt_tl[panel.tt_i]["m"])
        panel.anim()
    assert "block" in ms and "hit" not in ms
    assert panel.tt_past == 1



def test_data_geometry_never_mashes():
    """Canon rebuild 2026-07-13: every act of the versus training (pick faceoff /
    fire_out / fire_in+shield / hit strobe / aftermath) renders inside the LCD,
    driven through a full real session."""
    import random
    random.seed(3)
    p = Pet(num=102, stage="Champion", vaccine=5, data_power=5, virus=5)
    p.obedience = 500
    panel = T.TrainingPanel(p)
    panel.gi = 2
    panel.key("enter")
    assert panel.phase == "play"
    for _ in range(3000):
        if panel.phase == "done":
            break
        if panel.phase == "play" and not panel.fired:
            panel.key("up")                            # fire high every round
        panel.anim()
        assert all(len(r) <= T.COLS for r in panel.text().plain.split("\n"))
    assert panel.phase == "done"



def test_virus_geometry_and_the_strike_clamp():
    """Virus layout audit (Joel 2026-07-06) -- CLEAN, pin the load-bearers:
    the track keeps symmetric margins (x4..35, y from the band top -- no
    border touches; the drill has no mon on stage), and the SHARED strike
    placement (all four drills ride it) clamps the widest mon in-bounds even
    at full rear-back (place_combatant's clamp_grid)."""
    import random
    from tuipet import data as _d, strikefx
    random.seed(3)
    p = Pet(num=102, stage="Champion", vaccine=5, data_power=5, virus=5)
    p.obedience = 500
    panel = T.TrainingPanel(p)
    panel.gi = 3
    panel.key("enter")
    for _ in range(10):
        panel.anim()
        assert all(len(r) <= T.COLS for r in panel.text().plain.split("\n"))
    pf = _d.load_sprites()[1][102]["frames"][0]
    for xshift in (0, 3, -2):                       # windup rear-back / release lunge
        placements, _mouth = strikefx.place_combatant(True, pf, xshift)
        fr, x, _m = placements[0]
        assert x + max(len(r) for r in fr) - 1 <= T.COLS - 1, f"clipped at xshift {xshift}"
    panel.key("space")                              # stop -> the shared volley -> done
    for _ in range(80):
        panel.anim()
        assert all(len(r) <= T.COLS for r in panel.text().plain.split("\n"))
        if panel.phase == "done":
            break
    assert panel.phase == "done"
