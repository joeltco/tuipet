"""Central UI palette + runtime theme switching (no green).

One source of truth for every colour in the app. Screens import the derived
names (LCD_ON/LCD_BG/INK/INK_B/DIM/SEL/...) from here. `apply()` swaps the live
theme by rewriting those names in this module AND in every already-loaded screen
module, so a switch takes effect on the next repaint.
"""
import os
import sys

# Each theme: ink (on), screen (bg), mid (dim/secondary), accent, pos/neg
# (affinity), border (bezel), silhouette ink over habitat art (day/night), and
# the per-phase (ink, screen) tint that dims toward night like an LCD backlight.
THEMES = {
    "grey": {  # clean neutral pocket-LCD
        "on": "#2b2e31", "bg": "#c6c9cc", "mid": "#7d8186",
        "accent": "#b04a3a", "pos": "#3a6ea5", "neg": "#a23b2f", "border": "#7a7e78",
        "sil_day": "#2b2e31", "sil_night": "#e4e7ea",
        "phases": {"dawn": ("#33363a", "#d2d5d8"), "day": ("#2b2e31", "#c6c9cc"),
                   "dusk": ("#39352f", "#bdb8b2"), "night": ("#9aa0a6", "#23262a")},
    },
    "mono": {  # crisp white-on-black
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_day": "#101010", "sil_night": "#f0f0f0",
        "phases": {"dawn": ("#f0f0f0", "#141414"), "day": ("#e8e8e8", "#0c0c0c"),
                   "dusk": ("#e0c0a0", "#0c0a08"), "night": ("#9a9a9a", "#050505")},
    },
    "amber": {  # amber phosphor
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        "accent": "#ff6a3a", "pos": "#8fd0ff", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_day": "#2a1c06", "sil_night": "#ffd877",
        "phases": {"dawn": ("#ffc23a", "#160f05"), "day": ("#ffb000", "#1a1206"),
                   "dusk": ("#ff8a3a", "#1a0f04"), "night": ("#a8741a", "#0d0903")},
    },
    "midnight": {  # cool backlit blue
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_day": "#16202e", "sil_night": "#cfe0f5",
        "phases": {"dawn": ("#b9d2f0", "#15202f"), "day": ("#a9c8ee", "#101826"),
                   "dusk": ("#d0a070", "#181420"), "night": ("#6d86a8", "#0a0f18")},
    },
}
_DEFAULT = "grey"
_ORDER = list(THEMES)
_current = _DEFAULT

# names this module exports + pushes into screen modules on a theme switch
_NAMES = ("LCD_ON", "LCD_BG", "MID", "INK", "INK_B", "DIM", "SEL", "ACCENT",
          "POS", "NEG", "BORDER", "SIL_DAY", "SIL_NIGHT", "PHASE_PALETTE")
_SCREEN_MODULES = ("app", "battlescreen", "training", "adventurescreen",
                   "tournamentscreen", "shopscreen", "habitatscreen",
                   "jogressscreen", "digicorescreen", "eggselectscreen")


def _derive(t):
    on, bg, mid = t["on"], t["bg"], t["mid"]
    return {
        "LCD_ON": on, "LCD_BG": bg, "MID": mid,
        "INK": f"{on} on {bg}", "INK_B": f"bold {on} on {bg}",
        "DIM": f"{mid} on {bg}", "SEL": f"bold {bg} on {on}",
        "ACCENT": t["accent"], "POS": t["pos"], "NEG": t["neg"], "BORDER": t["border"],
        "SIL_DAY": t["sil_day"], "SIL_NIGHT": t["sil_night"], "PHASE_PALETTE": t["phases"],
    }


def apply(name, propagate=True):
    """Make `name` the live theme. Rewrites this module's colour names and (when
    propagate) pushes them into every already-loaded screen module."""
    global _current
    if name not in THEMES:
        name = _DEFAULT
    _current = name
    vals = _derive(THEMES[name])
    globals().update(vals)
    if propagate:
        for m in _SCREEN_MODULES:
            mod = sys.modules.get(__name__.rsplit(".", 1)[0] + "." + m)
            if mod is None:
                continue
            for k in _NAMES:
                if hasattr(mod, k):
                    setattr(mod, k, vals[k])
    return name


def current():
    return _current


def cycle():
    return apply(_ORDER[(_ORDER.index(_current) + 1) % len(_ORDER)])


# --- persistence of the chosen theme ---
_CONF = os.path.expanduser("~/.local/share/tuipet/theme.txt")


def save_choice(name):
    try:
        os.makedirs(os.path.dirname(_CONF), exist_ok=True)
        with open(_CONF, "w") as fh:
            fh.write(name)
    except OSError:
        pass


def load_choice():
    try:
        n = open(_CONF).read().strip()
        return n if n in THEMES else _DEFAULT
    except OSError:
        return _DEFAULT


# initialise the module-level names at import (screens read these via `from
# .theme import ...`); don't propagate yet — modules aren't all loaded.
apply(_DEFAULT, propagate=False)
