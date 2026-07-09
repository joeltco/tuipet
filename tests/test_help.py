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
    for token in ("feed", "adventure", "cup", "lobby", "DNA", "shop", "bug"):
        assert token in body
