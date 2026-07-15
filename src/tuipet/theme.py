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
        "weather": {"rain": ("#2e3a4a", 0.30), "snow": ("#d6dee6", 0.26), "cloud": ("#5a5e62", 0.09)},
        "void": "#000000", "flash": ("#f2f6fa", "#1a2026", "#e8eef2"),
        "phases": {"dawn": ("#33363a", "#d2d5d8"), "day": ("#2b2e31", "#c6c9cc"),
                   "dusk": ("#39352f", "#bdb8b2"), "night": ("#9aa0a6", "#23262a")},
    },
    "mono": {
        "on": "#e8e8e8", "bg": "#0c0c0c", "mid": "#808080",
        "accent": "#d05a3a", "pos": "#7fa8d8", "neg": "#d05a3a", "border": "#333333",
        "sil_day": "#101010", "sil_night": "#f0f0f0",
        "heart": "#d8d8d8", "energy": "#b8b8b8", "mood": "#a8a8a8", "life": "#c8c8c8", "coin": "#e8e8e8",
        "weather": {"rain": ("#1c1c1c", 0.32), "snow": ("#dcdcdc", 0.26), "cloud": ("#383838", 0.09)},
        "void": "#000000", "flash": ("#ffffff", "#0c0c0c", "#e8e8e8"),
        "phases": {"dawn": ("#f0f0f0", "#141414"), "day": ("#e8e8e8", "#0c0c0c"),
                   "dusk": ("#e0c0a0", "#0c0a08"), "night": ("#9a9a9a", "#050505")},
    },
    "amber": {
        "on": "#ffb000", "bg": "#1a1206", "mid": "#9a6b18",
        "accent": "#ff6a3a", "pos": "#8fd0ff", "neg": "#ff6a3a", "border": "#3a2a0c",
        "sil_day": "#2a1c06", "sil_night": "#ffd877",
        "heart": "#ff7a3a", "energy": "#ffb000", "mood": "#e0923a", "life": "#ffc24a", "coin": "#ffd877",
        "weather": {"rain": ("#241a0c", 0.34), "snow": ("#ece0c8", 0.26), "cloud": ("#2e2410", 0.1)},
        "void": "#000000", "flash": ("#ffe8b0", "#1a1206", "#ffd890"),
        "phases": {"dawn": ("#ffc23a", "#160f05"), "day": ("#ffb000", "#1a1206"),
                   "dusk": ("#ff8a3a", "#1a0f04"), "night": ("#a8741a", "#0d0903")},
    },
    "midnight": {
        "on": "#a9c8ee", "bg": "#101826", "mid": "#5d7491",
        "accent": "#e0884a", "pos": "#7fb0e0", "neg": "#e06a5a", "border": "#2a3850",
        "sil_day": "#16202e", "sil_night": "#cfe0f5",
        "heart": "#e0884a", "energy": "#6fb0e0", "mood": "#9a8fe0", "life": "#5fc7b0", "coin": "#e0c060",
        "weather": {"rain": ("#0a1626", 0.36), "snow": ("#c4d8f0", 0.26), "cloud": ("#16223a", 0.11)},
        "void": "#000000", "flash": ("#dce8f8", "#101826", "#c8d8f0"),
        "phases": {"dawn": ("#b9d2f0", "#15202f"), "day": ("#a9c8ee", "#101826"),
                   "dusk": ("#d0a070", "#181420"), "night": ("#6d86a8", "#0a0f18")},
    },
    # the classic 4-shade DMG pea-soup LCD (the default stays grey; this is
    # an option).  NB the v0.2.284 putty-shell chrome experiment was REVERTED
    # (Joel 2026-07-05: "this looks bad") -- gameboy rides the fallbacks.
    "gameboy": {
        "on": "#0f380f", "bg": "#9bbc0f", "mid": "#306230",
        "accent": "#7a3a22", "pos": "#2a5a8a", "neg": "#8a3a2a", "border": "#4a5a28",
        "sil_day": "#0f380f", "sil_night": "#d8e8a0",
        "heart": "#8a4a2a", "energy": "#2a6a8a", "mood": "#6a4a8a", "life": "#306230", "coin": "#8a7a1a",
        "weather": {"rain": ("#1a3020", 0.30), "snow": ("#e0e8c8", 0.26), "cloud": ("#3a4a28", 0.09)},
        "void": "#0f380f", "flash": ("#e0f0c0", "#0f380f", "#d8e8a0"),
        # GB layering (redo 2026-07-05: 4-shade backgrounds ATE the sprites --
        # "their blending into the background"): backgrounds get the LIGHT
        # three shades only; the darkest DMG green belongs to sprites alone,
        # so the mon is always the darkest thing on the LCD
        "bg_ramp": ("#306230", "#8bac0f", "#9bbc0f"),
        "phases": {"dawn": ("#1a4418", "#a8c83a"), "day": ("#0f380f", "#9bbc0f"),
                   "dusk": ("#3a3a10", "#a8a838"), "night": ("#7aa060", "#142810")},
    },
    "paper": {
        "on": "#2a2620", "bg": "#efe9dc", "mid": "#8a8274",
        "accent": "#a04a2a", "pos": "#3a6a8a", "neg": "#a03a2a", "border": "#b8ac97",
        "sil_day": "#2a2620", "sil_night": "#f4efe4",
        "heart": "#a04a2a", "energy": "#3a6a8a", "mood": "#7a5a92", "life": "#567a68", "coin": "#967a2a",
        "weather": {"rain": ("#3a4450", 0.25), "snow": ("#f4f0e6", 0.30), "cloud": ("#6a655c", 0.08)},
        "void": "#000000", "flash": ("#ffffff", "#2a2620", "#faf6ec"),
        # paper layering (Joel 2026-07-12: "apply this to the paper theme --
        # white instead of green"): backgrounds get the light ink-wash trio,
        # the near-black ink stays sprite-only, same law as gameboy
        "bg_ramp": ("#8a8274", "#d5cdbb", "#efe9dc"),
        "phases": {"dawn": ("#332e26", "#f4eee0"), "day": ("#2a2620", "#efe9dc"),
                   "dusk": ("#463a2c", "#e6dcc8"), "night": ("#9a948a", "#262218")},
    },
    "sakura": {
        "on": "#f0b8c8", "bg": "#241820", "mid": "#8a5a6c",
        "accent": "#ff8a5a", "pos": "#8ac8e8", "neg": "#ff6a6a", "border": "#4a2a3a",
        "sil_day": "#2a1a24", "sil_night": "#ffd0dc",
        "heart": "#ff7a8a", "energy": "#8ac8e8", "mood": "#c89ae8", "life": "#7ad0b0", "coin": "#f0c86a",
        "weather": {"rain": ("#1a1428", 0.34), "snow": ("#f0dce4", 0.26), "cloud": ("#32222c", 0.1)},
        "void": "#000000", "flash": ("#ffe8f0", "#241820", "#f8d8e4"),
        "phases": {"dawn": ("#ffc8d8", "#2a1c26"), "day": ("#f0b8c8", "#241820"),
                   "dusk": ("#f0a878", "#241410"), "night": ("#9a7484", "#140c12")},
    },
    "ocean": {
        "on": "#7fd8d0", "bg": "#0a1e22", "mid": "#3f7a78",
        "accent": "#f0a05a", "pos": "#8ab8f0", "neg": "#f07a5a", "border": "#1c3a3e",
        "sil_day": "#0f2a2e", "sil_night": "#c8f0e8",
        "heart": "#f07a6a", "energy": "#6ac8e0", "mood": "#9a9ae8", "life": "#5ad0a0", "coin": "#e8c86a",
        "weather": {"rain": ("#06141e", 0.36), "snow": ("#c0dcd8", 0.26), "cloud": ("#0e2a30", 0.11)},
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


_BG_QUANT: dict = {}         # (theme, frame) -> quantized frame memo


def themed_bg(frame):
    """Background art under the active theme: full colour normally; a theme
    that declares `bg_ramp` (gameboy: the light DMG shades; paper: the ink-
    wash whites) gets the frame clustered onto the ramp as CLEAN SHAPES --
    per-frame colour clustering with a majority-vote smoothing pass, so
    scenery reads like hand-tiled GB art.  (The redo history, all Joel:
    flat absolute bands = mud; Bayer dither = static at 40x24 -- "it looks
    like garbage" [2026-07-05]; luminance banding = hue-blind flattening --
    "some backgrounds look like shit" [2026-07-12].)  Frame-level and
    memoized; render._paint_cells is the one caller, so weather tints,
    cross-fades and lightning blends all inherit the palette."""
    ramp = THEMES[_current].get("bg_ramp")
    if not ramp or not frame:
        return frame
    key = (_current, tuple(frame))
    v = _BG_QUANT.get(key)
    if v is None:
        if len(_BG_QUANT) > 512:              # cross-fades mint transient frames
            _BG_QUANT.clear()
        v = _quant_frame(frame, ramp)
        _BG_QUANT[key] = v
    return v


def _quant_frame(frame, ramp):
    """Deterministic per-frame COLOUR clustering onto the ramp (redo
    2026-07-12).  The old luminance banding was hue-blind: features that
    differ in colour but not brightness merged into one flat shade (the
    desert\'s dunes vs its sky, digicoreDa\'s dark core vs its blue bricks),
    and its contrast stretch amplified near-flat texture noise into random
    blotches.  Now: k-means (k = ramp size) in RGB, seeded at luminance
    percentiles so runs are stable, finds the frame\'s actual colour
    structure; clusters whose centres nearly coincide MERGE (a flat frame
    renders flat, not blotchy); groups rank dark-to-light onto the ramp --
    a luminance near-tie goes to the group sitting higher on screen, so
    skies read light (the GB idiom) -- and the 3x3 majority vote on the
    shade indices keeps the chunky authored look."""
    n = len(ramp)
    h = len(frame)
    w = len(frame[0]) // 6
    pts = []
    for row in frame:
        for x in range(0, w * 6, 6):
            pts.append((int(row[x:x + 2], 16), int(row[x + 2:x + 4], 16),
                        int(row[x + 4:x + 6], 16)))

    def lum(c):
        return (299 * c[0] + 587 * c[1] + 114 * c[2]) / 255000.0

    # deterministic k-means, farthest-point seeded: hue-diverse starts even
    # when luminance is narrow (percentile-of-luminance seeds collapsed the
    # savanna/underwater scenes to one flat shade -- same-brightness hues
    # need seats too)
    def d2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2

    fit = pts[::4] if len(pts) >= 4 * n else pts   # centres fit on a sample --
    mean = (sum(p[0] for p in fit) / len(fit),     # cross-fades quantize a fresh
            sum(p[1] for p in fit) / len(fit),     # transient frame every tick
            sum(p[2] for p in fit) / len(fit))
    seeds = [max(fit, key=lambda p: d2(p, mean))]
    while len(seeds) < n:
        seeds.append(max(fit, key=lambda p: min(d2(p, q) for q in seeds)))
    centers = [tuple(float(v) for v in q) for q in seeds]
    for _ in range(10):
        sums = [[0.0, 0.0, 0.0, 0] for _ in range(n)]
        for p in fit:
            j = min(range(n), key=lambda k: d2(p, centers[k]))
            s_ = sums[j]
            s_[0] += p[0]; s_[1] += p[1]; s_[2] += p[2]; s_[3] += 1
        moved = 0.0
        for j, (r, g, b, cnt) in enumerate(sums):
            if not cnt:
                continue                     # empty seat: parked, excluded below
            c = (r / cnt, g / cnt, b / cnt)
            moved += sum(abs(c[i] - centers[j][i]) for i in range(3))
            centers[j] = c
        if moved < 1.0:
            break
    assign = [min(range(n), key=lambda k: d2(p, centers[k])) for p in pts]
    counts = [0] * n
    for j in assign:
        counts[j] += 1
    # a farthest-point seed can be a lone outlier pixel: a cluster under 1%
    # of the frame is noise, not a shape -- fold it into its nearest neighbour
    floor = max(4, len(pts) // 100)
    live = [j for j in range(n) if counts[j]]
    for j in range(n):
        if counts[j] and counts[j] < floor and len(live) > 1:
            near = min((k for k in live if k != j),
                       key=lambda k: d2(centers[j], centers[k]))
            for i, a in enumerate(assign):
                if a == j:
                    assign[i] = near
            counts[near] += counts[j]
            counts[j] = 0
            live.remove(j)

    # merge near-coincident clusters: ~10/channel is texture noise, not shape
    MERGE = 30.0
    root = list(range(n))

    def find(a):
        while root[a] != a:
            a = root[a]
        return a

    for a in range(n):
        for b in range(a + 1, n):
            if not counts[a] or not counts[b]:
                continue
            d = sum((centers[a][i] - centers[b][i]) ** 2 for i in range(3)) ** 0.5
            if d < MERGE:
                root[find(b)] = find(a)

    rowsum = [0] * n
    for i, j in enumerate(assign):
        rowsum[j] += i // w
    groups = {}
    for j in range(n):
        if counts[j]:
            groups.setdefault(find(j), []).append(j)
    ginfo = []                               # [members, luma, mean row, size]
    for members in groups.values():
        cnt = sum(counts[j] for j in members)
        gl = sum(lum(centers[j]) * counts[j] for j in members) / cnt
        ry = sum(rowsum[j] for j in members) / cnt
        ginfo.append([members, gl, ry, cnt])
    ginfo.sort(key=lambda g: g[1])
    for i in range(len(ginfo) - 1):          # sky idiom: on a luma near-tie the
        a, b = ginfo[i], ginfo[i + 1]        # group sitting HIGHER on screen
        if b[1] - a[1] < 0.05 and a[2] < b[2]:   # takes the lighter shade
            ginfo[i], ginfo[i + 1] = b, a

    m = len(ginfo)
    if max(g[3] for g in ginfo) > 0.60 * len(pts):
        # a flat field with accents (one colour owns the frame): every group
        # sits at its ABSOLUTE lightness and groups may share a shade -- a
        # near-flat frame renders flat.  Rank-spreading here manufactured
        # contrast that is not in the art (digicoreVb, a faint white-on-white
        # glow, grew a dark ring).  Accent groups take the ADJACENT shade in
        # their true direction -- features stay visible (egg10Back, a door on
        # a wall), at neighbour contrast, never across the whole ramp
        fi = max(range(m), key=lambda i: ginfo[i][3])
        base = min(n - 1, round(ginfo[fi][1] * (n - 1)))
        slots = [max(0, min(n - 1, base + (1 if g[1] > ginfo[fi][1] else -1)))
                 for g in ginfo]
        slots[fi] = base
    elif m >= n:                             # balanced scenery: full-span rank
        slots = list(range(n))
    else:                                    # fewer shapes than shades: place by
        slots = [min(n - 1, round(g[1] * (n - 1))) for g in ginfo]   # absolute luma,
        for i in range(1, m):                                        # keep distinct
            slots[i] = max(slots[i], slots[i - 1] + 1)
        over = slots[-1] - (n - 1)
        if over > 0:
            slots = [max(0, s_ - over) for s_ in slots]
            for i in range(1, m):
                slots[i] = max(slots[i], slots[i - 1] + 1)
    slot_of = {}
    for (members, _, _, _), sl in zip(ginfo, slots):
        for j in members:
            slot_of[j] = sl

    idx = [[slot_of[assign[y * w + x]] for x in range(w)] for y in range(h)]
    strip = [c[1:] for c in ramp]            # bare 6-hex cells for row concat
    out = []
    for y in range(h):                       # 3x3 majority vote: chunky, authored
        cells = []
        for x in range(w):
            votes = [0] * n
            for yy in range(max(0, y - 1), min(h, y + 2)):
                for xx in range(max(0, x - 1), min(w, x + 2)):
                    votes[idx[yy][xx]] += 1
            best = max(range(n), key=lambda i: (votes[i], i == idx[y][x]))
            cells.append(strip[best])
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


# Canon BackgroundAnim.getBackgroundTint's PHASE component: the precip frame is
# ALSO tinted by the time of day -- changeColor(red, 0, blue, alpha) with
# Morning blue=80, the sunset hour red=60, and Night alpha 40->80 (an extra 40
# of black).  We dropped this when the per-theme weather tints came in, so the
# shared precip frame (index 4, drawn day-bright in every sheet) rendered at
# full daylight at night: every Drizzling<->Cloudy roll (10s cadence, ~21
# frame swaps a game day on Plains) hard-flipped the night scene to a day one
# and back -- "backgrounds keep going back and forth between night and day"
# (background audit 2026-07-15).  The theme weather tint stays as the base
# gloom (canon's flat alpha-40, themed); these compose ON TOP, precip only --
# canon gives Cloudy no phase mod (it shows the normal time-of-day frame).
_PHASE_TINT = {"dawn": ("#000050", 40 / 255),    # Morning: blue=80 at alpha 40
               "dusk": ("#3c0000", 40 / 255),    # isSunset: red=60 at alpha 40
               "night": ("#000000", 40 / 255)}   # Night: alpha 40 -> 80


def weather_tint(frame, weather, phase="day"):
    """Blend a habitat background frame toward the active theme's weather tint
    (rain/snow/cloud), then canon's time-of-day precip tint on top. `frame` is
    a list of rows of 6-hex-char cells; returns a new tinted frame (or the
    original when the weather is clear)."""
    cat = _wcat(weather) if frame else None
    spec = WEATHER.get(cat) if cat else None
    if not spec:
        return frame
    frame = blend_frame(frame, *spec)
    if cat in ("rain", "snow"):
        pspec = _PHASE_TINT.get(phase)
        if pspec:
            frame = blend_frame(frame, *pspec)
    return frame


# --- the cloudy-night frame (background rebuild 2026-07-15) -------------------
# The sheets ship ONE overcast frame (index 4) and it is drawn day-bright, so
# every clouded night wore a daytime sky -- "it looks like day cloudy, because
# thats all we got" (Joel).  Rather than tint around it, each sheet gets a
# DERIVED cloudy-night frame built from its own pixels, no hand-drawn art:
#
#   * ground rows  = the night frame verbatim (hills, town lights, lava);
#   * the sky band = the overcast frame's cloud texture posterized to three
#     dark tones mixed from THIS sheet's night-sky colour (so a Plains
#     overcast stays navy and a Volcano one stays ember-warm);
#   * the moon and stars are covered -- that is what an overcast night does.
#
# The horizon is read off the DAY+DUSK frames (terrain geometry is identical
# across frames 0-3): a pixel is sky only when both agree it sits in the flat
# sky field (the dusk vote splits the sea from the sky -- same blue by day,
# only the sky goes sunset-orange), or when it is bright in both (the white
# day clouds).  A sheet qualifies only if its night sky carries ISOLATED
# bright dots -- real stars; a lit window is a bright REGION -- so City and
# Underwater (no open sky) return None and keep their plain night frame.
_NIGHT_CLOUDS = {}                 # sheet key -> derived frame | None
_NC_GRAY = (150, 155, 165)         # storm gray the tones lean toward


def _cell(fr, x, y):
    row = fr[y]
    return (int(row[x * 6:x * 6 + 2], 16), int(row[x * 6 + 2:x * 6 + 4], 16),
            int(row[x * 6 + 4:x * 6 + 6], 16))


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _cdist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _build_night_clouds(frames):
    day, dusk, night, prec = frames[1], frames[2], frames[3], frames[4]
    W, H = len(day[0]) // 6, len(day)
    pix = sorted((_cell(night, x, y) for y in range(3) for x in range(W)),
                 key=_luma)
    dim = pix[:max(1, int(len(pix) * 0.6))]    # the flat sky, stars excluded
    nsky = tuple(sum(c[i] for c in dim) / len(dim) for i in range(3))

    def isdot(x, y):               # a star: bright dot on a darker field
        c = _cell(night, x, y)
        if _luma(c) <= _luma(nsky) + 55:
            return False
        return sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)
                   and 0 <= x + dx < W and 0 <= y + dy < H
                   and _luma(_cell(night, x + dx, y + dy)) < _luma(c) - 40) >= 4

    if sum(isdot(x, y) for y in range(int(H * 0.4)) for x in range(W)) < 3:
        return None                # no starfield -> no open sky to cloud over
    dref = tuple(sum(_cell(day, x, y)[i] for y in range(2) for x in range(W))
                 / (2 * W) for i in range(3))
    uref = tuple(sum(_cell(dusk, x, y)[i] for y in range(2) for x in range(W))
                 / (2 * W) for i in range(3))

    def is_sky(x, y):
        d, u = _cell(day, x, y), _cell(dusk, x, y)
        return ((_cdist(d, dref) < 110 and _cdist(u, uref) < 110)
                or (_luma(d) > _luma(dref) + 30 and _luma(u) > _luma(uref) - 15))

    cap = int(H * 0.8)
    raw = []
    for x in range(W):
        y = 0
        while y < cap and is_sky(x, y):
            y += 1
        raw.append(y)
    hor = [sorted(raw[max(0, x - 2):x + 3])[len(raw[max(0, x - 2):x + 3]) // 2]
           for x in range(W)]      # median-of-5: no single-column streaks

    def tone(k, g):                # night-sky hue stepped up, pulled to gray
        return tuple(min(255.0, nsky[i] * k + (_NC_GRAY[i] - nsky[i] * k) * g)
                     for i in range(3))

    # The first cut snapped the cloud texture into three flat tones and the
    # blobs came out hard-edged ("they look sharo and edgy" -- Joel
    # 2026-07-15).  The sheets themselves are soft anti-aliased art, so the
    # clouds now match: the overcast frame's brightness field gets one 3x3
    # box-blur pass (rounds the masses, kills single-pixel jaggies), then
    # maps CONTINUOUSLY onto the dark->light ramp between the same two
    # endpoint tones.
    lum = [[_luma(_cell(prec, x, y)) for x in range(W)] for y in range(H)]
    blur = [[0.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            s = n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if 0 <= x + dx < W and 0 <= y + dy < H:
                        s += lum[y + dy][x + dx]
                        n += 1
            blur[y][x] = s / n
    vals = sorted(blur[y][x] for y in range(6) for x in range(W))
    lo, hi = vals[int(len(vals) * 0.05)], vals[int(len(vals) * 0.95)]
    A, B = tone(1.0, 0.22), tone(1.85, 0.5)
    out = []
    for y in range(H):
        cells = []
        for x in range(W):
            if y < hor[x]:
                t = max(0.0, min(1.0, (blur[y][x] - lo) / max(1.0, hi - lo)))
                c = tuple(A[i] + (B[i] - A[i]) * t for i in range(3))
                cells.append("%02x%02x%02x" % tuple(int(v) for v in c))
            else:
                cells.append(night[y][x * 6:(x + 1) * 6])
        out.append("".join(cells))
    return out


def night_cloud_frame(key, frames):
    """The sheet's derived cloudy-night frame (built once, cached), or None
    when the sheet has no open sky (City's wall, Underwater)."""
    if key not in _NIGHT_CLOUDS:
        _NIGHT_CLOUDS[key] = (_build_night_clouds(frames)
                              if frames and len(frames) > 4 else None)
    return _NIGHT_CLOUDS[key]


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
