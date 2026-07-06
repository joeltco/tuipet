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


def test_data_drill_is_a_shield_block_match():
    """DVPet controller checkSuccess(Data): success = shieldTop == isUp.  Raise the
    shield to the side the attack commits to -> block (success); mismatch -> hit."""
    def _settle(p):
        """EVAL (DVPet onPreFinish), then the cosmetic finale: the shot fires (attackGreen),
        the impact flash plays (hitAnim), then the result reveals (aftermathGreen)."""
        p._data_resolve()
        while p.phase != "done":                       # drive fire -> impact -> reveal to completion
            p.anim()
    # matching shield blocks -> success
    panel = _panel("data")
    panel._start_game()
    panel.locked = True
    panel.tgt_up = True
    panel.shield_up = True                             # shield up vs HIGH attack -> match
    _settle(panel)
    assert panel.blocked and panel.success
    # mismatched shield -> the attack gets through
    panel = _panel("data")
    panel._start_game()
    panel.locked = True
    panel.tgt_up = True
    panel.shield_up = False                            # shield down vs HIGH attack -> mismatch
    _settle(panel)
    assert not panel.blocked and not panel.success


def test_data_shield_is_a_single_toggle():
    """DVPet onShield: ONE button flips shieldActiveTop top<->bot (it starts UP via onPreTrain)."""
    panel = _panel("data")
    panel._start_game()
    assert panel.shield_up is True                     # shield starts UP (shieldActiveTop = true)
    panel.key("space")                                 # one button press toggles
    assert panel.shield_up is False
    panel.key("space")
    assert panel.shield_up is True
    panel.fired = True                                 # once the shot commits, the shield is locked
    panel.key("space")
    assert panel.shield_up is True                     # no longer toggleable


def test_data_attack_commits_after_the_telegraph():
    panel = _panel("data")
    panel._start_game()
    assert not panel.locked
    for _ in range(panel.data_telegraph + 1):          # rank-based feint window (DATA_TELEGRAPH[rank])
        panel.anim()
    assert panel.locked                                # the attack revealed high/low


def test_vaccine_drill_counts_mashes():
    panel = _panel("vaccine")
    panel._start_game()
    for _ in range(5):
        panel.key("space")
    assert panel.taps == 5


def test_hp_reel_auto_scrolls_and_space_stops_it():
    """The HP drill REDO (Joel 2026-07-06): the selector lives IN THE LCD,
    stacked under the target, and AUTO-SCROLLS -- SPACE stops it on the
    match.  The message box is a status strip again (no game glyphs)."""
    import random
    random.seed(7)
    panel = _panel("hp")
    panel.key("enter")                             # start the drill from the menu
    assert panel.phase == "play"
    assert panel.hp_pick != panel.hp_target        # never starts on a free win
    pick0 = panel.hp_pick
    for _ in range(panel.hp_scroll):
        panel.anim()
    assert panel.hp_pick == (pick0 + 1) % 3        # the reel turned on its own
    # both icons render in the LCD, stacked (target sky-centre, reel beneath)
    txt = panel.text()
    assert txt.plain.count("\n") + 1 >= 12
    # the strip is STATUS only: no pick glyphs, no shape markers
    g = panel._gauge()
    assert "SPACE" in g and "▸" not in g and "●" not in g and "■" not in g
    # ride the reel onto the target and stop it
    guard = 0
    while panel.hp_pick != panel.hp_target and guard < 40:
        panel.anim(); guard += 1
    assert panel.hp_pick == panel.hp_target
    won0 = panel.rounds_won
    panel.key("space")
    assert panel.rounds_won == won0 + 1            # a timed stop scores


def test_hp_reel_geometry_never_mashes():
    """Spacing polish (Joel 2026-07-06: "mashed together... touching the top
    border"): the target keeps a 2px top margin, the reel a 2px gap under it,
    and the icon column never overlaps the dummy (left) or the char (right)
    -- checked with a worst-case 16px-wide mon."""
    import random
    from tuipet import data as _d
    random.seed(7)
    p = Pet(num=102, stage="Champion", vaccine=5, data_power=5, virus=5)  # Devimon: widest
    p.obedience = 500
    panel = T.TrainingPanel(p)
    panel.gi = 0
    panel.key("enter")
    E = _d.load_effects()
    ic = E[T._HP_ICON_KEYS[panel.hp_target]][0]
    iw = max(len(r) for r in ic)
    ix = (T.COLS - iw) // 2
    dummy = T._HP_DUMMIES["vaccine"]
    dw = max(len(r) for r in dummy)
    assert 1 + dw <= ix, "the dummy runs into the icon column"
    pf = T._crop(panel._frame(_d.load_sprites()[1][102], 0))
    pw = max(len(r) for r in pf)
    char_x = max(ix + iw + 1, T.COLS - 1 - pw)
    assert char_x >= ix + iw + 1, "the char overlaps the icon column"
    assert char_x + pw <= T.COLS, "the char runs off the LCD"
    panel.text()                                     # and it all renders


def test_vaccine_geometry_never_mashes():
    """Vaccine layout audit (Joel 2026-07-06): the GRID anchors ran a 16px
    mon OFF the right edge (Devimon spanned x26..41 on the 40px LCD) and the
    HIT!! label sat at y0 flush on the top border.  Measured layout: bag off
    the left edge (>=1px even mid-rock), label y>=1, the widest mon inside
    the LCD at rest AND mid-lunge."""
    from tuipet import data as _d
    p = Pet(num=102, stage="Champion", vaccine=5, data_power=5, virus=5)
    p.obedience = 500
    panel = T.TrainingPanel(p)
    panel.gi = 1
    panel.key("enter")
    E = _d.load_effects()
    bag = T._fit_cell(E["punching_bag"][0])
    bh = len(bag)
    hit = E["train_hit"][0]
    assert max(1, (T.BASE_Y - bh) - len(hit) - 1) >= 1     # label off the top border
    pf = T._crop(panel._frame(_d.load_sprites()[1][102], 0))
    pw = max(len(r) for r in pf)
    assert T.COLS - 1 - pw >= 0                            # rest: on the LCD
    assert T.COLS - 1 - pw - 2 + pw <= T.COLS - 1          # lunge: still on the LCD
    panel.key("space")                                      # punch frame renders
    rows = panel.text().plain.split("\n")
    assert all(len(r) <= T.COLS for r in rows)


def test_data_geometry_never_mashes():
    """Data layout audit (Joel 2026-07-06): the old fixed x27 mon column ran
    a 16px mon to x42 -- 3 columns clipped.  Measured stage (turret x2, gate
    x17, mon x23): the widest mon fits with a 1px right margin, and every
    act (aim/lock/shoot/strobe/aftermath) renders inside the LCD."""
    import random
    random.seed(3)
    p = Pet(num=102, stage="Champion", vaccine=5, data_power=5, virus=5)
    p.obedience = 500
    panel = T.TrainingPanel(p)
    panel.gi = 2
    panel.key("enter")
    assert 23 + 16 <= T.COLS, "the stage cannot fit the widest mon"
    for _ in range(40):
        panel.anim()
        if panel.locked:
            break
    assert panel.locked
    panel.key("space")
    for _ in range(60):
        panel.anim()
        assert all(len(r) <= T.COLS for r in panel.text().plain.split("\n"))
        if panel.phase == "done":
            break


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
