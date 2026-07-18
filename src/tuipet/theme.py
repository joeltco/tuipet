"""Central UI palette + runtime theme switching (no green).

One source of truth for every colour in the app. Screens import the derived
names (LCD_ON/LCD_BG/INK/INK_B/DIM/SEL/...) from here. `apply()` swaps the live
theme by rewriting those names in this module AND in every already-loaded screen
module, so a switch takes effect on the next repaint.
"""
import os
import sys

# Each theme: ink/screen/mid + accent, pos/neg (affinity), border (bezel),
# silhouette ink over habitat art (day/night), per-phase (ink, screen) tint,
# and the STATUS readout colours (heart/energy/mood/life/coin).  (The
# per-weather scene tints and precip inks left with the weather system;
# BASIC VPET 2026-07-16.)
THEMES = {
    "grey": {
        "on": "#2b2e31", "bg": "#c6c9cc", "mid": "#7d8186",
        "accent": "#b04a3a", "pos": "#3a6ea5", "neg": "#a23b2f", "border": "#7a7e78",
        "sil_day": "#2b2e31", "sil_night": "#e4e7ea",
        "heart": "#c25a4a", "energy": "#4a90c2", "mood": "#a06ac2", "life": "#3f9a86", "coin": "#c2a24a",
        "void": "#000000", "flash": ("#f2f6fa", "#1a2026", "#e8eef2"),
    },
    "mono": {
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_day": "#101010", "sil_night": "#f0f0f0",
        "heart": "#d8d8d8", "energy": "#b8b8b8", "mood": "#a8a8a8", "life": "#c8c8c8", "coin": "#e8e8e8",
        "void": "#000000", "flash": ("#ffffff", "#0c0c0c", "#e8e8e8"),
    },
    "amber": {
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        "accent": "#ff6a3a", "pos": "#8fd0ff", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_day": "#2a1c06", "sil_night": "#ffd877",
        "heart": "#ff7a3a", "energy": "#ffb000", "mood": "#e0923a", "life": "#ffc24a", "coin": "#ffd877",
        "void": "#000000", "flash": ("#ffe8b0", "#1a1206", "#ffd890"),
    },
    "midnight": {
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_day": "#16202e", "sil_night": "#cfe0f5",
        "heart": "#e0884a", "energy": "#6fb0e0", "mood": "#9a8fe0", "life": "#5fc7b0", "coin": "#e0c060",
        "void": "#000000", "flash": ("#dce8f8", "#101826", "#c8d8f0"),
    },
    # the classic 4-shade DMG pea-soup LCD (the default stays grey; this is
    # an option).  NB the v0.2.284 putty-shell chrome experiment was REVERTED
    # (Joel 2026-07-05: "this looks bad") -- gameboy rides the fallbacks.
    "gameboy": {
        "on": "#0f380f", "bg": "#9bbc0f", "mid": "#306230",
        "accent": "#7a3a22", "pos": "#2a5a8a", "neg": "#8a3a2a", "border": "#4a5a28",
        "sil_day": "#0f380f", "sil_night": "#d8e8a0",
        "heart": "#8a4a2a", "energy": "#2a6a8a", "mood": "#6a4a8a", "life": "#306230", "coin": "#8a7a1a",
        "void": "#0f380f", "flash": ("#e0f0c0", "#0f380f", "#d8e8a0"),
        # (the bg_ramp background quantizer is GONE -- Joel 2026-07-18:
        # "get rid of the green and white background pallet switcher in
        # gameboy and paper. it looks like shit".  Backdrops render full
        # colour like every theme; the DMG shades stay for chrome+sprites.)
    },
    "paper": {
        "on": "#2a2620", "bg": "#efe9dc", "mid": "#8a8274",
        "accent": "#a04a2a", "pos": "#3a6a8a", "neg": "#a03a2a", "border": "#b8ac97",
        "sil_day": "#2a2620", "sil_night": "#f4efe4",
        "heart": "#a04a2a", "energy": "#3a6a8a", "mood": "#7a5a92", "life": "#567a68", "coin": "#967a2a",
        "void": "#000000", "flash": ("#ffffff", "#2a2620", "#faf6ec"),
        # (bg_ramp removed with gameboy's -- 2026-07-18, see above)
    },
    "sakura": {
        "on": "#f0b8c8", "bg": "#241820", "mid": "#8a5a6c",
        "accent": "#ff8a5a", "pos": "#8ac8e8", "neg": "#ff6a6a", "border": "#4a2a3a",
        "sil_day": "#2a1a24", "sil_night": "#ffd0dc",
        "heart": "#ff7a8a", "energy": "#8ac8e8", "mood": "#c89ae8", "life": "#7ad0b0", "coin": "#f0c86a",
        "void": "#000000", "flash": ("#ffe8f0", "#241820", "#f8d8e4"),
    },
    "ocean": {
        "on": "#7fd8d0", "bg": "#0a1e22", "mid": "#3f7a78",
        "accent": "#f0a05a", "pos": "#8ab8f0", "neg": "#f07a5a", "border": "#1c3a3e",
        "sil_day": "#0f2a2e", "sil_night": "#c8f0e8",
        "heart": "#f07a6a", "energy": "#6ac8e0", "mood": "#9a9ae8", "life": "#5ad0a0", "coin": "#e8c86a",
        "void": "#000000", "flash": ("#e0f8f4", "#0a1e22", "#c8ece6"),
    },
}
_DEFAULT = "grey"
_ORDER = list(THEMES)
_current = _DEFAULT

_NAMES = ("LCD_ON", "LCD_BG", "MID", "INK", "INK_B", "DIM", "SEL", "ACCENT",
          "POS", "NEG", "BORDER", "SIL_DAY", "SIL_NIGHT",
          "HEART", "ENERGY", "MOOD", "LIFE", "COIN", "VOID", "FLASH",
          "BEZEL", "SHELL", "LABEL", "KEY")
# (the hand-maintained _SCREEN_MODULES registry is gone -- apply() discovers
# palette-bound modules from sys.modules; hardening 2026-07-05)


# Static declarations of the palette names so linters/type-checkers can see them.
# apply(_DEFAULT) runs at import (bottom of file) and overwrites these with the live
# theme via globals().update(_derive(...)); they are never actually the empties below.
LCD_ON = LCD_BG = MID = INK = INK_B = DIM = SEL = ACCENT = POS = NEG = BORDER = ""
SIL_DAY = SIL_NIGHT = HEART = ENERGY = MOOD = LIFE = COIN = VOID = ""
BEZEL = SHELL = LABEL = KEY = ""
FLASH: tuple = ("", "", "")


def _derive(t):
    on, bg, mid = t["on"], t["bg"], t["mid"]
    return {
        "LCD_ON": on, "LCD_BG": bg, "MID": mid,
        "INK": f"{on} on {bg}", "INK_B": f"bold {on} on {bg}",
        "DIM": f"{mid} on {bg}", "SEL": f"bold {bg} on {on}",
        "ACCENT": t["accent"], "POS": t["pos"], "NEG": t["neg"], "BORDER": t["border"],
        "SIL_DAY": t["sil_day"], "SIL_NIGHT": t["sil_night"],
        "HEART": t["heart"], "ENERGY": t["energy"], "MOOD": t["mood"],
        "LIFE": t["life"], "COIN": t["coin"],
        "VOID": t["void"], "FLASH": t["flash"],
        # shell chrome (optional per theme; the plain themes keep border/mid):
        # bezel = the LCD's thick frame, shell = the outer boxes, label = the
        # printed titles/key-hint text, key = the action-bar shortcut letters
        # (the DMG shell polish, 2026-07-05)
        "BEZEL": t.get("bezel", t["border"]),
        "SHELL": t.get("shell", t["border"]),
        "LABEL": t.get("label", t["mid"]),
        "KEY": t.get("key", "cyan"),
    }


def apply(name, propagate=True):
    """Make `name` the live theme. Rewrites this module's colour names and (when
    propagate) pushes them into every already-loaded screen module.

    Screens are DISCOVERED, not listed: any loaded tuipet module that bound
    LCD_ON or INK at import gets retinted.  The old hand-maintained
    _SCREEN_MODULES tuple failed SILENTLY when a new screen wasn't registered
    -- it kept its import-time colours on theme switch (hardening 2026-07-05)."""
    global _current
    if name not in THEMES:
        name = _DEFAULT
    _current = name
    vals = _derive(THEMES[name])
    globals().update(vals)
    if propagate:
        pkg = __name__.rsplit(".", 1)[0] + "."
        for mname, mod in list(sys.modules.items()):
            if (mod is None or not mname.startswith(pkg)
                    or mname == __name__
                    or not (hasattr(mod, "LCD_ON") or hasattr(mod, "INK"))):
                continue
            for k in _NAMES:
                if hasattr(mod, k):
                    setattr(mod, k, vals[k])
    return name


def current():
    return _current


def names():
    return list(_ORDER)


def blend_frames(fa, fb, a):
    """Cell-wise lerp between two equal-shaped frames (rows of 6-hex-char
    cells) -- the interpolant for the background cross-fade."""
    if a <= 0:
        return fa
    if a >= 1:
        return fb
    out = []
    for ra, rb in zip(fa, fb):
        cells = []
        for i in range(0, len(ra), 6):
            r1, g1, b1 = int(ra[i:i + 2], 16), int(ra[i + 2:i + 4], 16), int(ra[i + 4:i + 6], 16)
            r2, g2, b2 = int(rb[i:i + 2], 16), int(rb[i + 2:i + 4], 16), int(rb[i + 4:i + 6], 16)
            cells.append("%02x%02x%02x" % (int(r1 + (r2 - r1) * a), int(g1 + (g2 - g1) * a), int(b1 + (b2 - b1) * a)))
        out.append("".join(cells))
    return out


# (the star-twinkle + lava-ember night art -- _cell/_luma/_find_stars/
# star_frame/tw_beat/_find_lava/ember_frame and their caches -- left with
# the day/night system: home scenes are one look each and the arena no
# longer tracks the clock.  BASIC VPET 2026-07-17)

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


# initialise module-level names at import (default theme); don't propagate yet.
apply(_DEFAULT, propagate=False)
