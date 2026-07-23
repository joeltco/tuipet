"""Adventure rebuild — WILD ENCOUNTERS (phase 3, 2026-07-20).

Pins the per-leg wild roll, the win/flee/loss/fail resolution + adventure lives,
and the panel integration: a fight rides BattlePanel as a SubHost child on the
road's own biome, and a real bout runs to a verdict through the sub.
"""
import random
from tuipet import adventure
from tuipet.adventure import Adventure, MAX_LIVES
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _champ():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _to_travelling(pan):
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            return
    raise AssertionError("never started travelling")


# -- engine -------------------------------------------------------------------
def test_a_forced_encounter_pulls_a_real_wild_and_holds_the_leg(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    a = Adventure(_champ())
    r = a.travel()
    assert isinstance(r, tuple) and r[0] == "encounter"
    e = r[1]
    assert e["num"] and e["name"] and not e.get("boss")   # a real, non-boss roster mon
    assert a.loc == 0                                       # the leg did not progress


def test_win_grants_a_grace_leg_then_the_march_resumes(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)   # isolate the grace leg
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)  # (immunity covers
    # encounters only -- an unlucky hazard roll made this flake, 2026-07-23)
    a = Adventure(_champ())
    a.travel()                                             # encounter
    assert a.resolve(True) == "won"
    assert a._immunity >= 1
    assert a.travel() == "step" and a.loc == 1            # grace leg walks, no re-fight


def test_flee_costs_no_life_and_no_progress(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    a = Adventure(_champ())
    a.travel()
    assert a.resolve(False, fled=True) == "fled"
    assert a.lives == MAX_LIVES and a.loc == 0


def test_three_losses_fail_the_run(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    a = Adventure(_champ())
    outs = []
    for _ in range(MAX_LIVES):
        a._immunity = 0
        a.travel()
        outs.append(a.resolve(False))
    assert outs == ["lost"] * (MAX_LIVES - 1) + ["failed"]
    assert a.failed and a.lives == 0
    assert a.travel() is None                              # a failed run does not move


def test_suppressed_encounters_cross_clean(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    bossless = {"name": "Testfield", "scene": "greenhills",
                "steps": adventure.INTERACTIVE_STEPS, "randoms": [], "bosses": []}
    a = Adventure(_champ(), zone=bossless)     # bossless: the crossing is the win
    res = [a.travel() for _ in range(a.total)]
    assert res[-1] == "arrived" and a.done and a.lives == MAX_LIVES


# -- panel integration --------------------------------------------------------
def test_the_panel_opens_a_wild_fight_on_the_road_biome(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    pan = AdventurePanel(_champ())
    _to_travelling(pan)
    for _ in range(20):
        pan.anim()
        if pan.sub is not None:
            break
    assert type(pan.sub).__name__ == "BattlePanel"
    assert pan.sub.wild and pan.sub.scene == pan.adv.scene   # the road says where
    assert not pan.travelling                                # the march paused
    assert pan.text() is not None and pan.strip() is not None


def test_a_real_fight_runs_through_the_sub_and_resolves(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 1.0)
    random.seed(5)
    pan = AdventurePanel(_champ())
    _to_travelling(pan)
    for _ in range(20):
        pan.anim()
        if pan.sub is not None:
            break
    b = pan.sub
    pan.key("space")                          # skip intro (routed to the sub)
    for _ in range(6):
        pan.anim()
    b.bar = (b.mega_lo + b.mega_hi) // 2
    pan.key("space")                          # lock the timing bar
    for _ in range(3000):
        pan.anim()
        if b.phase == "result":
            break
    assert b.phase == "result"
    pan.key("space")                          # finish -> sub_key fires _battle_done
    assert pan.sub is None                     # the fight closed and cleared
    # survived (marching on) or fell (failing home) -- both are valid outcomes
    assert pan.travelling or (pan.adv.failed and pan._trans is not None)


def test_life_pips_ride_the_march_strip(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    pan = AdventurePanel(_champ())
    _to_travelling(pan)
    assert "♥" in pan.strip()                  # full hearts while marching
