"""In-app Help screen (Joel 2026-07-09): controls + how-to, opened with ?."""
import pathlib
import re

from tuipet.pet import Pet
from tuipet.helpscreen import HelpPanel, HELP, VIS
from tuipet.app import TuiPetApp, keys_markup

README = pathlib.Path(__file__).resolve().parent.parent / "README.md"


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", bits=99)


def _glyph(key):
    """The key as a PLAYER sees it (Textual's identifiers never reach a page)."""
    return {"question_mark": "?", "enter": "ENTER"}.get(key, key)


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


def test_help_lists_every_binding():
    """The bar has been pinned against BINDINGS since the n egg-guide miss --
    HELP itself never was, and `?` had quietly fallen off its own page while
    the bar, the README and the Keys page all carried it (help audit
    2026-07-21).  Four hand-maintained surfaces, four pins now."""
    lines = [t for t, kind in HELP if kind == 1]
    for key, action, _label in TuiPetApp.BINDINGS:
        g = _glyph(key)
        assert any(re.search(r"(?:^|\s)%s\s" % re.escape(g), t) for t in lines), \
            f"{action} ({g}) missing from the in-game Help"


def test_readme_keys_table_lists_every_binding():
    """The README table had drifted furthest of the four: no ENTER row at all,
    and the word "gift" appeared nowhere in the file (help audit 2026-07-21)."""
    body = README.read_text(encoding="utf-8")
    table = body.split("## Keys", 1)[1].split("## ", 1)[0]
    for key, action, _label in TuiPetApp.BINDINGS:
        assert f"**{_glyph(key)}**" in table, \
            f"{action} ({_glyph(key)}) missing from the README key table"


def test_help_page_jumps_and_clamps():
    """PageUp/PageDown page the scrollers, lobby-chat style (grammar sweep
    2026-07-18): VIS-1 rows a jump, clamped both ends."""
    pan = HelpPanel(_pet())
    pan.key("pagedown")
    assert pan.top == VIS - 1
    pan.key("pageup")
    assert pan.top == 0
    for _ in range(200):
        pan.key("pagedown")
    assert pan.top == max(0, len(HELP) - VIS)      # clamped at the bottom
    pan.key("pageup")
    assert pan.top == max(0, len(HELP) - VIS) - (VIS - 1)


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


def test_help_teaches_the_gift_and_the_key_grammar():
    """Coverage gaps closed (help audit 2026-07-19): the ENTER gift-accept
    had no bar slot AND no help line — a player watching the gift-call
    pose had no documented answer; and the 0.5.64 grammar (SPACE=ENTER,
    page keys) reached the README but not the in-game help.  Every help
    line also holds the 38-col budget."""
    joined = "\n".join(t for t, _k in HELP)
    assert "ENTER accepts a found gift" in joined
    assert "SPACE doubles ENTER on most screens" in joined   # honest since the help audit 2026-07-22
    assert "PgUp/PgDn" in joined
    for text, _kind in HELP:
        assert len(text) <= 38, text


def test_help_teaches_the_grave_and_the_shop_tabs():
    """The memorial's E/B and E/K prompts drive a PERMANENT inheritance
    choice and had no help text at all; Honors and the Options rows were
    likewise hidden behind one-word entries (help audit 2026-07-21)."""
    joined = "\n".join(t for t, _k in HELP)
    assert "E etch its data for your heir" in joined
    assert "B keep the care bonus instead" in joined
    assert "K keeps the elder's." in joined
    assert "HONORS" in joined
    assert "cloud sync" in joined


# ---- the two claims HELP makes about the WHOLE app ---------------------------

def _long_list_panels():
    """Every cursor list a player can actually walk a long way."""
    from tuipet import (adventure, adventurescreen, backgroundscreen,
                        eggselectscreen, shop, shopscreen, tournamentscreen)
    pet = Pet(num=100, stage="Champion", attribute="Vaccine", bits=99999)
    # a FULL bag and an opened map: the empty-list case is a no-op by design,
    # so an unstocked fixture would pass this test without exercising anything
    for e in shop.catalog():
        pet.inventory[e["key"]] = 1
    pet.adv_progress = len(adventure.ZONES) - 1
    return [
        ("shop", shopscreen.ShopPanel(pet)),
        ("bag", shopscreen.ShopPanel(pet, start_mode="bag")),
        ("scenes", backgroundscreen.BackgroundPanel(pet)),
        ("zones", adventurescreen.ZonePickPanel(pet)),
        ("cup", tournamentscreen.TournamentPanel(pet)),
        ("eggs", eggselectscreen.EggSelectPanel(Pet.new_egg())),
    ]


def test_page_keys_leap_through_every_long_list():
    """Help and the README have promised "PgUp/PgDn leap through long lists"
    since 0.5.64, but only the top/window scrollers implemented it -- the
    CURSOR lists (the 31-row scene picker, the 24-slot cup board, the shop,
    the bag, the zone picker, the egg carousel) silently ATE the key
    (help audit 2026-07-21).  A stated law has to hold everywhere."""
    for name, pan in _long_list_panels():
        def where():
            return pan.cursor if hasattr(pan, "cursor") else pan.pos
        for _ in range(9):                          # to the top first (the zone
            pan.key("pageup")                       # picker OPENS on the frontier)
        top = where()
        pan.key("pagedown")
        assert where() != top, f"{name}: PgDn did nothing"
        pan.key("pageup")
        assert where() == top, f"{name}: PgUp did not come back"
        pan.text()                                  # and the window still paints


def test_space_equals_enter_at_the_memorial_prompts():
    """The one non-text panel that broke the SPACE=ENTER law: the digimemory
    etch prompts took ("e", "enter") only (help audit 2026-07-21)."""
    from tuipet.deathscreen import DeathPanel
    mem = {"name": "Elder", "vaccine": 1, "data": 1, "virus": 1}
    pet = Pet(num=100, stage="Champion", attribute="Vaccine")
    pet.dead = True

    pan = DeathPanel(pet, new_mem=mem, hold=0)
    assert pan.ask_etch
    pan.key("space")                                # SPACE answers the etch...
    assert not pan.ask_etch

    pan = DeathPanel(pet, new_mem=mem, old_mem=dict(mem, name="Old"), hold=0)
    pan.key("space")
    assert pan.asking                               # ...and the only-one prompt
    pan.key("space")
    assert not pan.asking


def test_every_binding_is_taught_in_the_guide():
    """The coverage ratchet (help audit 2026-07-22): every home binding must
    appear in the guide -- a new action-bar key without a HELP line ships an
    untaught feature.  (The inverse -- help teaching dead keys -- is caught
    by the claims audit, not greppable.)"""
    from tuipet.app import TuiPetApp
    keymap = {"question_mark": "?", "enter": "ENTER"}
    lines = [ln for ln, kind in HELP if kind == 1]
    for key, _action, label in TuiPetApp.BINDINGS:
        k = keymap.get(key, key)
        taught = any(ln.startswith(k + " ") or f"  {k} " in ln or f" {k} " in ln
                     for ln in lines)
        assert taught, f"binding '{k}' ({label}) is not taught in HELP"


def test_the_guides_reach_claims_stay_honest():
    """"any time" was an overclaim: with a screen open every key routes to
    that screen (app.on_key) -- ? answers from HOME.  And SPACE=ENTER has
    its shipped exception (digicore: SPACE pages, ENTER opens the doors)."""
    text = "\n".join(ln for ln, _ in HELP)
    assert "any time you're home" in text
    assert "SPACE doubles ENTER on most screens" in text
    assert "wherever ENTER does" not in text


def test_help_teaches_the_care_mistake_counter():
    """Gameplay polish #18 (2026-07-22): ✗N steers every line's CM gates,
    resets each stage, 20 is fatal (5 for a frail late-stage elder) --
    and its meaning appeared NOWHERE.  Help CARE carries it now."""
    text = " ".join(t for t, _k in HELP)
    assert "care mistakes" in text
    assert "reset each stage" in text
    assert "20 is fatal" in text and "5" in text
    assert "bits/hour" in text        # the assistant's retainer named (#22)


def test_every_need_call_names_its_key():
    """Gameplay polish #19: lights always said (S); hungry/sick/cleaning
    -- the three commonest calls -- named no key."""
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0

    async def go():
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(82, 32)):
            return {
                "hungry": app._need_message(_state(p, hunger=0)),
                "sick": app._need_message(_state(p, hunger=4, sick=True)),
                "clean": app._need_message(_state(p, sick=False, poop=3)),
                "effort": app._need_message(_state(p, poop=0, strength=0)),
            }

    def _state(pet, **kw):
        for k, v in kw.items():
            setattr(pet, k, v)
        return pet

    msgs = asyncio.run(go())
    assert "F" in msgs["hungry"] and "hungry" in msgs["hungry"]
    assert "I" in msgs["sick"] and "pill" in msgs["sick"]
    assert "C" in msgs["clean"]
    assert "T" in msgs["effort"]
