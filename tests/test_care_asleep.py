"""A sleeping pet must not be silently cared for: every care action is blocked
while it sleeps. (DM20 Ver.20th no longer penalises waking, so blocking is a plain
no-op with a 'mind its sleep' nudge — no stat change.)"""
from tuipet.pet import Pet


def _sleeping():
    p = Pet(num=-1, stage="Rookie")
    p.asleep = True
    p.poop = 3            # so clean would otherwise have work to do
    p.sick = True         # so heal would otherwise have work to do
    return p


def test_all_care_actions_block_while_asleep():
    for action in ("feed", "clean", "heal"):
        p = _sleeping()
        msg = getattr(p, action)()
        assert "sleep" in msg.lower(), f"{action} did not block while asleep: {msg!r}"


def test_blocked_action_changes_nothing():
    p = _sleeping()
    poop0, sick0 = p.poop, p.sick
    p.heal()
    assert p.sick is True, "heal-while-asleep must not cure"
    p.clean()
    assert p.poop == poop0, "clean-while-asleep must not tidy up"
    assert p.sick == sick0, "care while asleep is a no-op (DM20: waking is free)"


def test_care_works_again_once_awake():
    p = _sleeping()
    p.asleep = False
    assert "sleep" not in p.clean().lower()   # poop=3 -> actually cleans now
