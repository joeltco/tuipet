"""The THEME CONTACT SHEET (theme-variant audit 2026-07-22).

menu_sheet.py proves layout; THIS proves legibility: every panel state is
re-rendered under EVERY theme, each style span actually used is resolved
to (fg, bg) truecolor, and the WCAG contrast ratio is scored.  The mono
.#% decode can never show a grey-on-grey row -- this can.

For spans with no explicit background the theme's LCD_BG is assumed (the
box every menu paints on).  Silhouette inks are excluded: they draw over
scene ART, not the solid box, and are MEANT to sit near it.

Usage: HOME=<throwaway> python tools/theme_sheet.py [theme ...]
       flags: FAIL < 2.0 : 1 (illegible on the box), WARN < 3.0 : 1
"""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from rich.color import Color  # noqa: E402
from rich.style import Style  # noqa: E402
from rich.text import Text  # noqa: E402

from tuipet import theme  # noqa: E402

FAIL, WARN = 2.0, 3.0
# inks that deliberately hug their ground (silhouettes over art, the void)
EXCLUDE = {"SIL_SCENE", "SIL_LIGHTSOFF", "VOID"}


def _lum(rgb):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(fg, bg):
    la, lb = _lum(fg), _lum(bg)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _rgb(color):
    t = color.get_truecolor()
    return (t.red, t.green, t.blue)


def audit_theme(name):
    """Apply `name`, render every sheet state, score every span."""
    theme.apply(name)
    import menu_sheet

    seen = {}                      # style string -> first panel title
    BLOCKS = set("▀▄█▌▐░▒▓●◇◆ \n")    # art cells + swatch chips: adjacent image
    #                                pixels SHARE hue by nature -- only spans
    #                                with real GLYPHS are legibility pairs

    def grab(title, panel, budget=40):
        txt = panel.text()
        for span in txt.spans:
            body = txt.plain[span.start:span.end]
            if not body or set(body) <= BLOCKS:
                continue
            seen.setdefault(str(span.style), title)
        strip = getattr(panel, "strip", lambda: "")()
        if strip:
            for span in Text.from_markup(strip).spans:
                seen.setdefault(str(span.style), f"{title} [strip]")

    menu_sheet.show, real_show = grab, menu_sheet.show
    try:
        for state, fn in menu_sheet.SHEET.items():
            if state == "chrome":     # markup lines, not a panel: below
                continue
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    fn()
                except Exception as e:   # a state that cannot stage offline
                    print(f"  ! state {state} did not stage: {e}")
    finally:
        menu_sheet.show = real_show

    from tuipet import statusbox, app
    p = menu_sheet._pet()
    for raw in statusbox.home_lines(p):
        t = Text.from_markup(raw)
        for span in t.spans:
            body = t.plain[span.start:span.end]
            if body and not set(body) <= BLOCKS:
                seen.setdefault(str(span.style), "status card")
    kt = Text.from_markup(app.keys_markup())
    for span in kt.spans:
        body = kt.plain[span.start:span.end]
        if body and not set(body) <= BLOCKS:
            seen.setdefault(str(span.style), "action bar")

    bg_default = _rgb(Color.parse(theme.LCD_BG))
    rows = []
    for style_str, where in seen.items():
        try:
            st = Style.parse(style_str)
        except Exception:
            continue
        if st.color is None:
            continue
        fg = _rgb(st.color)
        bg = _rgb(st.bgcolor) if st.bgcolor is not None else bg_default
        rows.append((contrast(fg, bg), style_str, where,
                     st.bgcolor is None))
    return rows


def main(names):
    bad = 0
    for name in names:
        rows = audit_theme(name)
        flagged = [r for r in rows if r[0] < WARN]
        print(f"\n===== theme: {name}  ({len(rows)} styles scored) =====")
        if not flagged:
            print("  all spans >= 3.0:1 — clean")
        for ratio, style_str, where, assumed in sorted(flagged):
            tag = "FAIL" if ratio < FAIL else "warn"
            note = " (bg assumed LCD_BG)" if assumed else ""
            print(f"  {tag} {ratio:4.2f}:1  [{style_str}]  first seen: {where}{note}")
            if ratio < FAIL:
                bad += 1
    print(f"\n{bad} FAIL span(s) across {len(names)} theme(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    names = sys.argv[1:] or theme.names()
    sys.exit(main(names))
