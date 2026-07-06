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
# STATUS readout colours (heart/energy/mood/life/coin), and a per-weather
# scene tint {category: (hex, alpha)} blended over the habitat background.
THEMES = {
    "grey": {
        "on": "#2b2e31", "bg": "#c6c9cc", "mid": "#7d8186",
        "accent": "#b04a3a", "pos": "#3a6ea5", "neg": "#a23b2f", "border": "#7a7e78",
        "sil_day": "#2b2e31", "sil_night": "#e4e7ea",
        "heart": "#c25a4a", "energy": "#4a90c2", "mood": "#a06ac2", "life": "#3f9a86", "coin": "#c2a24a",
        "weather": {"rain": ("#2e3a4a", 0.30), "snow": ("#d6dee6", 0.26), "cloud": ("#5a5e62", 0.18)},
        "void": "#000000", "flash": ("#f2f6fa", "#1a2026", "#e8eef2"),
        "phases": {"dawn": ("#33363a", "#d2d5d8"), "day": ("#2b2e31", "#c6c9cc"),
                   "dusk": ("#39352f", "#bdb8b2"), "night": ("#9aa0a6", "#23262a")},
    },
    "mono": {
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_day": "#101010", "sil_night": "#f0f0f0",
        "heart": "#d8d8d8", "energy": "#b8b8b8", "mood": "#a8a8a8", "life": "#c8c8c8", "coin": "#e8e8e8",
        "weather": {"rain": ("#1c1c1c", 0.32), "snow": ("#dcdcdc", 0.26), "cloud": ("#383838", 0.18)},
        "void": "#000000", "flash": ("#ffffff", "#0c0c0c", "#e8e8e8"),
        "phases": {"dawn": ("#f0f0f0", "#141414"), "day": ("#e8e8e8", "#0c0c0c"),
                   "dusk": ("#e0c0a0", "#0c0a08"), "night": ("#9a9a9a", "#050505")},
    },
    "amber": {
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        "accent": "#ff6a3a", "pos": "#8fd0ff", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_day": "#2a1c06", "sil_night": "#ffd877",
        "heart": "#ff7a3a", "energy": "#ffb000", "mood": "#e0923a", "life": "#ffc24a", "coin": "#ffd877",
        "weather": {"rain": ("#241a0c", 0.34), "snow": ("#ece0c8", 0.26), "cloud": ("#2e2410", 0.20)},
        "void": "#000000", "flash": ("#ffe8b0", "#1a1206", "#ffd890"),
        "phases": {"dawn": ("#ffc23a", "#160f05"), "day": ("#ffb000", "#1a1206"),
                   "dusk": ("#ff8a3a", "#1a0f04"), "night": ("#a8741a", "#0d0903")},
    },
    "midnight": {
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_day": "#16202e", "sil_night": "#cfe0f5",
        "heart": "#e0884a", "energy": "#6fb0e0", "mood": "#9a8fe0", "life": "#5fc7b0", "coin": "#e0c060",
        "weather": {"rain": ("#0a1626", 0.36), "snow": ("#c4d8f0", 0.26), "cloud": ("#16223a", 0.22)},
        "void": "#000000", "flash": ("#dce8f8", "#101826", "#c8d8f0"),
        "phases": {"dawn": ("#b9d2f0", "#15202f"), "day": ("#a9c8ee", "#101826"),
                   "dusk": ("#d0a070", "#181420"), "night": ("#6d86a8", "#0a0f18")},
    },
    # the classic 4-shade DMG pea-soup LCD in its putty-grey shell
    # (the default stays grey; this is an option)
    "gameboy": {
        "on": "#0f380f", "bg": "#9bbc0f", "mid": "#306230",
        "accent": "#a83a6a",                                  # the A/B button magenta
        "pos": "#5c5ab8", "neg": "#b04578",                   # the bezel stripes: navy / burgundy
        "border": "#4a5a28",
        "bezel": "#565663",     # the dark screen-surround plate (Joel: "lcd border gray like a dmg")
        "shell": "#b8b4aa",     # the putty body around everything else
        "label": "#9a968c",     # printed shell text (titles, key hints)
        "key": "#b04578",       # action-bar letters wear the A/B button magenta
        "sil_day": "#0f380f", "sil_night": "#d8e8a0",
        "heart": "#b04578", "energy": "#5c5ab8", "mood": "#8a86c0", "life": "#6f8f26", "coin": "#b0a86a",
        "weather": {"rain": ("#1a3020", 0.30), "snow": ("#e0e8c8", 0.26), "cloud": ("#3a4a28", 0.18)},
        "void": "#0f380f", "flash": ("#e0f0c0", "#0f380f", "#d8e8a0"),
        "bg_ramp": ("#0f380f", "#306230", "#8bac0f", "#9bbc0f"),   # the 4 DMG shades, dark -> light
        "phases": {"dawn": ("#1a4418", "#a8c83a"), "day": ("#0f380f", "#9bbc0f"),
                   "dusk": ("#3a3a10", "#a8a838"), "night": ("#7aa060", "#142810")},
    },
    "paper": {
        "on": "#2a2620", "bg": "#efe9dc", "mid": "#8a8274",
        "accent": "#a04a2a", "pos": "#3a6a8a", "neg": "#a03a2a", "border": "#b8ac97",
        "sil_day": "#2a2620", "sil_night": "#f4efe4",
        "heart": "#a04a2a", "energy": "#3a6a8a", "mood": "#7a5a92", "life": "#567a68", "coin": "#967a2a",
        "weather": {"rain": ("#3a4450", 0.25), "snow": ("#f4f0e6", 0.30), "cloud": ("#6a655c", 0.16)},
        "void": "#000000", "flash": ("#ffffff", "#2a2620", "#faf6ec"),
        "phases": {"dawn": ("#332e26", "#f4eee0"), "day": ("#2a2620", "#efe9dc"),
                   "dusk": ("#463a2c", "#e6dcc8"), "night": ("#9a948a", "#262218")},
    },
    "sakura": {
        "on": "#f0b8c8", "bg": "#241820", "mid": "#8a5a6c",
        "accent": "#ff8a5a", "pos": "#8ac8e8", "neg": "#ff6a6a", "border": "#4a2a3a",
        "sil_day": "#2a1a24", "sil_night": "#ffd0dc",
        "heart": "#ff7a8a", "energy": "#8ac8e8", "mood": "#c89ae8", "life": "#7ad0b0", "coin": "#f0c86a",
        "weather": {"rain": ("#1a1428", 0.34), "snow": ("#f0dce4", 0.26), "cloud": ("#32222c", 0.20)},
        "void": "#000000", "flash": ("#ffe8f0", "#241820", "#f8d8e4"),
        "phases": {"dawn": ("#ffc8d8", "#2a1c26"), "day": ("#f0b8c8", "#241820"),
                   "dusk": ("#f0a878", "#241410"), "night": ("#9a7484", "#140c12")},
    },
    "ocean": {
        "on": "#7fd8d0", "bg": "#0a1e22", "mid": "#3f7a78",
        "accent": "#f0a05a", "pos": "#8ab8f0", "neg": "#f07a5a", "border": "#1c3a3e",
        "sil_day": "#0f2a2e", "sil_night": "#c8f0e8",
        "heart": "#f07a6a", "energy": "#6ac8e0", "mood": "#9a9ae8", "life": "#5ad0a0", "coin": "#e8c86a",
        "weather": {"rain": ("#06141e", 0.36), "snow": ("#c0dcd8", 0.26), "cloud": ("#0e2a30", 0.22)},
        "void": "#000000", "flash": ("#e0f8f4", "#0a1e22", "#c8ece6"),
        "phases": {"dawn": ("#9ae0d8", "#0e262a"), "day": ("#7fd8d0", "#0a1e22"),
                   "dusk": ("#d0a068", "#14201e"), "night": ("#4a8a84", "#05130f")},
    },
}
_DEFAULT = "grey"
_ORDER = list(THEMES)
_current = _DEFAULT

_NAMES = ("LCD_ON", "LCD_BG", "MID", "INK", "INK_B", "DIM", "SEL", "ACCENT",
          "POS", "NEG", "BORDER", "SIL_DAY", "SIL_NIGHT", "PHASE_PALETTE",
          "HEART", "ENERGY", "MOOD", "LIFE", "COIN", "VOID", "FLASH",
          "BEZEL", "SHELL", "LABEL", "KEY")
# (the hand-maintained _SCREEN_MODULES registry is gone -- apply() discovers
# palette-bound modules from sys.modules; hardening 2026-07-05)

_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}

# Static declarations of the palette names so linters/type-checkers can see them.
# apply(_DEFAULT) runs at import (bottom of file) and overwrites these with the live
# theme via globals().update(_derive(...)); they are never actually the empties below.
LCD_ON = LCD_BG = MID = INK = INK_B = DIM = SEL = ACCENT = POS = NEG = BORDER = ""
SIL_DAY = SIL_NIGHT = HEART = ENERGY = MOOD = LIFE = COIN = VOID = ""
BEZEL = SHELL = LABEL = KEY = ""
FLASH: tuple = ("", "", "")
PHASE_PALETTE: dict = {}
WEATHER: dict = {}


def _derive(t):
    on, bg, mid = t["on"], t["bg"], t["mid"]
    return {
        "LCD_ON": on, "LCD_BG": bg, "MID": mid,
        "INK": f"{on} on {bg}", "INK_B": f"bold {on} on {bg}",
        "DIM": f"{mid} on {bg}", "SEL": f"bold {bg} on {on}",
        "ACCENT": t["accent"], "POS": t["pos"], "NEG": t["neg"], "BORDER": t["border"],
        "SIL_DAY": t["sil_day"], "SIL_NIGHT": t["sil_night"], "PHASE_PALETTE": t["phases"],
        "HEART": t["heart"], "ENERGY": t["energy"], "MOOD": t["mood"],
        "LIFE": t["life"], "COIN": t["coin"], "WEATHER": t["weather"],
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


_BG_QUANT: dict = {}         # (theme, frame) -> dithered frame memo
_BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def themed_bg(frame):
    """Background art under the active theme: full colour normally; a theme
    that declares `bg_ramp` (gameboy: the 4 DMG shades) gets the frame
    ORDERED-DITHERED onto the ramp -- Bayer 4x4, the way real DMG ports
    rendered continuous art.  (The first cut was flat luminance bands: large
    muddy zones -- Joel 2026-07-05.)  Frame-level and memoized, and
    render._paint_cells is the one caller, so weather tints, cross-fades and
    lightning blends all inherit the palette."""
    ramp = THEMES[_current].get("bg_ramp")
    if not ramp or not frame:
        return frame
    key = (_current, tuple(frame))
    v = _BG_QUANT.get(key)
    if v is None:
        if len(_BG_QUANT) > 512:              # cross-fades mint transient frames
            _BG_QUANT.clear()
        v = _dither_frame(frame, ramp)
        _BG_QUANT[key] = v
    return v


def sprite_halo():
    """The 1px outline shade sprites wear over ramp-quantized art -- the pet's
    silhouette ink IS the darkest ramp shade, so it vanished into dark dithered
    regions (Joel 2026-07-05: 'background is showing the same colors as the
    mon').  GB games kept sprites readable on busy 4-shade backgrounds exactly
    this way.  The lightest ramp shade; None on full-colour themes."""
    ramp = THEMES[_current].get("bg_ramp")
    return ramp[-1] if ramp else None


def _dither_frame(frame, ramp):
    """Contrast-stretch the frame's luminance to the full ramp, then Bayer
    4x4 ordered dither.  ABSOLUTE luminance wasted the palette -- most art is
    bright, so whole frames collapsed into the top two shades and the detail
    vanished; GB art was hand-authored to span all four, and the per-frame
    stretch is the automated equivalent (2nd..98th percentile, with a
    near-uniform guard so a flat frame doesn't amplify noise)."""
    n1 = len(ramp) - 1
    strip = [c[1:] for c in ramp]             # bare 6-hex cells for row concat
    lums = [[(299 * int(row[x:x + 2], 16) + 587 * int(row[x + 2:x + 4], 16)
              + 114 * int(row[x + 4:x + 6], 16)) / 255000.0
             for x in range(0, len(row), 6)] for row in frame]
    flat = sorted(v for r in lums for v in r)
    lo = flat[int(0.02 * (len(flat) - 1))]
    hi = flat[int(0.98 * (len(flat) - 1))]
    span = hi - lo
    if span < 0.08:                           # near-uniform frame: absolute mapping
        lo, span = 0.0, 1.0
    out = []
    for y, lrow in enumerate(lums):
        br = _BAYER[y & 3]
        cells = []
        for x, lum in enumerate(lrow):
            t = (lum - lo) / span
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            idx = int(t * n1 + (br[x & 3] + 0.5) / 16)
            cells.append(strip[n1 if idx > n1 else idx])
        out.append("".join(cells))
    return out


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



def _wcat(weather):
    if weather in _RAIN:
        return "rain"
    if weather in _SNOW:
        return "snow"
    if weather == "Cloudy":
        return "cloud"
    return None


def blend_frame(frame, hexcol, a):
    """Blend a full-colour frame (rows of 6-hex-char cells) toward `hexcol` by
    alpha `a`.  Shared by the weather tints and the lightning flash."""
    tr, tg, tb = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    out = []
    for row in frame:
        cells = []
        for i in range(0, len(row), 6):
            r = int(row[i:i + 2], 16); g = int(row[i + 2:i + 4], 16); b = int(row[i + 4:i + 6], 16)
            cells.append("%02x%02x%02x" % (int(r + (tr - r) * a), int(g + (tg - g) * a), int(b + (tb - b) * a)))
        out.append("".join(cells))
    return out


def weather_tint(frame, weather):
    """Blend a habitat background frame toward the active theme's weather tint
    (rain/snow/cloud). `frame` is a list of rows of 6-hex-char cells; returns a
    new tinted frame (or the original when the weather is clear)."""
    spec = WEATHER.get(_wcat(weather)) if frame else None
    if not spec:
        return frame
    return blend_frame(frame, *spec)


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
