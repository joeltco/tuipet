"""The authentic DM20 dot-matrix is 16 dots tall.  The LCD canvas is taller (24px)
so a background can show in the margins, but NOTHING the game draws is allowed
outside the 16-dot play band -- the status overlay is laid out inside it (Zzz above
the head, sick marker beside the pet, poop on the floor) and render_screen's `band`
clip is the structural backstop.  This pins both so a regression can't drift a pixel
back into the margin."""
from types import SimpleNamespace as NS

from rich.console import Console

from tuipet import app
from tuipet.render import render_screen


def _styled(text):
    """Capture the styled (ANSI) render -- render_screen paints every cell as the same
    '▀' glyph and only varies the colour, so .plain is identical for any pixels; the
    styled capture is what actually reflects which dots are lit."""
    c = Console(force_terminal=True, color_system="truecolor", width=200)
    with c.capture() as cap:
        c.print(text, end="")
    return cap.get()


def _pet(**kw):
    base = dict(dead=False, num=1, poop=0, asleep=False, sick=False, anim="idle",
                is_injured=lambda: False,
                has_medicine=lambda: False, has_bandage=lambda: False, hunger=2)
    base.update(kw)
    return NS(**base)


def _bounds(pet):
    px_h = app.SCREEN_ROWS * 2
    pr = (app.SCREEN_COLS - app.SPRITE_W) // 2 + app.SPRITE_W
    return app._effect_overlay(pet, 0, app.SCREEN_COLS, px_h, tick=0, pet_right=pr)


def test_band_constants_describe_a_16_dot_screen():
    assert app.BAND_BOT - app.BAND_TOP == 16
    assert app.PLAY_BAND == (app.BAND_TOP, app.BAND_BOT)


def test_status_overlay_never_leaves_the_band():
    states = [
        _pet(asleep=True),                                             # Zzz above head
        _pet(sick=True, is_injured=lambda: True),                      # condition markers
        _pet(poop=3),                                                  # droppings on the floor
        _pet(hunger=0),                                                # care-call bubble
        _pet(anim="happy"), _pet(anim="unhappy"),                      # reaction emotes
        _pet(asleep=True, sick=True, poop=3),                          # everything at once
    ]
    for pet in states:
        for x, y in _bounds(pet):
            assert app.PLAY_X0 <= x < app.PLAY_R, f"x={x} outside play window"
            assert app.BAND_TOP <= y < app.BAND_BOT, f"y={y} outside 16-dot band"


def test_render_screen_band_clips_out_of_band_pixels():
    # a full-height sprite column: with band set, only the band rows stay lit
    tall = ["1"] * (app.SCREEN_ROWS * 2)
    clipped = _styled(render_screen(tall, app.SCREEN_COLS, app.SCREEN_ROWS, band=app.PLAY_BAND))
    full = _styled(render_screen(tall, app.SCREEN_COLS, app.SCREEN_ROWS))
    assert clipped != full                       # the band actually dropped pixels
    # an overlay pixel above the band ceiling must not light anything
    above = _styled(render_screen([], app.SCREEN_COLS, app.SCREEN_ROWS,
                                  overlay=[(app.PLAY_X0, app.BAND_TOP - 1)], band=app.PLAY_BAND))
    empty = _styled(render_screen([], app.SCREEN_COLS, app.SCREEN_ROWS))
    assert above == empty
    # ...but a pixel inside the band does light up
    inside = _styled(render_screen([], app.SCREEN_COLS, app.SCREEN_ROWS,
                                   overlay=[(app.PLAY_X0, app.BAND_TOP)], band=app.PLAY_BAND))
    assert inside != empty
