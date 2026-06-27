"""A sleeping pet must not be silently cared for: every care action is blocked
(and counts as a sleep disturbance), consistently. Previously only feed/play
blocked; praise/scold penalised-then-acted-anyway, and clean/heal ignored sleep."""
from tuipet.pet import Pet


def _sleeping():
    p = Pet(num=-1, stage="Rookie")
    p.asleep = True
    p.poop = 3            # so clean would otherwise have work to do
    p.sick = True         # so heal would otherwise have work to do
    return p


def test_all_care_actions_block_while_asleep():
    for action in ("feed", "play", "praise", "scold", "clean", "heal"):
        p = _sleeping()
        msg = getattr(p, action)()
        assert "sleep" in msg.lower(), f"{action} did not block while asleep: {msg!r}"


def test_disturbing_sleep_costs_mood_and_counts():
    p = _sleeping()
    mood0, disturb0 = p.mood, p.disturb
    p.praise()                          # used to praise-anyway; now it's a disturbance
    assert p.disturb == disturb0 + 1
    assert p.mood < mood0               # DisturbMoodDec applied
    assert p.sick is True               # heal-while-asleep didn't secretly cure
    p.heal()
    assert p.sick is True               # still blocked — the illness remains


def test_care_works_again_once_awake():
    p = _sleeping()
    p.asleep = False
    assert "sleep" not in p.clean().lower()   # poop=3 -> actually cleans now
