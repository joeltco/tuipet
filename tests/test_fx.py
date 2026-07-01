"""Care-animation (fx) state machine + re-trigger gating (Workstream C).

The #lcd Screen owns a care-action fx (eat/clean/cheer/...) advanced one step per
frame. Two correctness concerns:
  - an fx must run exactly `steps` frames then end (and 'clean' chains into the
    'cheer' sunshine);
  - a care action must not start a second fx while one is running (the re-trigger
    that caused the old feed-status flicker).

The state machine is tested directly here (methods bound onto a plain object, no
Textual mount). The per-action gating is verified by inspection: action_feed /
action_clean / action_heal each early-return on `self.screen_w.fx is not None`
(and this test guards that the guard is present in source). Pinning the engine
means a refactor can't silently break completion or the clean->cheer chain.
"""
import os
import re

from tuipet.app import Screen
from tuipet.pet import Pet


class _FakeScreen:
    fx = None
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


def test_clean_chains_into_cheer():
    s = _FakeScreen()
    s.start_fx("clean")
    steps = s.fx["steps"]
    for _ in range(steps):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer", "a wash ends in the sunshine cheer"


def test_advance_with_no_fx_is_safe():
    s = _FakeScreen()
    assert s.advance_fx() is False         # no active fx -> no-op, no crash


def test_care_actions_guard_against_retrigger():
    """Every care action that starts an fx must early-return while one is active."""
    here = os.path.dirname(__import__("tuipet").__file__)
    src = open(os.path.join(here, "app.py")).read()
    # find each `def action_*` body and check feed/clean/heal guard
    GUARDED = ["action_feed", "action_clean", "action_heal"]
    missing = []
    for name in GUARDED:
        m = re.search(rf"def {name}\(self.*?\):(.*?)(?=\n    def )", src, re.S)
        body = m.group(1) if m else ""
        if "self.screen_w.fx is not None" not in body:
            missing.append(name)
    assert not missing, f"care actions missing the fx re-trigger guard: {missing}"
