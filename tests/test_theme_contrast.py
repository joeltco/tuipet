"""Theme legibility RATCHET (theme-variant audit 2026-07-22).

tools/theme_sheet.py renders every panel under every theme and scores
each style span's WCAG contrast; this pins the palette itself so an
edit can't quietly ship grey-on-grey.  The audit's finds, fixed here:
grey's coin gold read 1.48:1 on the light box and gameboy's coin olive
1.97:1 on the pea LCD.  (The audit also flagged the terminal-cyan key
letters as palette roulette -- but cyan keys are PINNED design from the
shell-revert ruling (test_theme), so they stand until a named order.)

Thresholds are the shipped floor, not aspiration: text pairs >= 3.0:1,
status tints >= 2.0:1 (the quiet default's DIM is quiet BY DESIGN --
grey mid sits at 2.36 and stays).  Silhouette inks are exempt: they
draw over scene art and are meant to hug it."""
from tuipet.theme import THEMES

TEXT_MIN = 3.0     # on/ink and SEL (inverted)
TINT_MIN = 2.0     # mid/dim + the status readout tints


def _lum(hexcol):
    h = hexcol.lstrip("#")
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _ratio(fg, bg):
    la, lb = _lum(fg), _lum(bg)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def test_text_pairs_stay_legible_in_every_theme():
    for name, t in THEMES.items():
        bg = t["bg"]
        assert _ratio(t["on"], bg) >= TEXT_MIN, (name, "on")     # INK / INK_B
        assert _ratio(bg, t["on"]) >= TEXT_MIN, (name, "SEL")    # inverted rows


def test_tints_never_vanish_into_the_box():
    for name, t in THEMES.items():
        bg = t["bg"]
        for k in ("mid", "accent", "pos", "neg",
                  "heart", "energy", "care", "life", "coin"):
            assert _ratio(t[k], bg) >= TINT_MIN, \
                f"{name}.{k} = {_ratio(t[k], bg):.2f}:1 -- below the shipped floor"
