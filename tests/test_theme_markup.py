"""Guard: every theme must populate ALL palette globals, and the stats box must
produce VALID Rich markup.

Regression for v0.2.65-0.2.70, where removing the weather palette accidentally
deleted "LIFE"/"COIN" from theme._derive (they shared a line with "WEATHER").
That left theme.COIN/LIFE == "" -> the stats box emitted `[]...[/]` -> Textual's
visualize() raised MarkupError on launch. Unit tests missed it because they never
rendered the markup through Rich, only through Textual at runtime.
"""
from rich.markup import render as render_markup

from tuipet import theme


def test_every_theme_populates_all_palette_globals():
    for th in theme._ORDER:
        theme.apply(th)
        for name in theme._NAMES:
            val = getattr(theme, name)
            if name == "PHASE_PALETTE":
                assert isinstance(val, dict) and val, f"{th}.{name} empty"
            else:
                assert isinstance(val, str) and val, f"{th}.{name} is empty -> broken markup"


def test_stats_style_markup_parses_in_every_theme():
    # the two lines that broke: the day/night clock (COIN) and the Life bar (LIFE)
    for th in theme._ORDER:
        theme.apply(th)
        for line in (f"[{theme.COIN}]☀[/] [dim]5m00s[/]",
                     f"Life [{theme.LIFE}]███[/]",
                     f"Weight 2g   [{theme.COIN}]0b[/]"):
            render_markup(line)   # raises MarkupError if a tag has nothing to close
