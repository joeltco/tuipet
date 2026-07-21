"""Adventure rebuild — the zone BOSS FIGHT (phase 5, 2026-07-20).

Pins the gate: reaching the end opens the zone's boss (not an instant win),
felling it conquers the zone, a survivable loss stands the pet at the gate to
retry (SPACE) or turn back (ESC), and 0 lives fails the run home.
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, MAX_LIVES
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _champ():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _boss_zone():
    return next(z for z in ZONES if z["bosses"])


def _reach_end(a):
    for _ in range(a.total + 2):
        r = a.travel()
        if isinstance(r, tuple) and r[0] == "boss":
            return r
    raise AssertionError("never reached the boss gate")


def _panel_at_boss(monkeypatch, zone=None):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)   # clean march to the gate
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_champ(), zone=zone)
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            return pan
    raise AssertionError("boss fight never opened")


def _through_celebration(pan):
    """Walk anim through the zoneChange pulse (and any parade), rendering."""
    from tuipet.adventurescreen import PULSE_T, PARADE_T
    for _ in range(PULSE_T + 3 * PARADE_T + 4):
        if pan._pulse is None and pan._parade is None:
            return
        pan.anim()
        assert pan.text()


class _Win:
    won = True


class _Loss:
    won = False


# -- engine -------------------------------------------------------------------
def test_reaching_the_end_opens_the_boss_not_an_instant_win(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    r = _reach_end(a)
    assert r[1] is a.boss and r[1].get("boss")            # the zone's gate boss
    assert not a.done and a.loc == a.total                # crossing did NOT win


def test_felling_the_boss_conquers_the_zone(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    assert a.resolve_boss(True) == "won" and a.done


def test_a_survivable_boss_loss_retries_then_fails_at_zero(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    outs = [a.resolve_boss(False) for _ in range(MAX_LIVES)]
    assert outs == ["retry"] * (MAX_LIVES - 1) + ["failed"]
    assert a.failed and a.lives == 0 and not a.done


def test_fleeing_the_boss_turns_back_without_winning(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    a = Adventure(_champ(), zone=_boss_zone())
    _reach_end(a)
    assert a.resolve_boss(False, fled=True) == "fled"
    assert not a.done and not a.failed                     # neither win nor loss


# -- panel --------------------------------------------------------------------
def test_the_panel_opens_the_boss_on_its_biome(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    assert type(pan.sub).__name__ == "BattlePanel"
    assert pan.sub._enemy is pan.adv.boss and pan.sub._enemy.get("boss")
    assert pan.sub.scene == pan.adv.scene                  # fought on the zone biome
    assert not pan.travelling


def test_a_boss_win_teleports_home_conquered(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Win())
    assert pan.adv.done and "felled" in pan._home_msg
    assert pan._pulse is not None                 # the zoneChange pulse celebrates first
    _through_celebration(pan)
    assert pan._summary                           # the results card follows the show
    pan.key("space")                              # dismiss -> rides the teleport home
    assert pan._trans is not None


def test_a_boss_loss_stands_at_the_gate_and_space_re_engages(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Loss())
    assert pan._at_gate and not pan._fighting_boss
    assert "fight" in pan.strip().lower()                  # the retry prompt
    pan.key("space")
    assert pan._fighting_boss and type(pan.sub).__name__ == "BattlePanel"


def test_the_zone_pulse_flashes_the_world_and_locks_input(monkeypatch):
    """The zoneChange celebration (restored old build): felling a gate boss
    pulses the backdrop bright on the canon beat spans with the chirp on
    each span start; input is locked until the show ends."""
    from tuipet.adventurescreen import PULSE_ON, PULSE_T
    from tuipet import menu
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Win())
    assert pan._pulse is not None and not pan._pulse["parade"]  # mid-map: no parade
    road = pan._road_bg()
    bgs, chirps = [], 0
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, bg, **k: (bgs.append(bg), real(pl, bg, **k))[1])
    for _ in range(PULSE_T + 1):
        if pan._pulse is None:
            break
        pan.key("escape")                          # locked: must NOT cut the show
        assert pan._trans is None
        pan.text()
        if pan.sfx == "select":
            chirps, pan.sfx = chirps + 1, None
        pan.anim()
    flashed = sum(1 for b in bgs if b is not road)
    assert 0 < flashed < len(bgs)                  # it PULSES: bright spans + rests
    assert chirps == len(PULSE_ON)                 # a chirp per zonePulse beat
    assert pan._summary                            # then the results card


def test_the_map_final_boss_chains_the_boss_parade(monkeypatch):
    """A parade_msg boss (each map's final gate) chains the BossParade after
    the pulse: the map's own bosses march across right-to-left, ONE at a time
    (the one-mon rule serialises canon's three-abreast), under the victory
    line -- then the results card."""
    from tuipet.adventurescreen import PULSE_T, PARADE_T
    from tuipet import menu
    z = next(z for z in ZONES
             if z["bosses"] and z["bosses"][0].get("parade_msg"))
    pan = _panel_at_boss(monkeypatch, zone=z)
    pan.sub = None
    pan._battle_done(_Win())
    assert pan._pulse is not None and pan._pulse["parade"]
    for _ in range(PULSE_T + 1):
        pan.anim()
        if pan._parade is not None:
            break
    assert pan._parade is not None
    assert 1 <= len(pan._parade["nums"]) <= 3      # canon shows three
    assert "saved the Digital World" in pan.strip()
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append(pl), real(pl, *a, **k))[1])
    xs = []
    for _ in range(PARADE_T):                      # the first marcher's crossing
        assert pan.text()
        assert len(calls[-1]) == 1                 # ONE mon on the LCD at a time
        xs.append(calls[-1][0][1])
        pan.anim()
    assert xs[0] > xs[-1]                          # it marched right -> left
    _through_celebration(pan)
    assert pan._parade is None and pan._summary    # the show ends at the card


def test_the_gate_is_a_faceoff_not_an_empty_road(monkeypatch):
    """The GATE FACEOFF (restored from the old build, audit pass 1): knocked
    back, the mon squares up at the LEFT edge facing the gate while the boss
    looms half-emerged past the RIGHT edge -- two sprites, one dread."""
    from tuipet import grid, menu
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Loss())                              # -> at the gate
    assert pan._at_gate
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append(pl), real(pl, *a, **k))[1])
    assert pan.text()
    (placements,) = calls
    assert len(placements) == 2                            # mon AND the boss
    (mrows, mx, mmirror), (brows, bx, bmirror) = placements
    assert mx == grid.X0 and mmirror is True               # squared up, facing it
    assert bx == grid.X1 - grid.width(brows) * 3 // 4      # looming half-emerged
    assert bmirror is False                                # native facing: at the mon


def test_the_gate_esc_turns_back_home(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.sub = None
    pan._battle_done(_Loss())                              # -> at the gate
    pan.key("escape")                                      # turn back -> results card
    assert pan._summary and "Turned back" in pan._home_msg
    pan.key("space")
    assert pan._trans is not None


def test_the_final_boss_loss_fails_the_run_home(monkeypatch):
    pan = _panel_at_boss(monkeypatch)
    pan.adv.lives = 1
    pan.sub = None
    pan._battle_done(_Loss())
    assert pan.adv.failed and "Defeated" in pan._home_msg
    assert pan._summary                           # the results card shows first
    pan.key("space")
    assert pan._trans is not None
