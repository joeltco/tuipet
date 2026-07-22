"""DNA system audit (2026-07-22, own-thing terms: shipped behavior IS the
spec -- no source-game diffing).  The full battery ran every UI claim
against the mechanics; nearly everything held.  Fixed: the result page
said "+N to both neighbors" on resonant wins, but the edge bands
(DeepSaver/DarkArea) splash exactly ONE; and the Divergence page now
tells the wipe rule out loud ("charges clear at every evolution") --
evolve_to's reset_dna was documented engine-side only, so an under-armed
charge died silently at the line climb.  These pins close the gaps the
existing DNA/divergence suites left open."""
from tuipet.pet import (Pet, DNA_STABILIZER_BET,
                        DNA_RESONANT_BET, dna_field_for_rate)
from tuipet import persistence


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    p.bits = 100000
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_rate_band_edges_hold():
    """<=8 too slow, >80 too fast, the nine real bands between."""
    assert dna_field_for_rate(0) == "None"
    assert dna_field_for_rate(8) == "None"
    assert dna_field_for_rate(9) == "DeepSaver"
    assert dna_field_for_rate(80) == "DarkArea"
    assert dna_field_for_rate(81) == "None"


def test_edge_band_resonance_splashes_one_neighbor_and_says_so():
    """DeepSaver/DarkArea have one adjacent band; the result row must not
    promise 'both'."""
    from tuipet.dnascreen import DNAPanel
    p = _pet()
    p.dna_bet(DNA_RESONANT_BET)
    f = p.dna_minigame_award(DNA_RESONANT_BET, 10)         # DeepSaver, the edge
    assert f == "DeepSaver"
    splashed = [k for k, v in p.dna_owned.items() if v and k != f]
    assert splashed == ["JungleTrooper"]                   # exactly one
    pan = DNAPanel(p)
    pan.phase, pan.won, pan.blink = "result", (f, DNA_RESONANT_BET, 10, 99, 0), 0
    plain = pan.text().plain
    assert "its one neighbor" in plain and "both" not in plain


def test_interior_resonance_still_says_both():
    from tuipet.dnascreen import DNAPanel
    p = _pet()
    p.dna_bet(DNA_RESONANT_BET)
    f = p.dna_minigame_award(DNA_RESONANT_BET, 30)         # NatureSpirit, interior
    assert f == "NatureSpirit"
    assert sorted(k for k, v in p.dna_owned.items() if v and k != f) \
        == ["JungleTrooper", "WindGuardian"]
    pan = DNAPanel(p)
    pan.phase, pan.won, pan.blink = "result", (f, DNA_RESONANT_BET, 30, 99, 0), 0
    assert "both neighbors" in pan.text().plain


def test_the_divergence_page_teaches_the_wipe_rule():
    """A Rookie Agumon HAS wild roads (the divergence suite's fixture) --
    the filled page must say the wipe rule, not just the arm hint."""
    from tuipet.dnascreen import DNAPanel
    p = _pet(stage="Rookie")
    pan = DNAPanel(p)
    assert pan._roads, "fixture lost its roads -- rebase on test_divergence.mk"
    pan.phase = "roads"
    plain = pan.text().plain
    assert "Charge 8 in ONE Field to arm" in plain      # the note's head renders
    # the tail rides the marquee (notes scroll, they never clip) -- pin the
    # SOURCE string, not one frozen phase (the round-two lesson)
    import inspect
    from tuipet import dnascreen
    assert "charges clear at every evolution" in inspect.getsource(dnascreen)


def test_evolution_wipes_charges_but_keeps_the_bank():
    p = _pet()
    p.dna_owned["DarkArea"] = 7
    p.dna_applied["DarkArea"] = 5
    p.reset_dna()
    assert p.dna_applied["DarkArea"] == 0
    assert p.dna_owned["DarkArea"] == 7


def test_interrupted_wager_settles_as_a_spoiled_mash(isolate_save=None):
    """S2 ruling 2026-07-20, never pinned: a paid mash in flight at quit
    settles on load at rate 0 -- the stake stays spent, a plain wager
    wastes (None), a stabilized stake still buys its band."""
    p = _pet()
    p.dna_bet(50)
    assert p.dna_wager_pending == 50
    save = persistence.to_save_dict(p)
    q, msg = persistence.pet_from_save(save)
    assert q.dna_wager_pending == 0
    assert "settled" in msg and q.dna_owned.get("None", 0) == 50   # the dud bin banks
    r = _pet()
    r.dna_bet(DNA_STABILIZER_BET)
    save = persistence.to_save_dict(r)
    s, msg = persistence.pet_from_save(save)
    assert s.dna_wager_pending == 0
    assert s.dna_owned.get("DeepSaver", 0) == 99           # clamped into the low band
    assert "DeepSaver banked" in msg


def test_the_charge_meter_and_award_share_one_band_map():
    """The live mash meter's Field preview and the award must never disagree:
    both read dna_field_for_rate (single source)."""
    from tuipet import dnascreen
    import inspect
    src = inspect.getsource(dnascreen)
    assert "dna_field_for_rate(rate)" in src               # the strip preview
    assert "DNA_RATE_BANDS" in src                         # no private band copy
    for rate in (0, 9, 25, 47, 80, 99):
        p = _pet()
        p.dna_bet(10)
        assert p.dna_minigame_award(10, rate) == dna_field_for_rate(rate)


def test_the_mash_scene_and_result_blink_animate():
    """DNA visual audit (2026-07-22): the mash bob flips on its urgency beat
    (2), a press flashes the strike pose for exactly its decay, and the
    result's Field name blinks in on the reveal cadence.  Frames compared
    at the PIXEL tap -- .plain of a painted scene is all half-blocks and
    proves nothing (the theme-audit lesson)."""
    from tuipet import render
    from tuipet.dnascreen import DNAPanel
    grabbed = {}
    real = render._paint_cells
    def tap(buf, *a, **k):
        grabbed["buf"] = tuple(tuple(r) for r in buf)
        return real(buf, *a, **k)
    render._paint_cells = tap
    try:
        p = _pet()
        pan = DNAPanel(p)
        pan.phase = "mash"
        def frame():
            pan.text()
            return grabbed["buf"]
        pan.frame_i = 0; f0 = frame()
        pan.frame_i = 1; assert frame() == f0          # holds within the beat
        pan.frame_i = 2; f2 = frame()
        assert f2 != f0                                # flips at beat 2
        pan._mash_flash = 2
        assert frame() != f2                           # the strike pose lands
        assert pan._mash_flash == 1                    # ...and decays
    finally:
        render._paint_cells = real
    pan = DNAPanel(_pet())
    pan.phase, pan.won = "result", ("NatureSpirit", 500, 30, 99, 0)
    pan.blink = 0
    assert "Nature Spirit" in pan.text().plain         # the reveal
    pan.blink = 2
    assert "Nature Spirit" not in pan.text().plain     # the blink out


# --- the teachings ride where the player IS (gameplay polish #12-14) ---------

def test_the_charge_screen_alternates_both_truths():
    """The wipe law lived only on the Divergence page while the SPENDING
    happens on Charge -- a 5/8 charge died silently at the stage timer.
    The note now alternates the two honest lines on the sealed-tease
    cadence (40 ticks), armed state outranking both."""
    from tuipet.dnascreen import DNAPanel
    from tuipet import evolution
    p = _pet(stage="Rookie")
    pan = DNAPanel(p)
    pan.phase = "charge"
    # long notes MARQUEE (they never clip) -- sample the cycle and pin the
    # SOURCE strings, this file's own round-two lesson
    frames = []
    for t in range(0, 160, 4):
        pan.frame_i = t
        frames.append(pan.text().plain)
    union = "".join(frames)
    assert "arms the Divergence road" in union       # truth A's head
    assert "charges clear" in union                  # truth B scrolls through
    assert len(set(frames)) > 1                      # it genuinely alternates
    import inspect
    from tuipet import dnascreen
    src = inspect.getsource(dnascreen)
    assert "charges clear at every evolution — arm before the clock fills" in src
    p.dna_applied["DeepSaver"] = evolution.DIVERGE_NEED["Rookie"]
    pan2 = DNAPanel(p)                              # _roads resolve at init
    pan2.phase = "charge"
    assert "ARMED" in pan2.text().plain             # armed outranks the cycle


def test_the_dna_home_teaches_the_whole_loop():
    """help GROW's grammar, on the screen itself: generate, charge ONE
    Field, take the road -- 'then charge it' never said WHY."""
    from tuipet.dnascreen import DNAPanel
    pan = DNAPanel(_pet(stage="Rookie"))
    plain = pan.text().plain
    assert "charge ONE Field" in plain and "road" in plain


def test_the_hud_carries_the_standing_armed_notice():
    """Gameplay polish #14: an armed steer set hours ago fired with zero
    warning outside the DNA screen.  The idle HUD now carries it -- and
    every need outranks it (the cascade is untouched above it)."""
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet import evolution
    p = _pet(stage="Rookie")
    p.line_id = "ver1"
    p.hunger, p.energy = 4, 24                     # no needs: the idle slot
    p._sicken = lambda *a, **k: None
    p.dna_applied["DeepSaver"] = evolution.DIVERGE_NEED["Rookie"]

    async def go():
        app = TuiPetApp(pet=p)
        async with app.run_test(size=(82, 32)) as pilot:
            await pilot.pause()
            await pilot.press("enter")             # title -> main view
            await pilot.pause()
            app.on_tick()
            app.on_tick()                          # clear-slot tick, then armed
            armed = str(app.msg_w.render())
            p.hunger = 0                           # a need arrives: it outranks
            app.on_tick()
            need = str(app.msg_w.render())
            p.hunger = 4
            p.dna_applied["DeepSaver"] = 0         # disarmed: the notice clears
            app.on_tick()
            app.on_tick()
            gone = str(app.msg_w.render())
            return armed, need, gone

    armed, need, gone = asyncio.run(go())
    # the HUD box clips at its width and the full line marquees -- pin the
    # head here and the full wording at its source
    assert "DNA armed" in armed
    import inspect
    from tuipet import app as app_mod
    assert "next evolution rides the" in inspect.getsource(app_mod)
    assert "hungry" in need and "DNA armed" not in need
    assert "DNA armed" not in gone
