"""The DVPet training strike sequence (ANIMATION_SPEC.md §6): after the skill drill
the pet fires at the punching bag (or green target), it flashes, then breaks on
success / the pet recoils on a fail -- attackDefault -> hitAnim -> aftermathDefault.
Reuses the projectile + impact-flash art already in effects.json.gz and battle's
strong-vs-normal attack/hit sounds."""
from tuipet import training as T, data
from tuipet.pet import Pet


def _panel(game="vaccine"):
    p = Pet(num=1, stage="Rookie", vaccine=5, data_power=5, virus=5)
    panel = T.TrainingPanel(p)
    panel.gi = {"hp": 0, "vaccine": 1, "data": 2, "virus": 3}[game]
    return panel


def test_finish_launches_the_strike_then_reveals_result():
    panel = _panel()
    panel._finish(2, 30, "Vaccine", "vaccine")
    assert panel.phase == "strike"          # not straight to "done"
    assert panel.strike_step == 0
    assert panel.result                     # the outcome is decided, just not shown yet
    assert panel.flash == ""                # ...held until the strike lands
    # drive the sequence; it must terminate in exactly STRIKE_TOTAL ticks
    for _ in range(T.STRIKE_TOTAL):
        panel.anim()
    assert panel.phase == "done"
    assert panel.result in panel.flash      # score revealed when the strike completes


def test_strike_sfx_timing_and_strength():
    def sfx_trace(hits):
        panel = _panel()
        panel._finish(hits, 30, "Vaccine", "vaccine")
        trace = {}
        for _ in range(T.STRIKE_TOTAL):
            panel.sfx = None
            panel.anim()
            if panel.sfx:
                trace[panel.strike_step] = panel.sfx
        return trace

    strong = sfx_trace(3)
    assert strong[1] == "strongAttack"                 # launch sting (full success)
    assert strong[T.STRIKE_FIRE + 1] == "strongHit"    # impact, on the bag
    good = sfx_trace(2)
    assert good[1] == "attack"
    assert good[T.STRIKE_FIRE + 1] == "attackHit"
    miss = sfx_trace(0)
    assert miss[1] == "attack"                         # the pet still fires...
    assert miss[T.STRIKE_FIRE + 1] == "cancel"         # ...but the impact is the miss thud


def test_strike_ignores_input_and_renders_every_drill():
    for game in ("hp", "vaccine", "data", "virus"):
        for hits in (3, 2, 0):
            panel = _panel(game)
            panel._finish(hits, 30, None if game == "hp" else "Vaccine", game)
            steps_seen = 0
            while panel.phase == "strike" and steps_seen < 60:
                assert panel.text() is not None            # composes without error every frame
                assert panel.key("space") is None          # input is swallowed mid-strike
                panel.anim()
                steps_seen += 1
            assert panel.phase == "done"


def test_strike_opponent_art_exists():
    e = data.load_effects()
    for k in ("punching_bag", "punching_bag_broken", "train_green", "attack", "flash"):
        assert k in e and e[k], f"missing strike asset: {k}"


# ---- DVPet-faithful drill mechanics (the rebuild) --------------------------

def test_hp_drill_is_guess_the_hidden_attribute():
    """HP = pick which of 3 attributes the hidden bag is, best of 3 -> Effort."""
    panel = _panel("hp")
    panel._start_game()
    assert panel.phase == "play"
    for _ in range(T.HP_ROUNDS):                       # guess correctly every round
        assert panel.phase in ("play", "strike")
        if panel.phase != "play":
            break
        panel.hp_pick = panel.hp_target               # know the answer -> pick it
        panel.key("space")
    # three correct guesses -> a strong, successful drill
    assert panel.rounds_won == T.HP_ROUNDS
    assert panel.phase == "strike" and panel.success and panel._strong


def test_hp_timeout_counts_as_wrong():
    panel = _panel("hp")
    panel._start_game()
    for _ in range(T.HP_ROUNDS * (T.HP_ROUND_LEN + 1)):
        if panel.phase != "play":
            break
        panel.anim()                                   # never guess -> every round times out
    assert panel.rounds_won == 0 and not panel.success


def test_data_drill_only_scores_on_the_up_frame():
    panel = _panel("data")
    panel._start_game()
    panel.tgt_up = True
    panel.key("space")                                 # shot while UP -> a hit
    assert panel.hits == 1
    panel.tgt_up = False
    panel.key("space")                                 # shot while down -> a miss
    assert panel.hits == 1                             # unchanged


def test_vaccine_drill_counts_mashes():
    panel = _panel("vaccine")
    panel._start_game()
    for _ in range(5):
        panel.key("space")
    assert panel.taps == 5
