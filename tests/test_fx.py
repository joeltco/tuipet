"""Care-animation (fx) state machine + re-trigger gating (Workstream C).

The #lcd Screen owns a care-action fx (eat/clean/cheer/...) advanced one step per
frame. Two correctness concerns:
  - an fx must run exactly `steps` frames then end (and 'clean' chains into the
    'cheer' sunshine);
  - a care action must not start a second fx while one is running (the re-trigger
    that caused the old feed-status flicker).

The state machine is tested directly here (methods bound onto a plain object, no
Textual mount). The per-action gating is verified by inspection: action_feed /
_clean / _praise / _scold / _play / _heal each early-return on
`self.screen_w.fx is not None` (and this test guards that the guard is present in
source). Pinning the engine means a refactor can't silently break completion or
the clean->cheer chain.
"""
import os
import re

from tuipet.app import Screen
from tuipet.pet import Pet


class _FakeScreen:
    fx = None
    frame_i = 0     # advance_fx keeps weather/filth animating via frame_i
_FakeScreen.start_fx = Screen.start_fx
_FakeScreen.advance_fx = Screen.advance_fx


def test_fx_runs_exactly_steps_then_ends():
    s = _FakeScreen()
    s.start_fx("cheer")
    assert s.fx is not None
    steps = s.fx["steps"]
    for _ in range(steps - 1):
        assert s.advance_fx() is True, "fx should stay active until the last step"
    s.advance_fx()                       # the final step
    assert s.fx is None, "fx must end after exactly `steps` frames"


def test_clean_chains_into_cheer_only_when_filthy():
    # DVPet clean(): cheer(true) chains ONLY if filth was actually washed;
    # an empty-room wash just ends (no celebration).
    s = _FakeScreen()
    s.start_fx("clean", poop=2)
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer", "a filthy wash ends in the sunshine cheer"
    s2 = _FakeScreen()
    s2.start_fx("clean")                 # nothing to wash
    for _ in range(s2.fx["steps"]):
        s2.advance_fx()
    assert s2.fx is None, "an empty-room wash ends without a cheer"


def test_evolve_chains_into_cheer():
    # DVPet evolFinish(true): every evolution ends in cheer(true, _happy).
    s = _FakeScreen()
    s.start_fx("evolve", old_num=-1)
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer", "evolution ends in the praise cheer"


def test_eat_fx_scales_with_glutton():
    glut = _FakeScreen(); glut.start_fx("eat", "f:0", pet=Pet(num=-1, glutton=1))
    picky = _FakeScreen(); picky.start_fx("eat", "f:0", pet=Pet(num=-1, glutton=-1))
    # a glutton wolfs food (mod 0.9 -> fewer steps); a picky eater dawdles (mod 1.1)
    assert glut.fx["steps"] == int(34 ** 0.9) + 1
    assert picky.fx["steps"] == int(34 ** 1.1) + 1
    assert glut.fx["steps"] < picky.fx["steps"]


def test_advance_with_no_fx_is_safe():
    s = _FakeScreen()
    assert s.advance_fx() is False         # no active fx -> no-op, no crash


def test_care_actions_guard_against_retrigger():
    """Every care action that starts an fx must early-return while one is active."""
    here = os.path.dirname(__import__("tuipet").__file__)
    src = open(os.path.join(here, "app.py")).read()
    # find each `def action_*` body and check feed/clean/praise/scold/play/heal guard
    GUARDED = ["action_feed", "action_clean", "action_praise",
               "action_scold", "action_play", "action_heal"]
    missing = []
    for name in GUARDED:
        m = re.search(rf"def {name}\(self.*?\):(.*?)(?=\n    def )", src, re.S)
        body = m.group(1) if m else ""
        if "self.screen_w.fx is not None" not in body:
            missing.append(name)
    assert not missing, f"care actions missing the fx re-trigger guard: {missing}"


def test_gift_fx_chains_into_cheer():
    # ClockTic.giftEnd: the gifting amble always ends in State.Cheering
    s = _FakeScreen()
    s.start_fx("gift", icon="f:8")
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer"
