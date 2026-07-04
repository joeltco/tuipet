"""Message-system audit (2026-07-04): notes must never silently clip, the
battle defiance notice must be visible, and the evolution flash must name
the SPECIES (the 'babys name is intraining????' confusion)."""
from tuipet import menu
from tuipet.menu import W, NOTE_HOLD, NOTE_STEP


def test_short_note_renders_verbatim():
    assert menu.note("Fed!").plain == "Fed!\n"


def test_long_note_without_a_tick_clips_on_an_ellipsis():
    msg = "x" * (W + 20)
    out = menu.note(msg).plain
    assert out == "x" * (W - 1) + "…\n"           # visibly clipped, never silent


def test_long_note_with_a_tick_marquees_the_tail_into_view():
    msg = "HEAD " + "-" * W + " TAIL!"
    assert menu.note(msg, tick=0).plain.startswith("HEAD ")
    hold_end = NOTE_HOLD * NOTE_STEP - 1
    assert menu.note(msg, tick=hold_end).plain == menu.note(msg, tick=0).plain
    seen = set()
    for t in range(0, (len(msg) + NOTE_HOLD + 10) * NOTE_STEP * 2):
        seen.add(menu.note(msg, tick=t).plain)
    assert any("TAIL!" in s for s in seen)        # the clipped end surfaces
    assert any(s.startswith("HEAD ") for s in seen)   # ...and it loops home


def test_battle_defiance_notice_is_visible_in_the_menu():
    """'It IGNORED you!' was appended to the HP line and fell off the 38-char
    clip edge -- the player never saw the refusal."""
    import tuipet.battlescreen as bs
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.full_health = 15
    panel = bs.BattlePanel(p, {"num": 4, "name": "Foe", "stage": "Champion",
                               "vaccine": 5, "data_power": 5, "virus": 5,
                               "hp": 15, "bits": (0, 0), "boss": True})
    panel.phase = "menu"
    panel.battle.refused_order = True
    text = panel._render_menu().plain
    assert "It IGNORED you!" in text
    assert "BOSS" in text                          # the HP line keeps its tag
    panel.battle.refused_order = False
    panel.surrender_refused = True
    assert "It won't give up!" in panel._render_menu().plain


def test_evolution_flash_names_the_species_not_just_the_stage():
    """'X! evolved to InTraining!' read as if the STAGE were the pet's name;
    the flash now says who evolved into whom, stage in parentheses."""
    from tuipet.app import TuiPetApp
    from tuipet.pet import Pet
    app = TuiPetApp.__new__(TuiPetApp)             # no Textual mount needed
    app.pet = Pet.new_egg(egg_type=1)
    app.pet._hatch_into_fresh()
    old_num = app.pet.num
    app.pet.stage_seconds = 9e8
    app.pet._maybe_evolve()
    msg = app._evolve_msg(old_num)
    from tuipet import data
    _, by = data.load_sprites()
    assert f"evolved into [b]{app.pet.name}[/]" in msg
    assert f"({app.pet.stage})" in msg             # the stage reads as a CLASS, not a name
    assert by[old_num]["name"] in msg              # who it used to be
