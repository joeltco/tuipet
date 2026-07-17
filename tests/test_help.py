"""In-app Help screen (Joel 2026-07-09): controls + how-to, opened with ?."""
from tuipet.pet import Pet
from tuipet.helpscreen import HelpPanel, HELP, VIS
from tuipet.app import TuiPetApp, keys_markup


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", bits=99)


def test_help_is_bound_to_question_mark_and_listed():
    keys = {b[0]: b[1] for b in TuiPetApp.BINDINGS}
    assert keys.get("question_mark") == "help"
    assert hasattr(TuiPetApp, "action_help")
    assert "help" in keys_markup()                 # discoverable in the ACTIONS bar


def test_every_binding_is_on_the_actions_bar():
    """The ACTIONS bar is hand-maintained markup, separate from BINDINGS --
    the n egg-guide key shipped in 0.2.437 bound + in help but MISSING from
    the bar (Joel caught it).  Every home-screen binding must show its key."""
    bar = keys_markup()
    for key, action, _label in TuiPetApp.BINDINGS:
        if key == "enter":                         # the gift accept: no bar slot
            continue
        shown = "?" if key == "question_mark" else key
        assert f"]{shown}[/]" in bar, f"{action} ({shown}) missing from the ACTIONS bar"


def test_help_scrolls_and_clamps_and_exits():
    pan = HelpPanel(_pet())
    assert pan.top == 0
    for _ in range(3):
        pan.key("down")
    assert pan.top == 3
    for _ in range(200):                           # clamp at the bottom
        pan.key("down")
    assert pan.top == max(0, len(HELP) - VIS)
    for _ in range(200):                           # clamp at the top
        pan.key("up")
    assert pan.top == 0
    assert pan.key("escape") == ("done", None)


def test_help_lines_fit_the_box():
    assert all(len(t) <= 38 for t, _ in HELP)      # never overflow the 40-col LCD
    # every control section a new player needs is covered
    body = " ".join(t for t, _ in HELP)
    for token in ("feed", "raid", "cup", "lobby", "DNA", "shop", "bug"):
        assert token in body
