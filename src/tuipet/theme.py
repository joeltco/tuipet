"""Central UI palette + runtime theme switching.

One source of truth for every colour in the app. Screens import the derived
names (LCD_ON/LCD_BG/INK/INK_B/DIM/SEL/...) from here. `apply()` swaps the live
theme by rewriting those names in this module AND in every already-loaded screen
module, so a switch takes effect on the next repaint.
"""
import os
import sys

# Each theme: ink/screen/mid + accent, pos/neg (affinity), border (bezel),
# the two silhouette inks (sil_scene = the dark sprite over scene art at any
# hour; sil_lightsoff = the pale sprite in the lights-off room -- the old
# day/night names outlived the arena clock; naming audit 2026-07-19), and
# the STATUS readout colours (heart/energy/care/life/coin -- "care" tints
# the care-mistakes row; its old name "mood" outlived the mood system).
# (The per-weather scene tints and precip inks left with the weather
# system; BASIC VPET 2026-07-16.)
THEMES = {
    "grey": {
        "on": "#2b2e31", "bg": "#c6c9cc", "mid": "#7d8186",
        "accent": "#b04a3a", "pos": "#3a6ea5", "neg": "#a23b2f", "border": "#7a7e78",
        "sil_scene": "#2b2e31", "sil_lightsoff": "#e4e7ea",
        # energy/care/life darkened in-family (theme audit 2026-07-28):
        # the old #4a90c2/#a06ac2/#3f9a86 sat at 2.0-2.4:1 on the light
        # box -- the same washed-out class the 07-22 coin fix repaired --
        # while every sibling readout reads at 2.6+; now 3.1-3.4:1.
        "heart": "#c25a4a", "energy": "#34719f", "care": "#8350a8", "life": "#2c7a6a",
        "coin": "#7a5f14",   # was #c2a24a: 1.48:1 on the light box (theme audit 2026-07-22)
        "void": "#000000", "flash": ("#f2f6fa", "#1a2026", "#e8eef2"),
    },
    "mono": {
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_scene": "#101010", "sil_lightsoff": "#f0f0f0",
        "heart": "#d8d8d8", "energy": "#b8b8b8", "care": "#a8a8a8", "life": "#c8c8c8", "coin": "#e8e8e8",
        "void": "#000000", "flash": ("#ffffff", "#0c0c0c", "#e8e8e8"),
    },
    "amber": {
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        # pos was #8fd0ff -- a sky blue on the amber phosphor (Joel
        # 2026-07-28: "conquered was blue in an amber theme").  Amber is the
        # one theme whose whole world is a single phosphor: positive =
        # BRIGHTEST amber (the flash tuple's own celebration hex), warm neg
        # stays the warning pop.  The other themes keep the blue-pos
        # convention (the powers row's green/blue/red) on purpose.
        "accent": "#ff6a3a", "pos": "#ffe8b0", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_scene": "#2a1c06", "sil_lightsoff": "#ffd877",
        "heart": "#ff7a3a", "energy": "#ffb000", "care": "#e0923a", "life": "#ffc24a", "coin": "#ffd877",
        "void": "#000000", "flash": ("#ffe8b0", "#1a1206", "#ffd890"),
    },
    "midnight": {
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_scene": "#16202e", "sil_lightsoff": "#cfe0f5",
        "heart": "#e0884a", "energy": "#6fb0e0", "care": "#9a8fe0", "life": "#5fc7b0", "coin": "#e0c060",
        "void": "#000000", "flash": ("#dce8f8", "#101826", "#c8d8f0"),
    },
    # FOREST + DUSK replaced gameboy + paper (Joel 2026-10-15: "replace gameboy
    # and paper themes with something else. Forest and something"); a saved
    # choice of either old name maps over in load_choice (_RENAMED).
    "forest": {
        "on": "#b8d8a0", "bg": "#0f1a10", "mid": "#5f8054",
        "accent": "#e0a050", "pos": "#8ac0e8", "neg": "#e07a5a", "border": "#24382a",
        "sil_scene": "#142016", "sil_lightsoff": "#d8f0c0",
        "heart": "#e08a6a", "energy": "#7ac0d8", "care": "#b09ae0", "life": "#8ad08a", "coin": "#e0c860",
        "void": "#000000", "flash": ("#e8f8e0", "#0f1a10", "#d0e8c0"),
    },
    "dusk": {
        "on": "#d0b8f0", "bg": "#1a1426", "mid": "#7e6ea0",
        "accent": "#f0a060", "pos": "#8ac0f0", "neg": "#f07a7a", "border": "#3a2c50",
        "sil_scene": "#201830", "sil_lightsoff": "#e8dcf8",
        "heart": "#f08aa0", "energy": "#8ac8f0", "care": "#c8a0f0", "life": "#7ad8b8", "coin": "#f0d070",
        "void": "#000000", "flash": ("#f4ecfc", "#1a1426", "#e4d8f4"),
    },
    "sakura": {
        "on": "#f0b8c8", "bg": "#241820", "mid": "#8a5a6c",
        "accent": "#ff8a5a", "pos": "#8ac8e8", "neg": "#ff6a6a", "border": "#4a2a3a",
        "sil_scene": "#2a1a24", "sil_lightsoff": "#ffd0dc",
        "heart": "#ff7a8a", "energy": "#8ac8e8", "care": "#c89ae8", "life": "#7ad0b0", "coin": "#f0c86a",
        "void": "#000000", "flash": ("#ffe8f0", "#241820", "#f8d8e4"),
    },
    "ocean": {
        "on": "#7fd8d0", "bg": "#0a1e22", "mid": "#3f7a78",
        "accent": "#f0a05a", "pos": "#8ab8f0", "neg": "#f07a5a", "border": "#1c3a3e",
        "sil_scene": "#0f2a2e", "sil_lightsoff": "#c8f0e8",
        "heart": "#f07a6a", "energy": "#6ac8e0", "care": "#9a9ae8", "life": "#5ad0a0", "coin": "#e8c86a",
        "void": "#000000", "flash": ("#e0f8f4", "#0a1e22", "#c8ece6"),
    },
}
_DEFAULT = "grey"
_RENAMED = {"gameboy": "forest", "paper": "dusk"}   # retired 2026-10-15
_ORDER = list(THEMES)
_current = _DEFAULT

_NAMES = ("LCD_ON", "LCD_BG", "MID", "INK", "INK_B", "DIM", "SEL", "ACCENT",
          "POS", "NEG", "BORDER", "SIL_SCENE", "SIL_LIGHTSOFF",
          "HEART", "ENERGY", "CARE", "LIFE", "COIN", "VOID", "FLASH",
          "BEZEL", "SHELL", "LABEL", "KEY")
# (the hand-maintained _SCREEN_MODULES registry is gone -- apply() discovers
# palette-bound modules from sys.modules; hardening 2026-07-05)


# Static declarations of the palette names so linters/type-checkers can see them.
# apply(_DEFAULT) runs at import (bottom of file) and overwrites these with the live
# theme via globals().update(_derive(...)); they are never actually the empties below.
LCD_ON = LCD_BG = MID = INK = INK_B = DIM = SEL = ACCENT = POS = NEG = BORDER = ""
SIL_SCENE = SIL_LIGHTSOFF = HEART = ENERGY = CARE = LIFE = COIN = VOID = ""
BEZEL = SHELL = LABEL = KEY = ""
FLASH: tuple = ("", "", "")


SHELL_BG = "#121212"
SHELL_ROLES = ("accent", "pos", "neg", "heart", "energy", "care", "life", "coin")
_GREY_SHELL = dict(accent="#e47b6b", pos="#7fa8d8", neg="#e47b6b",
                   heart="#e47b6b", energy="#7fa8d8", care="#b28ad4",
                   life="#68b89f", coin="#d8b45c")


def shell_colors(t):
    """Semantic inks for dark cards, independent of the LCD palette."""
    colors = {role: t[role] for role in SHELL_ROLES}
    if t is THEMES["grey"]:
        colors.update(_GREY_SHELL)
    return colors


def shell_markup(markup):
    """Retint explicit card markup only; never rewrite LCD or sprite inks."""
    import re
    t = THEMES[_current]
    colors = shell_colors(t)
    mapping = {t[role]: colors[role] for role in SHELL_ROLES}
    return re.sub(r"#[0-9a-fA-F]{6}", lambda m: mapping.get(m[0], m[0]), markup)


def shell_feedback(markup):
    """Translate LCD feedback roles for the dark shell message box."""
    t = THEMES[_current]
    ink = t["sil_lightsoff"] if _current == "grey" else t["on"]
    return (shell_markup(markup).replace(f" on {t['bg']}", "")
            .replace(t["on"], ink))


def _derive(t):
    on, bg, mid = t["on"], t["bg"], t["mid"]
    return {
        "LCD_ON": on, "LCD_BG": bg, "MID": mid,
        "INK": f"{on} on {bg}", "INK_B": f"bold {on} on {bg}",
        "DIM": f"{mid} on {bg}", "SEL": f"bold {bg} on {on}",
        "ACCENT": t["accent"], "POS": t["pos"], "NEG": t["neg"], "BORDER": t["border"],
        "SIL_SCENE": t["sil_scene"], "SIL_LIGHTSOFF": t["sil_lightsoff"],
        "HEART": t["heart"], "ENERGY": t["energy"], "CARE": t["care"],
        "LIFE": t["life"], "COIN": t["coin"],
        "VOID": t["void"], "FLASH": t["flash"],
        # shell chrome (optional per theme; the plain themes keep border/mid):
        # bezel = the LCD's thick frame, shell = the outer boxes, label = the
        # printed titles/key-hint text, key = the action-bar shortcut letters
        # (the DMG shell polish, 2026-07-05)
        "BEZEL": t.get("bezel", t["border"]),
        "SHELL": t.get("shell", t["border"]),
        "LABEL": t.get("label", "#7d8186" if t is THEMES["grey"] else t["on"]),
        "KEY": t.get("key", "cyan"),   # cyan is PINNED design (the shell-revert
        #                                ruling, test_theme) -- the 2026-07-22
        #                                theme audit flagged it as terminal-
        #                                palette roulette; change only on a
        #                                named order
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
def _conf_path():
    """theme.txt under the LIVE save dir, resolved at call time (the
    injectable-paths law).  The old hardcoded ~/.local/share/tuipet path
    ignored TUIPET_SAVE_DIR and the iOS dir pick: the choice silently
    never saved on iOS, tests could touch the real pref, and erase_all
    swept a theme.txt that wasn't this one (naming audit 2026-07-19;
    sound.txt always did it right)."""
    from . import persistence
    return os.path.join(persistence.SAVE_DIR, "theme.txt")


def save_choice(name):
    try:
        p = _conf_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(name)
    except OSError:
        pass


def load_choice():
    try:
        n = open(_conf_path(), encoding="utf-8").read().strip()
        n = _RENAMED.get(n, n)
        return n if n in THEMES else _DEFAULT
    except OSError:
        return _DEFAULT


# initialise module-level names at import (default theme); don't propagate yet.
apply(_DEFAULT, propagate=False)
